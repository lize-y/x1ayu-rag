from functools import wraps
import click
import sys
from rich.console import Console
from x1ayu_rag_v2.api.system_api import SystemAPI

console = Console()
system_api = SystemAPI()

def require_init(f):
    """装饰器：确保系统已初始化，否则提示用户并退出"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not system_api.is_initialized():
            console.print("[red]RAG 环境未初始化。请先运行 'init'。[/red]")
            sys.exit(1)
        return f(*args, **kwargs)
    return wrapper
