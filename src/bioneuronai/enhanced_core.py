"""
BioNeuronAI 增強核心 - 2025優化版
===============================

基於2024-2025最新AI架構研究的增強核心實現
包含混合專家系統、注意力機制、多模態支持和RAG集成
"""

import numpy as np
import time
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import threading
from abc import ABC, abstractmethod

from .mega_core import MegaBioNet, NetworkTopology, MegaBioNeuron
from .rag_integration import BioRAGSystem
from .ai_optimization_2025 import AI_ARCHITECTURE_TRENDS_2024_2025


@dataclass
class AttentionConfig:
    """注意力機制配置"""
    num_heads: int = 8
    head_dim: int = 64
    dropout_rate: float = 0.1
    use_sparse: bool = True
    sparse_ratio: float = 0.1
    use_flash_attention: bool = True


@dataclass  
class MemoryConfig:
    """記憶系統配置"""
    working_memory_size: int = 512
    episodic_memory_size: int = 1000
    semantic_memory_size: int = 5000
    consolidation_threshold: float = 0.7
    decay_rate: float = 0.01


@dataclass
class MoEConfig:
    """專家混合配置"""
    num_experts: int = 8
    expert_capacity: float = 1.25
    top_k_experts: int = 2
    gating_noise: float = 0.1
    load_balancing_loss_weight: float = 0.01


class BioAttentionMechanism:
    """生物啟發的注意力機制
    
    結合生物神經網路的選擇性注意和Transformer注意力
    """
    
    def __init__(self, config: AttentionConfig, input_dim: int):
        self.config = config
        self.input_dim = input_dim
        self.head_dim = config.head_dim
        self.num_heads = config.num_heads
        
        # 初始化權重矩陣
        self.W_q = np.random.normal(0, 0.02, (input_dim, config.num_heads * config.head_dim))
        self.W_k = np.random.normal(0, 0.02, (input_dim, config.num_heads * config.head_dim))
        self.W_v = np.random.normal(0, 0.02, (input_dim, config.num_heads * config.head_dim))
        self.W_o = np.random.normal(0, 0.02, (config.num_heads * config.head_dim, input_dim))
        
        # 生物啟發的門控機制
        self.gate_threshold = 0.5
        self.attention_history = []
        
    def compute_attention(
        self, 
        query: np.ndarray, 
        key: np.ndarray, 
        value: np.ndarray,
        mask: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """計算注意力權重"""
        batch_size, seq_len = query.shape[0], query.shape[1]
        
        # 計算Q, K, V
        Q = self._reshape_for_heads(np.dot(query, self.W_q))
        K = self._reshape_for_heads(np.dot(key, self.W_k))  
        V = self._reshape_for_heads(np.dot(value, self.W_v))
        
        # 縮放點積注意力
        attention_scores = np.matmul(Q, K.transpose(0, 1, 3, 2)) / np.sqrt(self.head_dim)
        
        # 應用mask
        if mask is not None:
            attention_scores = np.where(mask, attention_scores, -1e9)
            
        # 生物啟發的稀疏注意力
        if self.config.use_sparse:
            attention_scores = self._apply_sparse_gating(attention_scores)
            
        # Softmax
        attention_weights = self._softmax(attention_scores)
        
        # 應用dropout (訓練時)
        if self.config.dropout_rate > 0:
            attention_weights = self._dropout(attention_weights, self.config.dropout_rate)
            
        # 計算輸出
        attention_output = np.matmul(attention_weights, V)
        
        # 重新組織維度
        attention_output = self._combine_heads(attention_output)
        
        # 輸出投影
        output = np.dot(attention_output, self.W_o)
        
        # 記錄注意力模式
        self._record_attention_pattern(attention_weights)
        
        return output
    
    def _reshape_for_heads(self, x: np.ndarray) -> np.ndarray:
        """重組維度用於多頭注意力"""
        batch_size, seq_len, _ = x.shape
        x = x.reshape(batch_size, seq_len, self.num_heads, self.head_dim)
        return x.transpose(0, 2, 1, 3)  # (batch, heads, seq_len, head_dim)
    
    def _combine_heads(self, x: np.ndarray) -> np.ndarray:
        """合併多頭注意力結果"""
        batch_size, _, seq_len, _ = x.shape
        x = x.transpose(0, 2, 1, 3)  # (batch, seq_len, heads, head_dim)
        return x.reshape(batch_size, seq_len, self.num_heads * self.head_dim)
    
    def _apply_sparse_gating(self, attention_scores: np.ndarray) -> np.ndarray:
        """應用生物啟發的稀疏門控"""
        # 計算每個位置的重要性
        importance = np.mean(np.abs(attention_scores), axis=-1, keepdims=True)
        
        # 只保留最重要的連接
        threshold = np.percentile(importance, (1 - self.config.sparse_ratio) * 100)
        mask = importance >= threshold
        
        return attention_scores * mask
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """數值穩定的softmax"""
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)
    
    def _dropout(self, x: np.ndarray, rate: float) -> np.ndarray:
        """Dropout正則化 (簡化版)"""
        if rate > 0:
            mask = np.random.random(x.shape) > rate
            return x * mask / (1 - rate)
        return x
    
    def _record_attention_pattern(self, attention_weights: np.ndarray):
        """記錄注意力模式用於分析"""
        pattern = np.mean(attention_weights, axis=(0, 1))  # 平均跨batch和heads
        self.attention_history.append(pattern)
        
        # 保持歷史記錄大小
        if len(self.attention_history) > 100:
            self.attention_history.pop(0)


