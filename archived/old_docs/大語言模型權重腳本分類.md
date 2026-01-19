# 後訓練時代的架構工程：大語言模型權重後的腳本分類、功能解析與部署自動化全書

## 摘要

在大語言模型（Large Language Model,
LLM）的生命週期中，模型權重的收斂與訓練完成並非終點，而是另一個複雜工程階段的起點。這一階段被稱為「後訓練階段」（Post-Training
Phase），它涉及將原始的神經網絡參數轉化為可部署、可交互且具備高效能的生產級應用。本報告旨在為機器學習工程師、研究人員及系統架構師提供一份詳盡的技術指南，深入剖析在模型權重完成後所需的各類腳本與工具鏈。

報告內容涵蓋六大核心領域：工件整合與格式轉換、計算資源優化（量化）、多維度評估與驗證、推論服務與編排、應用層接口邏輯，以及部署自動化與容器化。我們將不僅限於列舉腳本名稱，而是深入探討其背後的數學原理（如量化中的
Hessian 矩陣應用）、系統架構設計（如 vLLM 的 PagedAttention
機制），以及實際操作中的參數配置策略。透過對 GitHub 開源社群主流工具（如
llama.cpp, AutoGPTQ, vLLM,
LM-Evaluation-Harness）的深度解構，本報告揭示了如何通過精細化的腳本工程，解決記憶體瓶頸、提升推論吞吐量、確保模型安全性，並最終實現從實驗室到生產環境的無縫過渡。

## 第一章：引言 --- 從模型權重到生產力工件

在當前的人工智慧開發範式中，訓練一個基礎模型（Base
Model）或對其進行微調（Fine-Tuning）僅僅完成了智慧生成的「大腦」部分。然而，要讓這個大腦能夠理解人類的指令格式、在有限的硬體資源上運行，並以低延遲響應請求，需要一系列精密的「後訓練」腳本進行處理。

「權重完成」這一術語在實際工程中具有多重含義：它可能指預訓練（Pre-training）結束後的
Checkpoint，也可能指監督式微調（SFT）或人類回饋強化學習（RLHF）後的模型，甚至是參數高效微調（PEFT）產生的
Adapter 權重。無論處於哪個階段，原始權重通常以浮點數（FP32, FP16,
BF16）形式存在，且往往分散在多個分片文件中。直接加載這些權重進行服務不僅效率低落，甚至可能因為格式不兼容或安全性問題而無法運行。

因此，後訓練腳本生態系統應運而生。這些腳本扮演著「編譯器」與「連結器」的角色，將抽象的數學參數實體化為具備工程價值的軟體工件。從將
LoRA
適配器融合進主幹網路的數學加法操作，到為了邊緣計算而進行的極致位元壓縮（Quantization），再到為了對齊人類偏好而設計的自動化評估流程，每一個環節都由特定的腳本驅動。本報告將依照數據流向，系統性地拆解這一過程。

## 第二章：工件整合與格式轉換腳本

在現代 LLM 開發流程中，為了降低訓練成本，開發者廣泛採用 LoRA（Low-Rank
Adaptation）等參數高效微調技術。這導致訓練產物並非一個完整的模型，而是依附於基礎模型的一組增量權重。此外，為了適應不同的推論引擎（如基於
C++ 的 llama.cpp 或基於 Python 的
vLLM），模型文件格式的轉換也是必不可少的一環。

### 2.1 權重合併與適配器融合腳本

當模型經過 PEFT 微調後，我們通常會得到包含 adapter_model.bin 或
adapter_config.json
的目錄。雖然某些推論框架支援動態加載適配器，但在高並發的生產環境中，將適配器權重永久性地合併到基礎模型中（Model
Merging）是提升加載速度和減少顯存碎片化的標準做法。

#### 合併腳本的數學原理與邏輯

合併腳本的核心邏輯建立在線性代數的矩陣加法之上。對於使用 LoRA
的模型，其權重更新量 \$\\Delta W\$ 被分解為兩個低秩矩陣 \$A\$ 和 \$B\$
的乘積。合併腳本的任務是計算 \$W\_{final} = W\_{base} + \\alpha (B
\\times A)\$，並將結果保存為新的權重文件。

典型的合併腳本通常基於 peft 和 transformers
庫構建。以下是此類腳本必須處理的關鍵細節：

1.  **精度管理**：腳本必須能夠處理混合精度。基礎模型可能是 FP16，而 LoRA
    權重可能是 FP32。合併腳本需要將它們統一到目標精度（通常是 FP16 或
    BF16）以避免數值溢出或精度損失 ^1^。

2.  **設備分配**：對於 70B 參數以上的大模型，直接在 GPU
    上進行合併可能會導致顯存不足（OOM）。因此，健壯的合併腳本會通過
    \--device cpu 參數強制在系統 RAM
    中進行矩陣運算，雖然速度較慢，但能確保穩定性 ^2^。

