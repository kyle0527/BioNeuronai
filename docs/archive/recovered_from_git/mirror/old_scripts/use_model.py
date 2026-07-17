"""
專業模型使用工具
===============
完整的模型交互、評估和管理系統

功能：
- 多模型管理和切換
- 完整的對話系統
- 批次處理和並行化
- 性能評估和基準測試
- 生成質量分析
- 日誌和錯誤處理
- 配置管理
- 結果導出
"""

import torch
import json
from pathlib import Path
import sys
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import argparse

sys.path.insert(0, str(Path(__file__).parent / "src"))
from src.bioneuronai.tiny_llm import TinyLLM, TinyLLMConfig
from src.bioneuronai.bilingual_tokenizer import BilingualTokenizer


# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('model_usage.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class GenerationConfig:
    """生成配置"""
    max_new_tokens: int = 50
    temperature: float = 0.7
    top_k: int = 50
    top_p: float = 0.9
    repetition_penalty: float = 1.0
    do_sample: bool = True


@dataclass
class GenerationResult:
    """生成結果"""
    prompt: str
    output: str
    tokens_generated: int
    time_taken: float
    tokens_per_second: float
    model_version: str
    config: GenerationConfig
    timestamp: str


class ModelManager:
    """模型管理器 - 處理多模型加載和切換"""
    
    def __init__(self):
        self.models: Dict[str, Tuple[TinyLLM, BilingualTokenizer]] = {}
        self.current_model: Optional[str] = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"初始化模型管理器 - 設備: {self.device}")
    
    def load_model(self, model_path: str, name: Optional[str] = None) -> bool:
        """載入模型"""
        try:
            model_path_obj = Path(model_path)
            if not model_path_obj.exists():
                logger.error(f"模型路徑不存在: {model_path_obj}")
                return False
            
            name = name or model_path_obj.name
            
            logger.info(f"載入模型: {name} from {model_path_obj}")
            
            # 載入配置
            with open(model_path_obj / "config.json", 'r') as f:
                config_dict = json.load(f)
            
            config = TinyLLMConfig(
                vocab_size=config_dict["vocab_size"],
                max_seq_length=config_dict["max_position_embeddings"],
                embed_dim=config_dict["hidden_size"],
                num_heads=config_dict["num_attention_heads"],
                num_layers=config_dict["num_hidden_layers"],
            )
            
            # 載入模型
            model = TinyLLM(config)
            weights = torch.load(
                model_path_obj / "pytorch_model.bin",
                map_location=self.device
            )
            model.load_state_dict(weights)
            model.to(self.device)
            model.eval()
            
            # 載入分詞器
            tokenizer = BilingualTokenizer.load(str(model_path_obj / "tokenizer.pkl"))
            
            self.models[name] = (model, tokenizer)
            
            if self.current_model is None:
                self.current_model = name
            
            logger.info(f"✅ 模型載入成功: {name} ({model.count_parameters():,} 參數)")
            return True
            
        except Exception as e:
            logger.error(f"載入模型失敗: {e}")
            return False
    
    def switch_model(self, name: str) -> bool:
        """切換當前模型"""
        if name not in self.models:
            logger.error(f"模型不存在: {name}")
            return False
        
        self.current_model = name
        logger.info(f"切換到模型: {name}")
        return True
    
    def get_current_model(self) -> Tuple[TinyLLM, BilingualTokenizer]:
        """獲取當前模型"""
        if self.current_model is None:
            raise ValueError("沒有載入任何模型")
        
        return self.models[self.current_model]
    
    def list_models(self) -> List[str]:
        """列出所有已載入的模型"""
        return list(self.models.keys())