class HierarchicalMemorySystem:
    """層次化記憶系統
    
    模擬生物大腦的多層記憶結構
    """
    
    def __init__(self, config: MemoryConfig, embedding_dim: int):
        self.config = config
        self.embedding_dim = embedding_dim
        
        # 工作記憶 - 當前任務相關信息
        self.working_memory = []
        
        # 情節記憶 - 具體經驗和事件
        self.episodic_memory = []
        
        # 語義記憶 - 抽象知識和概念  
        self.semantic_memory = {}
        
        # 記憶索引
        self.memory_index = {}
        
        # 鞏固機制
        self.consolidation_timer = time.time()
        
    def store_working_memory(self, content: np.ndarray, context: Dict = None):
        """存儲到工作記憶"""
        memory_item = {
            'content': content,
            'context': context or {},
            'timestamp': time.time(),
            'access_count': 1
        }
        
        self.working_memory.append(memory_item)
        
        # 容量管理
        if len(self.working_memory) > self.config.working_memory_size:
            # 移除最舊的項目
            removed_item = self.working_memory.pop(0)
            # 考慮轉移到長期記憶
            if removed_item['access_count'] > 3:
                self._promote_to_episodic(removed_item)
    
    def store_episodic_memory(self, episode: Dict):
        """存儲情節記憶"""
        episode_item = {
            **episode,
            'timestamp': time.time(),
            'importance': self._calculate_importance(episode)
        }
        
        self.episodic_memory.append(episode_item)
        
        # 容量管理
        if len(self.episodic_memory) > self.config.episodic_memory_size:
            # 基於重要性排序，移除最不重要的
            self.episodic_memory.sort(key=lambda x: x['importance'], reverse=True)
            removed = self.episodic_memory.pop()
            # 提取語義信息存儲到語義記憶
            self._extract_to_semantic(removed)
    
    def retrieve_memories(self, query: np.ndarray, memory_type: str = 'all') -> List[Dict]:
        """檢索相關記憶"""
        results = []
        
        if memory_type in ['all', 'working']:
            results.extend(self._search_working_memory(query))
            
        if memory_type in ['all', 'episodic']:
            results.extend(self._search_episodic_memory(query))
            
        if memory_type in ['all', 'semantic']:
            results.extend(self._search_semantic_memory(query))
        
        # 按相關性排序
        results.sort(key=lambda x: x.get('relevance', 0), reverse=True)
        
        return results[:10]  # 返回最相關的10個
    
    def consolidate_memories(self):
        """記憶鞏固過程"""
        current_time = time.time()
        
        # 定期執行鞏固
        if current_time - self.consolidation_timer > 3600:  # 每小時一次
            self._consolidation_process()
            self.consolidation_timer = current_time
    
    def _promote_to_episodic(self, memory_item: Dict):
        """將工作記憶提升到情節記憶"""
        episode = {
            'type': 'promoted_working_memory',
            'content': memory_item['content'],
            'context': memory_item['context'],
            'original_timestamp': memory_item['timestamp']
        }
        self.store_episodic_memory(episode)
    
    def _calculate_importance(self, episode: Dict) -> float:
        """計算情節重要性"""
        # 基於多種因素計算重要性
        importance = 0.5  # 基礎重要性
        
        # 訪問頻率
        if 'access_count' in episode:
            importance += min(episode['access_count'] * 0.1, 0.3)
            
        # 情感強度 (如果有)
        if 'emotion_strength' in episode:
            importance += episode['emotion_strength'] * 0.2
            
        # 新穎性
        if 'novelty' in episode:
            importance += episode['novelty'] * 0.3
            
        return min(importance, 1.0)
    
    def _extract_to_semantic(self, episode: Dict):
        """從情節記憶提取語義信息"""
        # 提取關鍵概念
        if 'concepts' in episode:
            for concept in episode['concepts']:
                if concept not in self.semantic_memory:
                    self.semantic_memory[concept] = {
                        'strength': 1.0,
                        'associations': [],
                        'last_access': time.time()
                    }
                else:
                    self.semantic_memory[concept]['strength'] += 0.1
                    self.semantic_memory[concept]['last_access'] = time.time()
    
    def _search_working_memory(self, query: np.ndarray) -> List[Dict]:
        """搜索工作記憶"""
        results = []
        
        for item in self.working_memory:
            similarity = self._compute_similarity(query, item['content'])
            if similarity > 0.3:
                results.append({
                    **item,
                    'relevance': similarity,
                    'memory_type': 'working'
                })
                
        return results
    
    def _search_episodic_memory(self, query: np.ndarray) -> List[Dict]:
        """搜索情節記憶"""
        results = []
        
        for episode in self.episodic_memory:
            if 'content' in episode:
                similarity = self._compute_similarity(query, episode['content'])
                if similarity > 0.2:
                    results.append({
                        **episode,
                        'relevance': similarity * episode['importance'],
                        'memory_type': 'episodic'
                    })
                    
        return results
    
    def _search_semantic_memory(self, query: np.ndarray) -> List[Dict]:
        """搜索語義記憶 (簡化版)"""
        # 在實際實現中，這裡會使用更複雜的語義匹配
        results = []
        
        for concept, info in list(self.semantic_memory.items())[:20]:
            # 簡單的概念匹配
            concept_score = info['strength'] * 0.5
            if concept_score > 0.3:
                results.append({
                    'concept': concept,
                    'info': info,
                    'relevance': concept_score,
                    'memory_type': 'semantic'
                })
                
        return results
    
    def _compute_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """計算向量相似度"""
        if isinstance(vec2, dict) and 'content' in vec2:
            vec2 = vec2['content']
            
        # 確保向量維度匹配
        if len(vec1) != len(vec2):
            return 0.0
            
        # 餘弦相似度
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
    
    def _consolidation_process(self):
        """記憶鞏固過程"""
        # 應用遺忘衰減
        current_time = time.time()
        
        for concept in list(self.semantic_memory.keys()):
            age = current_time - self.semantic_memory[concept]['last_access']
            decay_factor = np.exp(-age * self.config.decay_rate / 86400)  # 以天為單位
            
            self.semantic_memory[concept]['strength'] *= decay_factor
            
            # 移除太弱的記憶
            if self.semantic_memory[concept]['strength'] < 0.1:
                del self.semantic_memory[concept]


