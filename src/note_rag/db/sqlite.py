import sqlite3
from importlib import resources

_conn = None
db_path = ".note_rag/sqlite.db"


def get_conn():
    global _conn
    if _conn is None:
        if db_path is None:
            raise ValueError("Database not initialized yet")
        _conn = sqlite3.connect(db_path)
        _conn.row_factory = sqlite3.Row
    return _conn


def close_conn():
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


def initialize_db():
    conn = get_conn()
    # 读取 schema SQL 文件
    sql = (
        resources.files("note_rag.config.file")
        .joinpath("db.sql")
        .read_text(encoding="utf-8")
    )
    # 执行 SQL
    conn.executescript(sql)
    conn.commit()
