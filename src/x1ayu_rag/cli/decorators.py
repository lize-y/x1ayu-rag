from functools import wraps
import sys
from rich.console import Console
from x1ayu_rag.api.system_api import SystemAPI

console = Console()
system_api = SystemAPI()

def require_init(f):
    """装饰器：确保系统已初始化，否则提示用户并退出"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not system_api.is_initialized():
            console.print("RAG 环境未初始化。请先运行 'init'。")
            sys.exit(1)
        return f(*args, **kwargs)
    return wrapper

def require_embedding_config(f):
    """装饰器：确保 Embedding 配置完整且有效"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        success, msg = system_api.validate_embedding_config()
        if not success:
            console.print(f"{msg}")
            sys.exit(1)
        return f(*args, **kwargs)
    return wrapper

def require_chat_config(f):
    """装饰器：确保 Chat 配置完整且有效"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        success, msg = system_api.validate_chat_config()
        if not success:
            console.print(f"{msg}")
            sys.exit(1)
        return f(*args, **kwargs)
    return wrapper
