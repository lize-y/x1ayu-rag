from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_milvus import Milvus
from langchain.tools import tool
from langchain.agents import create_agent
from uuid import uuid4
from langchain_core.documents import Document
import json

model = ChatOllama(
    model="qwen3:4b",
    base_url="http://host.docker.internal:11434",
)

embeddings = OllamaEmbeddings(
    model="embeddinggemma:latest",
    base_url="http://host.docker.internal:11434",
)

URI = "./milvus_example.db"

vector_store = Milvus(
    embedding_function=embeddings,
    connection_args={"uri": URI},
    index_params={"index_type": "FLAT", "metric_type": "L2"},
)

with open("uv.md", "r", encoding="utf-8") as f:
    markdown_document = f.read()

headers_to_split_on = [
    ("#", "Header1"),
    ("##", "Header2"),
    ("###", "Header3"),
    ("####", "Header4"),
]

markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on, return_each_line=True
)
md_docs = markdown_splitter.split_text(markdown_document)
updated_docs = [
    Document(
        page_content=doc.page_content,
        metadata={"mk_struct": json.dumps(doc.metadata, ensure_ascii=False)},
    )
    for doc in md_docs
]

uuids = [str(uuid4()) for _ in range(len(md_docs))]
print("===========================metadata after update=========================")
print(updated_docs[-1].metadata)
for item in updated_docs[-1].metadata.items():
    print(type(item[0]), item[0])
    print(type(item[1]), item[1])
print("==============================================")
vector_store.add_documents(documents=updated_docs, ids=uuids)

results = vector_store.similarity_search_with_score("怎么创建uv项目？", k=1)

for res, score in results:
    print(f"* [SIM={score:3f}] {res.page_content} [{res.metadata}]")