3.  **分片處理（Sharding）**：合併後的模型體積巨大，腳本需要包含分片邏輯，將模型切割成多個
    2GB-10GB 的 chunks（如
    pytorch_model-00001-of-00003.bin），這對於後續在有限記憶體的設備上進行並行加載至關重要
    ^1^。

**腳本功能參數解析：**

- \--base_model_name_or_path：指定基礎模型的 Hugging Face ID
  或本地路徑。

- \--adapter_path：微調後的 Adapter 權重路徑。

- \--output_dir：合併後模型的輸出目錄。

- \--push_to_hub：可選參數，用於在合併完成後自動上傳至 Hugging Face
  Hub，這通常需要集成 huggingface_hub 的 API Token 驗證邏輯 ^3^。

### 2.2 格式轉換腳本：從 PyTorch 到 Safetensors

傳統的 PyTorch 模型使用 Python 的 pickle
模組進行序列化。這帶來了嚴重的安全隱患，因為 pickle
允許在加載過程中執行任意代碼。業界正大規模遷移至 **Safetensors**
格式，這是一種專為深度學習張量設計的安全、快速存儲格式。

轉換腳本的核心機制：

轉換腳本（如 convert_to_safetensors.py）的主要功能是遍歷 PyTorch 的
state_dict，並將張量數據寫入一種支援「零拷貝」（Zero-copy）記憶體映射（mmap）的二進制結構中。

- **記憶體映射優化**：腳本在寫入數據時會對齊內存頁面，使得在後續推論加載時，操作系統可以直接將文件映射到
  RAM，而無需進行昂貴的 CPU 解碼和複製操作。這對於冷啟動時間極為敏感的
  Serverless 部署場景至關重要 ^4^。

- **張量命名標準化**：腳本有時需要處理張量名稱的映射問題，例如將
  model.layers.0.self_attn.q_proj.weight 映射到 Safetensors
  支援的標準命名空間，確保跨框架兼容性。

### 2.3 跨框架轉換腳本：GGUF 與 ONNX

為了在邊緣設備（如筆記本電腦 CPU、移動端）上運行 LLM，必須將模型轉換為
llama.cpp 生態系統支援的 **GGUF** 格式，或通用的 **ONNX** 格式。

#### GGUF 轉換工作流

GGUF（GPT-Generated Unified
Format）是一種二進制格式，它將模型權重、架構超參數、詞彙表（Vocabulary）及量化資訊封裝在單一文件中。

負責此任務的腳本曾經是 convert.py，但隨著架構演進（如 Llama 3
的出現），現在主要由 convert-hf-to-gguf.py 承擔
^5^。此腳本的功能極為複雜，包含以下子模組：

1.  **詞彙表提取與編碼**：腳本必須解析 tokenizer.json 或
    tokenizer.model，處理 BPE（Byte Pair Encoding）或 SentencePiece
    的特殊 Token。對於 Llama 3
    等新模型，腳本需要正確處理擴展的詞彙表大小（如 128k tokens）和特殊的
    tic_token 編碼邏輯 ^6^。

2.  **張量重排（Permutation）**：某些模型架構（如具備 Rotary Positional
    Embeddings, RoPE 的模型）要求 Query 和 Key
    張量在存儲前進行特定的交錯排列，以便 C++ 推論引擎能直接使用 SIMD
    指令集進行計算。轉換腳本負責執行這種預處理 ^7^。

3.  **元數據嵌入**：腳本會將 context length、layer count、head count
    等關鍵參數寫入文件頭，使得 GGUF 文件具備自描述性（Self-contained）。

**代碼執行範例：**

> Bash

python llama.cpp/convert-hf-to-gguf.py./my-merged-model \\\
\--outfile./my-model-f16.gguf \\\
\--outtype f16 \\\
\--vocab-type bpe

此命令不僅轉換格式，還可能涉及將 FP32 權重降轉為 FP16
以節省空間，這是量化前的必要準備 ^5^。

## 第三章：計算優化與量化腳本

在模型權重整合完畢後，面對動輒數百 GB
的顯存需求，**量化（Quantization）**
成為了部署環節中不可或缺的步驟。量化腳本的目標是在盡可能保留模型精度的前提下，將權重從高精度浮點數（FP16/BF16）壓縮為低精度整數（INT8,
INT4 甚至 INT2）。

### 3.1 量化理論與腳本分類

量化腳本通常分為兩大類：

1.  **後訓練量化（Post-Training Quantization,
    PTQ）**：在模型訓練完成後，使用少量校準數據（Calibration
    Data）來計算量化參數（Scale 和 Zero-point）。這是目前最主流的做法。

