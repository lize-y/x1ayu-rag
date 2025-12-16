from x1ayu_rag.cli.cli import cli
import warnings
import logging


if __name__ == "__main__":
    # 忽略所有 UserWarning
    warnings.filterwarnings("ignore", category=UserWarning)
    # 完全禁用 Milvus 相关日志
    milvus_logger = logging.getLogger("langchain_milvus.vectorstores.milvus")
    milvus_logger.disabled = True
    cli()
