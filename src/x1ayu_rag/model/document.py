from __future__ import annotations
from x1ayu_rag.model.chunk import Chunk
from uuid import uuid4
from x1ayu_rag.utils.hash import text_hash
from x1ayu_rag.utils.mdSplitter import split_markdown_from_content
import os


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
        """构造函数

        参数:
            uuid: 文档唯一标识（可为空，空则自动生成）
            name: 文件名
            path: 文件目录路径
            hash: 文档全文内容的哈希值
            chunks: 文档对应的分块列表
        """
        self.uuid = uuid if uuid else str(uuid4())
        self.name = name
        self.path = path
        self.hash = hash
        if chunks:
            for chunk in chunks:
                chunk.document_id = self.uuid
        self.chunks = chunks

    def __eq__(self, other):
        """比较两个文档是否相等（使用内容哈希与文件名）

        参数:
            other: 另一个待比较的对象
        返回:
            bool: 若哈希与名称均相同则认为相等
        """
        if isinstance(other, Document):
            return self.hash == other.hash and self.name == other.name
        return NotImplemented


    @classmethod
    def from_file(cls, file_path: str) -> Document:
        """工厂方法：从文件构建文档（只读取一次）"""
        file_name = os.path.basename(file_path)
        dir_path = os.path.dirname(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return cls.from_content(file_name, dir_path, content)

    @classmethod
    def from_content(
        cls,
        file_name: str,
        dir_path: str | None,
        content: str,
        uuid: str | None = None,
    ) -> Document:
        """工厂方法：从已知内容构建文档（避免重复 IO）"""
        doc_hash = text_hash(content)
        abs_dir_path = dir_path
        rel_dir_path = None
        if dir_path:
            try:
                rel_dir_path = os.path.relpath(dir_path, os.getcwd())
            except Exception:
                rel_dir_path = dir_path
        md_docs = split_markdown_from_content(file_name, rel_dir_path, content)
        chunks = [Chunk(hash=text_hash(doc.page_content), lc_document=doc) for doc in md_docs]
        document = cls(uuid=uuid, name=file_name, path=abs_dir_path or "", hash=doc_hash, chunks=chunks)
        return document
