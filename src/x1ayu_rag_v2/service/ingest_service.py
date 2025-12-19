import os
from x1ayu_rag_v2.model.document import Document
from x1ayu_rag_v2.repository.document_repository import DocumentRepository
from x1ayu_rag_v2.db.sqlite_db import SqliteDB

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
            file_path: 文件绝对路径
            
        返回:
            str: 文档 UUID
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # 1. 解析与切分 (内存操作)
        # 不再需要传递 splitter，Document 内部自动使用 get_splitter()
        doc = Document.from_file(file_path)
        
        # 2. 检查是否存在 (可选，或者 Repository层处理冲突)
        # 这里我们假设是添加新文档，如果存在同名同路径的，先不做处理或报错
        # 简单起见，先检查
        existing = self.doc_repo.get_by_path_and_name(doc.path, doc.name)
        if existing:
            # 如果哈希一样，跳过
            if existing.hash == doc.hash:
                return existing.uuid
            # 如果不一样，可能需要更新（先删后加），这里 v2 先只实现 add
            # 或者抛出异常
            print(f"Document {doc.name} exists but hash differs. Skipping update in simple add.")
            return existing.uuid

        # 3. 持久化 (原子操作)
        self.doc_repo.add(doc)
        
        return doc.uuid
