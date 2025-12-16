-- 文档表
CREATE TABLE IF NOT EXISTS documents (
    uuid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(name, path)
);

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
