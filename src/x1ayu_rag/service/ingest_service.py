from __future__ import annotations
import os
from typing import Optional, Tuple, Protocol, List
from x1ayu_rag.repository.document_repository import DocumentRepository
from x1ayu_rag.repository.chunk_repository import ChunkRepository
from typing import Iterable
from x1ayu_rag.utils.hash import text_hash
from x1ayu_rag.model.document import Document
from x1ayu_rag.model.chunk import Chunk
from x1ayu_rag.splitter.markdown import MarkdownSplitter

class Splitter(Protocol):
    """文档切分器协议。"""
    def split_text(self, text: str) -> List[Chunk]:
        ...

class IngestService:
    """文档摄取服务
    
    负责将文件新增或更新至系统，比较哈希判断是否需要重建分块与索引。
    """
    def __init__(self, repo: Optional[DocumentRepository] = None, splitter: Optional[Splitter] = None):
        """初始化服务
        
        参数:
            repo: 文档仓储（可选），默认为系统内置实现
            splitter: 文档切分器（可选），默认为 MarkdownSplitter
        """
        self.repo = repo or DocumentRepository(ChunkRepository())
        self.splitter = splitter or MarkdownSplitter()

    def list_documents(self) -> list[dict]:
        """获取所有文档的详细列表。
        
        返回:
            list[dict]: 包含文档详细信息的字典列表。
        """
        return self.repo.list_all_with_details()

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
            new_doc = Document.from_content(file_name, dir_path, content, splitter=self.splitter)
            self.repo.store(new_doc)
            return ("added", new_doc.uuid)
        # 存在, 哈希未变化, 不操作
        if existing.hash == new_hash:
            return ("noop", existing.uuid)
        # 存在, 哈希变化, 更新
        replaced_doc = Document.from_content(file_name, dir_path, content, uuid=existing.uuid, splitter=self.splitter)
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

    def sync_directory(self, root_path: str) -> Tuple[list[Tuple[str, str, str]], list[Tuple[str, Exception]], list[Tuple[str, str]]]:
        """同步目录
        
        扫描指定目录下的所有 Markdown 文件，执行新增/更新操作，并清理数据库中存在但文件系统中已删除的记录。
        
        参数:
            root_path: 根目录路径（绝对路径或相对路径）
            
        返回:
            (successes, failures, deleted_docs):
            - successes: [(file_path, action, uuid), ...]
            - failures: [(file_path, error), ...]
            - deleted_docs: [(relative_path, uuid), ...]
        """
        root_path_abs = os.path.abspath(root_path)
        path_obj = os.path.abspath(root_path)
        
        # 1. 扫描文件并批量处理
        md_files = []
        for root, _, files in os.walk(root_path_abs):
            for file in files:
                if file.endswith(".md"):
                    md_files.append(os.path.join(root, file))
                    
        successes, failures = self.add_or_update_many(md_files)
        
        # 2. 清理遗留数据
        deleted_docs = []
        rel_root = os.path.relpath(root_path_abs, os.getcwd())
        
        # 如果是在当前目录下，获取所有文档；否则按前缀获取
        docs = self.repo.list_all() if rel_root in (".", "") else self.repo.list_by_path_prefix(rel_root)
        
        for doc in docs:
            # 构建预期文件系统路径
            if rel_root in (".", ""):
                fs_path = os.path.join(root_path_abs, doc.path, doc.name)
            else:
                # 检查文档路径是否属于该根目录
                if not (doc.path == rel_root or doc.path.startswith(f"{rel_root}/")):
                    continue
                # 计算相对后缀
                rel_suffix = os.path.relpath(doc.path, rel_root)
                fs_path = os.path.join(root_path_abs, "" if rel_suffix == "." else rel_suffix, doc.name)
            
            if not os.path.exists(fs_path):
                self.repo.delete_by_uuid(doc.uuid)
                rel_path = os.path.relpath(fs_path, root_path_abs)
                deleted_docs.append((rel_path, doc.uuid))
                
        return successes, failures, deleted_docs

    def _resolve_paths(self, file_path: str) -> Tuple[str, str, str]:
        """解析文件路径，返回绝对路径、文件名和相对目录路径。"""
        abs_path = os.path.abspath(file_path)
        file_name = os.path.basename(abs_path)
        dir_path_abs = os.path.dirname(abs_path)
        try:
            dir_path = os.path.relpath(dir_path_abs, os.getcwd())
        except Exception:
            dir_path = dir_path_abs
        return abs_path, file_name, dir_path

    def _read_content_hash(self, abs_path: str) -> Tuple[str, str]:
        """读取文件内容并计算哈希值。"""
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content, text_hash(content)
