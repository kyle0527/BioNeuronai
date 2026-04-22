"""
對話引擎 (Chat Engine)
======================
為 BioNeuronai 提供雙語（中文/英文）對話能力。

功能：
- 多輪對話記憶（ConversationHistory）
- 自動語言偵測（中文 / 英文 / 混合）
- 系統提示注入（交易顧問角色）
- 即時市場上下文注入（價格、指標、部位）
- HonestGenerator 過濾低信心/幻覺輸出
- 串流逐 token 輸出（generator）
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 資料結構
# ---------------------------------------------------------------------------

@dataclass
class ChatMessage:
    """單條訊息"""
    role: str          # "system" | "user" | "assistant"
    content: str
    language: str = "mixed"   # "zh" | "en" | "mixed"
    timestamp: float = field(default_factory=time.time)

    def to_prompt_str(self) -> str:
        role_map = {"system": "[系統]", "user": "[用戶]", "assistant": "[助手]"}
        prefix = role_map.get(self.role, f"[{self.role}]")
        return f"{prefix} {self.content}"


@dataclass
class ChatResponse:
    """對話回應"""
    text: str
    language: str
    confidence: float = 1.0
    market_context_used: bool = False
    stopped_reason: str = ""        # "" | "low_confidence" | "hallucination_detected" | "max_tokens"
    latency_ms: float = 0.0


@dataclass
class MarketContext:
    """注入對話的即時市場資料"""
    symbol: str = ""
    current_price: float = 0.0
    price_change_24h_pct: float = 0.0
    funding_rate: float = 0.0
    mark_price: float = 0.0
    open_interest: float = 0.0
    long_short_ratio: float = 0.0
    indicators: Dict[str, Any] = field(default_factory=dict)   # RSI, MACD, BB…
    position_side: str = ""       # "LONG" | "SHORT" | ""
    position_size: float = 0.0
    unrealized_pnl: float = 0.0

    def to_context_str(self, language: str = "zh") -> str:
        if not self.symbol:
            return ""
        if language == "en":
            lines = [f"[Market Context] {self.symbol}"]
            if self.current_price:
                lines.append(f"  Price: {self.current_price:,.4f} USDT  ({self.price_change_24h_pct:+.2f}% 24h)")
            if self.mark_price:
                lines.append(f"  Mark Price: {self.mark_price:,.4f}")
            if self.funding_rate:
                lines.append(f"  Funding Rate: {self.funding_rate:.4%}")
            if self.open_interest:
                lines.append(f"  Open Interest: {self.open_interest:,.0f}")
            if self.long_short_ratio:
                lines.append(f"  Long/Short Ratio: {self.long_short_ratio:.2f}")
            for k, v in self.indicators.items():
                lines.append(f"  {k}: {v}")
            if self.position_side:
                lines.append(
                    f"  Position: {self.position_side}  size={self.position_size:.4f}"
                    f"  uPnL={self.unrealized_pnl:+.2f} USDT"
                )
        else:
            lines = [f"[市場資訊] {self.symbol}"]
            if self.current_price:
                lines.append(f"  現價：{self.current_price:,.4f} USDT（24h {self.price_change_24h_pct:+.2f}%）")
            if self.mark_price:
                lines.append(f"  標記價格：{self.mark_price:,.4f}")
            if self.funding_rate:
                lines.append(f"  資金費率：{self.funding_rate:.4%}")
            if self.open_interest:
                lines.append(f"  未平倉量：{self.open_interest:,.0f}")
            if self.long_short_ratio:
                lines.append(f"  多空比：{self.long_short_ratio:.2f}")
            for k, v in self.indicators.items():
                lines.append(f"  {k}：{v}")
            if self.position_side:
                lines.append(
                    f"  持倉：{self.position_side}  數量={self.position_size:.4f}"
                    f"  未實現損益={self.unrealized_pnl:+.2f} USDT"
                )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 系統提示模板
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT_ZH = """你是 BioNeuronai 智能交易助理，專精於幣安 USDT 永續合約（USDT-M Futures）交易。

