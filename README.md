# note_rag
基于langChain+Ollama+Milvus+sqlite实现的本地个人笔记rag系统
## Markdown
### 风格
### 解析
#### langchain_text_splitters.MarkdownHeaderTextSplitter
简单解析，仅能按标题分块，支持自定义标题，能将标题结构存储到metaData中
### 检索回答
回答结果为
```
引用：文件，标题，内容
回答：xx
```
通过langChain调用工具检索数据库实现
## 功能
- (uuid + hash(doc) + doc_name) + 相似度检查
  - 判断文章是否变动
- doc_id + hash(chunk) + link(doc_id,hash_chunk)
  - 判断chunk是否变动
- 用sqlite存储两张表
  - 文章表
  - 块表



## 运行
### 前置条件
ollama embeddinggemma:latest模型用于embedding
### 打包运行
- 在项目根目录下执行`uv build`进行打包
- 执行`uv pip install dist/note_rag-0.1.0-py3-none-any.whl`安装打包出来的whl文件
- 执行`rag -h`查看使用教程

## todo
1. 支持更新（不用全量更新）
2. 支持目录导入（对已有的进行更新，不需要更新就跳过）
3. 支持配置文件（不同模型）
4. 增加ai回复（chain[query->rag->llm]即可，后续版本有需要再改为agent+tools）
5. 补全readme