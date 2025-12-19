from __future__ import annotations
from typing import List
from x1ayu_rag.db.sqlite import get_conn
from x1ayu_rag.db.milvus import get_vector_store
from x1ayu_rag.model.chunk import Chunk
from x1ayu_rag.exceptions import ModelConnectionError, DatabaseError, ConfigurationError

class ChunkRepository:
    """分块仓储
    
    负责文档分块数据的持久化，包括 SQLite 中的元数据和向量数据库中的向量数据。
    """
    def list_by_document_id(self, document_id: str) -> list[Chunk]:
        """列出指定文档的所有分块。"""
        try:
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
        except Exception as e:
            raise DatabaseError(f"列出分块失败: {str(e)}", e)

    def store(self, chunks: list[Chunk]) -> None:
        """存储分块。
        
        同时写入向量数据库和 SQLite 数据库。
        """
        if not chunks:
            return
        try:
            ids = [c.pkid for c in chunks]
            get_vector_store().add_documents(
                documents=[c.lc_document for c in chunks if c.lc_document is not None],
                ids=ids,
            )
        except ConfigurationError:
            raise
        except Exception as e:
            raise ModelConnectionError(f"生成 Embedding 或连接向量库失败: {str(e)}", e)

        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    "INSERT OR IGNORE INTO chunks (pkid, document_id, hash, position) VALUES (?, ?, ?, ?)",
                    [(c.pkid, c.document_id, c.hash, c.position) for c in chunks],
                )
        except Exception as e:
            raise DatabaseError(f"存储分块到数据库失败: {str(e)}", e)

    def delete_by_ids(self, ids: list[str]) -> None:
        """通过 ID 删除分块。
        
        同时从向量数据库和 SQLite 数据库中删除。
        """
        if not ids:
            return
        try:
            get_vector_store().delete(ids)
        except ConfigurationError:
            raise
        except Exception as e:
            raise ModelConnectionError(f"从向量库删除失败: {str(e)}", e)
        
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.executemany("DELETE FROM chunks WHERE pkid = ?", [(i,) for i in ids])
        except Exception as e:
             raise DatabaseError(f"从数据库删除分块失败: {str(e)}", e)
