from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser
from x1ayu_rag.llm.factory import LLMFactory
from x1ayu_rag.chain.prompt import get_prompt_node

class Generator:
    """RAG 生成器组件
    
    负责构建 Prompt 和调用 LLM 生成回答。
    """
    
    def get_llm(self):
        """获取配置好的 LLM 实例"""
        return LLMFactory.get_chat_model()

    def as_runnable(self) -> Runnable:
        """返回生成部分的 Runnable (SysPrompt -> Prompt -> LLM -> Parser)"""
        return (
            get_prompt_node()
            | self.get_llm() 
            | StrOutputParser()
        )
