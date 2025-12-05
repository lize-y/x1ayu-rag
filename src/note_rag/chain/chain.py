from note_rag.db.milvus import get_similar_data
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

_chain = None

template = """
你是一个知识问答助手。
{sys_prompt}
对不确定的问题，请说明不确定性而不是编造答案。
基于以下检索内容回答问题。

问题:
{query}

检索内容:
{docs}

回答格式为:
- 回答内容
- 参考资料来源列表，格式为文件路径加内容摘要
"""

debug = RunnableLambda(
    lambda x: print(
        "========================================Prompt========================================\n",
        x,
    )
    or x
)


def get_chain(mode: str | None = None, sys_prompt: str | None = None):
    global _chain
    if _chain is None:
        rag_node = RunnableLambda(
            lambda x: {
                "query": x["question"],
                "docs": rag_search(x["question"], k=2),
                "sys_prompt": sys_prompt if sys_prompt else "",
            }
        )
        template_node = PromptTemplate.from_template(template)
        llm_node = ChatOllama(
            model="qwen3:0.6b",
            temperature=0,
            base_url="http://host.docker.internal:11434",
        )
        if mode == "debug":
            _chain = rag_node | template_node | debug | llm_node | StrOutputParser()
        else:
            _chain = rag_node | template_node | llm_node | StrOutputParser()
    return _chain


def rag_search(query: str, k: int = 2):
    docs = get_similar_data(query, k)
    return "\n".join(
        [
            f"""- {doc.metadata["dir_path"]}/{doc.metadata["file_name"]}
    {doc.metadata["mk_struct"]}:{repr(doc.page_content)}
[SIM={score:3f}]"""
            for doc, score in docs
        ]
    )
