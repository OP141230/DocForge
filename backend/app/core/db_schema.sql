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
    attachments TEXT NOT NULL DEFAULT '[]',  -- JSON array of MessageAttachment objects
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
    FOREIGN KEY (brief_id) REFERENCES document_briefs(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES knowledge_files(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(brief_id, file_id)
);

CREATE INDEX IF NOT EXISTS idx_brief_attachments_brief_id ON brief_file_attachments(brief_id);
CREATE INDEX IF NOT EXISTS idx_brief_attachments_file_id ON brief_file_attachments(file_id);

-- Phase 3: DocumentBrief planning system
-- (also created by migrate_phase3.py; kept here so a brand-new database works
-- without having to remember a migration step)
CREATE TABLE IF NOT EXISTS document_briefs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    conversation_id TEXT,
    document_type TEXT NOT NULL,
    title TEXT NOT NULL,
    topic TEXT NOT NULL,
    purpose TEXT,
    audience TEXT,
    language TEXT DEFAULT 'en',
    desired_length TEXT,
    tone TEXT,
    writing_style TEXT,
    document_specific_data TEXT NOT NULL DEFAULT '{}',
    required_sections TEXT NOT NULL DEFAULT '[]',
    important_points TEXT NOT NULL DEFAULT '[]',
    topics_to_avoid TEXT NOT NULL DEFAULT '[]',
    additional_instructions TEXT,
    citation_style TEXT,
    outline TEXT,
    outline_approved INTEGER DEFAULT 0,
    outline_approved_at TEXT,
    document_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_document_briefs_user_id ON document_briefs(user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_document_briefs_conversation ON document_briefs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_document_briefs_document ON document_briefs(document_id);

-- ===========================================================================
-- Phase 5: Research, Citations & Factual Verification
-- ===========================================================================
-- notes:
--  * every table carries user_id so access control is enforced in SQL, not only
--    in Python;
--  * timestamps are ISO-8601 TEXT to match Phases 1-4;
--  * child rows are deleted explicitly by the repositories because SQLite only
--    enforces ON DELETE CASCADE when PRAGMA foreign_keys is enabled, and
--    enabling it globally would change Phase 1-4 delete semantics.

CREATE TABLE IF NOT EXISTS research_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    brief_id TEXT,
    document_id TEXT,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    external_research INTEGER NOT NULL DEFAULT 0,
    include_knowledge_base INTEGER NOT NULL DEFAULT 1,
    citation_style TEXT NOT NULL DEFAULT 'apa',
    requested_urls TEXT NOT NULL DEFAULT '[]',
    knowledge_file_ids TEXT NOT NULL DEFAULT '[]',
    provider TEXT,
    provider_message TEXT,
    error TEXT,
    progress_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (brief_id) REFERENCES document_briefs(id) ON DELETE SET NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_research_sessions_user ON research_sessions(user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_research_sessions_brief ON research_sessions(brief_id);
CREATE INDEX IF NOT EXISTS idx_research_sessions_document ON research_sessions(document_id);

CREATE TABLE IF NOT EXISTS research_questions (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    question TEXT NOT NULL,
    rationale TEXT,
    order_index INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES research_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_research_questions_session ON research_questions(session_id, order_index);

CREATE TABLE IF NOT EXISTS research_sources (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    research_question_id TEXT,
    source_type TEXT NOT NULL DEFAULT 'web',
    retrieval_status TEXT NOT NULL DEFAULT 'discovered',
    title TEXT NOT NULL,
    url TEXT,
    canonical_url TEXT,
    publisher TEXT,
    author TEXT,
    published_date TEXT,
    accessed_at TEXT,
    content_text TEXT,
    excerpt TEXT,
    word_count INTEGER NOT NULL DEFAULT 0,
    http_status INTEGER,
    error TEXT,
    source_type_label TEXT NOT NULL DEFAULT 'unknown',
    evaluation_notes TEXT NOT NULL DEFAULT '[]',
    relevance_score REAL,
    knowledge_file_id TEXT,
    chunk_id TEXT,
    page_number INTEGER,
    section_title TEXT,
    selected INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    UNIQUE(session_id, canonical_url),
    FOREIGN KEY (session_id) REFERENCES research_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (knowledge_file_id) REFERENCES knowledge_files(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_research_sources_session ON research_sources(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_research_sources_user ON research_sources(user_id);
CREATE INDEX IF NOT EXISTS idx_research_sources_file ON research_sources(knowledge_file_id);

CREATE TABLE IF NOT EXISTS research_evidence (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    research_question_id TEXT,
    claim_or_finding TEXT NOT NULL,
    passage TEXT NOT NULL,
    passage_hash TEXT NOT NULL,
    evidence_type TEXT NOT NULL DEFAULT 'context',
    url TEXT,
    knowledge_file_id TEXT,
    page_number INTEGER,
    section_title TEXT,
    retrieved_at TEXT NOT NULL,
    user_selected INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    UNIQUE(session_id, source_id, passage_hash),
    FOREIGN KEY (session_id) REFERENCES research_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES research_sources(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_research_evidence_session ON research_evidence(session_id, retrieved_at);
CREATE INDEX IF NOT EXISTS idx_research_evidence_source ON research_evidence(source_id);

CREATE TABLE IF NOT EXISTS citations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    research_session_id TEXT,
    evidence_id TEXT,
    section_id TEXT,
    section_title TEXT,
    marker TEXT,
    locator TEXT,
    style TEXT NOT NULL DEFAULT 'apa',
    in_text TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES research_sources(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_citations_document ON citations(document_id, created_at);
CREATE INDEX IF NOT EXISTS idx_citations_source ON citations(source_id);

CREATE TABLE IF NOT EXISTS claim_verifications (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    research_session_id TEXT,
    claim_id TEXT NOT NULL,
    claim_text TEXT NOT NULL,
    section_id TEXT,
    section_title TEXT,
    status TEXT NOT NULL DEFAULT 'not_checked',
    explanation TEXT,
    verification_method TEXT NOT NULL DEFAULT 'deterministic',
    time_sensitive INTEGER NOT NULL DEFAULT 0,
    manual_review INTEGER NOT NULL DEFAULT 0,
    checked_at TEXT,
    UNIQUE(document_id, claim_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_claim_verifications_document ON claim_verifications(document_id, status);

CREATE TABLE IF NOT EXISTS claim_verification_evidence (
    verification_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    relation TEXT NOT NULL DEFAULT 'supporting',
    PRIMARY KEY (verification_id, evidence_id, relation),
    FOREIGN KEY (verification_id) REFERENCES claim_verifications(id) ON DELETE CASCADE,
    FOREIGN KEY (evidence_id) REFERENCES research_evidence(id) ON DELETE CASCADE
);

-- ===========================================================================
-- Phase 6: AI Reviewer & Advanced Editing
-- ===========================================================================
-- conventions carried over from Phase 5:
--   * every table carries user_id so ownership is enforced in SQL as well as
--     in Python;
--   * child rows carry explicit foreign keys; repositories delete children
--     explicitly because PRAGMA foreign_keys is not globally enabled;
--   * ISO-8601 TEXT timestamps everywhere.

CREATE TABLE IF NOT EXISTS review_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    brief_id TEXT,
    mode TEXT NOT NULL DEFAULT 'quick',
    categories TEXT NOT NULL DEFAULT '[]',
    scope TEXT NOT NULL DEFAULT 'document',
    section_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    document_fingerprint TEXT,
    provider TEXT,
    provider_message TEXT,
    error TEXT,
    progress_message TEXT,
    findings_total INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (brief_id) REFERENCES document_briefs(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_review_sessions_user ON review_sessions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_review_sessions_document ON review_sessions(document_id, created_at DESC);

CREATE TABLE IF NOT EXISTS review_findings (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    review_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'ai',
    title TEXT NOT NULL,
    explanation TEXT NOT NULL DEFAULT '',
    section_id TEXT,
    section_title TEXT,
    block_id TEXT,
    original_text TEXT,
    start_offset INTEGER,
    end_offset INTEGER,
    suggested_text TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    evidence_ids TEXT NOT NULL DEFAULT '[]',
    citation_ids TEXT NOT NULL DEFAULT '[]',
    document_fingerprint TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (review_id) REFERENCES review_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_review_findings_review ON review_findings(review_id, severity);
CREATE INDEX IF NOT EXISTS idx_review_findings_document ON review_findings(document_id, status);

CREATE TABLE IF NOT EXISTS edit_proposals (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    review_id TEXT,
    finding_id TEXT,
    operation TEXT NOT NULL,
    target_type TEXT NOT NULL DEFAULT 'section',
    section_id TEXT,
    block_id TEXT,
    original_text TEXT NOT NULL,
    proposed_text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'proposed',
    base_fingerprint TEXT,
    provider TEXT,
    notes TEXT,
    impact TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (review_id) REFERENCES review_sessions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_edit_proposals_document ON edit_proposals(document_id, status);

-- Provenance for document_versions. Kept as a side table (rather than adding
-- columns) so an existing database needs no ALTER TABLE migration.
CREATE TABLE IF NOT EXISTS document_version_notes (
    document_id TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    origin TEXT NOT NULL DEFAULT 'manual',
    operation TEXT,
    summary TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY (document_id, version_number),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS compliance_checks (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    brief_id TEXT,
    overall TEXT NOT NULL,
    results TEXT NOT NULL DEFAULT '[]',
    document_fingerprint TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_compliance_checks_document ON compliance_checks(document_id, created_at DESC);
