from langchain_core.runnables import RunnableLambda
from x1ayu_rag.config.app_config import load_config

def get_debug_model_info_node() -> RunnableLambda:
    """调试节点：打印模型配置"""
    def _print_info(x):
        cfg = load_config()
        chat_config = cfg.get("chat", {})
        print(
            f"========================================Model========================================\n"
            f"Provider: {chat_config.get('provider')}\n"
            f"Model:    {chat_config.get('model')}\n"
            f"Base URL: {chat_config.get('base_url')}\n"
            f"===================================================================================\n"
        )
        return x
    return RunnableLambda(_print_info)

def get_debug_context_node() -> RunnableLambda:
    """调试节点：打印检索上下文信息"""
    def _print_context(x):
        print(
            "========================================Context========================================\n"
            f"Question: {x.get('question')}\n"
            f"User Prompt: {x.get('user_prompt')}\n"
            f"Docs Preview: {x.get('docs')[:200]}...\n"
            "=======================================================================================\n"
        )
        return x
    return RunnableLambda(_print_context)
