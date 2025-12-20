# IngestService 功能增强计划

## 1. 目标
在 `IngestService` 中实现 `add_document`, `delete_document`, `update_document` 方法，并将判断是添加还是更新的逻辑放在更高一层（即调用者或统一的入口方法，如 `add_or_update_document`）。

## 2. 修改 `IngestService` (src/x1ayu_rag_v2/service/ingest_service.py)

### 2.1 `add_document(self, file_path: str) -> str`
- **功能**: 纯粹的添加逻辑。
- **逻辑**:
    1. 检查文件是否存在。
    2. 解析文件为 `Document` 对象。
    3. 调用 `self.doc_repo.add(doc)` 进行持久化。
    4. 返回 `doc.uuid`。
- **注意**: 不再在此方法内做“是否存在”的复杂判断，假设调用此方法时已经确定是新文档。但为了健壮性，如果 Repo 抛出主键冲突，需要捕获并处理（或者让上层处理）。根据用户需求“判断逻辑放在更高一层”，这里应保持原子性和单一职责。

### 2.2 `delete_document(self, uuid: str) -> None`
- **功能**: 删除指定 UUID 的文档。
- **逻辑**:
    1. 调用 `self.doc_repo.delete_by_uuid(uuid)`。
    2. 如果需要，可以先检查是否存在（可选，Repo 层通常处理了）。

### 2.3 `update_document(self, uuid: str, file_path: str) -> str`
- **功能**: 更新指定 UUID 的文档内容。
- **逻辑**:
    1. 检查文件是否存在。
    2. 解析文件为 `Document` 对象。
    3. **关键**: 保持 UUID 不变（或者使用新 UUID 但替换旧记录，通常保持 UUID 不变对引用更友好，但 `Document` 对象是不可变的，通常创建新对象）。
    4. 如果 `Document` 构造函数生成新 UUID，需要手动设置为旧 UUID，或者 `update` 逻辑是“删旧加新”。
    5. 考虑到向量数据库的更新通常是“删除旧 chunks -> 插入新 chunks”，且 SQLite 中也需要更新 hash 等字段。
    6. 实现方式：
        - `doc = Document.from_file(file_path)` (会生成新 UUID)
        - `doc.uuid = uuid` (强制使用旧 UUID)
        - `self.doc_repo.delete_by_uuid(uuid)` (先删)
        - `self.doc_repo.add(doc)` (后加)
        - 或者在 Repo 层实现 `update` 方法（更优，但目前 Repo 只有 add/delete）。
        - **方案**: 采用“先删后加”的逻辑在 Service 层实现，或者如果 Repo 支持事务，可以封装在一个事务中。鉴于 Repo 已有原子性 `delete` 和 `add`，Service 层组合调用可能非原子。
        - **改进方案**: 在 `DocumentRepository` 增加 `update` 方法，或者在 Service 层使用 `delete` + `add` 但需注意事务。
        - **用户需求**: “判断是添加更新的放在更高一层”。
        - 这里简单实现：先调用 Repo 删除旧的，再调用 Repo 添加新的（复用 UUID）。

### 2.4 `ingest_document(self, file_path: str) -> str` (更高一层的逻辑)
- **功能**: 智能判断是添加还是更新。
- **逻辑**:
    1. 解析路径，获取 `file_name` 和 `dir_path`。
    2. 查询 DB: `existing = self.doc_repo.get_by_path_and_name(dir_path, file_name)`。
    3. 如果 `existing` 存在:
        - 计算新文件 hash。
        - 如果 `existing.hash == new_hash`: 返回 `existing.uuid` (无变化)。
        - 否则: 调用 `self.update_document(existing.uuid, file_path)`。
    4. 如果 `existing` 不存在:
        - 调用 `self.add_document(file_path)`。

## 3. 修改 `DocumentRepository` (src/x1ayu_rag_v2/repository/document_repository.py)
- 目前 `delete_by_uuid` 和 `add` 已经存在。
- 确认 `get_by_path_and_name` 是否可用（已存在）。

## 4. 步骤
1.  修改 `IngestService`，添加 `delete_document` 和 `update_document`。
2.  重构 `add_document`，移除内部的“检查是否存在”逻辑（或者保留作为防御性编程，但主要逻辑外移）。
3.  添加 `ingest_document` (或类似命名) 作为高层入口。

## 5. 验证
- 编写简单的测试脚本或使用 CLI (如果已集成) 验证添加、更新（内容变化）、删除功能。