2.  **量化感知訓練（Quantization-Aware Training,
    QAT）**：在訓練過程中模擬量化誤差。這通常屬於訓練階段，不在此報告的「後訓練」範疇內，但在某些高級優化中，PTQ
    腳本會包含類似 QAT 的微調步驟（如 AutoRound）。

### 3.2 AutoGPTQ 與 GPTQ 量化腳本

GPTQ（Generative Pre-trained Transformer
Quantization）是一種逐層量化算法，它利用二階導數信息（Hessian
矩陣）來優化權重捨入誤差。

AutoGPTQ 腳本架構 8：

AutoGPTQ
庫提供了一套完整的腳本工具鏈，涵蓋量化、評估與基準測試。其核心量化腳本通常包含以下關鍵模組：

- **校準數據加載器**：腳本需要加載一小部分真實數據（如 C4 或 WikiText
  數據集的 128 個樣本）。這些數據被輸入模型以計算每一層的激活值分佈和
  Hessian
  矩陣。腳本必須確保校準數據的分佈與預期推理數據相符，否則量化後的模型會出現「過擬合」於校準集的情況
  ^10^。

- **矩陣分解與打包**：GPTQ 算法核心在於逐列更新權重矩陣。腳本執行
  Cholesky 分解來求解最優更新量，然後將量化後的 INT4
  權重「打包」（Pack）成 INT32
  整數存儲。這一步驟是計算密集型的，腳本通常會調用 CUDA 內核來加速
  ^11^。

**關鍵參數解析：**

- \--bits 4：指定目標位寬。

- \--group_size 128：這是影響精度與速度平衡的關鍵參數。它指定每 128
  個參數共享一組量化參數（Scale/Zero）。若設為 -1
  則為逐通道（Per-channel）量化。腳本需要根據此參數生成對應結構的量化表
  ^10^。

- \--desc_act（Activation
  Order）：這是一個布林開關。當開啟時，腳本會根據激活值的大小重新排列矩陣處理順序，將最重要的權重優先處理。這能顯著提升精度（Perplexity），但生成的模型在某些舊版推理內核上可能無法加速，腳本使用者需根據部署環境權衡
  ^8^。

### 3.3 AWQ（Activation-aware Weight Quantization）腳本

AWQ 算法認為並非所有權重都同等重要，約 1%
的權重對模型性能有決定性影響。AWQ
腳本的核心邏輯不在於複雜的權重更新，而在於「保護」這 1%
的顯著權重（Salient Weights）。

**腳本工作流：**

1.  **激活值統計**：腳本運行前向傳播，收集每一層的激活值幅度。

2.  **搜尋最優縮放因子**：腳本會在一個搜尋空間內尋找最佳的縮放因子
    \$\\alpha\$，將顯著權重放大，同時將輸入激活值縮小，從而減少量化誤差對這些關鍵權重的影響
    ^7^。

3.  **Clip 與 Round**：應用縮放後，腳本執行標準的 Round-to-nearest
    量化。

由於 vLLM 等高性能引擎對 AWQ 有原生優化支援，AWQ
腳本在生產環境部署中正變得越來越流行 ^12^。

### 3.4 GGUF 的 K-Quants 量化腳本

在 llama.cpp 生態中，量化由 llama-quantize 二進制工具（或對應的 Python
綁定腳本）執行。它引入了 **K-Quants** 方法，這是一種混合精度量化策略。

腳本邏輯分析：

與統一的 INT4 量化不同，K-Quants
腳本允許對模型的不同部分使用不同的精度。例如，q4_k_m 模式下，Attention
的 v 權重可能使用 6-bit 量化，而 Feed-forward 的權重使用 4-bit
量化。這種精細的粒度控制要求腳本具備對模型架構的深刻理解，能夠識別並區分不同類型的張量塊（Block）6。

## 第四章：多維度評估與驗證腳本

模型經過合併與量化後，其能力是否受損？是否引入了新的安全漏洞？這需要通過一系列評估腳本來驗證。評估不僅僅是跑一個分數，它是決定模型能否上線的「質量閘門」（Quality
Gate）。

### 4.1 學術基準測試腳本：LM-Evaluation-Harness

EleutherAI 開發的 lm-evaluation-harness
是目前最權威的開源評估框架。它將模型加載、任務定義、數據處理和結果聚合封裝成了一套標準化的腳本介面
^13^。

#### 腳本架構解析

該工具的核心腳本 lm_eval 採用模組化設計，分離了 **Model
Backend**（模型後端）與 **Task Registry**（任務註冊表）。

