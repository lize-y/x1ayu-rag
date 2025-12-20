from langchain_milvus import Milvus
from x1ayu_rag.config.constants import MILVUS_DB_PATH
from x1ayu_rag.llm.factory import LLMFactory

class MilvusDB:
    _vector_store = None

    @classmethod
    def get_vector_store(cls):
        if cls._vector_store is None:
            cls._vector_store = Milvus(
                embedding_function=LLMFactory.get_embeddings(),
                connection_args={"uri": MILVUS_DB_PATH},
                index_params={"index_type": "FLAT", "metric_type": "L2"},
                auto_id=False # 我们自己管理 ID
            )
        return cls._vector_store
