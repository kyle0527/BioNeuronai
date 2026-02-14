# 風險管理模組 (Risk Management)

**路徑**: `src/bioneuronai/risk_management/`  
**版本**: v4.0  
**更新日期**: 2026-02-14

---

## 📋 目錄

1. [模組概述](#模組概述)
2. [核心文件](#核心文件)
3. [主要功能](#主要功能)
4. [使用示例](#使用示例)
5. [相關文檔](#相關文檔)

---

## 🎯 模組概述

風險管理模組提供倉位管理和風險控制功能，確保交易安全性。

### 模組職責
- ✅ 倉位大小計算
- ✅ 槓桿控制
- ✅ 風險評估
- ✅ 資金管理

---

## 📁 核心文件

### `position_manager.py`
倉位管理器，負責計算和管理交易倉位。

**主要類**:
- `PositionManager` - 倉位管理器

**核心功能**:
```python
# 倉位計算
position_size = position_manager.calculate_position_size(
    account_balance=10000,
    risk_per_trade=0.02,
    stop_loss_distance=100
)

# 槓桿控制
max_leverage = position_manager.get_max_leverage(risk_level="MODERATE")
```

---

## 🛠️ 主要功能

### 1. 倉位計算
根據風險參數計算合適的倉位大小。

### 2. 槓桿管理
控制最大槓桿使用率，防止過度風險。

### 3. 風險評估
評估當前持倉的風險水平。

---

## 💡 使用示例

```python
from src.bioneuronai.risk_management import PositionManager

# 初始化倉位管理器
pm = PositionManager()

# 計算倉位
position = pm.calculate_position_size(
    balance=10000,
    risk_percent=2,
    stop_loss=50
)

print(f"建議倉位: {position}")
```

---

## 📚 相關文檔

- **主文檔**: [風險管理手冊](../../../docs/RISK_MANAGEMENT_MANUAL.md)
- **父模組**: [BioNeuronai 主模組](../README.md)

---

**最後更新**: 2026年1月22日
