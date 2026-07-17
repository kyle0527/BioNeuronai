# 舊腳本歸檔索引
歸檔日期: 2026-01-23

## 歸檔原因分類

### 1. 功能重複（被新版本替代）
| 文件 | 替代者 | 原因 |
|------|--------|------|
| `run_ai_trading.py` | `ai_trade_nexttick.py` | 舊版 AI 交易腳本，新版功能更完整 |
| `run_backtest_demo.py` | `test_backtest_system.py` | 回測演示，測試版本更穩定 |

### 2. 需要完整配置（未實際使用）
| 文件 | 需求 | 狀態 |
|------|------|------|
| `use_trading_engine_v2.py` | API Key, 完整環境配置 | 執行失敗 |
| `use_crypto_trader.py` | 配置文件, API 憑證 | 未測試 |
| `use_backtest_mode.py` | 回測配置 | 未測試 |

### 3. 未完成/過時
| 文件 | 狀態 | 備註 |
|------|------|------|
| `test_ai_with_history.py` | 未測試 | 可能過時 |
| `use_model.py` | 舊版 | 早期模型使用腳本 |
| `use_model_evolving.py` | 實驗性 | 模型演化實驗 |
| `use_rag.py` | 實驗性 | RAG 功能測試 |

## 已刪除（功能已驗證完成）
- `test_ai_simple.py` - AI 基礎測試，功能已整合到主腳本
- `check_klines.py` - 一次性數據驗證工具，已確認數據 100% 完整
- `ai_output.txt` - 臨時輸出文件

## 保留在根目錄的核心腳本

### 主要功能
1. **`ai_trade_nexttick.py`** - 核心 AI 交易執行腳本
   - 使用 111.2M 參數 AI 模型
   - next_tick() 逐 K 線推進
   - 已驗證可執行（2026-01-10~15 測試）

### 測試腳本
2. **`test_backtest_system.py`** - 回測系統完整測試（5/5 通過）
3. **`test_integration.py`** - 整合測試（需修復）
4. **`test_all_strategies.py`** - 所有策略測試（待驗證）

### 工具腳本
5. **`check_db.py`** - 數據庫檢查工具
6. **`migrate_to_database.py`** - 數據庫遷移工具

---

## 如需恢復歸檔文件
從 `archived/old_scripts/` 目錄複製回根目錄即可。

## 下次整理建議
- 修復 `test_integration.py`
- 驗證 `test_all_strategies.py`
- 考慮將工具腳本移至 `tools/` 目錄
