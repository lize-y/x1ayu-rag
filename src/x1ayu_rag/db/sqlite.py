import sqlite3
from importlib import resources
from x1ayu_rag.config.constants import SQLITE_DB_PATH

_conn = None
db_path = SQLITE_DB_PATH


def get_conn():
    """获取 SQLite 连接（单例）

    返回:
        sqlite3.Connection: 已初始化的连接对象
    """
    global _conn
    if _conn is None:
        if db_path is None:
            raise ValueError("Database not initialized yet")
        _conn = sqlite3.connect(db_path)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys = ON")
    return _conn


def close_conn():
    """关闭并清理全局连接"""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


def initialize_db():
    """初始化数据库 Schema

    从包内资源读取 `db.sql` 并执行建表与索引创建。
    """
    conn = get_conn()
    # 读取 schema SQL 文件
    sql = (
        resources.files("x1ayu_rag.config.file")
        .joinpath("db.sql")
        .read_text(encoding="utf-8")
    )
    # 执行 SQL
    conn.executescript(sql)
    conn.commit()
