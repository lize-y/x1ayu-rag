from x1ayu_rag_v2.splitter.markdown import MarkdownSplitter

def get_splitter():
    """获取默认的 Markdown 切分器实例。
    
    目前固定使用 MarkdownSplitter。
    """
    return MarkdownSplitter()