class BioMixtureOfExperts:
    """生物啟發的專家混合系統"""
    
    def __init__(self, config: MoEConfig, input_dim: int, expert_dim: int):
        self.config = config
        self.input_dim = input_dim
        self.expert_dim = expert_dim
        
        # 創建專家網路
        self.experts = []
        for i in range(config.num_experts):
            expert = MegaBioNeuron(
                input_dim, 
                sparsity=0.8, 
                seed=42+i
            )
            self.experts.append(expert)
        
        # 門控網路
        self.gating_network = MegaBioNeuron(
            input_dim,
            sparsity=0.5
        )
        
        # 門控權重
        self.gate_weights = np.random.normal(0, 0.02, (input_dim, config.num_experts))
        
        # 負載均衡統計
        self.expert_usage = np.zeros(config.num_experts)
        self.total_tokens = 0
        
    def forward(self, x: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """前向傳播"""
        # 計算門控分數
        gate_logits = np.dot(x, self.gate_weights)
        
        # 添加噪聲 (訓練時)
        if self.config.gating_noise > 0:
            noise = np.random.normal(0, self.config.gating_noise, gate_logits.shape)
            gate_logits += noise
            
        # 選擇top-k專家
        top_k_indices = np.argsort(gate_logits)[-self.config.top_k_experts:]
        
        # 計算專家權重 (softmax)
        gate_scores = self._softmax(gate_logits[top_k_indices])
        
        # 專家輸出
        expert_outputs = []
        for i, expert_idx in enumerate(top_k_indices):
            expert_output = self.experts[expert_idx].forward(x)
            expert_outputs.append(expert_output)
            
            # 更新使用統計
            self.expert_usage[expert_idx] += 1
            
        # 加權組合
        output = np.zeros(expert_outputs[0].shape if isinstance(expert_outputs[0], np.ndarray) 
                         else 1)
        
        for i, expert_output in enumerate(expert_outputs):
            if isinstance(expert_output, (int, float)):
                expert_output = np.array([expert_output])
            output += gate_scores[i] * expert_output
            
        self.total_tokens += 1
        
        # 計算負載均衡損失
        load_balancing_loss = self._compute_load_balancing_loss()
        
        routing_info = {
            'selected_experts': top_k_indices,
            'expert_weights': gate_scores,
            'load_balancing_loss': load_balancing_loss,
            'expert_usage': self.expert_usage.copy()
        }
        
        return output, routing_info
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """數值穩定的softmax"""
        exp_x = np.exp(x - np.max(x))
        return exp_x / np.sum(exp_x)
    
    def _compute_load_balancing_loss(self) -> float:
        """計算負載均衡損失"""
        if self.total_tokens == 0:
            return 0.0
            
        # 計算使用率分佈
        usage_rates = self.expert_usage / self.total_tokens
        
        # 理想的均勻分佈
        ideal_rate = 1.0 / self.config.num_experts
        
        # L2損失
        load_loss = np.sum((usage_rates - ideal_rate) ** 2)
        
        return load_loss * self.config.load_balancing_loss_weight


class EnhancedBioCore:
    """增強版BioNeuronAI核心
    
    集成最新的AI架構優化技術
    """
    
    def __init__(
        self,
        input_dim: int = 2048,
        hidden_dims: List[int] = None,
        output_dim: int = 1024,
        attention_config: AttentionConfig = None,
        memory_config: MemoryConfig = None, 
        moe_config: MoEConfig = None,
        enable_rag: bool = True,
        rag_db_path: str = "enhanced_rag.db"
    ):
        # 默認配置
        if hidden_dims is None:
            hidden_dims = [4096, 8192, 4096, 2048]
        if attention_config is None:
            attention_config = AttentionConfig()
        if memory_config is None:
            memory_config = MemoryConfig()
        if moe_config is None:
            moe_config = MoEConfig()
            
        self.input_dim = input_dim
        self.output_dim = output_dim
        
        # 核心組件
        self.attention = BioAttentionMechanism(attention_config, input_dim)
        self.memory_system = HierarchicalMemorySystem(memory_config, input_dim)
        self.moe_layer = BioMixtureOfExperts(moe_config, input_dim, hidden_dims[0])
        
        # 基礎神經網路層
        self.layers = []
        prev_dim = input_dim
        
        for dim in hidden_dims:
            layer = MegaBioNeuron(prev_dim, sparsity=0.85)
            self.layers.append(layer)
            prev_dim = dim
            
        # 輸出層
        self.output_layer = MegaBioNeuron(prev_dim, sparsity=0.7)
        
        # RAG系統 (可選)
        self.rag_system = None
        if enable_rag:
            try:
                self.rag_system = BioRAGSystem(
                    db_path=rag_db_path,
                    embedding_dim=input_dim
                )
            except Exception as e:
                print(f"RAG系統初始化失敗: {e}")
                
        # 統計信息
        self.forward_count = 0
        self.processing_times = []
        
    def forward(
        self, 
        x: Union[np.ndarray, List[float]], 
        context: Optional[Dict] = None,
        use_attention: bool = True,
        use_memory: bool = True,
        use_moe: bool = True,
        query_rag: Optional[str] = None
    ) -> Dict[str, Any]:
        """增強前向傳播"""
        start_time = time.time()
        
        # 輸入預處理
        if isinstance(x, list):
            x = np.array(x, dtype=np.float32)
        if len(x.shape) == 1:
            x = x.reshape(1, -1)
            
        original_input = x.copy()
        
        # RAG增強 (如果啟用且提供查詢)
        rag_context = None
        if self.rag_system and query_rag:
            try:
                rag_result = self.rag_system.query(query_rag, max_docs=3)
                rag_context = rag_result
                # 將RAG信息融合到輸入中 (簡化版)
                if len(rag_result['sources']) > 0:
                    x = x * 1.1  # 簡單的信息增強
            except Exception as e:
                print(f"RAG查詢失敗: {e}")
        
        # 記憶檢索
        memory_context = None
        if use_memory:
            retrieved_memories = self.memory_system.retrieve_memories(x.flatten())
            memory_context = retrieved_memories
            
            # 融合記憶信息
            if retrieved_memories:
                memory_influence = sum(m.get('relevance', 0) for m in retrieved_memories[:3])
                x = x * (1 + memory_influence * 0.1)
        
        # 注意力處理
        attention_output = x
        if use_attention and x.shape[0] > 1:  # 需要序列長度 > 1
            try:
                attention_output = self.attention.compute_attention(x, x, x)
            except Exception as e:
                print(f"注意力計算錯誤: {e}")
                attention_output = x
        
        # MoE處理
        moe_output = attention_output
        moe_info = None
        if use_moe:
            try:
                moe_output, moe_info = self.moe_layer.forward(attention_output.flatten())
                if isinstance(moe_output, (int, float)):
                    moe_output = np.array([[moe_output]])
                elif len(moe_output.shape) == 1:
                    moe_output = moe_output.reshape(1, -1)
            except Exception as e:
                print(f"MoE處理錯誤: {e}")
                moe_output = attention_output
        
        # 通過主網路層
        layer_outputs = []
        current_input = moe_output.flatten()
        
        for i, layer in enumerate(self.layers):
            try:
                layer_output = layer.forward(current_input)
                layer_outputs.append(layer_output)
                
                # 為下一層準備輸入
                if isinstance(layer_output, (int, float)):
                    current_input = np.array([layer_output])
                else:
                    current_input = np.array(layer_output).flatten()
                    
                # 確保輸入維度匹配
                if len(current_input) != self.layers[min(i+1, len(self.layers)-1)].num_inputs:
                    current_input = np.resize(current_input, 
                                            self.layers[min(i+1, len(self.layers)-1)].num_inputs)
            except Exception as e:
                print(f"第{i}層處理錯誤: {e}")
                layer_outputs.append(0.0)
                current_input = np.zeros(100)  # 默認輸入
        
        # 輸出層
        try:
            final_output = self.output_layer.forward(current_input)
        except Exception as e:
            print(f"輸出層錯誤: {e}")
            final_output = 0.0
        
        # 存儲到記憶系統
        if use_memory:
            memory_content = {
                'input': original_input.flatten(),
                'output': np.array([final_output]).flatten(),
                'context': context or {},
                'rag_context': rag_context,
                'timestamp': time.time()
            }
            self.memory_system.store_working_memory(
                original_input.flatten(), 
                memory_content
            )
        
        # 處理時間統計
        processing_time = time.time() - start_time
        self.processing_times.append(processing_time)
        if len(self.processing_times) > 100:
            self.processing_times.pop(0)
            
        self.forward_count += 1
        
        return {
            'output': final_output,
            'layer_outputs': layer_outputs,
            'attention_weights': getattr(self.attention, 'attention_history', [])[-1:],
            'moe_info': moe_info,
            'memory_context': memory_context,
            'rag_context': rag_context,
            'processing_time': processing_time,
            'forward_count': self.forward_count
        }
    
    def learn(
        self, 
        inputs: List[np.ndarray], 
        targets: List[np.ndarray],
        learning_rate: float = 0.001,
        epochs: int = 1
    ):
        """增強學習過程"""
        for epoch in range(epochs):
            total_loss = 0
            
            for i, (x, target) in enumerate(zip(inputs, targets)):
                # 前向傳播
                result = self.forward(x)
                output = result['output']
                
                # 計算損失
                if isinstance(output, (int, float)):
                    output = np.array([output])
                if isinstance(target, (int, float)):
                    target = np.array([target])
                    
                loss = np.mean((output - target) ** 2)
                total_loss += loss
                
                # 反向傳播 (簡化版)
                error = output - target
                
                # 更新輸出層
                self.output_layer.learn(x.flatten(), error, learning_rate)
                
                # 更新其他層 (簡化)
                for layer in reversed(self.layers):
                    layer.learn(x.flatten(), error, learning_rate * 0.5)
                    
                # 存儲學習經驗到記憶
                learning_episode = {
                    'type': 'learning',
                    'input': x.flatten(),
                    'target': target.flatten(),
                    'output': output.flatten(),
                    'loss': loss,
                    'epoch': epoch
                }
                self.memory_system.store_episodic_memory(learning_episode)
            
            avg_loss = total_loss / len(inputs)
            if epoch % max(1, epochs // 10) == 0:
                print(f"Epoch {epoch}: Average Loss = {avg_loss:.6f}")
        
        # 記憶鞏固
        self.memory_system.consolidate_memories()
    
    def add_knowledge(self, content: str, metadata: Dict = None) -> str:
        """添加知識到RAG系統"""
        if self.rag_system:
            return self.rag_system.add_document(content, metadata=metadata)
        else:
            raise RuntimeError("RAG系統未啟用")
    
    def query_knowledge(self, question: str) -> Dict[str, Any]:
        """查詢RAG知識庫"""
        if self.rag_system:
            return self.rag_system.query(question)
        else:
            raise RuntimeError("RAG系統未啟用")
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """獲取系統統計信息"""
        stats = {
            'forward_count': self.forward_count,
            'avg_processing_time': np.mean(self.processing_times) if self.processing_times else 0,
            'memory_stats': {
                'working_memory_size': len(self.memory_system.working_memory),
                'episodic_memory_size': len(self.memory_system.episodic_memory), 
                'semantic_memory_size': len(self.memory_system.semantic_memory)
            },
            'moe_stats': {
                'expert_usage': self.moe_layer.expert_usage.tolist(),
                'total_tokens': self.moe_layer.total_tokens
            }
        }
        
        if self.rag_system:
            stats['rag_stats'] = self.rag_system.get_statistics()
            
        return stats
    
    def count_parameters(self) -> int:
        """計算總參數量"""
        total_params = 0
        
        # 注意力機制參數
        total_params += self.attention.W_q.size
        total_params += self.attention.W_k.size  
        total_params += self.attention.W_v.size
        total_params += self.attention.W_o.size
        
        # 層參數
        for layer in self.layers:
            total_params += layer.estimate_memory_usage() // 4  # 假設float32
            
        total_params += self.output_layer.estimate_memory_usage() // 4
        
        # MoE參數
        total_params += self.moe_layer.gate_weights.size
        for expert in self.moe_layer.experts:
            total_params += expert.estimate_memory_usage() // 4
            
        return total_params