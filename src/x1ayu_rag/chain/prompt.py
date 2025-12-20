from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda
from x1ayu_rag.config.app_config import load_config

# 默认 Prompt 模板
DEFAULT_TEMPLATE = """
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

def get_prompt_node() -> Runnable:
    """获取完整的 Prompt 处理节点
    
    包含：
    1. 系统提示词注入 (System Prompt Injection)
    2. 模板格式化 (Template Formatting)
    """
    
    def _inject_sys_prompt(x):
        cfg = load_config()
        sys_prompt = cfg.get("chat", {}).get("sys_prompt", "")
        
        # 优先使用 invoke 时传入的 override，否则使用全局配置
        if not x.get("user_prompt"):
            x["user_prompt"] = sys_prompt
        return x
        
    prompt_template = PromptTemplate.from_template(DEFAULT_TEMPLATE)
    
    return RunnableLambda(_inject_sys_prompt) | prompt_template
