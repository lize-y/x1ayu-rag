import os
import time
from x1ayu_rag.config.constants import DEFAULT_CONFIG_DIR, SQLITE_DB_PATH
from x1ayu_rag.repository.system_repository import SystemRepository

class SystemService:
    """系统服务
    
    负责系统级别的操作，如环境初始化、健康检查等。
    """
    def __init__(self, system_repo: SystemRepository = None):
        self.system_repo = system_repo or SystemRepository()
    
    def is_initialized(self) -> bool:
        """检查系统是否已初始化。
        
        返回:
            bool: 如果 SQLite 数据库文件存在，则返回 True，否则返回 False。
        """
        return os.path.exists(SQLITE_DB_PATH)
        
    def initialize_environment(self) -> bool:
        """初始化 RAG 运行环境。
        
        创建必要的目录并初始化数据库。
        
        返回:
            bool: 如果执行了初始化操作返回 True，如果环境已存在则返回 False。
        """
        os.makedirs(DEFAULT_CONFIG_DIR, exist_ok=True)
        
        if self.is_initialized():
            return False
        
        self.system_repo.initialize_database()
        return True