class ModelAssistant:
    """專業模型助手 - 完整的功能集"""
    
    def __init__(self, model_path="models/tiny_llm_en_zh_trained"):
        """初始化助手"""
        self.manager = ModelManager()
        self.generation_history: List[GenerationResult] = []
        self.default_config = GenerationConfig()
        
        # 載入默認模型
        success = self.manager.load_model(model_path, "default")
        if not success:
            raise RuntimeError(f"無法載入模型: {model_path}")
        
        logger.info("模型助手初始化完成")
    
    def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        return_metrics: bool = True
    ) -> GenerationResult:
        """生成文本並記錄完整信息"""
        
        if config is None:
            config = self.default_config
        
        model, tokenizer = self.manager.get_current_model()
        device = self.manager.device
        
        try:
            # 編碼
            ids = tokenizer.encode(prompt, add_special_tokens=False)
            if len(ids) > 20:
                ids = ids[:20]
                logger.warning(f"提示過長，截斷到20個token")
            
            input_tensor = torch.tensor([ids]).to(device)
            
            # 生成
            start_time = time.time()
            
            with torch.no_grad():
                output = model.generate(
                    input_tensor,
                    max_new_tokens=config.max_new_tokens,
                    temperature=config.temperature,
                    top_k=config.top_k,
                    top_p=config.top_p
                )
            
            time_taken = time.time() - start_time
            
            # 解碼
            result_text = tokenizer.decode(
                output[0].tolist(),
                skip_special_tokens=True
            )
            
            # 計算指標
            tokens_generated = output.shape[1] - input_tensor.shape[1]
            tokens_per_second = tokens_generated / time_taken if time_taken > 0 else 0
            
            # 創建結果
            result = GenerationResult(
                prompt=prompt,
                output=result_text,
                tokens_generated=tokens_generated,
                time_taken=time_taken,
                tokens_per_second=tokens_per_second,
                model_version=self.manager.current_model or "unknown",
                config=config,
                timestamp=datetime.now().isoformat()
            )
            
            # 記錄歷史
            self.generation_history.append(result)
            
            logger.info(f"生成完成 - {tokens_generated} tokens in {time_taken:.2f}s ({tokens_per_second:.2f} t/s)")
            
            return result
            
        except Exception as e:
            logger.error(f"生成失敗: {e}")
            raise
    
    def chat(self, prompt: str, config: Optional[GenerationConfig] = None) -> str:
        """簡單對話接口"""
        result = self.generate(prompt, config)
        
        print(f"\n{'='*60}")
        print(f"💬 輸入: {prompt}")
        print(f"🤖 輸出: {result.output}")
        print(f"⏱️  用時: {result.time_taken:.2f}s | 速度: {result.tokens_per_second:.2f} tokens/s")
        print(f"{'='*60}\n")
        
        return result.output
    
    def batch_generate(
        self,
        prompts: List[str],
        config: Optional[GenerationConfig] = None,
        show_progress: bool = True
    ) -> List[GenerationResult]:
        """批次生成"""
        results = []
        total = len(prompts)
        
        logger.info(f"開始批次生成 - 共 {total} 個輸入")
        
        for i, prompt in enumerate(prompts, 1):
            if show_progress:
                print(f"\n[{i}/{total}] 處理中...")
            
            result = self.generate(prompt, config)
            results.append(result)
            
            if show_progress:
                print(f"✓ 完成: {result.output[:50]}...")
        
        logger.info(f"批次生成完成 - {total} 個樣本")
        return results
    
    def interactive_mode(self):
        """交互對話模式"""
        print("\n" + "="*60)
        print("🤖 交互模式")
        print("="*60)
        print("命令:")
        print("  /help     - 顯示幫助")
        print("  /config   - 設置生成參數")
        print("  /stats    - 顯示統計信息")
        print("  /export   - 導出對話歷史")
        print("  /clear    - 清除歷史")
        print("  /quit     - 退出")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input = input("你: ").strip()
                
                if not user_input:
                    continue
                
                # 命令處理
                if user_input.startswith('/'):
                    if user_input == '/quit':
                        print("\n👋 再見！")
                        break
                    
                    elif user_input == '/help':
                        self._show_help()
                    
                    elif user_input == '/config':
                        self._configure_generation()
                    
                    elif user_input == '/stats':
                        self._show_stats()
                    
                    elif user_input == '/export':
                        self._export_history()
                    
                    elif user_input == '/clear':
                        self.generation_history.clear()
                        print("✅ 歷史已清除")
                    
                    else:
                        print("❌ 未知命令，輸入 /help 查看幫助")
                    
                    continue
                
                # 正常對話
                self.chat(user_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 再見！")
                break
            except Exception as e:
                logger.error(f"錯誤: {e}")
                print(f"❌ 錯誤: {e}\n")
    
    def benchmark(
        self,
        test_prompts: Optional[List[str]] = None,
        num_runs: int = 5
    ) -> Dict:
        """性能基準測試"""
        
        if test_prompts is None:
            test_prompts = [
                "你好",
                "Hello",
                "什麼是人工智慧",
                "What is machine learning",
            ]
        
        print(f"\n{'='*60}")
        print(f"🔬 性能基準測試")
        print(f"測試樣本: {len(test_prompts)}")
        print(f"重複次數: {num_runs}")
        print(f"{'='*60}\n")
        
        all_times = []
        all_tokens = []
        all_speeds = []
        
        for run in range(num_runs):
            print(f"運行 {run + 1}/{num_runs}...")
            
            for prompt in test_prompts:
                result = self.generate(prompt, return_metrics=True)
                all_times.append(result.time_taken)
                all_tokens.append(result.tokens_generated)
                all_speeds.append(result.tokens_per_second)
        
        # 統計
        avg_time = sum(all_times) / len(all_times)
        avg_tokens = sum(all_tokens) / len(all_tokens)
        avg_speed = sum(all_speeds) / len(all_speeds)
        
        results = {
            "total_runs": num_runs * len(test_prompts),
            "avg_time": avg_time,
            "avg_tokens": avg_tokens,
            "avg_speed": avg_speed,
            "min_time": min(all_times),
            "max_time": max(all_times),
            "device": self.manager.device
        }
        
        print(f"\n{'='*60}")
        print(f"📊 基準測試結果")
        print(f"{'='*60}")
        print(f"總運行次數: {results['total_runs']}")
        print(f"平均時間: {results['avg_time']:.3f}s")
        print(f"平均生成: {results['avg_tokens']:.1f} tokens")
        print(f"平均速度: {results['avg_speed']:.2f} tokens/s")
        print(f"時間範圍: {results['min_time']:.3f}s - {results['max_time']:.3f}s")
        print(f"設備: {results['device']}")
        print(f"{'='*60}\n")
        
        return results
    
    def evaluate_quality(self, prompts: List[str]) -> Dict:
        """評估生成質量"""
        
        print(f"\n{'='*60}")
        print(f"📊 質量評估")
        print(f"{'='*60}\n")
        
        results = self.batch_generate(prompts, show_progress=True)
        
        # 分析指標
        total_tokens = sum(r.tokens_generated for r in results)
        avg_tokens = total_tokens / len(results)
        
        # 重複度分析（簡單版）
        repetitions = 0
        for result in results:
            words = result.output.split()
            unique_words = set(words)
            if len(words) > 0:
                repetition_rate = 1 - (len(unique_words) / len(words))
                repetitions += repetition_rate
        
        avg_repetition = repetitions / len(results) if results else 0
        
        # 語言分布
        chinese_chars = 0
        english_chars = 0
        
        for result in results:
            for char in result.output:
                if '\u4e00' <= char <= '\u9fff':
                    chinese_chars += 1
                elif char.isalpha():
                    english_chars += 1
        
        total_chars = chinese_chars + english_chars
        chinese_ratio = chinese_chars / total_chars if total_chars > 0 else 0
        english_ratio = english_chars / total_chars if total_chars > 0 else 0
        
        quality_report = {
            "samples": len(results),
            "avg_tokens": avg_tokens,
            "avg_repetition": avg_repetition,
            "language_distribution": {
                "chinese": f"{chinese_ratio*100:.1f}%",
                "english": f"{english_ratio*100:.1f}%"
            }
        }
        
        print(f"\n{'='*60}")
        print(f"📈 質量報告")
        print(f"{'='*60}")
        print(f"測試樣本: {quality_report['samples']}")
        print(f"平均長度: {quality_report['avg_tokens']:.1f} tokens")
        print(f"重複率: {quality_report['avg_repetition']*100:.1f}%")
        print(f"語言分布:")
        print(f"  中文: {quality_report['language_distribution']['chinese']}")
        print(f"  英文: {quality_report['language_distribution']['english']}")
        print(f"{'='*60}\n")
        
        return quality_report
    
    def _show_help(self):
        """顯示幫助"""
        print("\n" + "="*60)
        print("📖 命令幫助")
        print("="*60)
        print("/help     - 顯示此幫助信息")
        print("/config   - 配置生成參數（溫度、長度等）")
        print("/stats    - 顯示使用統計")
        print("/export   - 導出對話歷史到文件")
        print("/clear    - 清除對話歷史")
        print("/quit     - 退出交互模式")
        print("="*60 + "\n")
    
    def _configure_generation(self):
        """配置生成參數"""
        print("\n當前配置:")
        print(f"  max_tokens: {self.default_config.max_new_tokens}")
        print(f"  temperature: {self.default_config.temperature}")
        print(f"  top_k: {self.default_config.top_k}")
        print(f"  top_p: {self.default_config.top_p}")
        
        try:
            max_tokens = input(f"\n最大生成長度 [{self.default_config.max_new_tokens}]: ")
            if max_tokens:
                self.default_config.max_new_tokens = int(max_tokens)
            
            temp = input(f"溫度 (0.0-2.0) [{self.default_config.temperature}]: ")
            if temp:
                self.default_config.temperature = float(temp)
            
            top_k = input(f"Top-K [{self.default_config.top_k}]: ")
            if top_k:
                self.default_config.top_k = int(top_k)
            
            top_p = input(f"Top-P (0.0-1.0) [{self.default_config.top_p}]: ")
            if top_p:
                self.default_config.top_p = float(top_p)
            
            print("\n✅ 配置已更新")
            
        except ValueError as e:
            print(f"❌ 無效輸入: {e}")
    
    def _show_stats(self):
        """顯示統計信息"""
        if not self.generation_history:
            print("\n還沒有生成記錄")
            return
        
        total = len(self.generation_history)
        total_tokens = sum(r.tokens_generated for r in self.generation_history)
        total_time = sum(r.time_taken for r in self.generation_history)
        avg_speed = sum(r.tokens_per_second for r in self.generation_history) / total
        
        print("\n" + "="*60)
        print("📊 使用統計")
        print("="*60)
        print(f"總生成次數: {total}")
        print(f"總生成token: {total_tokens}")
        print(f"總用時: {total_time:.2f}秒")
        print(f"平均速度: {avg_speed:.2f} tokens/s")
        print(f"當前模型: {self.manager.current_model}")
        print("="*60 + "\n")
    
    def _export_history(self):
        """導出歷史"""
        if not self.generation_history:
            print("\n還沒有生成記錄")
            return
        
        filename = f"generation_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = [asdict(r) for r in self.generation_history]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 已導出到: {filename}")


