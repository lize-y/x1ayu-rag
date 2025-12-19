from __future__ import annotations
from typing import Protocol, List, Tuple
from langchain_core.documents import Document as LCDocument
from x1ayu_rag.db.milvus import get_vector_store
from x1ayu_rag.db.sqlite import initialize_db, get_conn

class SystemRepository:
    """系统仓储
    
    负责系统级别的持久化操作，如数据库初始化。
    """
    def initialize_database(self) -> None:
        """初始化数据库 Schema"""
        initialize_db()

    def check_connection(self) -> bool:
        """检查数据库连接是否正常"""
        try:
            get_conn()
            return True
        except Exception:
            return False

class VectorRepository:
    """向量仓储
    
    负责向量数据库的直接操作，包括检索。
    虽然 ChunkRepository 处理了存储和删除，但检索通常被视为一种独立的“读取”操作，
    或者也可以将其整合到 ChunkRepository 中。为了保持单一职责，
    如果逻辑复杂，可以分开；如果简单，可以整合。
    这里为了响应“所有数据库操作都放到仓储层”的要求，我们将检索逻辑封装在此。
    """
    def __init__(self):
        self._store = get_vector_store()

    def search(self, query: str, k: int = 4) -> List[Tuple[LCDocument, float]]:
        """执行相似度检索"""
        return self._store.similarity_search_with_score(query, k=k)
