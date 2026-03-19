# BioNeuronai 專案完整報告生成器
# 整合樹狀圖、統計數據、程式碼分析

param(
    [string]$ProjectRoot = "C:\D\E\BioNeuronai",
    [string]$OutputDir = "C:\D\E\BioNeuronai\tools"
)

# 強制切換終端機 code page 為 UTF-8（必須在任何輸出之前）
chcp 65001 | Out-Null
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$OutputEncoding = [Text.Encoding]::UTF8

Write-Host "🚀 開始生成專案完整報告..." -ForegroundColor Cyan

# 要排除的目錄
$excludeDirs = @(
    '.git', '__pycache__', '.mypy_cache', '.ruff_cache',
    'node_modules', '.venv', 'venv', '.pytest_cache',
    '.tox', 'dist', 'build', '.egg-info', '.eggs',
    'htmlcov', '.coverage', '.hypothesis', '.idea', '.vscode'
)

# ==================== 1. 收集統計數據 ====================
Write-Host "`n📊 收集專案統計數據..." -ForegroundColor Yellow

# 副檔名統計
$allFiles = Get-ChildItem -Path $ProjectRoot -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $path = $_.FullName
        -not ($excludeDirs | Where-Object { $path -like "*\$_\*" })
    }

$extStats = $allFiles | Group-Object Extension |
    Select-Object @{Name='Extension';Expression={if($_.Name -eq ''){'.no_ext'}else{$_.Name}}}, Count |
    Sort-Object Count -Descending

# 程式碼行數統計
$codeExts = @('.py', '.js', '.ts', '.go', '.rs', '.sql', '.sh', '.bat', '.ps1', '.md', '.yaml', '.yml', '.toml', '.json', '.html', '.css')

$locStats = $allFiles |
    Where-Object { $codeExts -contains $_.Extension } |
    ForEach-Object {
        $lineCount = (Get-Content $_.FullName -ErrorAction SilentlyContinue | Measure-Object -Line).Lines
        [PSCustomObject]@{
            Extension = $_.Extension
            Lines = $lineCount
            File = $_.Name
        }
    } |
    Group-Object Extension |
    Select-Object @{Name='Extension';Expression={$_.Name}},
                  @{Name='TotalLines';Expression={($_.Group | Measure-Object -Property Lines -Sum).Sum}},
                  @{Name='FileCount';Expression={$_.Count}},
                  @{Name='AvgLines';Expression={[math]::Round(($_.Group | Measure-Object -Property Lines -Average).Average, 1)}} |
    Sort-Object TotalLines -Descending

# 多語言統計
$pythonStats = $locStats | Where-Object Extension -eq '.py'
$goStats = $locStats | Where-Object Extension -eq '.go'
$rustStats = $locStats | Where-Object Extension -eq '.rs'
$tsStats = $locStats | Where-Object Extension -in @('.ts', '.js')

$totalCodeLines = ($locStats | Measure-Object -Property TotalLines -Sum).Sum
$pythonPct = if ($pythonStats) { [math]::Round(($pythonStats.TotalLines / $totalCodeLines) * 100, 1) } else { 0 }
$goPct = if ($goStats) { [math]::Round(($goStats.TotalLines / $totalCodeLines) * 100, 1) } else { 0 }
$rustPct = if ($rustStats) { [math]::Round(($rustStats.TotalLines / $totalCodeLines) * 100, 1) } else { 0 }
$tsPct = if ($tsStats) { [math]::Round((($tsStats | Measure-Object -Property TotalLines -Sum).Sum / $totalCodeLines) * 100, 1) } else { 0 }

# ==================== 2. 生成樹狀圖 ====================
Write-Host "🌳 生成專案樹狀結構..." -ForegroundColor Yellow

