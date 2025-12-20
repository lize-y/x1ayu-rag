我已修复了 CLI 中 `[action]` 标签（如 `[added]`, `[error]`）不显示的问题。

**原因分析：**
`rich` 库将方括号中的内容（如 `[added]`）视为样式标签。由于这些标签通常未定义样式，Rich 在解析时会将其视为无效标签并可能将其吞掉，或者在某些情况下显示为空。

**修复方案：**
在 `src/x1ayu_rag/cli/cli.py` 中，使用 `rich.markup.escape()` 函数对 `action` 字符串进行转义。
例如，`[added]` 会被转义为 `\[added]`，这样 Rich 就会将其作为普通文本打印，而不是样式标签。

**代码变更：**
```python
from rich.markup import escape
# ...
safe_action = escape(action)
# ...
console.print(f"[{color}]{safe_action}[/{color}] ...")
```

现在运行 `rag add`，应该能正确看到带有颜色的 `[added]` 或 `[error]` 标签了。