def main():
    """主函數 - 完整的命令行接口"""
    parser = argparse.ArgumentParser(
        description="BioNeuronAI 專業模型工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--model",
        default="models/tiny_llm_en_zh_trained",
        help="模型路徑"
    )
    
    parser.add_argument(
        "--mode",
        choices=["interactive", "benchmark", "batch", "eval", "single"],
        default="interactive",
        help="運行模式"
    )
    
    parser.add_argument(
        "--prompt",
        help="單次生成的提示"
    )
    
    parser.add_argument(
        "--prompts-file",
        help="批次生成的提示文件（每行一個）"
    )
    
    parser.add_argument(
        "--output",
        help="輸出文件"
    )
    
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=50,
        help="最大生成長度"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="溫度參數"
    )
    
    args = parser.parse_args()
    
    try:
        # 初始化助手
        print(f"\n🚀 初始化 BioNeuronAI")
        assistant = ModelAssistant(args.model)
        
        # 設置配置
        assistant.default_config.max_new_tokens = args.max_tokens
        assistant.default_config.temperature = args.temperature
        
        # 根據模式運行
        if args.mode == "interactive":
            assistant.interactive_mode()
        
        elif args.mode == "benchmark":
            assistant.benchmark()
        
        elif args.mode == "single":
            if not args.prompt:
                print("❌ 單次模式需要 --prompt 參數")
                return
            
            result_obj = assistant.generate(args.prompt)
            print(f"\n輸出: {result_obj.output}")
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(asdict(result_obj), f, ensure_ascii=False, indent=2)
        
        elif args.mode == "batch":
            if not args.prompts_file:
                print("❌ 批次模式需要 --prompts-file 參數")
                return
            
            with open(args.prompts_file, 'r', encoding='utf-8') as f:
                prompts = [line.strip() for line in f if line.strip()]
            
            results = assistant.batch_generate(prompts)
            
            if args.output:
                data = [asdict(r) for r in results]
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        
        elif args.mode == "eval":
            if not args.prompts_file:
                print("❌ 評估模式需要 --prompts-file 參數")
                return
            
            with open(args.prompts_file, 'r', encoding='utf-8') as f:
                prompts = [line.strip() for line in f if line.strip()]
            
            report = assistant.evaluate_quality(prompts)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"運行錯誤: {e}", exc_info=True)
        print(f"\n❌ 錯誤: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
