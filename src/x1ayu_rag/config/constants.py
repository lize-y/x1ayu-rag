import os

# 应用名称
APP_NAME = "x1ayu_rag"

# 默认配置目录名称
CONFIG_DIR_NAME = ".x1ayu_rag"

# 默认配置目录路径（当前工作目录下的隐藏文件夹）
# 注意：如果需要支持全局配置，可以改为 os.path.join(os.path.expanduser("~"), CONFIG_DIR_NAME)
# 这里保持原逻辑，使用当前目录
DEFAULT_CONFIG_DIR = CONFIG_DIR_NAME

# 配置文件名
CONFIG_FILE_NAME = "config.json"
CONFIG_FILE_PATH = os.path.join(DEFAULT_CONFIG_DIR, CONFIG_FILE_NAME)

# SQLite 数据库路径
SQLITE_DB_NAME = "sqlite.db"
SQLITE_DB_PATH = os.path.join(DEFAULT_CONFIG_DIR, SQLITE_DB_NAME)

# Milvus 向量库路径
MILVUS_DB_NAME = "milvus.db"
MILVUS_DB_PATH = os.path.join(DEFAULT_CONFIG_DIR, MILVUS_DB_NAME)

# 默认相似度检索数量
DEFAULT_K = 2
