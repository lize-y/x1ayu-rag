from typing import Optional
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from x1ayu_rag.config.app_config import load_config
from x1ayu_rag.exceptions import ConfigurationError


def get_chat_llm(temperature: float = 0) -> BaseChatModel:
    """获取 Chat LLM 模型实例。
    
    根据配置文件加载 Chat 模型（Ollama 或 OpenAI）。
    
    参数:
        temperature: 模型温度，控制生成随机性。
        
    返回:
        BaseChatModel: 已初始化的 Chat 模型实例。
        
    异常:
        ConfigurationError: 如果配置缺失或无效。
    """
    cfg = load_config()
    chat_cfg = cfg.get("chat", {})
    provider = (chat_cfg.get("provider") or "").lower()
    model = chat_cfg.get("model") or ""
    base_url = chat_cfg.get("base_url") or ""
    api_key = chat_cfg.get("api_key") or ""
    if not provider or not model or not base_url:
        raise ConfigurationError("未设置 Chat 模型信息，请通过 init 或 config 命令设置 chat.provider/chat.model/chat.base_url")
    if provider == "openai":
        if not api_key:
            raise ConfigurationError("未设置 Chat API Key，请通过 init 或 config 命令设置 chat.api_key")
        return ChatOpenAI(model=model, temperature=temperature, api_key=api_key, base_url=base_url)
    return ChatOllama(model=model, temperature=temperature, base_url=base_url)


def get_embeddings() -> Embeddings:
    """获取 Embedding 模型实例。
    
    根据配置文件加载 Embedding 模型（Ollama 或 OpenAI）。
    
    返回:
        Embeddings: 已初始化的 Embedding 模型实例。
        
    异常:
        ConfigurationError: 如果配置缺失或无效。
    """
    cfg = load_config()
    emb_cfg = cfg.get("embedding", {})
    provider = (emb_cfg.get("provider") or "").lower()
    model = emb_cfg.get("model") or ""
    base_url = emb_cfg.get("base_url") or ""
    api_key = emb_cfg.get("api_key") or ""
    if not provider or not model or not base_url:
        raise ConfigurationError("未设置 Embedding 模型信息，请通过 init 或 config 命令设置 embedding.provider/embedding.model/embedding.base_url")
    if provider == "openai":
        if not api_key:
            raise ConfigurationError("未设置 Embedding API Key，请通过 init 或 config 命令设置 embedding.api_key")
        return OpenAIEmbeddings(model=model, api_key=api_key, base_url=base_url)
    return OllamaEmbeddings(model=model, base_url=base_url)