function Get-CleanTree {
    param(
        [string]$Path,
        [string]$Prefix = "",
        [int]$Level = 0,
        [int]$MaxLevel = 10
    )

    if ($Level -ge $MaxLevel) { return }

    try {
        $items = Get-ChildItem -Path $Path -Force -ErrorAction Stop |
            Where-Object {
                $name = $_.Name
                if ($_.PSIsContainer) {
                    $excludeDirs -notcontains $name
                } else {
                    $name -notlike '*.pyc' -and $name -notlike '*.pyo'
                }
            } |
            Sort-Object @{Expression={$_.PSIsContainer}; Descending=$true}, Name

        $itemCount = $items.Count
        for ($i = 0; $i -lt $itemCount; $i++) {
            $item = $items[$i]
            $isLast = ($i -eq $itemCount - 1)

            $connector = if ($isLast) { "└─" } else { "├─" }
            $extension = if ($isLast) { "    " } else { "│   " }

            if ($item.PSIsContainer) {
                $output = "$Prefix$connector📁 $($item.Name)/"
                Write-Output $output
                Get-CleanTree -Path $item.FullName -Prefix "$Prefix$extension" -Level ($Level + 1) -MaxLevel $MaxLevel
            } else {
                $icon = switch -Wildcard ($item.Extension) {
                    '.py' { '🐍' }
                    '.js' { '📜' }
                    '.ts' { '📘' }
                    '.md' { '📝' }
                    '.json' { '⚙️' }
                    '.yml' { '🔧' }
                    '.yaml' { '🔧' }
                    '.sql' { '🗄️' }
                    '.sh' { '⚡' }
                    '.bat' { '⚡' }
                    '.ps1' { '⚡' }
                    '.go' { '🔷' }
                    '.rs' { '🦀' }
                    '.txt' { '📄' }
                    '.html' { '🌐' }
                    '.css' { '🎨' }
                    default { '📄' }
                }
                Write-Output "$Prefix$connector$icon $($item.Name)"
            }
        }
    } catch {
        # 忽略無法存取的目錄
    }
}

$rootName = Split-Path $ProjectRoot -Leaf
$treeOutput = @()
$treeOutput += "📦 $rootName"
$treeOutput += Get-CleanTree -Path $ProjectRoot

# ==================== 3. 生成整合報告 ====================
Write-Host "📝 生成整合報告..." -ForegroundColor Yellow

# 確保輸出目錄存在
if (-not (Test-Path $OutputDir)) {
    New-Item -Path $OutputDir -ItemType Directory -Force | Out-Null
    Write-Host "   已創建輸出目錄: $OutputDir" -ForegroundColor Gray
}

$reportContent = @"
╔══════════════════════════════════════════════════════════════════════════════╗
║                      BioNeuronai 專案完整分析報告                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

生成時間: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
專案路徑: $ProjectRoot

═══════════════════════════════════════════════════════════════════════════════
📊 專案統計摘要
═══════════════════════════════════════════════════════════════════════════════

總文件數量: $($extStats | Measure-Object -Property Count -Sum | Select-Object -ExpandProperty Sum)
總程式碼行數: $($locStats | Measure-Object -Property TotalLines -Sum | Select-Object -ExpandProperty Sum)
程式碼檔案數: $($locStats | Measure-Object -Property FileCount -Sum | Select-Object -ExpandProperty Sum)

───────────────────────────────────────────────────────────────────────────────
🎯 檔案類型統計 (Top 10)
───────────────────────────────────────────────────────────────────────────────

$($extStats | Select-Object -First 10 | ForEach-Object {
    $ext = $_.Extension.PadRight(15)
    $count = $_.Count.ToString().PadLeft(6)
    "  $ext $count 個檔案"
} | Out-String)

───────────────────────────────────────────────────────────────────────────────
💻 程式碼行數統計 (依副檔名)
───────────────────────────────────────────────────────────────────────────────

$($locStats | ForEach-Object {
    $ext = $_.Extension.PadRight(10)
    $lines = $_.TotalLines.ToString().PadLeft(8)
    $files = $_.FileCount.ToString().PadLeft(5)
    $avg = $_.AvgLines.ToString().PadLeft(7)
    "  $ext $lines 行  ($files 個檔案, 平均 $avg 行/檔案)"
} | Out-String)

───────────────────────────────────────────────────────────────────────────────
📈 專案規模分析
───────────────────────────────────────────────────────────────────────────────

🐍 Python 程式碼: $($pythonStats.TotalLines) 行 ($($pythonStats.FileCount) 個檔案, $pythonPct% 佔比)
   平均每個檔案: $($pythonStats.AvgLines) 行

🔷 Go 程式碼: $(if ($goStats) { $goStats.TotalLines } else { 0 }) 行 ($(if ($goStats) { $goStats.FileCount } else { 0 }) 個檔案, $goPct% 佔比)
   $(if ($goStats) { "平均每個檔案: $($goStats.AvgLines) 行" } else { "無 Go 檔案" })

🦀 Rust 程式碼: $(if ($rustStats) { $rustStats.TotalLines } else { 0 }) 行 ($(if ($rustStats) { $rustStats.FileCount } else { 0 }) 個檔案, $rustPct% 佔比)
   $(if ($rustStats) { "平均每個檔案: $($rustStats.AvgLines) 行" } else { "無 Rust 檔案" })

