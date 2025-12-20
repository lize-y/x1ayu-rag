from typing import List, Dict, Any
import json
from x1ayu_rag.service.query_service import QueryService
from langchain_core.runnables import RunnableLambda

class Retriever:
    """RAG 检索器组件
    
    负责调用 QueryService 进行向量检索，并格式化结果供 LLM 使用。
    """
    
    def __init__(self, query_service: QueryService = None):
        self.query_service = query_service or QueryService()

    def _format_docs(self, chunks) -> str:
        """将检索到的 Chunk 列表格式化为 JSON 字符串"""
        formatted_docs = []
        for chunk in chunks:
            if not chunk.lc_document:
                continue
                
            doc = chunk.lc_document
            meta = doc.metadata or {}
            
            doc_info = {
                "doc_name": f"{meta.get('dir_path', '')}/{meta.get('file_name', '')}".lstrip('/'),
                "位置": meta.get("mk_struct", ""),
                "content": doc.page_content,
            }
            formatted_docs.append(doc_info)
            
        return json.dumps(formatted_docs, ensure_ascii=False, indent=2)

    def as_runnable(self, default_k: int = 2):
        """返回 LangChain Runnable 对象"""
        return RunnableLambda(
            lambda x: {
                "question": x["question"],
                "docs": self._format_docs(
                    self.query_service.search_chunks(
                        x["question"], 
                        top_k=x.get("k", default_k)
                    )
                ),
                "user_prompt": x.get("user_prompt", "")
            }
        )
