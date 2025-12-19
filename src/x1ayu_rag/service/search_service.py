from __future__ import annotations
from typing import List, Tuple, Protocol, Any
from langchain_core.documents import Document as LCDocument
from x1ayu_rag.repository.system_repository import VectorRepository

class SearchService:
    """检索服务
    
    提供基于向量库的相似度检索接口，供 CLI 与链路层调用。
    该服务屏蔽了底层向量数据库的具体实现细节，对外暴露统一的检索方法。
    """
    def __init__(self, vector_repo: VectorRepository = None):
        """
        初始化搜索服务。
        
        参数:
            vector_repo (VectorRepository, optional): 向量仓储实例。
        """
        self.vector_repo = vector_repo or VectorRepository()

    def search(self, query: str, k: int = 2) -> List[Tuple[LCDocument, float]]:
        """执行相似度检索
        
        参数:
            query (str): 查询文本，通常是用户的问题。
            k (int): 返回的相似结果数量，默认为 2。
            
        返回:
            List[Tuple[Document, float]]: 文档与相似度得分的二元组列表。
                                          Document 对象包含 page_content 和 metadata。
        """
        return self.vector_repo.search(query, k=k)
