from langchain_core.runnables import Runnable
from x1ayu_rag.chain.retriever import Retriever
from x1ayu_rag.chain.generator import Generator
from x1ayu_rag.chain.debug import get_debug_model_info_node, get_debug_context_node

class RAGChain:
    """RAG 链编排器
    
    组合 Retriever 和 Generator 构建完整的 RAG 流程。
    支持 debug 模式。
    """
    
    def __init__(self):
        self.retriever = Retriever()
        self.generator = Generator()

    def get_chain(self, mode: str = None, k: int = 2) -> Runnable:
        """构建 RAG 链
        
        参数:
            mode: 'debug' 开启调试输出
            k: 默认检索数量
        """
        retriever_node = self.retriever.as_runnable(default_k=k)
        generator_node = self.generator.as_runnable()
        
        if mode == "debug":
            # Debug 模式：
            # Input -> [Debug Model Info] -> Retriever -> [Debug Context] -> Generator
            return (
                get_debug_model_info_node()
                | retriever_node
                | get_debug_context_node()
                | generator_node
            )
        else:
            return retriever_node | generator_node
