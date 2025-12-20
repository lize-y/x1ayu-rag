我已按照你的建议，将配置校验逻辑重构为 CLI 装饰器，使代码更加简洁且复用性更高。

**变更内容：**

1.  **工厂层增强 (`src/x1ayu_rag/llm/factory.py`)**:
    *   新增了 `validate_chat_config()` 和 `validate_embedding_config()` 类方法，用于显式触发配置校验。

2.  **装饰器新增 (`src/x1ayu_rag/cli/decorators.py`)**:
    *   新增 `require_chat_config` 装饰器：调用工厂校验 Chat 配置，失败时打印红色错误信息并退出。
    *   新增 `require_embedding_config` 装饰器：调用工厂校验 Embedding 配置，失败时打印红色错误信息并退出。

3.  **CLI 应用 (`src/x1ayu_rag/cli/cli.py`)**:
    *   `add` 命令：添加了 `@require_embedding_config`。
    *   `select` 命令：添加了 `@require_embedding_config`。
    *   `chain` 命令：添加了 `@require_embedding_config` 和 `@require_chat_config`，并移除了函数内部重复的 `try-except ValueError` 块。

**效果：**
现在，当你运行这些命令时，如果相关配置缺失，系统会在执行任何业务逻辑之前就进行检查，并给出统一风格的错误提示。
