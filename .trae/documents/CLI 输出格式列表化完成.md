我已完成对 `rag add` 命令输出格式的修改。

**变更详情：**

1.  **Service 层 (`src/x1ayu_rag/service/ingest_service.py`)**:
    *   `sync_directory` 现在返回一个操作结果列表 `list[tuple[str, str, str]]`，每个元素包含 `(action_tag, file_path, detail)`。
    *   `ingest_document` 保持原逻辑，但其返回值被上层重新包装。

2.  **API 层 (`src/x1ayu_rag/api/ingest_api.py`)**:
    *   `ingest_document` 现在统一返回 `(success, message, results)`。
    *   对于单文件操作，也会将其包装成一个包含单条记录的列表，格式与目录同步一致：`[("[added]", "rel/path", "uuid")]`。

3.  **CLI 层 (`src/x1ayu_rag/cli/cli.py`)**:
    *   `add` 命令现在遍历 `results` 列表，并逐行打印。
    *   输出格式符合要求：
        *   成功：`[action] file uuid` (例如 `[added] docs/readme.md 1234-5678...`)，绿色显示。
        *   失败：`[error] file error` (例如 `[error] docs/secret.md Permission denied`)，红色显示。

**效果：**
现在无论是添加单个文件还是同步目录，输出都会是清晰的文件列表形式，直观展示每个文件的处理状态和结果（UUID 或 错误信息）。
