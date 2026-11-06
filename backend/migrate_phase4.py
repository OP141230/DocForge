"""Database migration script for Phase 4 - Knowledge Base & Source Ingestion."""
import asyncio
import aiosqlite
import os


async def migrate_phase4():
    """Migrate database to Phase 4 schema."""
    # Support running from project root or backend directory
    if os.path.exists("./docforge.db"):
        db_path = "./docforge.db"
    elif os.path.exists("./backend/docforge.db"):
        db_path = "./backend/docforge.db"
    else:
        db_path = "./docforge.db"
    
    if not os.path.exists(db_path):
        print("No existing database found. Run the application first to create initial schema.")
        return
    
    print("Migrating database to Phase 4 schema...")
    
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.cursor()
        
        # Check if knowledge_files table exists
        await cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_files'"
        )
        table_exists = await cursor.fetchone()
        
        if table_exists:
            print("✓ Phase 4 tables already exist")
        else:
            print("Creating Phase 4 tables...")
            
            # Create knowledge_files table
            await cursor.execute("""
                CREATE TABLE knowledge_files (
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
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
                )
            """)
            print("  ✓ Created knowledge_files table")
            
            # Create indexes for knowledge_files
            await cursor.execute("""
                CREATE INDEX idx_knowledge_files_user_id ON knowledge_files(user_id)
            """)
            await cursor.execute("""
                CREATE INDEX idx_knowledge_files_conversation_id ON knowledge_files(conversation_id)
            """)
            await cursor.execute("""
                CREATE INDEX idx_knowledge_files_content_hash ON knowledge_files(content_hash)
            """)
            print("  ✓ Created knowledge_files indexes")
            
            # Create extracted_content table
            await cursor.execute("""
                CREATE TABLE extracted_content (
                    id TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    page_count INTEGER,
                    word_count INTEGER NOT NULL,
                    extraction_metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (file_id) REFERENCES knowledge_files(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            print("  ✓ Created extracted_content table")
            
            # Create indexes for extracted_content
            await cursor.execute("""
                CREATE INDEX idx_extracted_content_file_id ON extracted_content(file_id)
            """)
            await cursor.execute("""
                CREATE INDEX idx_extracted_content_user_id ON extracted_content(user_id)
            """)
            print("  ✓ Created extracted_content indexes")
            
            # Create content_chunks table
            await cursor.execute("""
                CREATE TABLE content_chunks (
                    id TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    chunk_text TEXT NOT NULL,
                    chunk_size INTEGER NOT NULL,
                    page_number INTEGER,
                    section_title TEXT,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (file_id) REFERENCES knowledge_files(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            print("  ✓ Created content_chunks table")
            
            # Create indexes for content_chunks
            await cursor.execute("""
                CREATE INDEX idx_content_chunks_file_id ON content_chunks(file_id)
            """)
            await cursor.execute("""
                CREATE INDEX idx_content_chunks_user_id ON content_chunks(user_id)
            """)
            print("  ✓ Created content_chunks indexes")
            
            # Create FTS5 virtual table for full-text search on chunks
            await cursor.execute("""
                CREATE VIRTUAL TABLE content_chunks_fts USING fts5(
                    chunk_id UNINDEXED,
                    chunk_text,
                    section_title,
                    content=content_chunks,
                    content_rowid=rowid
                )
            """)
            print("  ✓ Created content_chunks_fts (FTS5 search table)")
            
            # Create triggers to keep FTS table in sync
            await cursor.execute("""
                CREATE TRIGGER content_chunks_fts_insert AFTER INSERT ON content_chunks BEGIN
                    INSERT INTO content_chunks_fts(rowid, chunk_id, chunk_text, section_title)
                    VALUES (new.rowid, new.id, new.chunk_text, new.section_title);
                END
            """)
            await cursor.execute("""
                CREATE TRIGGER content_chunks_fts_delete AFTER DELETE ON content_chunks BEGIN
                    DELETE FROM content_chunks_fts WHERE rowid = old.rowid;
                END
            """)
            await cursor.execute("""
                CREATE TRIGGER content_chunks_fts_update AFTER UPDATE ON content_chunks BEGIN
                    DELETE FROM content_chunks_fts WHERE rowid = old.rowid;
                    INSERT INTO content_chunks_fts(rowid, chunk_id, chunk_text, section_title)
                    VALUES (new.rowid, new.id, new.chunk_text, new.section_title);
                END
            """)
            print("  ✓ Created FTS5 sync triggers")
            
            # Create brief_file_attachments table
            await cursor.execute("""
                CREATE TABLE brief_file_attachments (
                    id TEXT PRIMARY KEY,
                    brief_id TEXT NOT NULL,
                    file_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    attached_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (brief_id) REFERENCES document_briefs(id) ON DELETE CASCADE,
                    FOREIGN KEY (file_id) REFERENCES knowledge_files(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE(brief_id, file_id)
                )
            """)
            print("  ✓ Created brief_file_attachments table")
            
            # Create indexes for brief_file_attachments
            await cursor.execute("""
                CREATE INDEX idx_brief_attachments_brief_id ON brief_file_attachments(brief_id)
            """)
            await cursor.execute("""
                CREATE INDEX idx_brief_attachments_file_id ON brief_file_attachments(file_id)
            """)
            await cursor.execute("""
                CREATE INDEX idx_brief_attachments_user_id ON brief_file_attachments(user_id)
            """)
            print("  ✓ Created brief_file_attachments indexes")
            
            await db.commit()
            print("\n✅ Phase 4 database migration complete!")
            print("\nNew tables:")
            print("- knowledge_files: Uploaded file metadata and status")
            print("- extracted_content: Raw extracted text from files")
            print("- content_chunks: Searchable text chunks with metadata")
            print("- content_chunks_fts: Full-text search index (FTS5)")
            print("- brief_file_attachments: Links files to document briefs")
            print("\nNew features:")
            print("- File upload and storage")
            print("- Text extraction from PDF, DOCX, TXT, MD, HTML, CSV")
            print("- Chunking and indexing for search")
            print("- Full-text search with FTS5")
            print("- Attach source files to document briefs")
            print("- Generate documents using uploaded sources")


if __name__ == "__main__":
    asyncio.run(migrate_phase4())