📘 TypeScript/JavaScript: $(if ($tsStats) { ($tsStats | Measure-Object -Property TotalLines -Sum).Sum } else { 0 }) 行 ($(if ($tsStats) { ($tsStats | Measure-Object -Property FileCount -Sum).Sum } else { 0 }) 個檔案, $tsPct% 佔比)
   $(if ($tsStats) { "平均每個檔案: " + [math]::Round((($tsStats | Measure-Object -Property AvgLines -Average).Average), 1) + " 行" } else { "無 TS/JS 檔案" })

📝 文檔 (Markdown) 行數: $($locStats | Where-Object Extension -eq '.md' | Select-Object -ExpandProperty TotalLines) 行
⚙️  配置檔案數量: $(($extStats | Where-Object {$_.Extension -in @('.json', '.yml', '.yaml', '.toml', '.ini')}) | Measure-Object -Property Count -Sum | Select-Object -ExpandProperty Sum) 個

───────────────────────────────────────────────────────────────────────────────
🌐 多語言架構概覽
───────────────────────────────────────────────────────────────────────────────

總程式碼檔案數: $($locStats | Measure-Object -Property FileCount -Sum | Select-Object -ExpandProperty Sum)
總程式碼行數: $totalCodeLines

語言分布:
  Python:     $pythonPct% ████████████████████
  Go:         $goPct%
  Rust:       $rustPct%
  TS/JS:      $tsPct%
  其他:       $([math]::Round(100 - $pythonPct - $goPct - $rustPct - $tsPct, 1))%

───────────────────────────────────────────────────────────────────────────────
🚫 已排除的目錄類型
───────────────────────────────────────────────────────────────────────────────

$($excludeDirs | ForEach-Object { "  • $_" } | Out-String)

═══════════════════════════════════════════════════════════════════════════════
🌳 專案目錄結構
═══════════════════════════════════════════════════════════════════════════════

$($treeOutput | Out-String)

═══════════════════════════════════════════════════════════════════════════════
� 專案架構說明 (AI 補充區)
═══════════════════════════════════════════════════════════════════════════════

⚠️ 此區域由 AI 分析補充,執行腳本後請提供此報告給 AI 進行深度分析

【待補充內容】
• 生物神經網路核心模組說明
• 加密貨幣交易引擎架構
• 數據分析與回測系統
• 模型訓練與預測流程
• 交易策略工作流程
• 技術棧詳細列表

請將此報告提供給 GitHub Copilot,它會分析程式碼並補充詳細的中文說明。


═══════════════════════════════════════════════════════════════════════════════
📌 報告說明
═══════════════════════════════════════════════════════════════════════════════

• 本報告整合了專案的檔案統計、程式碼行數分析和目錄結構
• 已自動排除虛擬環境、快取檔案、IDE 配置等非程式碼目錄
• 圖示說明:
  🐍 Python   📜 JavaScript   📘 TypeScript   📝 Markdown
  ⚙️ JSON      🔧 YAML         🗄️ SQL          ⚡ Shell/Batch
  � Jupyter   🔷 Config       🌐 HTML         🎨 CSS
  📁 目錄      📄 其他檔案

• BioNeuronai 專案架構:
  - Python: 生物神經網路核心、交易引擎、數據分析
  - 模型: 深度學習模型、預測系統
  - 數據: Binance 歷史數據、回測系統
  - 配置: 交易策略、風險管理


═══════════════════════════════════════════════════════════════════════════════
✨ 報告結束
═══════════════════════════════════════════════════════════════════════════════
"@

# 儲存報告
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$reportFile = Join-Path $OutputDir "PROJECT_REPORT_$timestamp.txt"
$reportContent | Out-File $reportFile -Encoding utf8

Write-Host "✅ 報告已生成: PROJECT_REPORT.txt" -ForegroundColor Green

# ==================== 4. 生成 Mermaid 圖表 ====================
Write-Host "`n📊 生成 Mermaid 架構圖..." -ForegroundColor Yellow

$mermaidContent = @"
# BioNeuronai 專案架構圖

## 1. 專案架構概覽

