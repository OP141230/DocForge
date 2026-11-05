-- DocForge Database Schema

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id, updated_at DESC);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_deleted INTEGER DEFAULT 0,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, sequence_number);

-- Documents table (updated with user_id and conversation_id)
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    conversation_id TEXT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,  -- JSON serialized DocumentIR.content
    metadata TEXT NOT NULL, -- JSON serialized DocumentIR.metadata
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    schema_version TEXT NOT NULL DEFAULT '1.0.0',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_updated_at ON documents(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS document_versions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL,  -- Full JSON serialized DocumentIR at this version
    created_at TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    UNIQUE(document_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_versions_document_id ON document_versions(document_id, version_number DESC);

-- Knowledge Base Tables (Sprint 1-3)

-- Knowledge files table (uploaded files)
CREATE TABLE IF NOT EXISTS knowledge_files (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    conversation_id TEXT,
    original_filename TEXT NOT NULL,
    stored_filename TEXT NOT NULL,
    file_extension TEXT NOT NULL,
    mime_type TEXT,
    file_size_bytes INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    upload_status TEXT NOT NULL DEFAULT 'uploaded',
    extraction_status TEXT NOT NULL DEFAULT 'pending',
    extraction_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_knowledge_files_user_id ON knowledge_files(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_files_conversation_id ON knowledge_files(conversation_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_files_content_hash ON knowledge_files(content_hash, user_id);

-- Extracted content table
CREATE TABLE IF NOT EXISTS extracted_content (
    id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    page_count INTEGER,
    word_count INTEGER NOT NULL,
    extraction_metadata TEXT,  -- JSON
    created_at TEXT NOT NULL,
    FOREIGN KEY (file_id) REFERENCES knowledge_files(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_extracted_content_file_id ON extracted_content(file_id);
CREATE INDEX IF NOT EXISTS idx_extracted_content_user_id ON extracted_content(user_id);

-- Content chunks table (for retrieval)
CREATE TABLE IF NOT EXISTS content_chunks (
    id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_size INTEGER NOT NULL,
    page_number INTEGER,
    section_title TEXT,
    metadata TEXT,  -- JSON
    created_at TEXT NOT NULL,
    FOREIGN KEY (file_id) REFERENCES knowledge_files(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_content_chunks_file_id ON content_chunks(file_id, chunk_index);
CREATE INDEX IF NOT EXISTS idx_content_chunks_user_id ON content_chunks(user_id);

-- FTS5 virtual table for full-text search with BM25 ranking
CREATE VIRTUAL TABLE IF NOT EXISTS content_chunks_fts USING fts5(
    chunk_text,
    content='content_chunks',
    content_rowid='rowid'
);

-- Triggers to keep FTS5 in sync with content_chunks

-- Insert trigger
CREATE TRIGGER IF NOT EXISTS content_chunks_ai AFTER INSERT ON content_chunks BEGIN
    INSERT INTO content_chunks_fts(rowid, chunk_text)
    VALUES (new.rowid, new.chunk_text);
END;

-- Update trigger
CREATE TRIGGER IF NOT EXISTS content_chunks_au AFTER UPDATE ON content_chunks BEGIN
    UPDATE content_chunks_fts
    SET chunk_text = new.chunk_text
    WHERE rowid = old.rowid;
END;

-- Delete trigger
CREATE TRIGGER IF NOT EXISTS content_chunks_ad AFTER DELETE ON content_chunks BEGIN
    DELETE FROM content_chunks_fts WHERE rowid = old.rowid;
END;

-- Brief file attachments table (links knowledge files to document briefs)
CREATE TABLE IF NOT EXISTS brief_file_attachments (
    id TEXT PRIMARY KEY,
    brief_id TEXT NOT NULL,
    file_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    attached_at TEXT NOT NULL,
    FOREIGN KEY (brief_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES knowledge_files(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(brief_id, file_id)
);

CREATE INDEX IF NOT EXISTS idx_brief_attachments_brief_id ON brief_file_attachments(brief_id);
CREATE INDEX IF NOT EXISTS idx_brief_attachments_file_id ON brief_file_attachments(file_id);
