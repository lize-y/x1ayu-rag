from __future__ import annotations
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document
import json
import os
from .base import SplitterStrategy


class MarkdownSplitter(SplitterStrategy):
    
    def split_from_content(self, file_name: str, dir_path: str | None, content: str) -> list[Document]:
        """按 Markdown 头级结构拆分给定内容"""
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
