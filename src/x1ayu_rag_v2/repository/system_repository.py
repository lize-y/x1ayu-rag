from __future__ import annotations
from x1ayu_rag_v2.db.sqlite_db import SqliteDB

class SystemRepository:
    """系统仓储
    
    负责系统级别的持久化操作，如数据库初始化。
    """
    def initialize_database(self) -> None:
        """初始化数据库 Schema"""
        SqliteDB.init_db()

    def check_connection(self) -> bool:
        """检查数据库连接是否正常"""
        try:
            SqliteDB.get_conn()
            return True
        except Exception:
            return False
