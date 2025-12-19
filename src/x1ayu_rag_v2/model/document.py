from __future__ import annotations
from typing import List, Optional, Any
from uuid import uuid4
import os
from x1ayu_rag_v2.model.chunk import Chunk
from x1ayu_rag_v2.utils.hash import text_hash
from x1ayu_rag_v2.utils.splitter_factory import get_splitter

class Document:
    """文档领域对象
    
    表示一个被摄取的文件，包含唯一标识、名称、路径、内容哈希以及其拆分后的分块列表。
    """
    uuid: str
    name: str
    path: str
    hash: str
    chunks: list[Chunk] | None

    def __init__(
        self,
        uuid: str | None,
        name: str,
        path: str,
        hash: str,
        chunks: list[Chunk] | None,
    ):
        self.uuid = uuid if uuid else str(uuid4())
        self.name = name
        self.path = path
        self.hash = hash
        if chunks:
            for chunk in chunks:
                chunk.document_id = self.uuid
        self.chunks = chunks

    @classmethod
    def from_file(cls, file_path: str) -> Document:
        """工厂方法：从文件构建文档"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        file_name = os.path.basename(file_path)
        dir_path = os.path.dirname(file_path)
        
        return cls.from_content(file_name, dir_path, content)

    @classmethod
    def from_content(
        cls,
        file_name: str,
        dir_path: str | None,
        content: str,
        uuid: str | None = None,
    ) -> Document:
        """工厂方法：从已知内容构建文档"""
        doc_hash = text_hash(content)
        
        splitter = get_splitter()
        
        # 使用 splitter 切分内容
        lc_docs = splitter.split_from_content(file_name, dir_path, content)

        chunks = [Chunk.from_lc_document(doc, i) for i, doc in enumerate(lc_docs)]

        return cls(uuid=uuid, name=file_name, path=dir_path or "", hash=doc_hash, chunks=chunks)
