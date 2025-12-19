import sqlite3
from x1ayu_rag_v2.config.constants import SQLITE_DB_PATH
import os

class SqliteDB:
    _conn = None
    
    @classmethod
    def get_conn(cls):
        if cls._conn is None:
            if not os.path.exists(os.path.dirname(SQLITE_DB_PATH)):
                 os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
            cls._conn = sqlite3.connect(SQLITE_DB_PATH)
            cls._conn.row_factory = sqlite3.Row
            cls._conn.execute("PRAGMA foreign_keys = ON")
        return cls._conn

    @classmethod
    def init_db(cls):
        conn = cls.get_conn()
        cursor = conn.cursor()
        
        # 创建 documents 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                uuid TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                path TEXT NOT NULL,
                hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建 chunks 表
        # v2: 移除 hash 字段 (根据用户需求，不需要增量更新块)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                pkid TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                position INTEGER NOT NULL,
                FOREIGN KEY(document_id) REFERENCES documents(uuid) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
