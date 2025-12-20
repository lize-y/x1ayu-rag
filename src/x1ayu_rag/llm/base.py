from abc import ABC, abstractmethod
from typing import Dict, Any
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

class ChatModelProvider(ABC):
    """聊天模型提供商接口"""
    
    @abstractmethod
    def get_chat_model(self, config: Dict[str, Any]) -> BaseChatModel:
        """获取聊天模型实例"""
        pass

class EmbeddingModelProvider(ABC):
    """Embedding 模型提供商接口"""

    @abstractmethod
    def get_embeddings(self, config: Dict[str, Any]) -> Embeddings:
        """获取 Embedding 模型实例"""
        pass

class LLMProvider(ChatModelProvider, EmbeddingModelProvider):
    """全功能 LLM 提供商接口"""
    pass
