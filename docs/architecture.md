# 存储
## sqlite
做一个简单的存储，文档和分块都存储在 sqlite 数据库中
### 文档表
```sql
CREATE TABLE IF NOT EXISTS documents (
    uuid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(name, path)
);
```
存储文档的元数据，包括 uuid、文件名、路径、哈希值、创建时间和更新时间。
- `uuid`：文档的唯一标识符，主键。
- `name`：文档的文件名。
- `path`：文档的路径，相对于根目录。
- `hash`：文档的哈希值，用于检测文档是否变化。
- `created_at`：文档的创建时间，默认值为当前时间。
- `updated_at`：文档的更新时间，默认值为当前时间。
### 分块表
```sql
-- Chunk表
CREATE TABLE IF NOT EXISTS chunks (
    pkid TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    hash TEXT NOT NULL,
    position INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(document_id) REFERENCES documents(uuid) ON DELETE CASCADE,
    UNIQUE(document_id, hash)
);

-- 索引
CREATE INDEX idx_document_id ON chunks (document_id);
CREATE INDEX idx_chunks_position ON chunks (document_id, position);
```
存储分块的元数据，包括 pkid、文档 id、哈希值、位置、创建时间。
- `pkid`：分块的唯一标识符，主键。
- `document_id`：分块所属的文档的 uuid。
- `hash`：分块的哈希值，用于检测分块是否变化。
- `position`：分块在文档中的位置，从 0 开始。
- `created_at`：分块的创建时间，默认值为当前时间。
## milvus
使用 milvus 存储分块的向量表示，用于相似度搜索。
向量数据
```python
Document(
  page_content=doc.page_content,
  metadata={
    "file_name": file_name,
    "dir_path": dir_path,  # 分块所属的相对目录路径
    "mk_struct": json.dumps(doc.metadata, ensure_ascii=False),
    },
)
```

# 功能
## 文档管理
通过一个add 命令添加文档到知识库。
- `add path`：添加指定路径的文档到知识库。
- `add dir`：添加指定目录下的所有文档到知识库。
add 操作逻辑
- 检查路径是否存在。
- 如果是文件，检查是否已存在相同文件名的文档。
- 如果是目录，递归遍历所有文件，检查是否已存在相同文件名的文档。
- 插入文档
  - 计算文档的哈希值
    - 文档存在
      - 哈希值相同，跳过
      - 哈希值不同，更新文档和分块
    - 文档不存在，查询数据库是否有相同哈希值的文档
      - 有相同哈希值的文档，更新文档和分块的路径（重命名或移动）
      - 没有相同哈希值的文档，插入文档和分块
- 删除未出现的文档
  - 遍历数据库中的所有文档
  - 检查文档是否在知识库中出现
    - 没有出现，删除文档和分块
    - 出现，跳过

