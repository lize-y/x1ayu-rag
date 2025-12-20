from typing import Dict, Any, Optional
from langchain_ollama import ChatOllama, OllamaEmbeddings
from x1ayu_rag.llm.base import ChatModelProvider, EmbeddingModelProvider

class OllamaProvider(ChatModelProvider, EmbeddingModelProvider):
    """Ollama 提供商实现"""

    def get_chat_model(self, config: Dict[str, Any]) -> ChatOllama:
        return ChatOllama(
            model=config["model"],
            base_url=config["base_url"],
            temperature=0
        )

    def get_embeddings(self, config: Dict[str, Any]) -> OllamaEmbeddings:
        return OllamaEmbeddings(
            model=config["model"],
            base_url=config["base_url"]
        )
