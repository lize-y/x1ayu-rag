from __future__ import annotations
from typing import List, Tuple
from langchain_core.documents import Document as LCDocument


class SearchService:
    """检索服务

    提供基于向量库的相似度检索接口，供 CLI 与链路层调用。
    """
    def search(self, query: str, k: int = 2) -> List[Tuple[LCDocument, float]]:
        """执行相似度检索

        参数:
            query: 查询文本
            k: 返回的相似结果数量
        返回:
            List[Tuple[Document, float]]: 文档与相似度得分的二元组列表
        """
        from x1ayu_rag.db.milvus import get_similar_data
        return get_similar_data(query, k)
