from typing import List, Dict, Any
from x1ayu_rag_v2.service.query_service import QueryService
from x1ayu_rag_v2.utils.path_utils import to_relative_path

class QueryAPI:
    """查询 API 层
    
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
