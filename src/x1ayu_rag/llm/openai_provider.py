from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from x1ayu_rag.llm.base import ChatModelProvider, EmbeddingModelProvider

class OpenAIProvider(ChatModelProvider, EmbeddingModelProvider):
    """OpenAI 提供商实现"""

    def get_chat_model(self, config: Dict[str, Any]) -> ChatOpenAI:
        return ChatOpenAI(
            model=config["model"],
            api_key=config["api_key"],
            base_url=config["base_url"],
            temperature=0
        )

    def get_embeddings(self, config: Dict[str, Any]) -> OpenAIEmbeddings:
        return OpenAIEmbeddings(
            model=config["model"],
            api_key=config["api_key"],
            base_url=config["base_url"]
        )
