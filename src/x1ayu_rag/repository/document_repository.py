from __future__ import annotations
from typing import Optional
import os
from x1ayu_rag.db.sqlite import get_conn
from x1ayu_rag.model.document import Document
from x1ayu_rag.model.chunk import Chunk
from x1ayu_rag.repository.chunk_repository import ChunkRepository
from x1ayu_rag.exceptions import DatabaseError, ModelConnectionError, ConfigurationError


class DocumentRepository:
    """文档仓储

    封装对文档与分块的持久化访问，抽象出数据操作接口，便于替换实现。
    """
    def __init__(self, chunk_repo: ChunkRepository | None = None):
        self.chunk_repo = chunk_repo or ChunkRepository()

    def get(self, dir_path: str, file_name: str) -> Optional[Document]:
        """按路径与文件名获取文档"""
        cursor = get_conn().cursor()
        cursor.execute(
            "SELECT * FROM documents WHERE path = ? AND name = ?",
            (dir_path, file_name),
        )
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return None
        document = Document(
            uuid=row["uuid"],
            name=row["name"],
            path=row["path"],
            hash=row["hash"],
            chunks=self.chunk_repo.list_by_document_id(row["uuid"]),
        )
        return document

    def store(self, document: Document):
        """存储文档与其分块
        
        使用事务保证文档和分块的原子性存储。如果分块存储（向量化）失败，
        回滚文档存储操作，确保数据库状态一致。
        """
        conn = get_conn()
        try:
            # 开启事务
            cursor = conn.cursor()
            try:
                # 1. 存储文档记录
                cursor.execute(
                    "INSERT INTO documents (uuid, name, path, hash) VALUES (?, ?, ?, ?)",
                    (document.uuid, document.name, document.path, document.hash),
                )
                
                # 2. 存储分块（可能涉及外部 API 调用，如 Embedding）
                if document.chunks:
                    self.chunk_repo.store(document.chunks)
                
                # 一切顺利，提交事务
                conn.commit()
            except Exception:
                # 发生异常（如 Embedding 失败），回滚事务
                conn.rollback()
                raise
            finally:
                cursor.close()
        except Exception as e:
            # 向上传递异常，以便上层（如 CLI）捕获并提示用户
            if isinstance(e, (ConfigurationError, ModelConnectionError, DatabaseError)):
                 raise e
            # 将其他异常包装为 DatabaseError
            raise DatabaseError(f"Failed to store document: {str(e)}", e)

    def delete_by_uuid(self, uuid: str):
        """按 uuid 删除文档与其分块"""
        chunks = self.chunk_repo.list_by_document_id(uuid)
        chunk_ids = [c.pkid for c in chunks]
        if chunk_ids:
            self.chunk_repo.delete_by_ids(chunk_ids)
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE uuid = ?", (uuid,))
            cursor.close()

    def list_chunks(self, document_id: str) -> list[Chunk]:
        """列出某文档的所有分块"""
        return self.chunk_repo.list_by_document_id(document_id)

    def update_hash(self, uuid: str, new_hash: str):
        """更新文档哈希"""
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE documents SET hash = ?, updated_at = datetime('now') WHERE uuid = ?", (new_hash, uuid))
            cursor.close()

    def replace_chunks(self, uuid: str, new_chunks: list[Chunk]):
        """替换指定文档的所有分块"""
        old_chunks = self.chunk_repo.list_by_document_id(uuid)
        old_ids = [c.pkid for c in old_chunks]
        if old_ids:
            self.chunk_repo.delete_by_ids(old_ids)
        if new_chunks:
            self.chunk_repo.store(new_chunks)

    def list_by_path_prefix(self, dir_path: str) -> list[Document]:
        """按目录前缀列出文档（不加载分块）
        
        要求：documents.path 为相对路径；dir_path 也应为相对路径。
        """
        cursor = get_conn().cursor()
        cursor.execute(
            "SELECT * FROM documents WHERE path = ? OR path LIKE ?",
            (dir_path, f"{dir_path}/%"),
        )
        rows = cursor.fetchall()
        cursor.close()
        docs: list[Document] = []
        for row in rows:
            docs.append(
                Document(
                    uuid=row["uuid"],
                    name=row["name"],
                    path=row["path"],
                    hash=row["hash"],
                    chunks=None,
                )
            )
        return docs

    def list_all(self) -> list[Document]:
        """返回所有文档（不加载分块）"""
        cursor = get_conn().cursor()
        cursor.execute("SELECT * FROM documents")
        rows = cursor.fetchall()
        cursor.close()
        docs: list[Document] = []
        for row in rows:
            docs.append(
                Document(
                    uuid=row["uuid"],
                    name=row["name"],
                    path=row["path"],
                    hash=row["hash"],
                    chunks=None,
                )
            )
        return docs

    def list_all_paths(self) -> list[tuple[str, str]]:
        """返回所有文档的 (path, name) 列表"""
        cursor = get_conn().cursor()
        cursor.execute("SELECT path, name FROM documents")
        rows = cursor.fetchall()
        cursor.close()
        return [(row["path"], row["name"]) for row in rows]

    def get_by_hash(self, hash_value: str) -> Optional[Document]:
        """通过哈希值获取文档。"""
        cursor = get_conn().cursor()
        cursor.execute("SELECT * FROM documents WHERE hash = ? LIMIT 1", (hash_value,))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return None
        return Document(
            uuid=row["uuid"],
            name=row["name"],
            path=row["path"],
            hash=row["hash"],
            chunks=None,
        )

    def list_all_with_details(self) -> list[dict]:
        """返回所有文档的详细信息，用于列表显示。"""
        cursor = get_conn().cursor()
        cursor.execute("SELECT name, path, created_at, updated_at FROM documents ORDER BY path, name")
        rows = cursor.fetchall()
        cursor.close()
        
        results = []
        for row in rows:
            results.append({
                "name": row["name"],
                "path": row["path"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        return results

    def update_path_name(self, uuid: str, new_path: str, new_name: str):
        """更新文档的路径和名称。"""
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE documents SET path = ?, name = ?, updated_at = datetime('now') WHERE uuid = ?",
                (new_path, new_name, uuid),
            )
            cursor.close()
