from langchain_core.documents import Document
from x1ayu_rag.splitter.markdown import MarkdownSplitter

def split_markdown_from_content(file_name: str, dir_path: str | None, content: str) -> list[Document]:
    """从 Markdown 内容中分割文档。
    
    参数:
        file_name: 文件名
        dir_path: 目录路径
        content: Markdown 内容
        
    返回:
        list[Document]: 分割后的文档列表
    """
    splitter = MarkdownSplitter()
    return splitter.split_from_content(file_name, dir_path, content)
