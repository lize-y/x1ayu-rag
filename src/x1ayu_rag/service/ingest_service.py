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
        abs_path, file_name, dir_path = self._resolve_paths(file_path)
        content, new_hash = self._read_content_hash(abs_path)
        existing = self.repo.get(dir_path, file_name)
        # 不存在
        if existing is None:
            # 检查是否有相同哈希的文档
            same = self.repo.get_by_hash(new_hash)
            if same is not None:
                # 存在相同哈希文档，更新路径名
                self.repo.update_path_name(same.uuid, dir_path, file_name)
                return ("moved", same.uuid)
            # 不存在相同哈希文档，新增文档
            new_doc = Document.from_content(file_name, dir_path, content)
            self.repo.store(new_doc)
            return ("added", new_doc.uuid)
        # 存在, 哈希未变化, 不操作
        if existing.hash == new_hash:
            return ("noop", existing.uuid)
        # 存在, 哈希变化, 更新
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

    def _resolve_paths(self, file_path: str) -> Tuple[str, str, str]:
        abs_path = os.path.abspath(file_path)
        file_name = os.path.basename(abs_path)
        dir_path_abs = os.path.dirname(abs_path)
        try:
            dir_path = os.path.relpath(dir_path_abs, os.getcwd())
        except Exception:
            dir_path = dir_path_abs
        return abs_path, file_name, dir_path

    def _read_content_hash(self, abs_path: str) -> Tuple[str, str]:
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content, text_hash(content)
