from typing import Tuple, Optional
import os
from x1ayu_rag_v2.service.ingest_service import IngestService
from x1ayu_rag_v2.service.constants import IngestOp
from x1ayu_rag_v2.utils.path_utils import to_relative_path

class IngestAPI:
    """摄取 API 层
    
    负责接收 CLI 或其他入口的请求，验证参数，并调用 Service 层。
    """
    def __init__(self):
        self.service = IngestService()

    def ingest_document(self, file_path: str) -> Tuple[bool, str]:
        """处理文档或目录摄取请求

        参数:
            file_path: 文件或目录路径

        返回:
            (success, message): 成功与否及提示信息
        """
        # 1. 参数校验
        if not file_path:
            return False, "Error: File path cannot be empty."
        
        # 检查存在性
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            return False, f"Error: Path not found: {to_relative_path(abs_path)}"
        
        # 2. 调用 Service (现在统一入口)
        try:
            op_type, result = self.service.ingest_document(abs_path)
            
            if op_type == IngestOp.BATCH_RESULT:
                # 目录递归结果
                summary = result
                added_count = len(summary[IngestOp.ADDED.value])
                updated_count = len(summary[IngestOp.UPDATED.value])
                deleted_count = len(summary[IngestOp.DELETED.value])
                errors_count = len(summary[IngestOp.ERROR.value])
                
                msg_parts = []
                if added_count: msg_parts.append(f"Added {added_count}")
                if updated_count: msg_parts.append(f"Updated {updated_count}")
                if deleted_count: msg_parts.append(f"Deleted {deleted_count}")
                if errors_count: msg_parts.append(f"Errors {errors_count}")
                
                if not msg_parts:
                    msg = "No changes detected."
                else:
                    msg = "Sync complete: " + ", ".join(msg_parts)
                    
                if errors_count > 0:
                    msg += f"\nFirst few errors: {summary[IngestOp.ERROR.value][:3]}"
                return True, msg
                
            elif op_type == IngestOp.ERROR:
                return False, f"Ingestion error: {result}"
            else:
                # 单文件操作结果 (ADDED, UPDATED, SKIPPED)
                return True, f"Success: {result}"
                
        except Exception as e:
            return False, f"Ingestion failed: {str(e)}"
