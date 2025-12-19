from x1ayu_rag.cli.cli import cli
import warnings
import logging
import os

# 1. 抑制 pkg_resources 相关的 UserWarning
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")
warnings.filterwarnings("ignore", category=UserWarning, module="milvus_lite")

# 2. 抑制 pymilvus 的异步初始化错误日志
# 这里的日志实际上是 pymilvus 在初始化时通过 logging 模块打印的，不是 warning
# 我们需要获取 pymilvus 的 logger 并禁用它
logging.getLogger("pymilvus").setLevel(logging.CRITICAL)

if __name__ == "__main__":
    # 忽略所有 UserWarning (保留之前的通用配置)
    warnings.filterwarnings("ignore", category=UserWarning)
    
    # 完全禁用 Langchain Milvus 相关日志
    milvus_logger = logging.getLogger("langchain_milvus.vectorstores.milvus")
    milvus_logger.disabled = True
    
    cli()
