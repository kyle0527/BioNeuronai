"""
知識蒸餾訓練 - AI老師版
========================
使用 AI 生成的高質量英中雙語數據來訓練模型
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import sys
from pathlib import Path
import json
from tqdm import tqdm
import time
import hashlib
from datetime import datetime
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from nlp.tiny_llm import TinyLLM, TinyLLMConfig, load_llm, save_llm
from nlp.bilingual_tokenizer import BilingualTokenizer


# ============================================================================
# AI 老師生成的訓練數據
# ============================================================================

AI_TEACHER_DATA = {
    "conversations": [
        # 英文對話
        {"input": "Hello, how are you?", "output": "I'm doing great, thank you! How can I help you today?"},
        {"input": "What is AI?", "output": "AI stands for Artificial Intelligence. It's the simulation of human intelligence by machines."},
        {"input": "Can you help me?", "output": "Of course! I'm here to help. What do you need assistance with?"},
        {"input": "Tell me a joke.", "output": "Why did the programmer quit his job? Because he didn't get arrays!"},
        {"input": "What's the weather like?", "output": "I'm an AI and don't have access to real-time weather data, but I can help you find weather information."},
        
        # 中文對話
        {"input": "你好，你是誰？", "output": "你好！我是一個人工智慧助手，很高興認識你。"},
        {"input": "什麼是機器學習？", "output": "機器學習是人工智慧的一個分支，讓電腦從數據中學習和改進。"},
        {"input": "你能幫我嗎？", "output": "當然可以！我很樂意幫助你。請告訴我你需要什麼。"},
        {"input": "今天天氣如何？", "output": "我是AI助手，無法直接獲取天氣資訊，但我可以教你如何查詢天氣。"},
        {"input": "謝謝你的幫助。", "output": "不客氣！很高興能幫到你。有其他問題隨時問我。"},
        
        # 英中混合
        {"input": "What is Python?", "output": "Python 是一種流行的編程語言，簡單易學且功能強大。"},
        {"input": "How to learn AI?", "output": "學習AI需要掌握數學、編程和機器學習基礎知識。"},
        {"input": "Tell me about machine learning.", "output": "機器學習讓電腦能夠從經驗中學習，無需明確編程。"},
    ],
    
    "knowledge": [
        # 英文知識
        "Artificial Intelligence is transforming the world in many ways.",
        "Machine learning algorithms can learn from data and make predictions.",
        "Deep learning uses neural networks with multiple layers.",
        "Natural language processing helps computers understand human language.",
        "Computer vision enables machines to interpret visual information.",
        
        # 中文知識
        "人工智慧正在改變世界的方方面面。",
        "機器學習算法可以從數據中學習並做出預測。",
        "深度學習使用多層神經網絡。",
        "自然語言處理幫助電腦理解人類語言。",
        "計算機視覺使機器能夠解釋視覺信息。",
        
        # 混合內容
        "Python is widely used in AI and data science.",
        "PyTorch 和 TensorFlow 是流行的深度學習框架。",
        "Transformers have revolutionized natural language processing.",
        "GPT 模型展示了大型語言模型的強大能力。",
    ],
    
    "instructions": [
        # 英文指令
        {"instruction": "Explain what AI is.", "response": "AI, or Artificial Intelligence, refers to computer systems that can perform tasks that typically require human intelligence, such as learning, reasoning, and problem-solving."},
        {"instruction": "Write a greeting.", "response": "Hello! Welcome! It's great to see you today. How can I assist you?"},
        {"instruction": "Describe Python.", "response": "Python is a high-level programming language known for its simplicity and readability. It's widely used in web development, data science, and AI."},
        
        # 中文指令
        {"instruction": "解釋什麼是深度學習。", "response": "深度學習是機器學習的一個子領域，使用多層神經網絡來學習數據的複雜模式。它在圖像識別、語音處理等領域表現出色。"},
        {"instruction": "寫一個問候語。", "response": "你好！歡迎！很高興今天見到你。我能為你做些什麼？"},
        {"instruction": "描述人工智慧。", "response": "人工智慧是指讓機器模擬人類智能的技術，包括學習、推理和解決問題的能力。"},
    ],
    
    # 🔍 功能性訓練數據
    "functional_abilities": {
        # 搜索能力
        "search": [
            {"query": "搜索關於機器學習的資料", "reasoning": "我需要找機器學習相關內容。首先確定關鍵詞：機器學習、ML、算法。然後搜索包含這些詞的文檔。", "action": "搜索"},
            {"query": "Find information about Python", "reasoning": "I need to search for Python-related content. Keywords: Python, programming, code. Search documents containing these terms.", "action": "search"},
            {"query": "找出最新的AI論文", "reasoning": "需要搜索AI論文。關鍵詞：AI、人工智慧、論文、paper。按時間排序，找最新的。", "action": "搜索最新"},
            {"query": "查找錯誤代碼", "reasoning": "要搜索錯誤相關的代碼。關鍵詞：error、錯誤、bug、異常。查找包含錯誤處理的代碼段。", "action": "代碼搜索"},
        ],
        
        # 判斷能力
        "judgment": [
            {"situation": "這段代碼有語法錯誤嗎？print('hello'", "analysis": "檢查代碼：print('hello' - 缺少右括號。", "judgment": "是的，有語法錯誤：缺少右括號 )", "correct": "print('hello')"},
            {"situation": "Is this number prime? 17", "analysis": "Check if 17 is prime. Divisors to check: 2, 3, 4. 17/2=8.5, 17/3=5.67, 17/4=4.25. No integer divisors.", "judgment": "Yes, 17 is a prime number.", "reason": "Only divisible by 1 and itself"},
            {"situation": "這個邏輯對嗎？如果下雨就帶雨傘，現在沒下雨，所以不用帶雨傘", "analysis": "分析邏輯：前提-下雨→帶傘。當前-沒下雨。結論-不帶傘。", "judgment": "邏輯有瑕疵", "reason": "可能等會下雨，應該看天氣預報"},
            {"situation": "Which is faster: linear search or binary search?", "analysis": "Compare algorithms: Linear search O(n), Binary search O(log n). For large datasets, log n < n.", "judgment": "Binary search is faster", "condition": "if data is sorted"},
        ],
        
        # 推理能力
        "reasoning": [
            {"premise": "所有程式設計師都懂邏輯。小明是程式設計師。", "reasoning": "前提1：程式設計師→懂邏輯。前提2：小明=程式設計師。推論：小明→懂邏輯。", "conclusion": "所以小明懂邏輯。"},
            {"premise": "If it's raining, the ground is wet. The ground is wet.", "reasoning": "Premise: rain → wet ground. Observation: wet ground. However, wet ground doesn't necessarily mean rain (could be sprinkler).", "conclusion": "We cannot conclude it's raining. Affirming the consequent fallacy."},
            {"premise": "Python比Java簡單。Java比C++簡單。", "reasoning": "建立關係：Python < Java < C++（難度）。遞移性質：如果A<B且B<C，則A<C。", "conclusion": "所以Python比C++簡單。"},
            {"premise": "All AI models need data. This needs data.", "reasoning": "Premise: AI models → need data. Observation: X needs data. But many things need data (databases, analytics, etc.).", "conclusion": "Cannot conclude this is an AI model. Invalid reasoning."},
        ],
        
        # 分析能力
        "analysis": [
            {"data": "程式執行時間：第一次10秒，第二次8秒，第三次7秒", "pattern": "觀察趨勢：10→8→7，時間遞減。", "analysis": "可能原因：1) 緩存效應 2) JIT編譯 3) 系統預熱", "conclusion": "執行速度正在優化"},
            {"data": "Error rate: Day1=50%, Day2=30%, Day3=15%", "pattern": "Pattern: Decreasing error rate. 50→30→15, approximately halving.", "analysis": "Possible reasons: 1) Model is learning 2) Data quality improving 3) Bug fixes", "conclusion": "Training is progressing well"},
            {"data": "用戶反饋：功能A使用率80%，功能B使用率5%", "pattern": "使用率差異大：A遠高於B。", "analysis": "分析原因：1) A更實用 2) B隱藏太深 3) B不好用 4) 用戶不知道B存在", "conclusion": "需要改進功能B或提高其可見度"},
            {"data": "Model accuracy: Train=95%, Test=60%", "pattern": "Large gap between train and test accuracy: 35% difference.", "analysis": "This indicates overfitting. Model memorized training data but fails to generalize.", "conclusion": "Need regularization, more data, or simpler model"},
        ],
        
        # 決策能力
        "decision": [
            {"scenario": "記憶體使用率95%，程式變慢", "options": "1)增加記憶體 2)優化代碼 3)重啟程式 4)關閉其他程式", "analysis": "緊急度高。短期：選項3或4。長期：選項1或2。", "decision": "立即：重啟程式並關閉不必要程式。之後：優化代碼和增加記憶體。"},
            {"scenario": "Choose sorting algorithm for 1 million records", "options": "1) Bubble sort 2) Quick sort 3) Merge sort 4) Insertion sort", "analysis": "Need efficient algorithm. Bubble O(n²), Quick O(n log n), Merge O(n log n), Insertion O(n²). For large data, avoid O(n²).", "decision": "Use Quick sort or Merge sort. Quick sort if average case, Merge sort if need stability."},
            {"scenario": "模型準確率85%但速度慢，需要改進", "options": "1)簡化模型 2)增加硬體 3)優化算法 4)降低準確率要求", "analysis": "權衡：準確率vs速度。取決於應用場景。", "decision": "如果速度更重要：選項1或3。如果準確率重要：選項2。靈活：選項4（如85%→83%換取2倍速度）。"},
            {"scenario": "Bug in production: affects 10% users", "options": "1) Hotfix immediately 2) Roll back 3) Wait for next release 4) Disable feature", "analysis": "Impact: 10% users affected. Severity depends on bug type. Balance: fix speed vs stability.", "decision": "If critical: Option 1 or 2. If minor: Option 4 temporarily, fix in next release. Test hotfix thoroughly."},
        ],
        
        # 比較能力
        "comparison": [
            {"items": "Python vs JavaScript", "dimensions": "語法、用途、速度、生態", "comparison": "語法：Python更簡潔。用途：Python偏數據科學，JS偏Web。速度：JS稍快。生態：都很豐富。", "conclusion": "選擇取決於應用：數據/AI選Python，Web前端選JS。"},
            {"items": "SQL vs NoSQL databases", "dimensions": "structure, scalability, consistency, use cases", "comparison": "Structure: SQL structured, NoSQL flexible. Scalability: NoSQL horizontal, SQL vertical. Consistency: SQL ACID, NoSQL eventual. Use: SQL transactions, NoSQL big data.", "conclusion": "SQL for complex queries and transactions. NoSQL for scalability and flexibility."},
            {"items": "機器學習 vs 深度學習", "dimensions": "複雜度、數據需求、準確率、解釋性", "comparison": "複雜度：深度學習更複雜。數據：深度學習需要更多。準確率：深度學習在大數據上更高。解釋性：機器學習更好解釋。", "conclusion": "小數據/需要解釋性：機器學習。大數據/高準確率需求：深度學習。"},
        ],
        
        # 問題解決
        "problem_solving": [
            {"problem": "程式運行很慢", "diagnosis": "1)檢查CPU使用率 2)檢查記憶體 3)分析瓶頸", "steps": "第一步：性能分析找瓶頸。第二步：針對瓶頸優化。第三步：測試改進效果。", "solution": "使用性能分析工具，找出最慢的函數，優化算法或添加緩存。"},
            {"problem": "Model not learning", "diagnosis": "1) Check learning rate 2) Verify data 3) Check loss function 4) Examine gradients", "steps": "Step 1: Print loss values. Step 2: Visualize training data. Step 3: Check if gradients flowing. Step 4: Adjust hyperparameters.", "solution": "Common fixes: Reduce learning rate, normalize data, fix data labels, check model architecture."},
            {"problem": "網站無法訪問", "diagnosis": "1)檢查網絡連接 2)檢查伺服器狀態 3)檢查DNS 4)檢查防火牆", "steps": "第一步：ping測試連接。第二步：檢查伺服器日誌。第三步：確認DNS解析。第四步：檢查端口開放。", "solution": "按診斷步驟逐一排查，找到具體原因後針對性解決。"},
        ],
        
        # 計劃能力
        "planning": [
            {"goal": "學習機器學習", "timeframe": "3個月", "plan": "第1月：Python基礎和數學（線性代數、微積分）。第2月：經典ML算法（線性回歸、決策樹）。第3月：深度學習入門（神經網絡、PyTorch）。", "milestones": "每月完成一個小項目"},
            {"goal": "Build a web app", "timeframe": "2 months", "plan": "Month 1: Frontend (React, HTML/CSS, design). Month 2: Backend (Node.js, database, API) and deployment.", "milestones": "Week 2: UI mockup. Week 4: Frontend complete. Week 6: Backend complete. Week 8: Deploy and test."},
            {"goal": "優化系統性能", "timeframe": "2週", "plan": "第1週：性能分析和瓶頸定位（工具：profiler）。第2週：實施優化（代碼、數據庫、緩存）和測試。", "metrics": "目標：響應時間減少50%，吞吐量提升30%"},
        ],
    },
}


class AITeacherDataset(Dataset):
    """AI 老師數據集"""
    
    def __init__(self, tokenizer: BilingualTokenizer, max_length: int = 128):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data: list[str] = []
        
        # 組合所有數據
        self._prepare_data()
    
    def _prepare_data(self):
        """準備訓練數據"""
        
        # 1. 對話數據
        for conv in AI_TEACHER_DATA["conversations"]:
            text = f"{conv['input']} {conv['output']}"
            self.data.append(text)
        
        # 2. 知識數據
        self.data.extend(AI_TEACHER_DATA["knowledge"])
        
        # 3. 指令數據
        for inst in AI_TEACHER_DATA["instructions"]:
            text = f"{inst['instruction']} {inst['response']}"
            self.data.append(text)
        
        # 4. 功能性數據
        if "functional_abilities" in AI_TEACHER_DATA:
            abilities = AI_TEACHER_DATA["functional_abilities"]
            
            # 搜索能力
            if "search" in abilities:
                for item in abilities["search"]:
                    text = f"Query: {item['query']} Reasoning: {item['reasoning']} Action: {item['action']}"
                    self.data.append(text)
            
            # 判斷能力
            if "judgment" in abilities:
                for item in abilities["judgment"]:
                    text = f"Situation: {item['situation']} Analysis: {item['analysis']} Judgment: {item['judgment']}"
                    if "reason" in item:
                        text += f" Reason: {item['reason']}"
                    self.data.append(text)
            
            # 推理能力
            if "reasoning" in abilities:
                for item in abilities["reasoning"]:
                    text = f"Premise: {item['premise']} Reasoning: {item['reasoning']} Conclusion: {item['conclusion']}"
                    self.data.append(text)
            
            # 分析能力
            if "analysis" in abilities:
                for item in abilities["analysis"]:
                    text = f"Data: {item['data']} Pattern: {item['pattern']} Analysis: {item['analysis']} Conclusion: {item['conclusion']}"
                    self.data.append(text)
            
            # 決策能力
            if "decision" in abilities:
                for item in abilities["decision"]:
                    text = f"Scenario: {item['scenario']} Options: {item['options']} Analysis: {item['analysis']} Decision: {item['decision']}"
                    self.data.append(text)
            
            # 比較能力
            if "comparison" in abilities:
                for item in abilities["comparison"]:
                    text = f"Compare: {item['items']} Dimensions: {item['dimensions']} Comparison: {item['comparison']} Conclusion: {item['conclusion']}"
                    self.data.append(text)
            
            # 問題解決
            if "problem_solving" in abilities:
                for item in abilities["problem_solving"]:
                    text = f"Problem: {item['problem']} Diagnosis: {item['diagnosis']} Steps: {item['steps']} Solution: {item['solution']}"
                    self.data.append(text)
            
            # 計劃能力
            if "planning" in abilities:
                for item in abilities["planning"]:
                    text = f"Goal: {item['goal']} Timeframe: {item['timeframe']} Plan: {item['plan']}"
                    if "milestones" in item:
                        text += f" Milestones: {item['milestones']}"
                    self.data.append(text)
        
        print(f"📚 AI老師數據: {len(self.data)} 個樣本")
        
        # 統計各類數據
        conv_count = len(AI_TEACHER_DATA["conversations"])
        know_count = len(AI_TEACHER_DATA["knowledge"])
        inst_count = len(AI_TEACHER_DATA["instructions"])
        func_count = len(self.data) - conv_count - know_count - inst_count
        
        print(f"   • 對話數據: {conv_count}")
        print(f"   • 知識數據: {know_count}")
        print(f"   • 指令數據: {inst_count}")
        print(f"   • 功能數據: {func_count}")

    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        text = self.data[idx]
        
        # 編碼
        ids = self.tokenizer.encode(text, add_special_tokens=True)
        
        # 截斷或填充
        if len(ids) > self.max_length:
            ids = ids[:self.max_length]
        else:
            ids = ids + [self.tokenizer.pad_token_id] * (self.max_length - len(ids))
        
        return torch.tensor(ids, dtype=torch.long)


def get_data_hash():
    """計算訓練數據的哈希值，用於檢測數據變化"""
    data_str = json.dumps(AI_TEACHER_DATA, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(data_str.encode('utf-8')).hexdigest()


def load_training_log():
    """載入訓練記錄"""
    log_file = Path("training_log.json")
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "training_history": [],
        "current_version": 0,
        "last_training_date": None,
        "models": {}
    }


def save_training_log(log_data):
    """保存訓練記錄"""
    with open("training_log.json", 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)


def check_if_already_trained(data_hash, epochs, learning_rate, batch_size):
    """檢查是否已經用相同參數訓練過"""
    log = load_training_log()
    
    for record in log["training_history"]:
        if (record["data_hash"] == data_hash and 
            record["epochs"] == epochs and
            record["learning_rate"] == learning_rate and
            record["batch_size"] == batch_size):
            return True, record
    
    return False, None


def train_with_ai_teacher(
    model_dir: str = "model/my_100m_model.pth",
    output_dir: str = "model/tiny_llm_finetuned.pth",
    epochs: int = 10,
    batch_size: int = 4,
    learning_rate: float = 5e-5,
    max_length: int = 128,
    force_retrain: bool = False,
):
    """使用 AI 老師數據訓練模型
    
    Args:
        force_retrain: 如果為 True，即使已訓練過也會重新訓練
    """
    
    print("=" * 70)
    print("🎓 知識蒸餾訓練 - AI 老師版")
    print("=" * 70)
    
    # 檢查是否已訓練過
    data_hash = get_data_hash()
    already_trained, previous_record = check_if_already_trained(
        data_hash, epochs, learning_rate, batch_size
    )
    
    if already_trained and not force_retrain:
        print("\n⚠️  檢測到相同配置的訓練記錄！")
        print(f"\n訓練時間: {previous_record['date']}")
        print(f"數據樣本: {previous_record['num_samples']}")
        print(f"訓練輪數: {previous_record['epochs']}")
        print(f"最終損失: {previous_record['final_loss']:.4f}")
        print(f"最終困惑度: {previous_record['final_perplexity']:.2f}")
        print(f"模型位置: {previous_record['model_path']}")
        print("\n選項:")
        print("  1. 跳過訓練（使用現有模型）")
        print("  2. 繼續訓練（在現有模型上增量訓練）")
        print("  3. 重新訓練（從頭開始）")
        
        choice = input("\n請選擇 (1/2/3) [默認:1]: ").strip() or "1"
        
        if choice == "1":
            print("\n✅ 跳過訓練，使用現有模型")
            return previous_record["model_path"]
        elif choice == "2":
            print("\n🔄 繼續訓練模式")
            model_dir = previous_record["model_path"]
            output_dir = previous_record["model_path"] + "_v" + str(int(time.time()))
        else:
            print("\n🔄 重新訓練模式")
    
    # 記錄訓練開始
    training_start_time = datetime.now()
    print(f"\n🕐 訓練開始時間: {training_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 載入模型和 tokenizer
    print("\n1️⃣ 載入學生模型...")

    model, _ = load_llm(model_dir, device="cpu")
    model.train()

    tok_path = Path(__file__).parent.parent.parent / "model" / "tokenizer" / "vocab.json"
    tokenizer = BilingualTokenizer.load(str(tok_path))
    
    print(f"✅ 學生模型: {model.count_parameters():,} 參數")
    
    # 2. 準備數據
    print("\n2️⃣ 準備 AI 老師數據...")
    dataset = AITeacherDataset(tokenizer, max_length=max_length)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    
    # 3. 設置優化器
    print("\n3️⃣ 設置訓練參數...")
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
    criterion = nn.CrossEntropyLoss(ignore_index=tokenizer.pad_token_id)
    
    print("優化器: AdamW")
    print(f"學習率: {learning_rate}")
    print(f"批次大小: {batch_size}")
    print(f"訓練輪數: {epochs}")
    
    # 4. 訓練
    print("\n4️⃣ 開始訓練...")
    print("👨‍🏫 AI 老師正在教導模型...\n")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    
    history: dict[str, list[float]] = {
        "losses": [],
        "perplexities": [],
    }
    
    for epoch in range(epochs):
        epoch_loss = 0
        num_batches = 0
        
        progress_bar = tqdm(dataloader, desc=f"Epoch {epoch+1}/{epochs}")
        
        for batch in progress_bar:
            batch = batch.to(device)
            
            # 前向傳播
            optimizer.zero_grad()
            logits = model(batch)
            
            # 計算損失
            shift_logits = logits[:, :-1, :].contiguous()
            shift_labels = batch[:, 1:].contiguous()
            
            loss = criterion(
                shift_logits.view(-1, model.config.vocab_size),
                shift_labels.view(-1)
            )
            
            # 反向傳播
            loss.backward()
            optimizer.step()
            
            # 記錄
            epoch_loss += loss.item()
            num_batches += 1
            
            # 更新進度條
            progress_bar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'avg_loss': f'{epoch_loss/num_batches:.4f}'
            })
        
        # 計算平均損失和困惑度
        avg_loss = epoch_loss / num_batches
        perplexity = torch.exp(torch.tensor(avg_loss)).item()
        
        history["losses"].append(avg_loss)
        history["perplexities"].append(perplexity)
        
        print(f"Epoch {epoch+1} - Loss: {avg_loss:.4f}, Perplexity: {perplexity:.2f}")
    
    # 5. 保存訓練後的模型（新格式：單一 .pth 檔案）
    print("\n5️⃣ 保存訓練後的模型...")
    save_llm(model, output_dir, metadata={
        "base_model": model_dir,
        "training_script": "train_with_ai_teacher.py",
        "epochs": epochs,
        "final_loss": history['losses'][-1],
    })
    print(f"✅ 模型已保存到: {output_dir}")
    
    # 6. 測試訓練後的模型
    print("\n6️⃣ 測試訓練後的模型...")
    model.eval()
    
    test_prompts = [
        "Hello",
        "你好",
        "What is AI",
        "什麼是機器學習",
        "搜索關於Python",
        "判斷：17是質數嗎",
        "分析：錯誤率在下降",
        "比較Python和Java",
    ]
    
    for prompt in test_prompts:
        print(f"\n提示: {prompt}")
        
        prompt_ids = tokenizer.encode(prompt, add_special_tokens=False)[:10]
        prompt_tensor = torch.tensor([prompt_ids]).to(device)
        
        with torch.no_grad():
            generated = model.generate(
                prompt_tensor,
                max_new_tokens=20,
                temperature=0.7,
                top_k=50
            )
        
        generated_text = tokenizer.decode(generated[0].tolist(), skip_special_tokens=True)
        print(f"生成: {generated_text}")
    
    # 7. 保存訓練記錄
    training_end_time = datetime.now()
    training_duration = (training_end_time - training_start_time).total_seconds()
    
    log = load_training_log()
    log["current_version"] += 1
    log["last_training_date"] = training_end_time.strftime('%Y-%m-%d %H:%M:%S')
    
    training_record = {
        "version": log["current_version"],
        "date": training_end_time.strftime('%Y-%m-%d %H:%M:%S'),
        "duration_seconds": training_duration,
        "data_hash": data_hash,
        "num_samples": len(dataset),
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "max_length": max_length,
        "initial_loss": history['losses'][0],
        "final_loss": history['losses'][-1],
        "initial_perplexity": history['perplexities'][0],
        "final_perplexity": history['perplexities'][-1],
        "model_path": str(output_path),
        "base_model": model_dir,
    }
    
    log["training_history"].append(training_record)
    log["models"][str(log["current_version"])] = {
        "path": str(output_path),
        "date": training_end_time.strftime('%Y-%m-%d %H:%M:%S'),
        "performance": {
            "final_loss": history['losses'][-1],
            "final_perplexity": history['perplexities'][-1],
        }
    }
    
    save_training_log(log)
    
    # 8. 總結
    print("\n" + "=" * 70)
    print("✅ 訓練完成!")
    print("=" * 70)
    
    print("\n📊 訓練統計:")
    print(f"  • 版本號: v{log['current_version']}")
    print(f"  • 訓練時長: {training_duration/60:.1f} 分鐘")
    print(f"  • 初始損失: {history['losses'][0]:.4f}")
    print(f"  • 最終損失: {history['losses'][-1]:.4f}")
    print(f"  • 初始困惑度: {history['perplexities'][0]:.2f}")
    print(f"  • 最終困惑度: {history['perplexities'][-1]:.2f}")
    print(f"  • 損失下降: {(1 - history['losses'][-1]/history['losses'][0])*100:.1f}%")
    
    print(f"\n💾 保存位置: {output_path}")
    print("📝 訓練記錄已更新到: training_log.json")
    print("\n💡 提示:")
    print("  • 這是一個簡化的訓練示範")
    print(f"  • 使用了 AI 老師生成的 {len(dataset)} 個樣本")
    print("  • 真實訓練需要更多數據和更長時間")
    print("  • 可以繼續訓練或添加更多數據")
    print("  • 使用 'python view_training_history.py' 查看完整歷史")
    
    return str(output_path)


def expand_teacher_data():
    """擴展 AI 老師數據 (可以添加更多)"""
    
    additional_data = {
        "conversations": [
            {"input": "Good morning!", "output": "Good morning! I hope you're having a wonderful day. How can I assist you?"},
            {"input": "早安！", "output": "早安！希望你有美好的一天。有什麼我可以幫忙的嗎？"},
            {"input": "What time is it?", "output": "I don't have access to real-time information, but I can help you with many other things!"},
            {"input": "現在幾點？", "output": "我無法獲取即時時間，但我可以幫你其他很多事情！"},
        ],
        "knowledge": [
            "Programming is the art of creating instructions for computers to follow.",
            "編程是創造讓電腦遵循的指令的藝術。",
            "Data science combines statistics, programming, and domain expertise.",
            "數據科學結合統計學、編程和領域專業知識。",
        ],
    }
    
    # 可以在這裡添加更多數據
    return additional_data


if __name__ == "__main__":
    print("\n🎓 知識蒸餾訓練系統")
    print("👨‍🏫 AI 老師: 我會用高質量的英中雙語數據教導你的模型\n")
    
    # 訓練
    train_with_ai_teacher(
        model_dir="model/my_100m_model.pth",
        output_dir="model/tiny_llm_finetuned.pth",
        epochs=20,  # 訓練 20 輪
        batch_size=4,
        learning_rate=5e-5,
        max_length=128,
    )
