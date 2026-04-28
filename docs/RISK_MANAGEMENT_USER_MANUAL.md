# BioNeuronai 風險管理使用手冊

> **版本**：v2.1  
> **更新日期**：2026-04-28  
> **模組路徑**：`src/bioneuronai/risk_management/position_manager.py`  
> **設定檔**：`config/risk_config_optimized.json`

---

## 📑 目錄

- [1. 概述](#1-概述)
- [2. 風險等級說明](#2-風險等級說明)
- [3. 風險參數詳解](#3-風險參數詳解)
- [4. 倉位計算邏輯](#4-倉位計算邏輯)
- [5. 投資組合風險評估](#5-投資組合風險評估)
- [6. 風險警報系統](#6-風險警報系統)
- [7. 進場前驗核中的風險整合](#7-進場前驗核中的風險整合)
- [8. 風險設定檔修改指引](#8-風險設定檔修改指引)
- [9. 最佳實踐建議](#9-最佳實踐建議)
- [10. 相關文件](#10-相關文件)

---

## 1. 概述

BioNeuronai 風險管理模組 (`RiskManager`) 是整個交易系統的核心安全機制，負責：

- **倉位計算**：根據帳戶餘額、止損距離和風險等級，自動計算合理倉位大小
- **投資組合風險評估**：計算 VaR、最大回撤、集中度風險等多維度指標
- **風險警報**：即時生成 LOW / MEDIUM / HIGH / CRITICAL 警報
- **進場前驗核整合**：`POST /api/v1/pretrade` 的第三道安全檢查

所有風險決策都是在**本地端**計算完成的，不需要額外的外部服務。

---

## 2. 風險等級說明

BioNeuronai 提供四個風險等級，由**保守**到**高風險**排列：

| 等級 | 識別碼 | 適合使用者 |
|---|---|---|
| 保守 | `CONSERVATIVE` | 新手、低風險承受度 |
| 中等（預設）| `MODERATE` | 一般交易者 |
| 積極 | `AGGRESSIVE` | 有經驗的交易者 |
| 高風險 | `HIGH_RISK` | 專業投機者（需了解高風險） |

> **預設等級**：系統啟動時使用 `MODERATE`。

---

## 3. 風險參數詳解

### 四個等級的完整參數對照表

| 參數 | 說明 | CONSERVATIVE | MODERATE | AGGRESSIVE | HIGH_RISK |
|---|---|---|---|---|---|
| `max_risk_per_trade` | 每筆交易最大虧損（佔帳戶） | 1% | **2%** | 3% | 5% |
| `max_daily_risk` | 每日最大允許虧損 | 3% | **5%** | 8% | 15% |
| `max_portfolio_risk` | 全投資組合最大暴露風險 | 15% | **25%** | 40% | 60% |
| `max_drawdown_limit` | 觸發停止的最大回撤 | 10% | **15%** | 25% | 40% |
| `max_correlation` | 持倉間最大相關係數 | 60% | **70%** | 80% | 90% |
| `max_leverage` | 最大允許槓桿倍率 | 2x | **3x** | 5x | 10x |
| `position_concentration` | 單一倉位最大佔比 | 20% | **25%** | 30% | 40% |
| `sector_concentration` | 同類資產最大佔比 | 40% | **50%** | 60% | 80% |

### 參數說明

**`max_risk_per_trade` — 每筆交易最大風險**
- 這是最重要的參數，決定「這筆交易最多虧多少」
- 例如帳戶 $10,000、MODERATE 等級：每筆最多虧 $200 (2%)
- 系統根據此參數反推最大可持倉量

**`max_daily_risk` — 每日最大虧損**
- 當日累計虧損達到此閾值，系統應停止開倉
- MODERATE 5% 意指：$10,000 帳戶每日最多虧 $500

**`max_drawdown_limit` — 最大回撤停止線**
- 當帳戶從高峰回撤超過此比例，系統觸發緊急停損
- 是最後一道防線

**`max_leverage` — 最大槓桿**
- 加密貨幣期貨允許高槓桿，但高槓桿大幅放大虧損
- **初學者嚴格建議使用 CONSERVATIVE (2x) 或不超過 3x**

**`position_concentration` — 倉位集中度**
- 防止過度集中在單一標的
- MODERATE 25%：單一倉位不超過帳戶的 25%

---

## 4. 倉位計算邏輯

當呼叫 `RiskManager.calculate_position_size()` 時，系統執行以下 9 步驟計算：

```
帳戶餘額 + 進場價 + 止損價 + 風險等級
          ↓
1. 計算止損距離 = |進場價 - 止損價| / 進場價
2. 風險基礎倉位 = 帳戶餘額 × max_risk_per_trade / 止損距離
3. Kelly 倉位（凱利公式，使用歷史勝率和賠率）
4. 波動率調整
5. 流動性限制調整
6. 相關性限制調整
7. 集中度限制調整
8. 取上述所有計算的最小值為最終倉位
9. 計算信心分數
```

### PositionSizing 回傳結果

| 欄位 | 說明 |
|---|---|
| `recommended_size` | 建議倉位大小（以交易對計價，如 BTC 數量） |
| `max_size` | 最大允許倉位（根據 `position_concentration`） |
| `risk_amount` | 此倉位的最大預期虧損金額 ($) |
| `stop_loss_distance` | 止損距離（百分比） |
| `entry_price` | 建議進場價 |
| `stop_loss_price` | 建議止損價 |
| `take_profit_price` | 建議止盈價（預設 1:2 風報比） |
| `risk_reward_ratio` | 風險報酬比（預設 2.0，即 1:2） |
| `kelly_fraction` | 凱利比例 |
| `confidence_score` | 倉位計算信心分數 (0~1) |

### 範例計算

```
帳戶：$10,000
進場價：$76,000 BTCUSDT
止損價：$73,000
風險等級：MODERATE

止損距離 = |76000 - 73000| / 76000 = 3.95%
最大虧損 = $10,000 × 2% = $200
建議倉位 = $200 / (3.95% × $76,000) = 0.0666 BTC
止盈價 = $76,000 × (1 + 3.95% × 2) = $82,004
```

---

## 5. 投資組合風險評估

`RiskManager.assess_portfolio_risk()` 計算以下指標：

### PortfolioRisk 指標說明

| 指標 | 說明 | 參考值 |
|---|---|---|
| `total_exposure` | 當前總暴露名義金額 | — |
| `var_1day_95` | 1 日 95% VaR | 應 < `max_portfolio_risk` |
| `var_1day_99` | 1 日 99% VaR（更保守）| 應 < `max_portfolio_risk × 1.5` |
| `expected_shortfall` | 尾部損失期望值（CVaR）| 應 < `max_portfolio_risk × 2` |
| `maximum_drawdown` | 當前持倉最大回撤 | 應 < `max_drawdown_limit` |
| `correlation_matrix` | 持倉間相關性矩陣 | 高相關代表未充分分散 |
| `concentration_risk` | 集中度風險分析 | 單一標的不超過 `position_concentration` |
| `liquidity_risk` | 流動性風險評分 | 越低越好 |
| `leverage_ratio` | 當前實際槓桿比率 | 應 < `max_leverage` |
| `risk_adjusted_return` | 風險調整後報酬 | 越高越好 |

### VaR 解讀

- **VaR 95% = $500** 代表：在正常市場條件下，有 95% 的信心認為，下一個交易日虧損不會超過 $500
- **Expected Shortfall (CVaR)** 是超出 VaR 的尾部損失平均值，是比 VaR 更保守的風險指標

---

## 6. 風險警報系統

### 警報嚴重程度

| 等級 | 顏色 | 說明 | 建議行動 |
|---|---|---|---|
| `LOW` | 🟡 黃色 | 輕微風險偏高 | 注意觀察 |
| `MEDIUM` | 🟠 橙色 | 明顯風險超標 | 縮小倉位 |
| `HIGH` | 🔴 紅色 | 嚴重風險 | 立即減倉 |
| `CRITICAL` | 🚨 深紅 | 緊急風險（近最大回撤）| 立即停止交易並平倉 |

### RiskAlert 欄位

| 欄位 | 說明 |
|---|---|
| `alert_type` | 警報類型，如 `DRAWDOWN`、`LEVERAGE`、`CONCENTRATION` |
| `severity` | 嚴重程度：LOW / MEDIUM / HIGH / CRITICAL |
| `message` | 人類可讀的警報訊息 |
| `suggested_action` | 建議採取的行動 |
| `timestamp` | 警報發生時間 |

### 觸發條件範例

| 觸發條件 | 預設閾值（MODERATE）| 嚴重程度 |
|---|---|---|
| 單日虧損超過每日限額 70% | > 3.5% 日虧損 | HIGH |
| 回撤超過限額 80% | > 12% 回撤 | HIGH |
| 回撤超過限額 95% | > 14.25% 回撤 | CRITICAL |
| 槓桿超過允許值 | > 3x | MEDIUM |
| 單一倉位超過集中度 | > 25% 帳戶 | MEDIUM |

---

## 7. 進場前驗核中的風險整合

當呼叫 `POST /api/v1/pretrade` 時，風險管理模組是第三個驗核步驟：

```
PreTrade 六點驗核流程：
Step 1: 市場時間 & 流動性檢查
Step 2: 技術指標訊號 (MACD, RSI, BB)
Step 3: ⚠️ 風險管理計算 ← RiskManager 在此介入
  ├── 計算建議倉位大小
  ├── 計算止損 / 止盈價格
  ├── 評估帳戶可承受的最大虧損
  └── 檢查是否符合 MODERATE 等級參數
Step 4: 新聞情緒分析
Step 5: RAG 知識庫安全檢查
Step 6: 綜合評分 → PROCEED / CAUTION / REJECT
```

**REJECT 觸發條件（風險相關）：**
- 帳戶餘額不足以開最小倉位
- 止損距離太近（< 0.5%，可能因手續費被洗出場）
- 止損距離太遠（> 20%，風險過高）
- 當日虧損已達 `max_daily_risk`

---

## 8. 風險設定檔修改指引

### 設定檔位置

```
config/risk_config_optimized.json
```

### 修改風險等級（API 方式）

目前沒有專用的「更改風險等級」端點，需透過設定檔或環境變數調整。

**方式一：修改設定檔**

開啟 `config/risk_config_optimized.json`，找到 `risk_level` 欄位：

```json
{
  "risk_level": "MODERATE",
  "custom_overrides": {
    "max_risk_per_trade": 0.015,
    "max_leverage": 2.5
  }
}
```

**方式二：程式碼中直接指定**

```python
from bioneuronai.risk_management import get_risk_params

# 取得指定等級的參數
params = get_risk_params("CONSERVATIVE")
print(params.max_risk_per_trade)  # 0.01

# 使用 RiskManager 計算倉位
from bioneuronai.risk_management.position_manager import RiskManager
manager = RiskManager()
# 使用 CONSERVATIVE 等級
result = await manager.calculate_position_size(
    symbol="BTCUSDT",
    entry_price=76000,
    stop_loss_price=73000,
    account_balance=10000,
    risk_level="CONSERVATIVE"  # ← 指定風險等級
)
```

### 自訂參數

若需要介於標準等級之間的設定，可以修改 `position_manager.py` 中的 `_initialize_risk_parameters()` 方法，新增自訂等級：

```python
"CUSTOM": RiskParameters(
    max_risk_per_trade=0.015,   # 1.5% (介於 CONSERVATIVE 和 MODERATE)
    max_daily_risk=0.04,        # 4%
    max_portfolio_risk=0.20,    # 20%
    max_drawdown_limit=0.12,    # 12%
    max_correlation=0.65,       # 65%
    max_leverage=2.5,           # 2.5x
    position_concentration=0.22, # 22%
    sector_concentration=0.45   # 45%
)
```

---

## 9. 最佳實踐建議

### 新手上路

1. **從 CONSERVATIVE 開始** — 1% per trade 確保犯錯時損失有限
2. **初始資金虛擬測試** — 先在 testnet 驗證策略，再用真實資金
3. **不超過 2x 槓桿** — 加密貨幣波動大，高槓桿極易爆倉
4. **嚴守止損** — 不要因「看好行情」而手動移除止損

### 中階操作

1. **監控每日虧損** — 到達 `max_daily_risk` 的 70% 時主動休息
2. **注意相關性** — 同時做多 BTC 和 ETH 等於沒有分散
3. **定期回測驗證** — 使用 BacktestPanel 每月重新評估策略

### 高級操作（AGGRESSIVE / HIGH_RISK）

> **僅適合有充分回測驗證和實盤經驗的交易者**

1. **HIGH_RISK 等級 5% per trade** — $10,000 帳戶一筆交易可虧 $500，需確保全年勝率足夠高
2. **最大回撤 40%** 代表帳戶可以從 $10,000 跌到 $6,000 才觸發停止
3. **HIGH_RISK 應配備嚴格的資金管理計劃**，不適合倉位集中

### 風險警報回應指南

| 警報等級 | 建議回應 |
|---|---|
| LOW | 記錄並觀察，暫不行動 |
| MEDIUM | 不再開新倉，考慮縮小現有倉位 |
| HIGH | 立即縮倉至 50% 以下 |
| CRITICAL | **立即全部平倉，停止交易，分析原因** |

---

## 10. 相關文件

| 文件 | 說明 |
|---|---|
| [ANALYSIS_MODULE_USER_MANUAL.md](ANALYSIS_MODULE_USER_MANUAL.md) | 分析模組（含技術指標）手冊 |
| [STRATEGY_MODULE_USER_MANUAL.md](STRATEGY_MODULE_USER_MANUAL.md) | 策略模組使用手冊 |
| [API_USER_MANUAL.md](API_USER_MANUAL.md) | REST API 端點參考（含 /pretrade 詳細說明） |
| [BACKTEST_SYSTEM_GUIDE.md](BACKTEST_SYSTEM_GUIDE.md) | 回測驗證風險設定的系統指南 |
| [FRONTEND_DASHBOARD_MANUAL.md](FRONTEND_DASHBOARD_MANUAL.md) | 前端 Dashboard 中 PreTradePanel 的操作說明 |