1.  **模型適配器**：腳本透過 \--model 參數調用不同的適配器。

    - \--model hf：使用 Hugging Face Transformers
      加載模型，適用於本地單卡或多卡評估。

    - \--model vllm：直接調用 vLLM 引擎進行評估，這通常比 HF
      快得多，且能測試模型在實際服務環境下的表現 ^13^。

    - \--model openai：通過 API 評估黑盒模型。

2.  Log-likelihood（對數似然）評估機制：\
    對於選擇題（如 MMLU,
    HellaSwag），腳本通常不讓模型生成文本，而是計算選項的條件概率。

    - 腳本構建 Prompt：「法國的首都是：」

    - 腳本分別計算接續詞為「巴黎」、「倫敦」、「柏林」的
      Log-Probability。

    - 腳本選擇概率最高的選項並與標準答案比對。這種方法消除了生成隨機性（Temperature）的干擾，是評估基礎模型能力的黃金標準
      ^15^。

**關鍵參數與優化：**

- \--batch_size
  auto：這是一個非常實用的腳本功能。它會自動進行二分查找，探測當前 GPU
  顯存能容納的最大 Batch Size，從而在不發生 OOM 的前提下最大化評估速度
  ^16^。

- \--num_fewshot：控制 Prompt 中包含的範例數量（Few-shot
  prompting）。腳本需要動態組裝這些範例，這會顯著增加 Context
  長度，因此在評估長上下文模型時需謹慎設置 ^15^。

### 4.2 LLM-as-a-Judge：主觀能力評估腳本

對於開放式問題（如「寫一首關於 Rust
語言的詩」），傳統的字串匹配指標（BLEU, ROUGE）失效。這時需要使用
**LLM-as-a-Judge** 腳本，即讓一個更強的模型（如 GPT-4）充當裁判。

FastChat 的 MT-Bench 腳本 17：

這類腳本通常包含三個階段：

1.  **生成階段**：腳本遍歷問題集（Question
    Registry），調用待測模型生成答案。

2.  **評判階段**：腳本將問題、待測模型的答案以及參考答案（可選）組裝成一個
    Prompt 發送給裁判模型（Judge Model）。Prompt
    中包含詳細的評分標準（Rubric），要求裁判打分（1-10分）並給出理由。

3.  **分析階段**：腳本解析裁判的輸出，繪製雷達圖或計算平均分。

DeepEval 框架：

DeepEval
的腳本進一步細化了指標，提供了諸如「幻覺檢測（Hallucination）」、「忠實度（Faithfulness）」等專項評估腳本。這些腳本對於
RAG（檢索增強生成）系統的評估尤為重要，它們會檢查模型生成的答案是否能在檢索到的上下文中找到依據
18。

### 4.3 安全性與對抗性測試腳本

隨著 AI 安全日益受重視，安全性評估腳本成為了標準配置。

- **對抗性攻擊腳本**：這些腳本會自動生成「越獄」（Jailbreak）Prompt（如
  DAN 模式），測試模型是否會繞過安全防護輸出有害內容。

- **量化漏洞檢測**：最新的研究指出，量化過程可能會破壞模型的安全對齊。專門的腳本（如
  ^4^ 中提及的框架）會對比全精度模型和量化模型在惡意 Prompt
  下的表現差異，確保量化沒有引入新的安全漏洞。

## 第五章：高效推論服務與調度腳本

評估通過後，模型需要被封裝成服務（Service）。這一階段的腳本負責啟動高性能的
HTTP 伺服器，管理 GPU 顯存，並調度並發請求。

### 5.1 vLLM 服務啟動腳本

vLLM 是目前最先進的開源推論引擎之一，其核心技術 **PagedAttention**
解決了 KV Cache 的顯存碎片化問題。啟動 vLLM 的腳本（vllm
serve）是生產環境中最常見的入口點。

#### 核心參數與系統影響分析

^20^

一個典型的生產級啟動腳本如下：

> Bash

python -m vllm.entrypoints.openai.api_server \\\
\--model /path/to/model \\\
\--tensor-parallel-size 2 \\\
\--gpu-memory-utilization 0.9 \\\
\--max-model-len 4096 \\\
\--disable-log-requests

1.  \--tensor-parallel-size（張量並行度）：\
    這是分佈式推論的關鍵參數。對於一個 70B 的模型，單張 A100 (80GB)
    無法容納（即便量化後加上 KV Cache 也捉襟見肘）。腳本設置此參數為 2
    或 4 時，會啟動 Ray 分佈式框架，將模型的權重矩陣切分到多張 GPU
    上。推論時，這些 GPU 必須通過 NVLink
    進行極高頻寬的通訊（All-Reduce）。腳本必須確保底層硬體拓撲支援這種通訊，否則性能會不如單卡
    12。

