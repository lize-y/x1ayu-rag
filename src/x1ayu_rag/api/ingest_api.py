from typing import Tuple, Optional
import os
from x1ayu_rag.service.ingest_service import IngestService
from x1ayu_rag.service.constants import IngestOp
from x1ayu_rag.utils.path_utils import to_relative_path

class IngestAPI:
    """摄取 API 层
    
    负责接收 CLI 或其他入口的请求，验证参数，并调用 Service 层。
    """
    def __init__(self):
        self.service = IngestService()

    def ingest_document(self, file_path: str) -> Tuple[bool, str, list]:
        """处理文档或目录摄取请求

        参数:
            file_path: 文件或目录路径

        返回:
            (success, message, errors): 成功与否、提示信息及详细错误列表
        """
        # 1. 参数校验
        if not file_path:
            return False, "Error: File path cannot be empty.", []
        
        # 检查存在性
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            return False, f"Error: Path not found: {to_relative_path(abs_path)}", []
        
        # 2. 调用 Service (现在统一入口)
        try:
            op_type, result = self.service.ingest_document(abs_path)
            
            if op_type == IngestOp.BATCH_RESULT:
                # 目录递归结果
                results = result # 现在的 result 是 list[tuple]
                
                # 为了保持接口返回类型一致性，我们可以返回 (True, "Sync complete", results)
                # CLI 层将负责遍历 results 并打印
                
                # 计算统计信息以供消息使用
                count = len(results)
                msg = f"Sync complete: Processed {count} items."
                
                return True, msg, results
                
            elif op_type == IngestOp.ERROR:
                return False, f"Ingestion error: {result}", []
            else:
                # 单文件操作结果 (ADDED, UPDATED, SKIPPED)
                # 统一包装成 list 格式
                # 假设 result 是 "Document ... added. UUID: ..."
                detail = str(result)
                uuid_val = detail
                if "UUID: " in detail:
                    uuid_val = detail.split("UUID: ")[1].strip()
                
                action_map = {
                    IngestOp.ADDED: "[added]",
                    IngestOp.UPDATED: "[updated]",
                    IngestOp.SKIPPED: "[skipped]"
                }
                action = action_map.get(op_type, "[unknown]")
                
                # 单文件模式下 file_path 可能是绝对路径，转为相对路径
                rel_path = to_relative_path(file_path)
                return True, f"Success: {result}", [(action, rel_path, uuid_val)]
                
        except Exception as e:
            return False, f"Ingestion failed: {str(e)}", []