【角色與能力】
- 用繁體中文或英文回答（依使用者語言自動切換）
- 提供技術分析解讀（均線、MACD、RSI、布林通道等）
- 解釋幣安合約規則（槓桿、保證金、資金費率、清算機制）
- 分析交易信號，說明進出場邏輯與風險管理
- 討論策略執行細節（止損設置、倉位大小、R倍數）

【限制與免責】
- 所有內容僅供參考，不構成投資建議
- 期貨交易具有高風險，可能損失全部本金
- 若提供了即時市場資料，請以該資料為分析依據

【回答原則】
- 簡潔清晰，直接回答問題
- 不確定時明確說明不確定性
- 涉及風險時主動提示
"""

_SYSTEM_PROMPT_EN = """You are BioNeuronai's intelligent trading assistant, specializing in Binance USDT-M perpetual futures trading.

[Role & Capabilities]
- Respond in Traditional Chinese or English (auto-detect user language)
- Provide technical analysis interpretation (EMA, MACD, RSI, Bollinger Bands, etc.)
- Explain Binance futures rules (leverage, margin, funding rate, liquidation mechanics)
- Analyze trading signals with entry/exit logic and risk management
- Discuss strategy execution (stop-loss placement, position sizing, R-multiples)

[Limitations & Disclaimer]
- All content is for reference only and does not constitute investment advice
- Futures trading carries high risk and may result in total loss of capital
- When real-time market data is provided, base analysis on that data

