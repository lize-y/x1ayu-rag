import argparse
import os
from pathlib import Path
from x1ayu_rag.db.sqlite import initialize_db
from x1ayu_rag.chain.chain import get_chain
from x1ayu_rag.service.ingest_service import IngestService
from x1ayu_rag.service.search_service import SearchService
from x1ayu_rag.repository.document_repository import DocumentRepository
from x1ayu_rag.db.sqlite import get_conn
from datetime import datetime, timezone


def init():
    """初始化 RAG 运行环境（创建目录并初始化数据库）"""
    os.makedirs(".x1ayu_rag", exist_ok=True)
    db_file = os.path.join(".x1ayu_rag", "sqlite.db")
    if os.path.exists(db_file):
        print("RAG environment already initialized.")
        return
    initialize_db()
    print("RAG environment initialized.")


def add_file(file_path: str):
    """新增或更新单个文件到系统"""
    service = IngestService()
    action, uuid = service.add_or_update(file_path)
    print(f"[{action}] {os.path.basename(file_path)} uuid={uuid}")


def add_path_recursive(root: str):
    """递归处理目录下所有 .md 文件，判断新增/更新"""
    p = Path(root)
    if p.is_dir():
        md_files = [str(fp) for fp in p.rglob("*.md")]
    else:
        md_files = [str(p)] if p.suffix.lower() == ".md" else []
    service = IngestService()
    if md_files:
        successes, failures = service.add_or_update_many(md_files)
        root_abs = str(p.resolve())
        for fp, action, uuid in successes:
            rel = os.path.relpath(fp, root_abs) if os.path.isdir(root_abs) else os.path.basename(fp)
            print(f"[{action}] {rel} uuid={uuid}")
        for fp, err in failures:
            rel = os.path.relpath(fp, root_abs) if os.path.isdir(root_abs) else os.path.basename(fp)
            print(f"[error] {rel}: {err}")
    else:
        print("No markdown files found under directory; checking deletions...")
    # 删除文件系统中已缺失的文档
    remove_missing_under_path(str(p.resolve()))


def remove_missing_under_path(root: str):
    """检测数据库中文档在文件系统是否已删除，补偿删除记录与索引"""
    repo = DocumentRepository()
    abs_root = os.path.abspath(root)
    docs = repo.list_by_path_prefix(abs_root)
    service = IngestService(repo)
    removed = 0
    for doc in docs:
        file_path = os.path.join(doc.path, doc.name)
        if not os.path.exists(file_path):
            # 删除文档及其分块与向量
            service.repo.delete_by_uuid(doc.uuid)
            removed += 1
            print(f"[deleted] {file_path} uuid={doc.uuid}")
    if removed == 0:
        print("No deletions detected.")

def show_documents():
    """打印 documents 表的内容"""
    cursor = get_conn().cursor()
    cursor.execute("SELECT name, path, created_at, updated_at FROM documents ORDER BY path, name")
    rows = cursor.fetchall()
    cursor.close()
    if not rows:
        print("documents is empty.")
        return
    def fmt_dt(v: str) -> str:
        if not v:
            return "-"
        vs = str(v).strip()
        if vs.isdigit():
            try:
                dt_utc = datetime.utcfromtimestamp(int(vs)).replace(tzinfo=timezone.utc)
                return dt_utc.astimezone().strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return vs
        try:
            try:
                dt_naive = datetime.strptime(vs, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                dt_naive = datetime.fromisoformat(vs)
            dt_utc = dt_naive.replace(tzinfo=timezone.utc) if dt_naive.tzinfo is None else dt_naive.astimezone(timezone.utc)
            return dt_utc.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return vs
    headers = ["NAME", "PATH", "CREATED", "UPDATED"]
    name_w = max(len(headers[0]), max(len(r["name"]) for r in rows))
    path_w = max(len(headers[1]), max(len(r["path"]) for r in rows))
    created_vals = [fmt_dt(r["created_at"]) for r in rows]
    updated_vals = [fmt_dt(r["updated_at"]) for r in rows]
    created_w = max(len(headers[2]), max(len(v) for v in created_vals))
    updated_w = max(len(headers[3]), max(len(v) for v in updated_vals))
    sep = "+" + "-" * (name_w + 2) + "+" + "-" * (path_w + 2) + "+" + "-" * (created_w + 2) + "+" + "-" * (updated_w + 2) + "+"
    print(sep)
    print(f"| {headers[0]:<{name_w}} | {headers[1]:<{path_w}} | {headers[2]:<{created_w}} | {headers[3]:<{updated_w}} |")
    print(sep)
    for r, cv, uv in zip(rows, created_vals, updated_vals):
        print(f"| {r['name']:<{name_w}} | {r['path']:<{path_w}} | {cv:<{created_w}} | {uv:<{updated_w}} |")
    print(sep)

def select_data(query: str, k: int = 2):
    """检索相似数据并在终端打印"""
    service = SearchService()
    results = service.search(query, k)
    for doc, score in results:
        meta = doc.metadata or {}
        dir_path = meta.get("dir_path", "")
        file_name = meta.get("file_name", "")
        mk_struct = meta.get("mk_struct", "")
        sim = f"{score:3f}"
        left = f"{dir_path}/{file_name}" if dir_path else file_name
        right = f"{mk_struct}"
        meta_line = f" | {left} | {right} | {sim} | "
        meta_sep = "-" * len(meta_line.strip())
        print(meta_sep)
        print(meta_line)
        # 第二块：内容行（原样），单条分隔线，宽度匹配内容最长行
        content = doc.page_content
        lines = content.splitlines() or [content]
        max_len = max(len(l) for l in lines)
        csep_len = max(max_len, len(meta_sep))
        csep = "-" * csep_len
        print(csep)
        print(content)
        print(csep)


def chain_results(query: str, mode: str | None = None, k: int = 2):
    """运行 RAG 链并输出答案"""
    chain = get_chain(mode)
    result = chain.invoke({"question": query})
    print(
        "========================================Chain Result========================================\n",
        result,
    )


def cli():
    """Command line interface entry point."""
    parser = argparse.ArgumentParser(description="My Note RAG Tool")
    subparsers = parser.add_subparsers(dest="command")

    # init
    sp_init = subparsers.add_parser("init", help="Initialize RAG environment")

    # add
    sp_add = subparsers.add_parser("add", help="Add files or directory to RAG")
    sp_add.add_argument("path", type=str, help="File or directory to add")

    # select
    sp_select = subparsers.add_parser("select", help="Query similar data")
    sp_select.add_argument("query", type=str, help="Query text")
    sp_select.add_argument("-k", type=int, default=2, help="Number of similar results")

    # chain
    sp_chain = subparsers.add_parser("chain", help="Run RAG chain with query")
    sp_chain.add_argument("query", type=str, help="Query text")
    sp_chain.add_argument("-m", "--mode", type=str, choices=["debug"], help="Mode for RAG chain")
    sp_chain.add_argument("-k", type=int, default=2, help="Top-K similar chunks")
    
    # show
    sp_show = subparsers.add_parser("show", help="Print documents table")

    args = parser.parse_args()

    if args.command == "init":
        init()
    elif args.command == "add":
        target = args.path
        if os.path.isdir(target):
            add_path_recursive(os.path.abspath(target))
        else:
            add_file(target)
    elif args.command == "select":
        select_data(args.query, args.k)
    elif args.command == "chain":
        chain = get_chain(args.mode)
        result = chain.invoke({"question": args.query})
        print(
            "========================================Chain Result========================================\n",
            result,
        )
    elif args.command == "show":
        show_documents()
    else:
        parser.print_help()
