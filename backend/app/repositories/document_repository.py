"""Document repository - data access layer."""
import json
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import uuid4

from app.models.document_ir import DocumentIR
from app.core.database import Database


class DocumentRepository:
    """Repository for document CRUD and version management."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def create(self, document: DocumentIR) -> DocumentIR:
        """Create a new document."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO documents (id, title, content, metadata, created_at, updated_at, schema_version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.id,
                    document.title,
                    json.dumps([section.model_dump() for section in document.content]),
                    json.dumps(document.metadata.model_dump()),
                    document.created_at.isoformat(),
                    document.updated_at.isoformat(),
                    document.schema_version,
                ),
            )
            await self.db.connection.commit()
        return document
    
    async def get_by_id(self, document_id: str) -> Optional[DocumentIR]:
        """Retrieve a document by ID."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM documents WHERE id = ?",
                (document_id,),
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_document(row)
    
    async def list_documents(self, limit: int = 20, offset: int = 0) -> Tuple[List[DocumentIR], int]:
        """List documents with pagination."""
        async with self.db.connection.cursor() as cursor:
            # Get total count
            await cursor.execute("SELECT COUNT(*) FROM documents")
            total = (await cursor.fetchone())[0]
            
            # Get documents
            await cursor.execute(
                "SELECT * FROM documents ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            rows = await cursor.fetchall()
            
            documents = [self._row_to_document(row) for row in rows]
            return documents, total
    
    async def update(self, document: DocumentIR) -> DocumentIR:
        """Update an existing document."""
        document.updated_at = datetime.utcnow()
        
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE documents
                SET title = ?, content = ?, metadata = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    document.title,
                    json.dumps([section.model_dump() for section in document.content]),
                    json.dumps(document.metadata.model_dump()),
                    document.updated_at.isoformat(),
                    document.id,
                ),
            )
            await self.db.connection.commit()
        
        return document
    
    async def delete(self, document_id: str) -> bool:
        """Delete a document."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            await self.db.connection.commit()
            return cursor.rowcount > 0
    
    async def create_version(self, document_id: str) -> dict:
        """Create a version snapshot of a document."""
        document = await self.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        async with self.db.connection.cursor() as cursor:
            # Get next version number
            await cursor.execute(
                "SELECT COALESCE(MAX(version_number), 0) + 1 FROM document_versions WHERE document_id = ?",
                (document_id,),
            )
            version_number = (await cursor.fetchone())[0]
            
            # Create version
            version_id = str(uuid4())
            created_at = datetime.utcnow().isoformat()
            
            await cursor.execute(
                """
                INSERT INTO document_versions (id, document_id, version_number, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    document_id,
                    version_number,
                    document.model_dump_json(),
                    created_at,
                ),
            )
            await self.db.connection.commit()
            
            return {
                "version_id": version_id,
                "version_number": version_number,
                "created_at": created_at,
            }
    
    async def list_versions(self, document_id: str) -> List[dict]:
        """List all versions of a document."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT version_number, created_at, content
                FROM document_versions
                WHERE document_id = ?
                ORDER BY version_number DESC
                """,
                (document_id,),
            )
            rows = await cursor.fetchall()
            
            versions = []
            for row in rows:
                content = json.loads(row[2])
                versions.append({
                    "version_number": row[0],
                    "created_at": row[1],
                    "content_preview": content.get("title", "")[:100],
                })
            
            return versions
    
    async def restore_version(self, document_id: str, version_number: int) -> DocumentIR:
        """Restore a document to a specific version."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT content FROM document_versions
                WHERE document_id = ? AND version_number = ?
                """,
                (document_id, version_number),
            )
            row = await cursor.fetchone()
            
            if not row:
                raise ValueError(f"Version {version_number} not found for document {document_id}")
            
            # Parse version content
            document_data = json.loads(row[0])
            document = DocumentIR(**document_data)
            
            # Update the current document
            document.updated_at = datetime.utcnow()
            await self.update(document)
            
            return document
    
    def _row_to_document(self, row) -> DocumentIR:
        """Convert database row to DocumentIR."""
        from app.models.document_ir import DocumentMetadata, Section
        
        return DocumentIR(
            id=row["id"],
            title=row["title"],
            content=[Section(**section) for section in json.loads(row["content"])],
            metadata=DocumentMetadata(**json.loads(row["metadata"])),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            schema_version=row["schema_version"],
        )
