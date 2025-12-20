from typing import Optional, Union, Type
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from x1ayu_rag.config.app_config import load_config
from x1ayu_rag.llm.base import ChatModelProvider, EmbeddingModelProvider
from x1ayu_rag.llm.openai_provider import OpenAIProvider
from x1ayu_rag.llm.ollama_provider import OllamaProvider

class LLMFactory:
    """LLM 工厂类"""
    
    _providers = {
        "openai": OpenAIProvider,
        "ollama": OllamaProvider
    }

    @classmethod
    def get_provider(cls, provider_name: str) -> Union[ChatModelProvider, EmbeddingModelProvider]:
        provider_cls = cls._providers.get(provider_name.lower())
        if not provider_cls:
            raise ValueError(f"Unsupported provider: {provider_name}")
        return provider_cls()

    @classmethod
    def _validate_config(cls, config: dict, config_type: str):
        """验证配置完整性"""
        required_fields = ["provider", "model", "base_url"]
        provider = config.get("provider")
        
        # 1. 检查通用必填项
        missing = [f for f in required_fields if not config.get(f)]
        if missing:
            raise ValueError(f"Missing required {config_type} configuration: {', '.join(missing)}")
            
        # 2. OpenAI 特有检查
        if provider == "openai" and not config.get("api_key"):
            raise ValueError(f"Missing required {config_type} configuration: api_key (required for OpenAI)")

    @classmethod
    def validate_chat_config(cls):
        """校验 Chat 配置"""
        config = load_config()
        chat_config = config.get("chat", {})
        if not chat_config:
             raise ValueError("Chat configuration is empty. Please run 'rag config' to set it up.")
        cls._validate_config(chat_config, "chat")

    @classmethod
    def validate_embedding_config(cls):
        """校验 Embedding 配置"""
        config = load_config()
        emb_config = config.get("embedding", {})
        if not emb_config:
             raise ValueError("Embedding configuration is empty. Please run 'rag config' to set it up.")
        cls._validate_config(emb_config, "embedding")

    @classmethod
    def get_chat_model(cls) -> BaseChatModel:
        """根据配置获取 Chat 模型"""
        cls.validate_chat_config()
        config = load_config()
        chat_config = config.get("chat", {})
        
        provider_name = chat_config.get("provider")
        
        provider = cls.get_provider(provider_name)
        if not isinstance(provider, ChatModelProvider):
            raise TypeError(f"Provider {provider_name} does not support Chat operations")
        return provider.get_chat_model(chat_config)

    @classmethod
    def get_embeddings(cls) -> Embeddings:
        """根据配置获取 Embedding 模型"""
        cls.validate_embedding_config()
        config = load_config()
        emb_config = config.get("embedding", {})
        
        provider_name = emb_config.get("provider")
        
        provider = cls.get_provider(provider_name)
        if not isinstance(provider, EmbeddingModelProvider):
             raise TypeError(f"Provider {provider_name} does not support Embedding operations")
        return provider.get_embeddings(emb_config)
