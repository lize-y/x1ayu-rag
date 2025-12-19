from __future__ import annotations
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document
import json
import os
from .base import SplitterStrategy


class MarkdownSplitter(SplitterStrategy):
    """Markdown 文档切分器。
    
    使用 LangChain 的 MarkdownHeaderTextSplitter 按标题层级进行切分。
    """
    
    def split_from_content(self, file_name: str, dir_path: str | None, content: str) -> list[Document]:
        """按 Markdown 头级结构拆分给定内容。
        
        参数:
            file_name: 文件名
            dir_path: 目录路径
            content: Markdown 内容
            
        返回:
            list[Document]: 切分后的文档列表，包含元数据（文件名、目录、标题结构）。
        """
        headers_to_split_on = [
            ("#", "Header1"),
            ("##", "Header2"),
            ("###", "Header3"),
            ("####", "Header4"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on, return_each_line=True
        )
        docs = markdown_splitter.split_text(content)
        final_docs = [
            Document(
                page_content=doc.page_content,
                metadata={
                    "file_name": file_name,
                    "dir_path": dir_path,
                    "mk_struct": json.dumps(doc.metadata, ensure_ascii=False),
                },
            )
            for doc in docs
        ]
        return final_docs
