from langchain_core.documents import Document
from x1ayu_rag.splitter.markdown import MarkdownSplitter

def split_markdown_from_content(file_name: str, dir_path: str | None, content: str) -> list[Document]:
    splitter = MarkdownSplitter()
    return splitter.split_from_content(file_name, dir_path, content)
