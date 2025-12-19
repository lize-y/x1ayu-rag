from typing import Optional
from x1ayu_rag_v2.model.document import Document
from x1ayu_rag_v2.db.sqlite_db import SqliteDB
from x1ayu_rag_v2.repository.chunk_repository import ChunkRepository
from x1ayu_rag_v2.error.exceptions import DatabaseError, ModelConnectionError

class DocumentRepository:
    """文档仓储
    
    负责 Document 的持久化，并协调 ChunkRepository 进行分块的存储。
    实现了原子性操作：Document 和 Chunks 要么都存成功，要么都回滚。
    """
    
    def add(self, document: Document):
        """原子性地添加文档及其分块"""
        conn = SqliteDB.get_conn()
        
        try:
            # 开启事务（SQLite 默认在执行 DML 时开启隐式事务，或者我们可以显式控制）
            cursor = conn.cursor()
            
            # 1. 插入 Document
            cursor.execute(
                "INSERT INTO documents (uuid, name, path, hash) VALUES (?, ?, ?, ?)",
                (document.uuid, document.name, document.path, document.hash)
            )
            
            # 2. 插入 Chunks (传递 conn 给 ChunkRepo)
            if document.chunks:
                chunk_repo = ChunkRepository(conn)
                chunk_repo.store_chunks(document.chunks)
            
            # 3. 提交事务
            conn.commit()
            
        except (DatabaseError, ModelConnectionError) as e:
            conn.rollback()
            raise e
        except Exception as e:
            conn.rollback()
            raise DatabaseError(f"Unexpected error adding document: {e}", e)

    def get_by_path_and_name(self, path: str, name: str) -> Optional[Document]:
        conn = SqliteDB.get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE path = ? AND name = ?", (path, name))
        row = cursor.fetchone()
        if row:
            return Document(
                uuid=row["uuid"],
                name=row["name"],
                path=row["path"],
                hash=row["hash"],
                chunks=None # 暂不加载 chunks，按需加载
            )
        return None

    def delete_by_uuid(self, uuid: str):
        """原子性地删除文档及其分块"""
        conn = SqliteDB.get_conn()
        try:
            cursor = conn.cursor()
        
            chunk_repo = ChunkRepository(conn)
            # 先调用 repo 删除逻辑，它负责 Milvus 删除和可能的 SQLite 删除
            chunk_repo.delete_by_document_id(uuid)
            
            # 再删除 Document
            cursor.execute("DELETE FROM documents WHERE uuid = ?", (uuid,))
            
            conn.commit()
        except (DatabaseError, ModelConnectionError) as e:
            conn.rollback()
            raise e
        except Exception as e:
            conn.rollback()
            raise DatabaseError(f"Unexpected error deleting document: {e}", e)