``````mermaid
graph TB
    subgraph "🐍 Python Layer"
        PY_CORE[BioNeuron 核心]
        PY_TRADING[交易引擎]
        PY_DATA[數據處理]
        PY_BACKTEST[回測系統]
    end

    subgraph "🧠 Model Layer"
        ML_NEURAL[神經網路模型]
        ML_PREDICT[預測系統]
    end

    subgraph "📊 Data Layer"
        DATA_BINANCE[Binance 數據]
        DATA_HISTORICAL[歷史數據]
    end

    subgraph "⚙️ Config Layer"
        CONFIG_TRADING[交易配置]
        CONFIG_STRATEGY[策略配置]
    end

    PY_CORE --> ML_NEURAL
    PY_CORE --> PY_TRADING
    PY_TRADING --> PY_DATA
    PY_DATA --> DATA_BINANCE
    PY_DATA --> DATA_HISTORICAL
    PY_BACKTEST --> PY_DATA
    ML_NEURAL --> ML_PREDICT
    ML_PREDICT --> PY_TRADING
    CONFIG_TRADING --> PY_TRADING
    CONFIG_STRATEGY --> PY_TRADING

    style PY_CORE fill:#3776ab
    style ML_NEURAL fill:#FF6B6B
    style DATA_BINANCE fill:#F0B90B
``````

## 2. 程式碼分布統計

``````mermaid
pie title 程式碼行數分布
    "Python ($pythonPct%)" : $($pythonStats.TotalLines)
    "Go ($goPct%)" : $(if ($goStats) { $goStats.TotalLines } else { 0 })
    "Rust ($rustPct%)" : $(if ($rustStats) { $rustStats.TotalLines } else { 0 })
    "TypeScript/JS ($tsPct%)" : $(if ($tsStats) { ($tsStats | Measure-Object -Property TotalLines -Sum).Sum } else { 0 })
    "其他" : $(($locStats | Where-Object { $_.Extension -notin @('.py', '.go', '.rs', '.ts', '.js') } | Measure-Object -Property TotalLines -Sum).Sum)
``````

## 3. 模組關係圖

``````mermaid
graph LR
    subgraph "services"
        aiva_common[aiva_common<br/>共用模組]
        core[core<br/>核心引擎]
        function[function<br/>功能模組]
        integration[integration<br/>整合層]
        scan[scan<br/>掃描引擎]
    end

    subgraph "function 子模組"
        func_py[Python 模組]
        func_go[Go 模組]
        func_rs[Rust 模組]
    end

    subgraph "scan 子模組"
        scan_py[Python 掃描]
        scan_ts[Node.js 掃描]
    end

    core --> aiva_common
    scan --> aiva_common
    function --> aiva_common
    integration --> aiva_common

    integration --> function
    integration --> scan

    function --> func_py
    function --> func_go
    function --> func_rs

    scan --> scan_py
    scan --> scan_ts

    style aiva_common fill:#90EE90
    style core fill:#FFD700
    style function fill:#87CEEB
    style integration fill:#FFA07A
    style scan fill:#DDA0DD
``````

## 4. 技術棧選擇流程圖

``````mermaid
flowchart TD
    Start([新功能需求]) --> Perf{需要高效能?}
    Perf -->|是| Memory{需要記憶體安全?}
    Perf -->|否| Web{是 Web API?}

    Memory -->|是| Rust[使用 Rust<br/>靜態分析/資訊收集]
    Memory -->|否| Go[使用 Go<br/>認證/雲端安全/SCA]

    Web -->|是| Python[使用 Python<br/>FastAPI/核心邏輯]
    Web -->|否| Browser{需要瀏覽器?}

    Browser -->|是| TS[使用 TypeScript<br/>Playwright 掃描]
    Browser -->|否| Python

    Rust --> MQ[Message Queue]
    Go --> MQ
    Python --> MQ
    TS --> MQ

    MQ --> Deploy([部署模組])

    style Rust fill:#CE422B
    style Go fill:#00ADD8
    style Python fill:#3776ab
    style TS fill:#3178C6
``````

生成時間: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
"@

$mermaidFile = Join-Path $OutputDir "tree_$timestamp.mmd"
$mermaidContent | Out-File $mermaidFile -Encoding utf8

Write-Host "✅ Mermaid 圖表已生成: tree_$timestamp.mmd" -ForegroundColor Green

# ==================== 5. 完成 ====================
Write-Host "`n" -NoNewline
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          ✨ 報告生成完成！                    ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "📄 報告位置: $reportFile" -ForegroundColor Cyan
Write-Host "📊 統計資料: 已整合" -ForegroundColor Cyan
Write-Host "🌳 目錄結構: 已整合" -ForegroundColor Cyan
Write-Host "📈 Mermaid 圖表: $mermaidFile" -ForegroundColor Cyan
Write-Host ""

# 打開報告
code $reportFile