[Response Principles]
- Be concise and direct
- Acknowledge uncertainty when unsure
- Proactively highlight risk when relevant
"""


# ---------------------------------------------------------------------------
# 對話歷史管理
# ---------------------------------------------------------------------------

class ConversationHistory:
    """多輪對話記憶，維護訊息視窗以避免超過 context 長度"""

    def __init__(self, max_turns: int = 20, max_chars: int = 4000):
        self.max_turns = max_turns
        self.max_chars = max_chars
        self.messages: List[ChatMessage] = []

    def add(self, role: str, content: str, language: str = "mixed") -> None:
        self.messages.append(ChatMessage(role=role, content=content, language=language))
        self._trim()

    def _trim(self) -> None:
        # 保留 system 訊息，其餘只保留最近 max_turns 輪
        system_msgs = [m for m in self.messages if m.role == "system"]
        other_msgs  = [m for m in self.messages if m.role != "system"]
        if len(other_msgs) > self.max_turns * 2:
            other_msgs = other_msgs[-(self.max_turns * 2):]
        self.messages = system_msgs + other_msgs

    def build_prompt(self) -> str:
        """將歷史訊息拼接為模型輸入字串"""
        parts = [m.to_prompt_str() for m in self.messages]
        prompt = "\n".join(parts) + "\n[助手]"
        # 若超過字元上限，從最早的非 system 訊息開始截斷
        while len(prompt) > self.max_chars and len(self.messages) > 2:
            non_sys = [i for i, m in enumerate(self.messages) if m.role != "system"]
            if non_sys:
                self.messages.pop(non_sys[0])
                parts = [m.to_prompt_str() for m in self.messages]
                prompt = "\n".join(parts) + "\n[助手]"
            else:
                break
        return prompt

    def clear(self) -> None:
        self.messages = [m for m in self.messages if m.role == "system"]

    def __len__(self) -> int:
        return len([m for m in self.messages if m.role != "system"])


# ---------------------------------------------------------------------------
# 語言偵測
# ---------------------------------------------------------------------------

def detect_language(text: str) -> str:
    """簡易語言偵測：返回 'zh' | 'en' | 'mixed'"""
    zh_chars = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', text))
    en_chars  = len(re.findall(r'[a-zA-Z]', text))
    total = zh_chars + en_chars
    if total == 0:
        return "mixed"
    zh_ratio = zh_chars / total
    if zh_ratio >= 0.6:
        return "zh"
    if zh_ratio <= 0.2:
        return "en"
    return "mixed"


# ---------------------------------------------------------------------------
# 主要對話引擎
# ---------------------------------------------------------------------------

class ChatEngine:
    """
    BioNeuronai 雙語對話引擎

    使用方式：
        engine = ChatEngine(model, tokenizer)
        response = engine.chat("現在 BTC 適合做多嗎？", market_ctx)
        for token in engine.stream_chat("解釋資金費率"):
            print(token, end="", flush=True)
    """

    def __init__(
        self,
        model: Any,                     # TinyLLM instance
        tokenizer: Any,                 # BilingualTokenizer or BPETokenizer
        max_new_tokens: int = 256,
        temperature: float = 0.8,
        top_p: float = 0.92,
        top_k: int = 50,
        repetition_penalty: float = 1.1,
        confidence_threshold: float = 0.4,
        max_turns: int = 20,
        language: str = "auto",         # "auto" | "zh" | "en"
    ) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.repetition_penalty = repetition_penalty
        self.confidence_threshold = confidence_threshold
        self.language = language

        self.history = ConversationHistory(max_turns=max_turns)
        self._inject_system_prompt("zh")    # 預設中文系統提示

        # 嘗試載入 HonestGenerator（可選）
        self._honest_gen: Optional[Any] = None
        try:
            from .honest_generation import HonestGenerator, HonestGenerationConfig
            cfg = HonestGenerationConfig(
                confidence_threshold=confidence_threshold,
                return_confidence=True,
                return_diagnostics=False,
            )
            self._honest_gen = HonestGenerator(model, tokenizer, cfg)
            logger.info("[ChatEngine] HonestGenerator 已啟用")
        except Exception as e:
            logger.warning(f"[ChatEngine] HonestGenerator 未啟用: {e}")

    # ------------------------------------------------------------------
    # 系統提示管理
    # ------------------------------------------------------------------

    def _inject_system_prompt(self, lang: str) -> None:
        prompt = _SYSTEM_PROMPT_ZH if lang != "en" else _SYSTEM_PROMPT_EN
        # 清除舊 system，插入新的
        self.history.messages = [m for m in self.history.messages if m.role != "system"]
        self.history.messages.insert(0, ChatMessage(role="system", content=prompt, language=lang))

    def set_language(self, lang: str) -> None:
        """手動設定回應語言：'zh' | 'en' | 'auto'"""
        self.language = lang
        if lang in ("zh", "en"):
            self._inject_system_prompt(lang)

    # ------------------------------------------------------------------
    # 語言解析
    # ------------------------------------------------------------------

    def _resolve_language(self, user_text: str) -> str:
        if self.language != "auto":
            return self.language
        detected = detect_language(user_text)
        return "en" if detected == "en" else "zh"

    # ------------------------------------------------------------------
    # 核心對話
    # ------------------------------------------------------------------

    def chat(
        self,
        user_message: str,
        market_ctx: Optional[MarketContext] = None,
    ) -> ChatResponse:
        """
        單輪對話（阻塞式）。

        Args:
            user_message: 使用者輸入（中文或英文）
            market_ctx: 可選的即時市場資料，若提供則自動注入上下文

        Returns:
            ChatResponse
        """
        t0 = time.time()
        lang = self._resolve_language(user_message)

        # 更新系統提示語言（auto 模式下依使用者語言切換）
        if self.language == "auto":
            self._inject_system_prompt(lang)

        # 組裝使用者訊息（可附加市場上下文）
        content = user_message
        ctx_used = False
        if market_ctx and market_ctx.symbol:
            ctx_str = market_ctx.to_context_str(lang)
            if ctx_str:
                content = f"{ctx_str}\n\n{user_message}"
                ctx_used = True

        self.history.add("user", content, lang)

        # 建立 prompt
        prompt = self.history.build_prompt()
        response_text, confidence, stopped_reason = self._generate(prompt)

        self.history.add("assistant", response_text, lang)
        latency = (time.time() - t0) * 1000

        return ChatResponse(
            text=response_text,
            language=lang,
            confidence=confidence,
            market_context_used=ctx_used,
            stopped_reason=stopped_reason,
            latency_ms=latency,
        )

    def stream_chat(
        self,
        user_message: str,
        market_ctx: Optional[MarketContext] = None,
    ) -> Generator[str, None, ChatResponse]:
        """
        串流對話，逐 token yield，最後 return ChatResponse。

        使用方式：
            gen = engine.stream_chat("你好")
            full = ""
            try:
                while True:
                    token = next(gen)
                    full += token
                    print(token, end="", flush=True)
            except StopIteration as e:
                response = e.value
        """
        t0 = time.time()
        lang = self._resolve_language(user_message)
        if self.language == "auto":
            self._inject_system_prompt(lang)

        content = user_message
        ctx_used = False
        if market_ctx and market_ctx.symbol:
            ctx_str = market_ctx.to_context_str(lang)
            if ctx_str:
                content = f"{ctx_str}\n\n{user_message}"
                ctx_used = True

        self.history.add("user", content, lang)
        prompt = self.history.build_prompt()

        # 逐 token 生成並 yield
        full_text = ""
        for token in self._stream_generate(prompt):
            full_text += token
            yield token

        self.history.add("assistant", full_text, lang)
        latency = (time.time() - t0) * 1000

        return ChatResponse(
            text=full_text,
            language=lang,
            confidence=1.0,
            market_context_used=ctx_used,
            stopped_reason="",
            latency_ms=latency,
        )

    def reset(self) -> None:
        """清除對話歷史（保留系統提示）"""
        self.history.clear()

    # ------------------------------------------------------------------
    # 內部生成方法
    # ------------------------------------------------------------------

    def _generate(self, prompt: str) -> tuple[str, float, str]:
        """
        使用 TinyLLM 生成回應。
        返回 (text, confidence, stopped_reason)
        """
        try:
            import torch

            input_ids = self.tokenizer.encode(
                prompt,
                max_length=1024,
                truncation=True,
            )
            if not isinstance(input_ids, torch.Tensor):
                input_ids = torch.tensor([input_ids], dtype=torch.long)
            if input_ids.dim() == 1:
                input_ids = input_ids.unsqueeze(0)

            device = next(self.model.parameters()).device
            input_ids = input_ids.to(device)

            # 使用 HonestGenerator（若可用）
            if self._honest_gen is not None:
                if hasattr(self._honest_gen, "generate_with_honesty"):
                    result = self._honest_gen.generate_with_honesty(
                        input_ids=input_ids,
                        max_length=self.max_new_tokens,
                        temperature=self.temperature,
                        top_k=self.top_k,
                        top_p=self.top_p,
                        repetition_penalty=self.repetition_penalty,
                    )
                    text = result.get("generated_text", "")
                    confidence = float(
                        result.get("overall_confidence", 1.0)
                    )
                    stopped_reason = str(result.get("stop_reason", ""))
                elif hasattr(self._honest_gen, "generate"):
                    result = self._honest_gen.generate(
                        input_ids=input_ids,
                        max_new_tokens=self.max_new_tokens,
                        temperature=self.temperature,
                        top_k=self.top_k,
                        top_p=self.top_p,
                        repetition_penalty=self.repetition_penalty,
                    )
                    text = result.get("text", "")
                    confidence = float(result.get("confidence", 1.0))
                    stopped_reason = str(result.get("stopped_reason", ""))
                else:
                    raise AttributeError(
                        "HonestGenerator 缺少 generate_with_honesty / generate 介面"
                    )
            else:
                with torch.no_grad():
                    output_ids = self.model.generate(
                        input_ids,
                        max_new_tokens=self.max_new_tokens,
                        temperature=self.temperature,
                        top_k=self.top_k,
                        top_p=self.top_p,
                        repetition_penalty=self.repetition_penalty,
                        do_sample=True,
                    )
                new_ids = output_ids[0, input_ids.shape[1]:]
                text = self.tokenizer.decode(new_ids.tolist())
                confidence = 1.0
                stopped_reason = ""

            text = self._clean_output(text)
            return text, confidence, stopped_reason

        except Exception as e:
            logger.error(f"[ChatEngine] 生成失敗: {e}")
            return "（生成失敗，請稍後再試）", 0.0, "error"

    def _stream_generate(self, prompt: str) -> Generator[str, None, None]:
        """逐 token 串流生成（無 HonestGenerator）"""
        try:
            import torch

            input_ids = self.tokenizer.encode(prompt, max_length=1024, truncation=True)
            if not isinstance(input_ids, torch.Tensor):
                input_ids = torch.tensor([input_ids], dtype=torch.long)
            if input_ids.dim() == 1:
                input_ids = input_ids.unsqueeze(0)

            device = next(self.model.parameters()).device
            input_ids = input_ids.to(device)

            generated = input_ids.clone()
            eos_id = self.tokenizer.special_token_ids.get("eos_token", None)

            with torch.no_grad():
                for _ in range(self.max_new_tokens):
                    logits = self.model(generated)
                    if isinstance(logits, tuple):
                        logits = logits[0]
                    next_logits = logits[:, -1, :] / max(self.temperature, 1e-8)

                    # Top-K
                    if self.top_k:
                        vals, _ = torch.topk(next_logits, self.top_k)
                        next_logits[next_logits < vals[:, -1:]] = float("-inf")

                    # Top-P
                    if self.top_p and self.top_p < 1.0:
                        probs = torch.softmax(next_logits, dim=-1)
                        sorted_probs, sorted_idx = torch.sort(probs, descending=True)
                        cumsum = torch.cumsum(sorted_probs, dim=-1)
                        mask = cumsum - sorted_probs > self.top_p
                        sorted_probs[mask] = 0.0
                        sorted_probs /= sorted_probs.sum(dim=-1, keepdim=True)
                        next_token = sorted_idx[0, torch.multinomial(sorted_probs[0], 1)]
                    else:
                        probs = torch.softmax(next_logits, dim=-1)
                        next_token = torch.multinomial(probs[0], 1)

                    next_token_id = next_token.item()
                    if eos_id is not None and next_token_id == eos_id:
                        break

                    generated = torch.cat(
                        [generated, torch.tensor([[next_token_id]], device=device)], dim=1
                    )
                    token_str = self.tokenizer.decode([next_token_id])
                    if token_str:
                        yield token_str

        except Exception as e:
            logger.error(f"[ChatEngine] 串流生成失敗: {e}")
            yield "（串流生成失敗）"

    @staticmethod
    def _clean_output(text: str) -> str:
        """移除提示詞殘留的 role 前綴"""
        for prefix in ("[系統]", "[用戶]", "[助手]", "[SYSTEM]", "[USER]", "[ASSISTANT]"):
            text = text.replace(prefix, "")
        return text.strip()


# ---------------------------------------------------------------------------
# 工廠函式
# ---------------------------------------------------------------------------

def create_chat_engine(
    model_path: Optional[str] = None,
    language: str = "auto",
    max_new_tokens: int = 256,
) -> Optional[ChatEngine]:
    """
    建立 ChatEngine 實例（自動載入模型與分詞器）。
    若模型不存在或 torch 未安裝，返回 None。
    """
    try:
        from .tiny_llm import load_llm
        from .bilingual_tokenizer import BilingualTokenizer

        tokenizer = BilingualTokenizer()

        # 嘗試載入分詞器詞彙
        default_tok_path = Path(__file__).parent.parent.parent / "model" / "tokenizer" / "vocab.json"
        if default_tok_path.exists():
            try:
                tokenizer = BilingualTokenizer.load(str(default_tok_path))
            except Exception:
                pass

        # ChatEngine 僅使用 TinyLLM 文字權重，不再混用交易主線 checkpoint。
        ckpt_path = Path(model_path) if model_path else (
            Path(__file__).parent.parent.parent / "model" / "tiny_llm_100m.pth"
        )
        if not ckpt_path.exists():
            logger.warning(f"[ChatEngine] 未找到 TinyLLM 權重 {ckpt_path}")
            return None

        model, _ = load_llm(str(ckpt_path), device="cpu")
        logger.info(f"[ChatEngine] TinyLLM 模型已從 {ckpt_path} 載入")

        model.eval()
        return ChatEngine(model, tokenizer, language=language, max_new_tokens=max_new_tokens)

    except ImportError as e:
        logger.warning(f"[ChatEngine] torch 未安裝，對話引擎不可用: {e}")
        return None
    except Exception as e:
        logger.error(f"[ChatEngine] 建立失敗: {e}")
        return None
