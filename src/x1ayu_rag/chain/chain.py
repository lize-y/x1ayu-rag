from x1ayu_rag.db.milvus import get_similar_data
from x1ayu_rag.llm.provider import get_chat_llm
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import PromptTemplate
from x1ayu_rag.config.app_config import load_config
from langchain_core.output_parsers import StrOutputParser

_chain = None

template = """
你是一个知识问答助手，回答时请严格遵循以下规则：

1. 只能使用提供的文档内容回答，不允许凭个人知识。
2. 每个结论必须标注文档来源，格式：[文档名-段落号]。
3. 用户可提供额外提示，请在回答中遵循。
4. 如果文档中信息不足，明确回答：“文档中未提供相关信息”。
5. 输出必须严格分为两部分：
   - 第一部分：回答正文
   - 第二部分：引用文档列表，每条文档显示格式：
       文件名: 文档内容
用户问题：{question}
用户提示：{user_prompt}
文档内容：{docs}
"""

cfg = load_config()

def get_debug_llm_input_node():
    """获取调试节点：打印 LLM 最终输入（Prompt）"""
    return RunnableLambda(
        lambda x: print(
            "========================================Prompt========================================\n",
            x,
            "===================================================================================\n"
        )
        or x
    )

def get_debug_model_info_node():
    """获取调试节点：打印模型配置信息"""
    # 重新加载配置以获取最新状态
    cfg = load_config()
    chat_config = cfg.get("chat", {})
    return RunnableLambda(
        lambda x: print(
            f"========================================Model========================================\n"
            f"Provider: {chat_config.get('provider')}\n"
            f"Model:    {chat_config.get('model')}\n"
            f"Base URL: {chat_config.get('base_url')}\n"
            f"===================================================================================\n"
        ) or x
    )

def get_rag_node(k: int = 2):
    """获取 RAG 检索节点"""
    cfg = load_config()
    # 从 chat 配置中读取 sys_prompt，不再使用独立的 prompt 配置
    user_sys_prompt = cfg.get("chat", {}).get("sys_prompt") or ""
    
    return RunnableLambda(
        lambda x: {
            "question": x["question"],
            "docs": rag_search(x["question"], k=x.get("k", k)), # 优先使用 invoke 参数中的 k，否则使用函数默认 k
            "user_prompt": user_sys_prompt,
        }
    )

def get_template_node():
    """获取 Prompt 模板节点"""
    return PromptTemplate.from_template(template)

def get_llm_node():
    """获取 LLM 节点"""
    return get_chat_llm(temperature=0)

def get_chain(mode: str | None = None, k: int = 2):
    """构建并返回 RAG 链

    参数:
        mode: 可选的调试模式（'debug'）
        k: 检索参考片段的数量，默认为 2
    返回:
        Runnable: 可调用链对象
    """
    rag_node = get_rag_node(k)
    template_node = get_template_node()
    llm_node = get_llm_node()
    
    if mode == "debug":
        debug_model_info = get_debug_model_info_node()
        debug_llm_input = get_debug_llm_input_node()
        chain_instance = debug_model_info | rag_node | template_node | debug_llm_input | llm_node | StrOutputParser()
    else:
        chain_instance = rag_node | template_node | llm_node | StrOutputParser()
    
    return chain_instance


import json

def rag_search(query: str, k: int = 2):
    """执行向量检索并格式化为模板可用的文本块"""
    docs = get_similar_data(query, k)
    
    formatted_docs = []
    for doc, score in docs:
        doc_info = {
            "doc_name": f"{doc.metadata.get('dir_path', '')}/{doc.metadata.get('file_name', '')}",
            "位置": doc.metadata.get("mk_struct", ""),
            "content": doc.page_content,
            "sim_score": score # Optional: include score if needed, though user didn't explicitly ask for it in JSON
        }
        formatted_docs.append(doc_info)
        
    return json.dumps(formatted_docs, ensure_ascii=False, indent=2)
