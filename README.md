# note_rag
基于langChain+Ollama+Milvus+sqlite实现的本地个人笔记rag系统
## 使用
### 打包
```bash
uv build
```
### 安装
将打包好的 `x1ayu_rag-0.1.0-py3-none-any.whl` 安装到系统中
```bash
pipx install x1ayu_rag-0.1.0-py3-none-any.whl
```
![alt text](docs/assets/install.png)
### 初始化与配置
```bash
rag init
```
![alt text](docs/assets/init.gif)
### 添加文档
```bash
rag add . # 添加当前目录下的所有文档
rag add test.md # 添加 test.md 文件
```
### 查看文档列表
```bash
rag show
```
![alt text](docs/assets/show.gif)
### 查询文档
```bash
rag select "如何设计权限系统"
```
![alt text](docs/assets/select.gif)
### 问答
```bash
rag chain "如何设计权限系统"
```
![alt text](docs/assets/chain.gif)
## 对比
使用小模型更能对比出rag的效果
### 无rag
![alt text](docs/assets/no_rag.gif)
### 有rag
![alt text](docs/assets/rag.gif)

## 模型支持
- ollama
- openai

## 项目结构
```bash
└── x1ayu_rag
    ├── __init__.py
    ├── chain
    │   ├── __init__.py
    │   └── chain.py    # 问答链
    ├── cli
    │   └── cli.py    # 命令行接口
    ├── config
    │   ├── __init__.py
    │   ├── app_config.py    # 应用配置
    │   ├── constants.py    # 常量配置
    │   └── file
    │       ├── __init__.py
    │       └── db.sql    # 数据库文件
    ├── db
    │   ├── __init__.py
    │   ├── milvus.py    # milvus数据库操作
    │   └── sqlite.py    # sqlite数据库操作
    ├── exceptions.py    # 异常处理
    ├── global
    │   └── global.py    # 全局变量
    ├── llm
    │   └── provider.py    # 大模型提供器
    ├── main.py
    ├── model
    │   ├── __init__.py    # 数据模型
    │   ├── chunk.py    # 文档分块模型
    │   └── document.py    # 文档模型
    ├── repository
    │   ├── chunk_repository.py    # 文档分块仓库
    │   └── document_repository.py    # 文档仓库
    ├── service
    │   ├── ingest_service.py    # 文档处理服务
    │   └── search_service.py    # 文档查询服务
    ├── splitter
    │   ├── base.py    # 文档分块器基类
    │   └── markdown.py    # markdown文档分块器
    └── utils
        ├── __init__.py    # 工具模块
        ├── hash.py    # 哈希工具
        └── mdSplitter.py    # markdown文档分块工具
```