2.  \--gpu-memory-utilization（顯存佔用率）：\
    此參數決定了 vLLM 預留多少顯存給 KV Cache（上下文記憶體）。默認為
    0.9。

    - *深度解析*：如果腳本將此值設得太高（如
      0.99），一旦有其他進程（如監控
      Agent）佔用顯存，服務就會崩潰。如果設得太低，則可同時處理的併發請求數（Batch
      Size）會減少，降低吞吐量。腳本編寫者需根據實際部署環境進行微調。

3.  \--max-model-len（最大上下文長度）：\
    許多模型聲稱支援 128k
    上下文，但這需要巨大的顯存。為了防止用戶惡意發送超長請求導致
    OOM，啟動腳本通常會強制限制此值（如 4096 或
    8192），以保障服務的穩定性 20。

### 5.2 FastChat 的分佈式架構腳本

FastChat 採用了 Controller-Worker-Server
的三層架構，適合需要管理多個模型實例的場景 ^17^。

- **Controller 腳本**：啟動一個中心註冊表，負責負載均衡。

- **Model Worker 腳本**：在具體的 GPU
  節點上啟動，負責加載模型並執行推論。它會向 Controller 發送心跳包。

- API Server 腳本：提供兼容 OpenAI 格式的 HTTP 接口，將請求轉發給
  Controller。\
  這種分離架構允許運維人員通過腳本動態增減 Worker 節點，實現彈性擴縮容。

### 5.3 邊緣端 llama.cpp Server 腳本

對於資源受限的環境，llama-server
腳本提供了一個極其輕量級的解決方案。它支援 **Slot
Management**（插槽管理），允許腳本預分配固定數量的上下文插槽。這意味著即便在
CPU 上，也可以並行處理多個用戶的請求（雖然延遲較高），只要總 Token
數不超過內存限制 ^22^。

## 第六章：應用接口與交互邏輯腳本

在底層 API 服務之上，應用層腳本負責處理用戶輸入、格式化
Prompt，並呈現結果。這通常涉及 Python 的 Web 框架如 Gradio 或
Streamlit。

### 6.1 Chat Template 應用邏輯

模型並不直接理解「對話」，它只理解 Token 序列。因此，應用層腳本必須使用
**Chat Template** 將對話歷史轉換為模型訓練時使用的特定格式。

apply_chat_template 的腳本實作 23：

Hugging Face Transformers 庫提供了一個強大的工具方法：

> Python

formatted_prompt = tokenizer.apply_chat_template(\
messages,\
tokenize=False,\
add_generation_prompt=True\
)

