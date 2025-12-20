from typing import Tuple, Dict, Any, Optional
from x1ayu_rag.service.system_service import SystemService
from x1ayu_rag.config.app_config import update_config, load_config

class SystemAPI:
    """系统 API 层
    
    负责处理系统初始化和配置相关的请求。
    """
    def __init__(self):
        self.service = SystemService()

    def initialize_system(self, config_values: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """初始化系统环境并应用配置
        
        参数:
            config_values: 可选的初始化配置字典
            
        返回:
            (success, message)
        """
        try:
            # 1. 初始化环境（目录和数据库）
            initialized = self.service.initialize_environment()
            msg_prefix = "Environment initialized" if initialized else "Environment already exists"
            
            # 2. 如果提供了配置，更新配置
            if config_values:
                update_config(config_values)
                msg_suffix = " and configuration updated."
            else:
                msg_suffix = "."
                
            return True, f"{msg_prefix}{msg_suffix}"
            
        except Exception as e:
            return False, f"Initialization failed: {str(e)}"

    def is_initialized(self) -> bool:
        """检查系统是否已初始化"""
        return self.service.is_initialized()

    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return load_config()

    def update_configuration(self, updates: Dict[str, Any]) -> Tuple[bool, str]:
        """更新配置
        
        参数:
            updates: 要更新的配置键值对
            
        返回:
            (success, message)
        """
        try:
            update_config(updates)
            return True, "Configuration updated successfully."
        except Exception as e:
            return False, f"Failed to update configuration: {str(e)}"

    def validate_embedding_config(self) -> Tuple[bool, str]:
        """校验 Embedding 配置有效性"""
        from x1ayu_rag.llm.factory import LLMFactory
        try:
            LLMFactory.validate_embedding_config()
            return True, ""
        except ValueError as e:
            return False, str(e)

    def validate_chat_config(self) -> Tuple[bool, str]:
        """校验 Chat 配置有效性"""
        from x1ayu_rag.llm.factory import LLMFactory
        try:
            LLMFactory.validate_chat_config()
            return True, ""
        except ValueError as e:
            return False, str(e)
