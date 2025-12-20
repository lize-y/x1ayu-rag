我已完成对 LLM 接口的重构，以支持将 Chat 和 Embedding 分离到不同的提供商。

**变更内容：**

1.  **接口拆分 (`src/x1ayu_rag_v2/llm/base.py`)**:
    *   将原有的 `LLMProvider` 拆分为 `ChatModelProvider` 和 `EmbeddingModelProvider` 两个独立的抽象基类。
    *   保留 `LLMProvider` 作为一个继承自前两者的混合接口，以保持对全功能提供商的兼容。

2.  **具体实现更新**:
    *   **OpenAIProvider** 和 **OllamaProvider** 现在明确继承自 `ChatModelProvider` 和 `EmbeddingModelProvider`。

3.  **工厂类更新 (`src/x1ayu_rag_v2/llm/factory.py`)**:
    *   `get_chat_model` 现在会检查获取的 Provider 是否实现了 `ChatModelProvider` 接口。
    *   `get_embeddings` 现在会检查获取的 Provider 是否实现了 `EmbeddingModelProvider` 接口。
    *   这种设计允许未来添加只支持 Chat 或只支持 Embedding 的提供商，并且在配置中可以自由组合（例如 Chat 用 OpenAI，Embedding 用 Ollama）。

现在，你可以完全根据配置文件的 `chat.provider` 和 `embedding.provider` 字段来独立控制使用哪个服务，系统会自动处理接口兼容性检查。
