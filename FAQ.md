# 常見問題 (FAQ)

## 如何在開發過程中執行測試？

使用專案根目錄中的 pytest 命令即可：

```bash
pytest --maxfail=1 --disable-warnings tests
```

若需檢查型別，請使用：

```bash
mypy src/bioneuronai examples
```

## BioNeuron 和 ImprovedBioNeuron 有什麼差異？

- `BioNeuron`：輕量、依賴最少的實作，提供核心 Hebbian 學習與新穎性評分。
- `ImprovedBioNeuron`：繼承統一的 `BaseNeuron` 介面，新增自適應閾值、強化
  新穎性評估與改進的學習規則，適合需要細緻控制的情境。

## 可以只使用套件的某些模組嗎？

可以。`bioneuronai.__init__` 匯出了 `BaseNeuron`、`BioNeuron`、`ImprovedBioNeuron`
等統一 API。若環境無法載入進階模組，`ImprovedBioNeuron` 的匯入會自動跳過，
而基礎功能仍可使用。

## 如何觸發 PyPI 自動發佈？

專案提供 `.github/workflows/publish.yml`。當維護者建立新的 GitHub Release（或
手動 `workflow_dispatch`）時，CI 會：

1. 安裝依賴並執行測試
2. 使用 `python -m build` 建立套件
3. 透過 `pypa/gh-action-pypi-publish` 上傳到 PyPI

請確保儲存庫設定了 `PYPI_API_TOKEN` secret。

## 是否有官方的程式碼風格規範？

有，詳見 [CONTRIBUTING.md](CONTRIBUTING.md)。需遵循 Black/Isort 格式化、mypy
靜態檢查並確保測試通過。
