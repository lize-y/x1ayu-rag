from typing import List, Optional
from x1ayu_rag.repository.document_repository import DocumentRepository
from x1ayu_rag.repository.chunk_repository import ChunkRepository
from x1ayu_rag.model.document import Document
from x1ayu_rag.model.chunk import Chunk
from x1ayu_rag.db.sqlite_db import SqliteDB

class QueryService:
    """查询服务
    
    提供文档检索、列表展示和过滤功能。
    """
    def __init__(self):
        self.doc_repo = DocumentRepository()
        self.chunk_repo = ChunkRepository(SqliteDB.get_conn())


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

    def search_chunks(self, query: str, top_k: int = 2) -> List[Chunk]:
        """搜索相关分块

        参数:
            query: 搜索关键词
            top_k: 返回结果数量
        """
        if not query or not query.strip():
            return []
        return self.chunk_repo.search_chunks(query, top_k)


    