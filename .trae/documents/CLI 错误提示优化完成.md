我已完成对 `rag add` 命令错误提示的改进。

**变更详情：**

1.  **Service 层改进 (`src/x1ayu_rag/service/ingest_service.py`)**:
    *   修改了 `sync_directory` 方法。当遇到 `IngestOp.ERROR` 时，不再只记录文件路径，而是记录 `(relative_path, error_message)` 元组，从而保留了具体的错误原因（如 Permission denied, File not found 等）。

2.  **API 层改进 (`src/x1ayu_rag/api/ingest_api.py`)**:
    *   更新了 `ingest_document` 方法的签名，现在返回 `(success, message, errors)` 三元组。
    *   在返回结果时，将 Service 层收集到的错误列表透传给调用方。

3.  **CLI 层改进 (`src/x1ayu_rag/cli/cli.py`)**:
    *   更新了 `add` 命令的处理逻辑。
    *   当操作成功（`success=True`）但存在部分错误（`errors` 列表非空，常见于目录同步的部分失败）时，会打印 `Detailed Errors` 列表。
    *   支持打印简单的错误字符串或 `(path, msg)` 元组，显示具体的错误文件和原因。

**效果：**
现在运行 `rag add .` 如果遇到错误，将会看到类似如下的详细输出：
```
Sync complete: Added 5, Errors 3

Detailed Errors:
- AIGC/ai.md: [Errno 13] Permission denied: ...
- python/rag.md: File format not supported
...
```
这直接解决了用户反馈的“First few errors: ['AIGC/ai.md', ...] 要提示具体错误”的问题。
