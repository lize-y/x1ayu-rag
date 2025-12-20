from typing import List
from x1ayu_rag.model.chunk import Chunk
from x1ayu_rag.db.sqlite_db import SqliteDB
from x1ayu_rag.db.milvus_db import MilvusDB
from x1ayu_rag.error.exceptions import DatabaseError, ModelConnectionError

class ChunkRepository:
    """分块仓储"""
    
    def __init__(self, db_conn):
        self.conn = db_conn
        self.vector_store = MilvusDB.get_vector_store()

    def store_chunks(self, chunks: List[Chunk]):
        """存储分块到 SQLite 和 Milvus"""
        if not chunks:
            return

        # 1. 写入 SQLite (作为事务的一部分，不 commit)
        try:
            cursor = self.conn.cursor()
            cursor.executemany(
                "INSERT OR IGNORE INTO chunks (pkid, document_id, position) VALUES (?, ?, ?)",
                [(c.pkid, c.document_id, c.position) for c in chunks],
            )
        except Exception as e:
            raise DatabaseError(f"Failed to insert chunks into SQLite: {e}", e)

        # 2. 写入 Milvus
        # 如果 Milvus 写入失败，外部会捕获异常并回滚 SQLite 事务
        try:
            # 过滤掉没有 lc_document 的 chunk
            valid_chunks = [c for c in chunks if c.lc_document]
            if valid_chunks:
                self.vector_store.add_documents(
                    documents=[c.lc_document for c in valid_chunks],
                    ids=[c.pkid for c in valid_chunks]
                )
        except Exception as e:
            raise ModelConnectionError(f"Failed to insert chunks into Milvus: {e}", e)

    def delete_by_document_id(self, document_id: str):
        """删除指定文档的所有分块"""
        # 1. 先查出所有 chunk id，以便从 Milvus 删除
        cursor = self.conn.cursor()
        cursor.execute("SELECT pkid FROM chunks WHERE document_id = ?", (document_id,))
        rows = cursor.fetchall()
        pkids = [row["pkid"] for row in rows]
        
        if not pkids:
            return

        # 2. 从 SQLite 删除
        try:
            cursor.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
        except Exception as e:
             raise DatabaseError(f"Failed to delete chunks from SQLite: {e}", e)

        # 3. 从 Milvus 删除
        try:
            self.vector_store.delete(pkids)
        except Exception as e:
             raise ModelConnectionError(f"Failed to delete chunks from Milvus: {e}", e)

    def search_chunks(self, query: str, top_k: int = 2) -> List[Chunk]:
        """搜索分块"""
        try:
            lc_docs = self.vector_store.similarity_search(query, top_k)
            # 将 LangChain Document 转换为领域对象 Chunk
            chunks = []
            for i, doc in enumerate(lc_docs):
                chunks.append(Chunk(lc_document=doc)) 
            return chunks
        except Exception as e:
            raise ModelConnectionError(f"Failed to search chunks in Milvus: {e}", e)
