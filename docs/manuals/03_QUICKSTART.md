# 🚀 BioNeuronai v2.1 / v2.2 訓練後驗證期快速開始指南

> 更新日期：2026-05-19
> 建議環境：本機全域 Python 3.13。Docker 留到本機功能收斂後最後重建。

## 📑 目錄

- [📦 1. 安裝與依賴](#📦-1-安裝與依賴)
- [🔑 2. 設定環境變數](#🔑-2-設定環境變數)
- [🧪 3. 驗證系統狀態](#🧪-3-驗證系統狀態)
- [🎯 4. 核心功能驗證](#🎯-4-核心功能驗證)

## 📦 1. 安裝與依賴

```bash
# 克隆專案
git clone https://github.com/BioNeuronai/BioNeuronai.git
cd BioNeuronai

# 安裝套件。本專案目前不使用專案內虛擬環境。
python -m pip install --upgrade pip
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.8.0+cpu torchvision==0.23.0+cpu torchaudio==2.8.0+cpu
python -m pip install -e .
```

PyTorch 2.8.0+cpu 是目前 Windows 本機已確認可 import 的 CPU 組合。第一次安裝成功後，後續日常啟動只需要檢查，不需要每次重新設定。

## 🔑 2. 設定環境變數

```bash
# 生成環境設定檔
cp .env.example .env
```
Windows PowerShell 可改用：
```powershell
Copy-Item .env.example .env
```
請編輯 `.env`，填入您的幣安金鑰，並確保 `BINANCE_TESTNET=true` 以安全試用。

## 🧪 3. 驗證系統狀態

```bash
python main.py status
```
預期出現各模組回報 `[OK]` 以及 `系統狀態: 正常`。若 API 已啟動，`GET /api/v1/status` 應回傳 `ready=true`、`blocking=[]`；缺少 PyTorch、現役交易模型、聊天模型或必要設定檔時應直接顯示阻擋項目。

## 🎯 4. 核心功能驗證

**步驟 A：觀察市場 (News)**
即時抓取並推敲市場事件情緒。
```bash
python main.py news --symbol BTCUSDT
```

**步驟 B：啟動高階計劃 (Plan)**
呼叫 `planning/` 模組分析市場大盤，給出是否適合進場的巨觀建議：
```bash
python main.py plan
```

**步驟 C：執行盤前檢查 (Pretrade)**
檢查技術面、資金及風控是否滿足硬性開倉條件：
```bash
python main.py pretrade --symbol BTCUSDT --action long
```

**步驟 D：啟動主交易引擎（建議先 paper-live）**
確認一切正常後，先啟動真正的主交易引擎入口；日常建議先用 `paper-live`，而不是直接進 testnet 或 live：
```bash
python main.py trade --symbol BTCUSDT --paper-live --paper-balance 10000
```
預期行為：

- `TradingEngine` 初始化成功
- 自動交易狀態被設定
- AI 模型載入
- 顯示即時價格與 paper log 目錄
- 進入持續監控流程；可用 `Ctrl+C` 中止

若要直接用測試網監控：

```bash
python main.py trade --symbol BTCUSDT --testnet
```

若要從 UI / API 啟用自動交易，請使用 `Trade Control` 的 `Testnet auto` 模式或 `POST /api/v1/trade/start` 的 `mode=testnet_auto`；不要把 CLI testnet 監控等同於正式網自動下單。

**步驟 E：執行 autonomous 單輪值班判斷**

如果你要的是「像值班操作員一樣，先做一輪 plan + pretrade + adaptation 判斷」，用：

```bash
python main.py autonomous --mode advisor --symbol BTCUSDT --output output/autonomous_advisor.json
```

這個入口會：

- 跑一輪高階計畫
- 挑候選交易對
- 對候選做 pretrade
- 給出 `advise_only`、`observe` 或可執行判斷
- 把結果寫入 decision ledger

它是單輪決策入口，不是長時間監控入口。長時間主線仍然是 `trade`。

**步驟 F（選用）：AI 對話助理 (Chat)**
以中文或英文詢問交易策略、幣安合約規則、技術分析等問題：
```bash
python main.py chat                     # 自動語言
python main.py chat --symbol BTCUSDT    # 附帶即時市場資料
python main.py chat --allow-rule-based-fallback  # 僅供開發測試
```
正式對話模式需要 PyTorch 與 `model/tiny_llm_100m.pth`。若模型未載入，現在不會默默降級；只有顯式加上 `--allow-rule-based-fallback` 才會進入開發用規則模式。
