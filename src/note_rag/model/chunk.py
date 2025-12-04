from __future__ import annotations
from note_rag.utils.hash import text_hash
from note_rag.db.sqlite import get_conn
from note_rag.db.milvus import get_vector_store
from langchain_core.documents import Document as LC_Document
from uuid import uuid4


class Chunk:

    pkid: str
    document_id: str
    hash: str

    lc_document: LC_Document | None

    def __init__(
        self,
        document_id: str | None = None,
        content: str | None = None,
        hash: str | None = None,
        pkid: str | None = None,
        lc_document: LC_Document | None = None,
    ):
        self.pkid = pkid if pkid else str(uuid4())
        self.document_id = document_id
        if hash:
            self.hash = hash
        else:
            if not content:
                raise ValueError("Content cannot be empty when hash is not provided.")
            self.hash = text_hash(content)
        self.lc_document = lc_document

    def __eq__(self, other):
        if isinstance(other, Chunk):
            return self.hash == other.hash
        return NotImplemented

    @staticmethod
    def select_by_doc_id(document_id: str) -> list[Chunk]:
        cursor = get_conn().cursor()
        cursor.execute("SELECT * FROM chunks WHERE document_id = ?", (document_id,))
        rows = cursor.fetchall()
        cursor.close()

        chunks = []
        for row in rows:
            chunk = Chunk(
                pkid=row["pkid"], document_id=row["document_id"], hash=row["hash"]
            )
            chunks.append(chunk)

        return chunks

    @staticmethod
    def store(chunks: list[Chunk]):
        # milvus中存储chunks
        ids = [chunk.pkid for chunk in chunks]
        get_vector_store().add_documents(
            documents=[
                chunk.lc_document for chunk in chunks if chunk.lc_document is not None
            ],
            ids=ids,
        )
        # sqlite中存储chunks
        try:
            with get_conn() as conn:  # 上下文管理器自动 commit/rollback
                cursor = conn.cursor()
                cursor.executemany(
                    "INSERT INTO chunks (pkid, document_id, hash) VALUES (?, ?, ?)",
                    [(chunk.pkid, chunk.document_id, chunk.hash) for chunk in chunks],
                )
        except Exception as e:
            raise e

    @staticmethod
    def delete_by_ids(ids: list[str]):
        # milvus中删除chunks
        get_vector_store().delete_ids(ids)
        # sqlite中删除chunks
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    "DELETE FROM chunks WHERE pkid = ?", [(id_,) for id_ in ids]
                )
        except Exception as e:
            raise e
