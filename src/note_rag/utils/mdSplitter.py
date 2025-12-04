from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document
import json


def split_markdown(file_name: str, dir_path: str | None = None) -> list[Document]:
    with open(dir_path+"/"+file_name, "r", encoding="utf-8") as f:
        markdown_text = f.read()
    headers_to_split_on = [
        ("#", "Header1"),
        ("##", "Header2"),
        ("###", "Header3"),
        ("####", "Header4"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on, return_each_line=True
    )
    docs = markdown_splitter.split_text(markdown_text)
    final_docs = [
        Document(
            page_content=doc.page_content,
            metadata={
                "file_name": file_name,
                "dir_path": dir_path,
                "mk_struct": json.dumps(doc.metadata, ensure_ascii=False),
            },
        )
        for doc in docs
    ]
    return final_docs