- **Jinja2 模板引擎**：腳本會讀取 tokenizer_config.json 中的
  chat_template 字段。這是一個 Jinja2 模板，定義了如何插入特殊 Token（如
  \`\`, \<\<SYS\>\>, \<\|im_start\|\>）。

- **add_generation_prompt=True 的重要性**：此參數告訴腳本在 Prompt
  的末尾添加一個觸發助手回答的 Token（如
  \<\|im_start\|\>assistant）。如果腳本遺漏此參數，模型可能會繼續續寫用戶的問題，而不是回答問題
  ^25^。

### 6.2 Gradio 交互式介面腳本

Gradio 是快速構建 LLM Demo 的標準工具。其腳本通常包含以下邏輯：

1.  **流式傳輸（Streaming）處理**：為了提供良好的用戶體驗，腳本不能等待整個答案生成完畢才返回。它必須使用
    Python 的生成器（Generator）模式，從 API 接收數據塊（Chunk），並實時
    yield 給前端更新 UI ^26^。

2.  **歷史記錄管理**：腳本需要維護 history
    列表。在發送請求前，腳本通常會檢查歷史記錄的總 Token
    數，並執行截斷（Truncation）操作，以防止超出模型的上下文窗口 ^28^。

## 第七章：部署自動化與容器化腳本

最後，為了將上述所有組件交付給運維團隊，需要編寫容器化和自動化部署腳本。

### 7.1 Docker 容器化腳本

編寫 LLM 的 Dockerfile 需要處理龐大的依賴和硬體驅動。

- **基礎鏡像選擇**：通常基於 nvidia/cuda 或官方的 vllm/vllm-openai。

- **緩存掛載（Volume
  Mounting）**：這是一個關鍵的優化點。生產環境的啟動腳本（docker
  run）必須包含 -v
  /host/cache:/root/.cache/huggingface。否則，每次容器重啟都會重新下載數十
  GB 的模型權重，導致啟動時間極長且浪費頻寬 ^29^。

- **共享內存（Shared Memory）配置**：PyTorch 和 NCCL（NVIDIA
  集合通信庫）依賴共享內存進行進程間通訊。Docker 默認的 SHM
  大小（64MB）遠遠不夠。部署腳本必須包含 \--ipc=host 或 \--shm-size 16g
  參數，否則在多卡推論時會直接報錯崩潰 ^31^。

### 7.2 Kubernetes 入口點（Entrypoint）腳本

在 K8s 環境中，entrypoint.sh 腳本負責在容器啟動時動態配置服務。

- **硬體感知**：腳本可以使用 nvidia-smi -L \| wc -l 自動檢測可用的 GPU
  數量，並據此設置 TP_SIZE（Tensor Parallel
  Size）環境變量，實現同一鏡像在不同規格節點上的自適應部署。

- **健康檢查（Health Check）**：腳本應包含 curl localhost:8000/health
  邏輯，配合 K8s 的 Liveness
  Probe，確保只有在模型完全加載並準備好接受請求後，流量才會被路由進來
  ^32^。

## 第八章：結論

大語言模型的後訓練階段是一個集算法、系統工程與運維於一體的複雜領域。從權重合併的算術運算，到量化過程中的矩陣分解；從評估腳本的統計學原理，到推論服務的並發調度，每一個環節都需要專門的腳本來支撐。

本報告詳細梳理了這一流程中的關鍵腳本及其功能。對於工程團隊而言，建立一套標準化、自動化的後訓練腳本庫（Script
Library），不僅是提升模型迭代效率的關鍵，更是確保 AI
應用穩定、安全、高效運行的基石。隨著 Agentic
Workflow（代理工作流）和端側模型的興起，未來的後訓練腳本將更加注重工具調用能力的評估以及異構硬體上的極致編譯優化。

### 表格：後訓練關鍵腳本分類與功能總覽

  ------------------------------------------------------------------------------------------------------------------------------------------------------------
  **腳本類別**     **核心功能**                         **代表工具/庫**   **關鍵參數/標誌**           **系統影響與備註**
  ---------------- ------------------------------------ ----------------- --------------------------- --------------------------------------------------------
  **權重整合**     合併 LoRA 適配器；轉換格式           peft,             \--device cpu, \--outtype   決定模型的加載速度與安全性；CPU 合併可避免 OOM。
                   (Safetensors, GGUF)。                transformers,                                 
                                                        llama.cpp                                     

  **計算優化**     降低權重精度 (INT4/INT8)             AutoGPTQ,         \--group_size, \--desc_act  影響推論速度與精度；Group Size 128 是常見平衡點。
                   以節省顯存與頻寬。                   AutoAWQ,                                      
                                                        llama-quantize                                

  **評估驗證**     基準測試                             lm-eval,          \--batch_size auto,         決定模型是否達標可上線；Auto Batch Size 防止崩潰。
                   (MMLU)、主觀能力裁判、安全性檢測。   FastChat,         \--num_fewshot              
                                                        DeepEval                                      

  **推論服務**     提供 API 接口；管理 KV Cache         vLLM, TGI,        \--tensor-parallel-size,    直接決定系統吞吐量與延遲；TP 設置需匹配物理 GPU 數。
                   與請求調度。                         FastChat          \--gpu-memory-utilization   

  **應用交互**     格式化對話                           Gradio,           apply_chat_template,        確保模型正確理解對話結構；錯誤的 Template
                   Prompt；管理用戶介面與歷史記錄。     Streamlit,        add_generation_prompt       會導致生成異常。
                                                        Tokenizer                                     

  **部署自動化**   容器封裝、環境變量配置、健康檢查。   Docker,           \--ipc=host, \--shm-size    確保生產環境穩定性；共享內存配置對於多卡推論至關重要。
                                                        Kubernetes, Bash                              
  ------------------------------------------------------------------------------------------------------------------------------------------------------------

#### 引用的著作

1.  smol training playbook - GitHub Gist, 檢索日期：1月 19, 2026，
    [[https://gist.github.com/jph00/3c97a2c6c5075c4e7b98faae634b033a]{.underline}](https://gist.github.com/jph00/3c97a2c6c5075c4e7b98faae634b033a)

2.  mlabonne/llm-course: Course to get into Large Language Models (LLMs)
    with roadmaps and Colab notebooks. - GitHub, 檢索日期：1月 19,
    2026，
    [[https://github.com/mlabonne/llm-course]{.underline}](https://github.com/mlabonne/llm-course)

3.  rasbt/LLMs-from-scratch: Implement a ChatGPT-like LLM in \... -
    GitHub, 檢索日期：1月 19, 2026，
    [[https://github.com/rasbt/LLMs-from-scratch]{.underline}](https://github.com/rasbt/LLMs-from-scratch)

4.  Exploiting LLM Quantization - NIPS papers, 檢索日期：1月 19, 2026，
    [[https://proceedings.neurips.cc/paper_files/paper/2024/file/496720b3c860111b95ac8634349dcc88-Paper-Conference.pdf]{.underline}](https://proceedings.neurips.cc/paper_files/paper/2024/file/496720b3c860111b95ac8634349dcc88-Paper-Conference.pdf)

5.  Why is convert.py missing? #7658 - ggml-org/llama.cpp - GitHub,
    檢索日期：1月 19, 2026，
    [[https://github.com/ggml-org/llama.cpp/issues/7658]{.underline}](https://github.com/ggml-org/llama.cpp/issues/7658)

6.  llama.cpp guide - Running LLMs locally, on any hardware, from
    scratch ::, 檢索日期：1月 19, 2026，
    [[https://steelph0enix.github.io/posts/llama-cpp-guide/]{.underline}](https://steelph0enix.github.io/posts/llama-cpp-guide/)

7.  The Complete Guide to LLM Quantization with vLLM: Benchmarks & Best
    Practices, 檢索日期：1月 19, 2026，
    [[https://docs.jarvislabs.ai/blog/vllm-quantization-complete-guide-benchmarks]{.underline}](https://docs.jarvislabs.ai/blog/vllm-quantization-complete-guide-benchmarks)

8.  AutoGPTQ/AutoGPTQ: An easy-to-use LLMs quantization package with
    user-friendly apis, based on GPTQ algorithm. - GitHub, 檢索日期：1月
    19, 2026，
    [[https://github.com/AutoGPTQ/AutoGPTQ]{.underline}](https://github.com/AutoGPTQ/AutoGPTQ)

9.  Efficient Model Quantization with AutoGPTQ: A Comprehensive Guide -
    Onegen AI, 檢索日期：1月 19, 2026，
    [[https://www.onegen.ai/project/efficient-model-quantization-with-autogptq-a-comprehensive-guide/]{.underline}](https://www.onegen.ai/project/efficient-model-quantization-with-autogptq-a-comprehensive-guide/)

10. AutoGPTQ/examples/quantization/basic_usage.py at main - GitHub,
    檢索日期：1月 19, 2026，
    [[https://github.com/AutoGPTQ/AutoGPTQ/blob/main/examples/quantization/basic_usage.py]{.underline}](https://github.com/AutoGPTQ/AutoGPTQ/blob/main/examples/quantization/basic_usage.py)

11. Model quantization techniques - GPTQ - AMD ROCm documentation,
    檢索日期：1月 19, 2026，
    [[https://rocm.docs.amd.com/en/docs-6.1.5/how-to/llm-fine-tuning-optimization/model-quantization.html]{.underline}](https://rocm.docs.amd.com/en/docs-6.1.5/how-to/llm-fine-tuning-optimization/model-quantization.html)

12. vllm-project/vllm: A high-throughput and memory-efficient \... -
    GitHub, 檢索日期：1月 19, 2026，
    [[https://github.com/vllm-project/vllm]{.underline}](https://github.com/vllm-project/vllm)

13. Evaluating LLM Accuracy with lm-evaluation-harness for local server:
    A Comprehensive Guide \| by Doil Kim \| Medium, 檢索日期：1月 19,
    2026，
    [[https://medium.com/@kimdoil1211/evaluating-llm-accuracy-with-lm-evaluation-harness-for-local-server-a-comprehensive-guide-933df1361d1d]{.underline}](https://medium.com/@kimdoil1211/evaluating-llm-accuracy-with-lm-evaluation-harness-for-local-server-a-comprehensive-guide-933df1361d1d)

14. EleutherAI/lm-evaluation-harness: A framework for few-shot
    evaluation of language models., 檢索日期：1月 19, 2026，
    [[https://github.com/EleutherAI/lm-evaluation-harness]{.underline}](https://github.com/EleutherAI/lm-evaluation-harness)

15. Integrating benchmarks into LM Evaluation Harness - Hugging Face,
    檢索日期：1月 19, 2026，
    [[https://huggingface.co/blog/Neo111x/integrating-benchmarks-into-lm-evaluation-harness]{.underline}](https://huggingface.co/blog/Neo111x/integrating-benchmarks-into-lm-evaluation-harness)

16. lm-evaluation-harness · 00252f91a22e172e2e28a4027ee2d640fc0492a4 ·
    Tambe Lab / BlockDialect - Stanford GitLab, 檢索日期：1月 19, 2026，
    [[https://code.stanford.edu/tambe-lab/blockdialect/-/tree/00252f91a22e172e2e28a4027ee2d640fc0492a4/lm-evaluation-harness]{.underline}](https://code.stanford.edu/tambe-lab/blockdialect/-/tree/00252f91a22e172e2e28a4027ee2d640fc0492a4/lm-evaluation-harness)

17. lm-sys/FastChat: An open platform for training, serving, and
    evaluating large language models. Release repo for Vicuna and
    Chatbot Arena. - GitHub, 檢索日期：1月 19, 2026，
    [[https://github.com/lm-sys/FastChat]{.underline}](https://github.com/lm-sys/FastChat)

18. Top 5 Open-Source LLM Evaluation Platforms - KDnuggets,
    檢索日期：1月 19, 2026，
    [[https://www.kdnuggets.com/top-5-open-source-llm-evaluation-platforms]{.underline}](https://www.kdnuggets.com/top-5-open-source-llm-evaluation-platforms)

19. LLM Evaluation Metrics: The Ultimate LLM Evaluation Guide -
    Confident AI, 檢索日期：1月 19, 2026，
    [[https://www.confident-ai.com/blog/llm-evaluation-metrics-everything-you-need-for-llm-evaluation]{.underline}](https://www.confident-ai.com/blog/llm-evaluation-metrics-everything-you-need-for-llm-evaluation)

20. vLLM server arguments \| Red Hat AI Inference Server \| 3.0 - Red
    Hat Documentation, 檢索日期：1月 19, 2026，
    [[https://docs.redhat.com/en/documentation/red_hat_ai_inference_server/3.0/html-single/vllm_server_arguments/index]{.underline}](https://docs.redhat.com/en/documentation/red_hat_ai_inference_server/3.0/html-single/vllm_server_arguments/index)

21. Chapter 2. Complete list of vLLM server arguments - Red Hat
    Documentation, 檢索日期：1月 19, 2026，
    [[https://docs.redhat.com/en/documentation/red_hat_ai_inference_server/3.0/html/vllm_server_arguments/all-server-arguments-server-arguments]{.underline}](https://docs.redhat.com/en/documentation/red_hat_ai_inference_server/3.0/html/vllm_server_arguments/all-server-arguments-server-arguments)

22. ggml-org/llama.cpp: LLM inference in C/C++ - GitHub, 檢索日期：1月
    19, 2026，
    [[https://github.com/ggml-org/llama.cpp]{.underline}](https://github.com/ggml-org/llama.cpp)

23. Templates for Chat Models - Hugging Face, 檢索日期：1月 19, 2026，
    [[https://huggingface.co/docs/transformers/v4.34.0/chat_templating]{.underline}](https://huggingface.co/docs/transformers/v4.34.0/chat_templating)

24. Templates for Chat Models - Hugging Face, 檢索日期：1月 19, 2026，
    [[https://huggingface.co/docs/transformers/v4.37.1/chat_templating]{.underline}](https://huggingface.co/docs/transformers/v4.37.1/chat_templating)

25. Chat templates - Hugging Face, 檢索日期：1月 19, 2026，
    [[https://huggingface.co/docs/transformers/chat_templating]{.underline}](https://huggingface.co/docs/transformers/chat_templating)

26. Creating A Chatbot Fast - Gradio, 檢索日期：1月 19, 2026，
    [[https://www.gradio.app/guides/creating-a-chatbot-fast]{.underline}](https://www.gradio.app/guides/creating-a-chatbot-fast)

27. Gradio Chatbot + LiteLLM Tutorial, 檢索日期：1月 19, 2026，
    [[https://docs.litellm.ai/docs/tutorials/gradio_integration]{.underline}](https://docs.litellm.ai/docs/tutorials/gradio_integration)

28. Quickstart - Gradio, 檢索日期：1月 19, 2026，
    [[https://www.gradio.app/guides/quickstart]{.underline}](https://www.gradio.app/guides/quickstart)

29. Deploying LLM APIs on GPU Server with Docker - ServerMania,
    檢索日期：1月 19, 2026，
    [[https://www.servermania.com/kb/articles/deploy-llm-api-docker-gpu-server]{.underline}](https://www.servermania.com/kb/articles/deploy-llm-api-docker-gpu-server)

30. Deploy vLLM with Docker Using Just One Script: A Complete Guide \|
    Medium, 檢索日期：1月 19, 2026，
    [[https://medium.com/@kimdoil1211/effortless-vllm-deployment-with-docker-a-comprehensive-guide-2a23119839e2]{.underline}](https://medium.com/@kimdoil1211/effortless-vllm-deployment-with-docker-a-comprehensive-guide-2a23119839e2)

31. Using Docker - vLLM, 檢索日期：1月 19, 2026，
    [[https://docs.vllm.ai/en/v0.8.4/deployment/docker.html]{.underline}](https://docs.vllm.ai/en/v0.8.4/deployment/docker.html)

32. Quick: Deploy with vLLM - Overview \| Verda Cloud Docs,
    檢索日期：1月 19, 2026，
    [[https://docs.verda.com/containers/tutorials/deploy-with-vllm-quick]{.underline}](https://docs.verda.com/containers/tutorials/deploy-with-vllm-quick)
