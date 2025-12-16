from langchain_ollama import OllamaEmbeddings
from langchain_milvus import Milvus

embeddings = OllamaEmbeddings(
    model="embeddinggemma:latest",
    base_url="http://host.docker.internal:11434",
)


URI = ".x1ayu_rag/milvus.db"

_vector_store = None


def get_vector_store():
    """获取 Milvus 向量存储（单例）

    返回:
        Milvus: LangChain 的 Milvus 向量库封装
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = Milvus(
            embedding_function=embeddings,
            connection_args={"uri": URI},
            index_params={"index_type": "FLAT", "metric_type": "L2"},
        )
    return _vector_store


def print_similar_data(query: str, k: int = 2):
    """打印相似度检索结果

    参数:
        query: 查询文本
        k: 返回结果数量
    """
    results = get_vector_store().similarity_search_with_score(query, k=k)
    for res, score in results:
        print(f"* [SIM={score:3f}] {res.page_content} [{res.metadata}]")


def get_similar_data(query: str, k: int = 2):
    """获取相似度检索结果

    参数:
        query: 查询文本
        k: 返回结果数量
    返回:
        list[tuple[Document, float]]: 文档与分数的二元组列表
    """
    results = get_vector_store().similarity_search_with_score(query, k=k)
    return results
