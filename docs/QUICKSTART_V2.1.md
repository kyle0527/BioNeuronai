# 🚀 BioNeuronai v2.1 快速開始指南

## 📑 目錄

1. 安裝與依賴
2. 設定環境變數
3. 驗證系統狀態
4. 核心功能驗證

## 📦 1. 安裝與依賴

```bash
# 克隆專案
git clone https://github.com/BioNeuronai/BioNeuronai.git
cd BioNeuronai

# 建立環境
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 安裝套件
pip install -r requirements-crypto.txt
```

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
預期出現各模組回報 `[OK]` 以及 `系統狀態: 正常`。如果缺少 `torch` 未安裝成功，系統會給予警告，但不會阻擋基礎的分析功能。

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

**步驟 D：模擬或測試網執行 (Trade)**
確認一切正常後，開啟機器人接收即時 WebSocket 數據進行自動交易（需連網）：
```bash
python main.py trade --symbol BTCUSDT --testnet
```
隨時可按 `Ctrl+C` 平順中止程式。

**步驟 E（選用）：AI 對話助理 (Chat)**
以中文或英文詢問交易策略、幣安合約規則、技術分析等問題：
```bash
python main.py chat                     # 自動語言
python main.py chat --symbol BTCUSDT    # 附帶即時市場資料
python main.py chat --allow-rule-based-fallback  # 僅供開發測試
```
正式對話模式需要 PyTorch 與 `model/tiny_llm_100m.pth`。若模型未載入，現在不會默默降級；只有顯式加上 `--allow-rule-based-fallback` 才會進入開發用規則模式。
