import os
from x1ayu_rag.model.document import Document
from x1ayu_rag.repository.document_repository import DocumentRepository
from x1ayu_rag.db.sqlite_db import SqliteDB
from x1ayu_rag.utils.path_utils import to_relative_path
from x1ayu_rag.service.constants import IngestOp

class IngestService:
    """摄取服务
    
    协调文档解析、切分和存储。
    """
    def __init__(self):
        self.doc_repo = DocumentRepository()
        # 确保 DB 已初始化
        SqliteDB.init_db()

    def add_document(self, file_path: str) -> str:
        """添加单个文档
        
        参数:
            file_path: 文件路径
            
        返回:
            str: 文档 UUID
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {to_relative_path(file_path)}")
            
        # 1. 解析与切分 (内存操作)
        # Document.from_file 会处理相对路径转换
        doc = Document.from_file(file_path)
        
        # 2. 持久化 (原子操作)
        self.doc_repo.add(doc)
        
        return doc.uuid

    def delete_document(self, uuid: str) -> None:
        """删除单个文档

        参数:
            uuid: 文档 UUID
        """
        self.doc_repo.delete_by_uuid(uuid)

    def update_document(self, uuid: str, file_path: str) -> str:
        """更新单个文档

        参数:
            uuid: 原文档 UUID
            file_path: 新文件路径

        返回:
            str: 文档 UUID (保持不变)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {to_relative_path(file_path)}")

        # 1. 解析新文档
        # 注意：这里生成的 doc 会有一个新的随机 UUID
        new_doc = Document.from_file(file_path)
        
        # 2. 强制使用旧 UUID
        new_doc.uuid = uuid
        # 同时更新 chunks 里的 document_id
        if new_doc.chunks:
            for chunk in new_doc.chunks:
                chunk.document_id = uuid

        # 3. 执行更新 (先删后加)
        # TODO: 理想情况下应该在 Repository 层作为一个事务处理
        self.doc_repo.delete_by_uuid(uuid)
        self.doc_repo.add(new_doc)
        
        return uuid

    def ingest_document(self, file_path: str) -> tuple[IngestOp, dict | str]:
        """处理文档或目录摄取请求。
        
        参数:
            file_path: 文件或目录的绝对路径
            
        返回:
            tuple[IngestOp, dict | str]: 操作类型和详情
            如果是目录，返回 (IngestOp.BATCH_RESULT, summary_dict)
            如果是文件，返回 (IngestOp.ADDED/UPDATED/SKIPPED/ERROR, message)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Path not found: {to_relative_path(file_path)}")

        if os.path.isdir(file_path):
            return IngestOp.BATCH_RESULT, self.sync_directory(file_path)
        else:
            try:
                doc = Document.from_file(file_path)
                existing = self.doc_repo.get_by_path_and_name(doc.path, doc.name)
                
                if existing:
                    uuid = self.update_document(existing.uuid, file_path)
                    if existing.hash == doc.hash:
                        return IngestOp.SKIPPED, f"Document UUID: {uuid} (unchanged)"
                    else:
                        uuid = self.update_document(existing.uuid, file_path)
                        return IngestOp.UPDATED, f"Document {doc.name} updated. UUID: {uuid}"
                else:
                    uuid = self.add_document(file_path)
                    return IngestOp.ADDED, f"Document {doc.name} added. UUID: {uuid}"
            except Exception as e:
                return IngestOp.ERROR, str(e)

    def sync_directory(self, root_path: str) -> list[tuple[str, str, str]]:
        """同步目录中的所有 Markdown 文件
        
        参数:
            root_path: 根目录路径
            
        返回:
            list: 操作结果列表，每个元素为 (action, file_path, detail/uuid)
        """
        results = []
        
        # 1. 递归扫描文件
        fs_files = []
        for root, _, files in os.walk(root_path):
            for file in files:
                if file.endswith(".md"):
                    fs_files.append(os.path.join(root, file))
        
        # 2. 处理添加/更新 - 调用 ingest_document
        for file_path in fs_files:
            op_type, result = self.ingest_document(file_path)
            rel_path = to_relative_path(file_path)
            
            # 转换 UUID 或错误信息
            # 如果是成功操作，result 包含 "Document ... UUID: <uuid>"，我们需要提取 UUID 或者保持原样
            # 为了符合用户要求的格式 `[action] file uuid`，我们需要从 message 中提取 UUID
            # ingest_document 返回的是 (op_type, message)
            # 我们可以修改 ingest_document 返回 (op_type, uuid/error) 但这会破坏单文件调用的兼容性
            # 这里简单解析一下 message
            
            detail = str(result)
            if "UUID: " in detail:
                detail = detail.split("UUID: ")[1].strip()
            
            if op_type == IngestOp.ERROR:
                results.append(("[error]", rel_path, detail))
            elif op_type == IngestOp.SKIPPED:
                # 显示 [skipped] 状态
                results.append(("[skipped]", rel_path, detail))
            elif op_type == IngestOp.ADDED:
                results.append(("[added]", rel_path, detail))
            elif op_type == IngestOp.UPDATED:
                results.append(("[updated]", rel_path, detail))

        # 3. 清理已删除的文件
        rel_root = to_relative_path(root_path)
        all_docs = self.doc_repo.list_all()
        
        for doc in all_docs:
            doc_full_path = os.path.join(doc.path, doc.name)
            
            is_in_scope = False
            if rel_root == "." or rel_root == "":
                is_in_scope = True
            else:
                if doc.path == rel_root or doc.path.startswith(rel_root + os.sep):
                    is_in_scope = True
            
            if is_in_scope:
                abs_doc_path = os.path.abspath(doc_full_path)
                if not os.path.exists(abs_doc_path):
                    self.delete_document(doc.uuid)
                    results.append(("[deleted]", to_relative_path(doc_full_path), doc.uuid))

        return results
