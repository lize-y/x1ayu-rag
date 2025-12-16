from __future__ import annotations
from x1ayu_rag.utils.hash import text_hash
from langchain_core.documents import Document as LC_Document
from uuid import uuid4


class Chunk:
    """文档分块领域对象

    表示文档的一个语义片段，包含唯一标识、所属文档ID、内容哈希以及可选的 LangChain 文档。
    """

    pkid: str
    document_id: str
    hash: str
    position: int | None

    lc_document: LC_Document | None

    def __init__(
        self,
        document_id: str | None = None,
        content: str | None = None,
        hash: str | None = None,
        pkid: str | None = None,
        lc_document: LC_Document | None = None,
        position: int | None = None,
    ):
        """构造函数

        参数:
            document_id: 所属文档的 uuid
            content: 当未提供 hash 时，用于计算哈希的原始内容
            hash: 分块内容哈希（可选，优先使用）
            pkid: 分块唯一标识（可为空，空则自动生成）
            lc_document: LangChain 的 Document，供向量库使用
            position: 分块在原文中的顺序位置（从0开始）
        """
        self.pkid = pkid if pkid else str(uuid4())
        self.document_id = document_id
        if hash:
            self.hash = hash
        else:
            if not content:
                raise ValueError("Content cannot be empty when hash is not provided.")
            self.hash = text_hash(content)
        self.lc_document = lc_document
        self.position = position if position is not None else 0

    def __eq__(self, other):
        """比较两个分块是否相等（基于哈希）"""
        if isinstance(other, Chunk):
            return self.hash == other.hash
        return NotImplemented

    @classmethod
    def from_lc_document(cls, document_id: str, lc_doc: LC_Document) -> "Chunk":
        """工厂方法：由 LangChain 文档创建分块并计算哈希"""
        return cls(
            document_id=document_id,
            content=lc_doc.page_content,
            lc_document=lc_doc,
        )
