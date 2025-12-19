from __future__ import annotations
from langchain_core.documents import Document as LC_Document
from uuid import uuid4
import hashlib

def text_hash(text: str) -> str:
    """计算文本的 SHA256 哈希值。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

class Chunk:
    """文档分块领域对象
    
    表示文档的一个语义片段，包含唯一标识、所属文档ID、内容哈希以及可选的 LangChain 文档。
    """

    pkid: str
    document_id: str
    position: int | None
    lc_document: LC_Document | None

    def __init__(
        self,
        document_id: str | None = None,
        pkid: str | None = None,
        lc_document: LC_Document | None = None,
        position: int | None = None,
    ):
        """构造函数"""
        self.pkid = pkid if pkid else str(uuid4())
        self.document_id = document_id
        self.lc_document = lc_document
        self.position = position if position is not None else 0

    @classmethod
    def from_lc_document(cls, lc_doc: LC_Document, position: int, document_id: str | None = None) -> "Chunk":
        """从 LangChain Document 构建 Chunk"""
        return cls(
            document_id=document_id,
            lc_document=lc_doc,
            position=position
        )
