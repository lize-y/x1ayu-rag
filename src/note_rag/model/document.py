from __future__ import annotations
from note_rag.model.chunk import Chunk
from uuid import uuid4
from note_rag.utils.hash import text_hash
from note_rag.utils.mdSplitter import split_markdown
from note_rag.db.sqlite import get_conn
import os


class Document:
    uuid: str
    name: str
    path: str
    hash: str
    chunks: list[Chunk] | None

    def __init__(
        self,
        uuid: str | None,
        name: str,
        path: str,
        hash: str,
        chunks: list[Chunk] | None,
    ):
        self.uuid = uuid if uuid else str(uuid4())
        self.name = name
        self.path = path
        self.hash = hash
        if chunks:
            for chunk in chunks:
                chunk.document_id = self.uuid
        self.chunks = chunks

    def __eq__(self, other):
        if isinstance(other, Document):
            return self.hash == other.hash & self.name == other.name
        return NotImplemented

    @staticmethod
    def generateDocument(file_path: str) -> Document:
        file_name = os.path.basename(file_path)
        dir_path = os.path.dirname(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        doc_hash = text_hash(content)
        md_docs = split_markdown(file_name, dir_path)
        chunks = [
            Chunk(hash=text_hash(doc.page_content), lc_document=doc) for doc in md_docs
        ]
        document = Document(
            uuid=None, name=file_name, path=dir_path, hash=doc_hash, chunks=chunks
        )
        return document

    @staticmethod
    def get(dir_path, file_name) -> Document | None:
        cursor = get_conn().cursor()
        cursor.execute(
            "SELECT * FROM documents WHERE path = ? AND name = ?", (dir_path, file_name)
        )
        row = cursor.fetchone
        cursor.close()

        if row:
            document = Document(
                uuid=row["uuid"],
                name=row["name"],
                path=row["path"],
                hash=row["hash"],
                chunks=Chunk.select_by_doc_id(row["uuid"]),
            )
            return document
        else:
            # todo: 文件更改名称或路径时的处理
            return None

    @staticmethod
    def store(document: Document):
        try:
            with get_conn() as conn:  # 上下文管理器自动 commit/rollback
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO documents (uuid, name, path, hash) VALUES (?, ?, ?, ?)",
                    (document.uuid, document.name, document.path, document.hash),
                )
                cursor.close()
            if document.chunks:
                Chunk.store(document.chunks)
        except Exception as e:
            raise e

    @staticmethod
    def delete_by_uuid(uuid: str):
        # 删除关联的chunks
        chunks = Chunk.select_by_doc_id(uuid)
        chunk_ids = [chunk.pkid for chunk in chunks]
        Chunk.delete_by_ids(chunk_ids)

        # 删除document
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM documents WHERE uuid = ?", (uuid,))
        except Exception as e:
            raise e

    # todo
    @staticmethod
    def update():
        pass
