from langchain_milvus import Milvus
from x1ayu_rag_v2.config.constants import MILVUS_DB_PATH
# 复用 v1 的 provider，假设配置结构不变
from x1ayu_rag.llm.provider import get_embeddings

class MilvusDB:
    _vector_store = None

    @classmethod
    def get_vector_store(cls):
        if cls._vector_store is None:
            cls._vector_store = Milvus(
                embedding_function=get_embeddings(),
                connection_args={"uri": MILVUS_DB_PATH},
                index_params={"index_type": "FLAT", "metric_type": "L2"},
                auto_id=False # 我们自己管理 ID
            )
        return cls._vector_store
