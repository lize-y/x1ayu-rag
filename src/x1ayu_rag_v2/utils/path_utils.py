import os

def to_relative_path(path: str) -> str:
    """将绝对路径转换为相对于当前工作目录的路径
    
    如果路径不在当前工作目录下，则返回原路径。
    """
    try:
        cwd = os.getcwd()
        rel_path = os.path.relpath(path, cwd)
        if rel_path.startswith(".."):
            return path
        return rel_path
    except Exception:
        return path
