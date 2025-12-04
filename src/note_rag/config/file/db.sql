-- 文档表
CREATE TABLE IF NOT EXISTS documents (
    uuid TEXT PRIMARY KEY,       -- UUID
    name TEXT NOT NULL,        -- 文档名
    path TEXT NOT NULL,         -- 文档存储路径
    hash TEXT NOT NULL      -- hash(文档内容)
);

-- Chunk表
CREATE TABLE IF NOT EXISTS chunks (
    pkid TEXT PRIMARY KEY,
    document_id TEXT NOT NULL, -- 关联的文档ID
    hash TEXT NOT NULL     -- hash(Chunk)
);

-- 索引
CREATE INDEX idx_document_id ON chunks (document_id);