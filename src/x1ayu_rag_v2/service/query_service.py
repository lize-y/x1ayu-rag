from typing import List, Optional
from x1ayu_rag_v2.repository.document_repository import DocumentRepository
from x1ayu_rag_v2.model.document import Document
from x1ayu_rag_v2.db.sqlite_db import SqliteDB

class QueryService:
    """查询服务
    
    提供文档检索、列表展示和过滤功能。
    """
    def __init__(self):
        self.doc_repo = DocumentRepository()
        # 确保 DB 已初始化 (查询时也需要，防止首次运行未建表)
        SqliteDB.init_db()

    def list_documents(self) -> List[Document]:
        """获取所有已摄取的文档"""
        return self.doc_repo.list_all()

    def search_documents(self, query: str) -> List[Document]:
        """搜索文档
        
        参数:
            query: 搜索关键词 (匹配文件名或路径)
        """
        if not query or not query.strip():
            return self.list_documents()
        return self.doc_repo.search_documents(query)
