from __future__ import annotations
from abc import ABC, abstractmethod
from langchain_core.documents import Document


class SplitterStrategy(ABC):
    @abstractmethod
    def split_from_content(self, file_name: str, dir_path: str | None, content: str) -> list[Document]:
        """将文件拆分为 LangChain 文档列表"""
