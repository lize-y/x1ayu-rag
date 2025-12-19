from __future__ import annotations
from abc import ABC, abstractmethod
from langchain_core.documents import Document


class SplitterStrategy(ABC):
    """切分器策略基类。"""
    
    @abstractmethod
    def split_from_content(self, file_name: str, dir_path: str | None, content: str) -> list[Document]:
        """将文件内容拆分为 LangChain 文档列表。
        
        参数:
            file_name: 文件名
            dir_path: 目录路径
            content: 文件内容
            
        返回:
            list[Document]: 切分后的文档列表
        """
