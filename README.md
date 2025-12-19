# note_rag
基于langChain+Ollama+Milvus+sqlite实现的本地个人笔记rag系统

## 架构设计

### 核心分层
系统采用经典的分层架构设计，确保关注点分离与可维护性：

1.  **CLI Layer (`cli/`)**
    - 使用 `Click` 构建命令行界面。
    - 负责用户交互、参数解析、环境检查与错误处理。
    - 通过 `Service` 层调用业务逻辑，不直接操作数据库。
    - 使用 `Rich` 库提供现代化的终端输出体验（表格、进度条、高亮）。

2.  **Service Layer (`service/`)**
    - 封装核心业务逻辑。
    - `IngestService`: 处理文档摄取、去重、更新检测与分块策略。
    - `SearchService`: 封装向量检索逻辑，提供统一的搜索接口。
    - 采用依赖注入（DI）模式，便于测试与组件替换。

3.  **Repository Layer (`repository/`)**
    - 负责数据持久化。
    - `DocumentRepository`: 管理 SQLite 中的文档元数据，提供事务支持。
    - `ChunkRepository`: 协调 SQLite（分块元数据）与 Milvus（向量数据）的双写一致性。

4.  **Model Layer (`model/`)**
    - 定义核心领域对象：`Document` 与 `Chunk`。
    - 包含业务规则，如哈希计算、对象构建工厂等。

### 关键实现逻辑

#### 1. 文档摄取与增量更新 (`IngestService.add_or_update`)
为避免重复处理，系统实现了智能增量更新机制：
1.  计算目标文件的内容哈希（Hash）。
2.  查询 SQLite 数据库：
    - **情况 A：不存在** -> 新增文档记录，切分并存入向量库。
    - **情况 B：存在且哈希一致** -> 跳过（No-op）。
    - **情况 C：存在但哈希变更** -> 标记为更新。
        - 开启数据库事务。
        - 删除旧分块（从向量库和 SQLite）。
        - 重新切分文档并存储新分块。
        - 更新文档哈希与时间戳。
        - 提交事务（失败则回滚）。
    - **情况 D：不存在但哈希匹配另一 ID** -> 判定为文件移动/重命名，仅更新路径信息。

#### 2. 事务与数据一致性 (`DocumentRepository.store`)
文档存储操作涉及 SQLite 和 Milvus 两个异构数据源，系统通过手动事务管理保证最终一致性：
```python
try:
    conn.commit() # 开启 SQLite 事务
    # 1. 写入文档元数据到 SQLite
    cursor.execute("INSERT INTO documents ...")
    
    # 2. 写入分块数据（可能涉及 Embedding API 调用与 Milvus 写入）
    chunk_repo.store(chunks)
    
    conn.commit() # 提交
except Exception:
    conn.rollback() # 任何步骤失败（包括网络错误），回滚 SQLite，防止脏数据
```

#### 3. 依赖注入设计
服务层通过构造函数接收依赖，不再硬编码具体实现：
```python
# SearchService 示例
class SearchService:
    def __init__(self, vector_store: VectorStore = None):
        # 允许注入 Mock 对象或不同的向量库实现
        self.vector_store = vector_store or get_vector_store()
```

## 功能特性
- **智能去重**: 基于内容哈希的增量更新，避免重复 Embedding 消耗。
- **原子性操作**: 确保文档元数据与向量索引的一致性。
- **交互式配置**: `rag init` 和 `rag config` 提供友好的引导式配置。
- **美观输出**: 命令行支持 Markdown 渲染、表格展示与加载动画。

## 运行
### 前置条件
- Python 3.8+
- UV 包管理器
- Ollama (提供 LLM 和 Embedding 服务)

### 快速开始
1.  **安装**:
    ```bash
    uv pip install dist/note_rag-0.1.0-py3-none-any.whl
    # 或直接源码运行
    uv sync
    ```

2.  **初始化**:
    ```bash
    rag init
    # 跟随引导配置 Ollama/OpenAI 地址与模型
    ```

3.  **使用**:
    ```bash
    # 添加文档
    rag add ./notes/

    # 检索
    rag select "关于架构设计的笔记"

    # 问答
    rag chain "如何实现增量更新？"
    
    # 查看文档列表
    rag show
    ```

## 命令行使用指南

### 1. 初始化 (init)
初始化 RAG 环境并配置模型参数（Chat 和 Embedding）。首次运行必须先执行此命令。

```bash
# 交互式初始化（推荐）
rag init

# 命令行参数初始化
rag init --chat-provider ollama --chat-model qwen2.5-coder:14b --emb-provider ollama --emb-model nomic-embed-text
```

### 2. 配置管理 (config)
查看或更新系统配置。支持交互式菜单和命令行参数两种模式。

```bash
# 进入交互式配置菜单（支持 Chat、Embedding、System Prompt 配置）
rag config

# 显示当前所有配置
rag config show

# 命令行快速更新 Chat 模型
rag config update --chat-model llama3:latest

# 命令行快速更新 System Prompt
rag config update --sys-prompt "你是一个资深 Python 专家"
```

### 3. 文档管理 (add/show)
管理知识库中的文档。支持添加单个文件或递归扫描目录。

```bash
# 添加单个文件
rag add ./notes/python.md

# 递归添加目录（自动扫描所有 .md 文件）
rag add ./knowledge_base/

# 查看已索引的文档列表
rag show
```

### 4. 检索查询 (select)
基于语义相似度检索最相关的文档片段。

```bash
# 检索与 "架构模式" 相关的 Top 2 片段
rag select "架构模式"

# 指定返回 Top 5 结果
rag select "设计原则" -k 5
```

### 5. RAG 问答链 (chain)
启动完整的 RAG 流程：检索相关文档 -> 构建提示词 -> 调用 LLM 生成回答。

```bash
# 默认问答
rag chain "如何实现增量更新？"

# 调试模式（显示构建的 Prompt 和中间过程）
rag chain "依赖注入的优势" --mode debug

# 指定参考片段数量
rag chain "事务一致性" -k 3
```

## 开发
- 使用 `uv run` 执行命令。
- 运行测试：`uv run pytest`。
