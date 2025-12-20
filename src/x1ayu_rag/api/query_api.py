from typing import List, Dict, Any
from x1ayu_rag.service.query_service import QueryService
from x1ayu_rag.utils.path_utils import to_relative_path

class QueryAPI:
    """查询 API 层
    s
    为 CLI 和其他客户端提供数据查询接口。
    """
    def __init__(self):
        self.service = QueryService()

    def get_document_table_data(self) -> List[Dict[str, Any]]:
        """获取用于表格展示的文档数据
        
        返回:
            List[Dict]: 包含 name, path, uuid 等字段的字典列表
        """
        docs = self.service.list_documents()
        return [
            {
                "Name": doc.name,
                "Path": to_relative_path(doc.path),
                "UUID": doc.uuid,
                # "Chunks": len(doc.chunks) if doc.chunks else 0 # 暂不加载 chunks
            }
            for doc in docs
        ]

    def search_for_select(self, query: str = "") -> List[str]:
        """获取用于交互式选择的选项列表
        
        参数:
            query: 搜索关键词
            
        返回:
            List[str]: 格式化的选项字符串列表 "filename (path)"
        """
        docs = self.service.search_documents(query)
        # 格式化为 "filename (relative_path)" 供用户选择
        return [f"{doc.name} ({to_relative_path(doc.path)})" for doc in docs]

    def search_chunks(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """搜索分块并返回前端友好的数据结构
        
        参数:
            query: 搜索关键词
            top_k: 返回数量
            
        返回:
            List[Dict]: 包含 content, score, metadata 等信息的列表
        """
        chunks = self.service.search_chunks(query, top_k)
        results = []
        for chunk in chunks:
            if not chunk.lc_document:
                continue
            
            # 提取元数据
            meta = chunk.lc_document.metadata or {}
            
            results.append({
                "content": chunk.lc_document.page_content,
                "metadata": meta,
                # 注意：ChunkRepository 返回的 LangChain Document 可能不包含 score
                # 除非我们修改 search_chunks 返回 (doc, score) 元组
                # Milvus 的 similarity_search 默认返回 docs
                # similarity_search_with_score 返回 (doc, score)
                # 目前 Repository 实现是 similarity_search，所以没有 score
            })
        return results

    
