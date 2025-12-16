from __future__ import annotations
from typing import List
from x1ayu_rag.db.sqlite import get_conn
from x1ayu_rag.db.milvus import get_vector_store
from x1ayu_rag.model.chunk import Chunk


class ChunkRepository:
    def list_by_document_id(self, document_id: str) -> list[Chunk]:
        cursor = get_conn().cursor()
        cursor.execute(
            "SELECT * FROM chunks WHERE document_id = ? ORDER BY position ASC",
            (document_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        chunks: list[Chunk] = []
        for row in rows:
            chunks.append(
                Chunk(
                    pkid=row["pkid"],
                    document_id=row["document_id"],
                    hash=row["hash"],
                    position=row["position"],
                )
            )
        return chunks

    def store(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        ids = [c.pkid for c in chunks]
        get_vector_store().add_documents(
            documents=[c.lc_document for c in chunks if c.lc_document is not None],
            ids=ids,
        )
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT OR IGNORE INTO chunks (pkid, document_id, hash, position) VALUES (?, ?, ?, ?)",
                [(c.pkid, c.document_id, c.hash, c.position) for c in chunks],
            )

    def delete_by_ids(self, ids: list[str]) -> None:
        if not ids:
            return
        get_vector_store().delete(ids)
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.executemany("DELETE FROM chunks WHERE pkid = ?", [(i,) for i in ids])
