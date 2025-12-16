from __future__ import annotations
import os
from typing import Optional, Tuple
from x1ayu_rag.repository.document_repository import DocumentRepository
from x1ayu_rag.repository.chunk_repository import ChunkRepository
from typing import Iterable
from x1ayu_rag.utils.hash import text_hash
from x1ayu_rag.model.document import Document
from x1ayu_rag.splitter.markdown import MarkdownSplitter


class IngestService:
    """文档摄取服务

    负责将文件新增或更新至系统，比较哈希判断是否需要重建分块与索引。
    """
    def __init__(self, repo: Optional[DocumentRepository] = None):
        """初始化服务

        参数:
            repo: 文档仓储（可选），默认为系统内置实现
        """
        self.repo = repo or DocumentRepository(ChunkRepository())
        self.splitter = MarkdownSplitter()

    def add_or_update(self, file_path: str) -> Tuple[str, str]:
        """新增或更新文档

        行为：
        - 不存在则新增并返回 ('added', uuid)
        - 内容未变化则不操作并返回 ('noop', uuid)
        - 内容变化则删除旧分块并重建，返回 ('updated', 新uuid)

        参数:
            file_path: 待处理的文件路径
        返回:
            (action, uuid): 操作结果与对应文档标识
        """
        abs_path = os.path.abspath(file_path)
        file_name = os.path.basename(abs_path)
        dir_path = os.path.dirname(abs_path)
        existing = self.repo.get(dir_path, file_name)
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
        new_hash = text_hash(content)
        # 重命名/移动检测：根据哈希匹配已有文档，直接更新 path/name，保留 uuid 与分块
        if existing is None:
            same = self.repo.get_by_hash(new_hash)
            if same is not None:
                self.repo.update_path_name(same.uuid, dir_path, file_name)
                return ("moved", same.uuid)
        new_doc = Document.from_content(file_name, dir_path, content)
        if existing is None:
            self.repo.store(new_doc)
            return ("added", new_doc.uuid)
        else:
            if existing.hash == new_hash:
                return ("noop", existing.uuid)
            # 保留稳定 uuid，替换哈希与分块
            replaced_doc = Document.from_content(file_name, dir_path, content, uuid=existing.uuid)
            self.repo.update_hash(existing.uuid, new_hash)
            self.repo.replace_chunks(existing.uuid, replaced_doc.chunks or [])
            return ("updated", existing.uuid)

    def add_or_update_many(self, file_paths: Iterable[str]) -> Tuple[list[Tuple[str, str, str]], list[Tuple[str, Exception]]]:
        """批量新增或更新，多文件一次处理，返回成功与失败列表
        
        成功项为 (file_path, action, uuid)，失败项为 (file_path, exception)。
        """
        successes: list[Tuple[str, str, str]] = []
        failures: list[Tuple[str, Exception]] = []
        for fp in file_paths:
            try:
                action, uuid = self.add_or_update(fp)
                successes.append((fp, action, uuid))
            except Exception as e:
                failures.append((fp, e))
        return successes, failures
