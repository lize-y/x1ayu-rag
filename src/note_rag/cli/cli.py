import argparse
import os
from pprint import pprint
from note_rag.db.sqlite import initialize_db
from note_rag.model.document import Document
from note_rag.db.milvus import get_similar_data


def init():
    os.makedirs(".note_rag", exist_ok=True)
    initialize_db()
    print("RAG environment initialized.")


def add_file(file_path: str):
    doc = Document.generateDocument(file_path)
    pprint(doc)
    Document.store(doc)
    print(f"File '{file_path}' added successfully.")


def select_data(query: str, k: int = 2):
    results = get_similar_data(query, k)
    pprint(results)


def cli():
    """Command line interface entry point."""
    parser = argparse.ArgumentParser(description="My Note RAG Tool")

    # 操作选项
    parser.add_argument(
        "-i", "--init", action="store_true", help="Initialize RAG environment"
    )
    parser.add_argument(
        "-a", "--add", type=str, metavar="FILE", help="Add a file to RAG"
    )
    parser.add_argument(
        "-s", "--select", type=str, metavar="QUERY", help="Query similar data"
    )
    parser.add_argument(
        "-k", type=int, default=2, help="Number of similar results (for select)"
    )

    args = parser.parse_args()

    # dispatch
    if args.init:
        init()
    elif args.add:
        add_file(args.add)
    elif args.select:
        select_data(args.select, args.k)
    else:
        parser.print_help()