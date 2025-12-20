我已按照要求处理了 `[skipped]` 状态的显示。

**变更详情：**

1.  **Service 层 (`src/x1ayu_rag/service/ingest_service.py`)**:
    *   在 `sync_directory` 中，当 `ingest_document` 返回 `SKIPPED` 状态时，现在会将其加入结果列表（此前是 `pass` 忽略）。
    *   结果格式为 `("[skipped]", rel_path, detail)`。

2.  **CLI 层 (`src/x1ayu_rag/cli/cli.py`)**:
    *   在打印循环中添加了对 `[skipped]` 标签的处理。
    *   设置其颜色为 `dim blue`（暗蓝色），以区分于添加（绿色）、更新（黄色）和删除（红色），既显示了状态又不会太显眼。

现在，当再次运行 `rag add .` 且文件没有变化时，你会看到类似 `[skipped] file.md Document skipped (unchanged)` 的输出，而不是什么都没有。
