import os

# 默认配置目录名称
CONFIG_DIR_NAME = ".x1ayu_rag_v2"

# 默认配置目录路径（当前工作目录下的隐藏文件夹）
DEFAULT_CONFIG_DIR = CONFIG_DIR_NAME

# SQLite 数据库路径
SQLITE_DB_NAME = "sqlite.db"
SQLITE_DB_PATH = os.path.join(DEFAULT_CONFIG_DIR, SQLITE_DB_NAME)

# Milvus 向量库路径
MILVUS_DB_NAME = "milvus.db"
MILVUS_DB_PATH = os.path.join(DEFAULT_CONFIG_DIR, MILVUS_DB_NAME)
