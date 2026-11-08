"""
Migration: Add image attachments support to messages table.

This adds an 'attachments' column to store image data for conversation messages.
Images are stored as JSON array of attachment objects with base64-encoded data.
"""
import sqlite3
import sys
from pathlib import Path

def migrate():
    """Add attachments column to messages table."""
    db_path = Path(__file__).parent / "docforge.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        print("   Run the backend first to create the database.")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(messages)")
        columns = {row[1] for row in cursor.fetchall()}
        
        if 'attachments' in columns:
            print("✅ Migration already applied: 'attachments' column exists")
            return
        
        print("🔧 Adding 'attachments' column to messages table...")
        
        # Add the new column (SQLite allows adding columns with ALTER TABLE)
        cursor.execute("""
            ALTER TABLE messages 
            ADD COLUMN attachments TEXT DEFAULT '[]'
        """)
        
        conn.commit()
        print("✅ Migration successful!")
        print("   Messages can now include image attachments.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
