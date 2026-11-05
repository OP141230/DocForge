"""DocumentBrief repository - data access layer."""
import json
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from uuid import uuid4

from app.models.document_brief import DocumentBrief, OutlineItem
from app.core.database import Database


class DocumentBriefRepository:
    """Repository for document brief CRUD operations."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def create(self, brief_data: Dict[str, Any], user_id: str) -> DocumentBrief:
        """Create a new document brief."""
        brief = DocumentBrief(
            id=str(uuid4()),
            user_id=user_id,
            **brief_data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO document_briefs (
                    id, user_id, conversation_id, document_type, title, topic,
                    purpose, audience, language, desired_length, tone, writing_style,
                    document_specific_data, required_sections, important_points,
                    topics_to_avoid, additional_instructions, citation_style,
                    outline, outline_approved, outline_approved_at, document_id,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    brief.id,
                    brief.user_id,
                    brief.conversation_id,
                    brief.document_type,
                    brief.title,
                    brief.topic,
                    brief.purpose,
                    brief.audience,
                    brief.language,
                    brief.desired_length,
                    brief.tone,
                    brief.writing_style,
                    json.dumps(brief.document_specific_data),
                    json.dumps(brief.required_sections),
                    json.dumps(brief.important_points),
                    json.dumps(brief.topics_to_avoid),
                    brief.additional_instructions,
                    brief.citation_style,
                    json.dumps([item.dict() for item in brief.outline]) if brief.outline else None,
                    1 if brief.outline_approved else 0,
                    brief.outline_approved_at.isoformat() if brief.outline_approved_at else None,
                    brief.document_id,
                    brief.created_at.isoformat(),
                    brief.updated_at.isoformat(),
                ),
            )
            await self.db.connection.commit()
        
        return brief
    
    async def get_by_id(self, brief_id: str, user_id: str) -> Optional[DocumentBrief]:
        """Get a document brief by ID, filtered by user_id for ownership verification."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM document_briefs WHERE id = ? AND user_id = ?",
                (brief_id, user_id),
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_brief(row)
    
    async def list_by_user(self, user_id: str, limit: int = 20, offset: int = 0) -> Tuple[List[DocumentBrief], int]:
        """List document briefs for a user with pagination."""
        async with self.db.connection.cursor() as cursor:
            # Get total count
            await cursor.execute(
                "SELECT COUNT(*) FROM document_briefs WHERE user_id = ?",
                (user_id,),
            )
            total = (await cursor.fetchone())[0]
            
            # Get briefs ordered by updated_at DESC
            await cursor.execute(
                """
                SELECT * FROM document_briefs 
                WHERE user_id = ? 
                ORDER BY updated_at DESC 
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset),
            )
            rows = await cursor.fetchall()
            
            briefs = [self._row_to_brief(row) for row in rows]
            return briefs, total
    
    async def update(self, brief_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[DocumentBrief]:
        """Update document brief, filtered by user_id for ownership verification."""
        # Get existing brief to verify ownership
        existing = await self.get_by_id(brief_id, user_id)
        if not existing:
            return None
        
        # Build update query dynamically
        update_fields = []
        values = []
        
        for key, value in updates.items():
            if key in ['id', 'user_id', 'created_at']:
                continue  # Skip immutable fields
            
            if key in ['document_specific_data', 'required_sections', 'important_points', 'topics_to_avoid']:
                update_fields.append(f"{key} = ?")
                values.append(json.dumps(value))
            elif key == 'outline' and value is not None:
                update_fields.append("outline = ?")
                values.append(json.dumps([item.dict() if hasattr(item, 'dict') else item for item in value]))
            elif key == 'outline_approved':
                update_fields.append("outline_approved = ?")
                values.append(1 if value else 0)
            elif key == 'outline_approved_at' and value is not None:
                update_fields.append("outline_approved_at = ?")
                values.append(value.isoformat() if isinstance(value, datetime) else value)
            else:
                update_fields.append(f"{key} = ?")
                values.append(value)
        
        if not update_fields:
            return existing
        
        # Always update updated_at
        update_fields.append("updated_at = ?")
        updated_at = datetime.utcnow()
        values.append(updated_at.isoformat())
        
        # Add WHERE clause values
        values.extend([brief_id, user_id])
        
        async with self.db.connection.cursor() as cursor:
            query = f"""
                UPDATE document_briefs 
                SET {', '.join(update_fields)}
                WHERE id = ? AND user_id = ?
            """
            await cursor.execute(query, values)
            await self.db.connection.commit()
            
            if cursor.rowcount == 0:
                return None
        
        # Return updated brief
        return await self.get_by_id(brief_id, user_id)
    
    async def delete(self, brief_id: str, user_id: str) -> bool:
        """Delete a document brief, filtered by user_id for ownership verification."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM document_briefs WHERE id = ? AND user_id = ?",
                (brief_id, user_id),
            )
            await self.db.connection.commit()
            return cursor.rowcount > 0
    
    def _row_to_brief(self, row) -> DocumentBrief:
        """Convert database row to DocumentBrief model."""
        # Parse JSON fields
        document_specific_data = json.loads(row["document_specific_data"]) if row["document_specific_data"] else {}
        required_sections = json.loads(row["required_sections"]) if row["required_sections"] else []
        important_points = json.loads(row["important_points"]) if row["important_points"] else []
        topics_to_avoid = json.loads(row["topics_to_avoid"]) if row["topics_to_avoid"] else []
        
        outline = None
        if row["outline"]:
            outline_data = json.loads(row["outline"])
            outline = [OutlineItem(**item) for item in outline_data]
        
        return DocumentBrief(
            id=row["id"],
            user_id=row["user_id"],
            conversation_id=row["conversation_id"],
            document_type=row["document_type"],
            title=row["title"],
            topic=row["topic"],
            purpose=row["purpose"],
            audience=row["audience"],
            language=row["language"],
            desired_length=row["desired_length"],
            tone=row["tone"],
            writing_style=row["writing_style"],
            document_specific_data=document_specific_data,
            required_sections=required_sections,
            important_points=important_points,
            topics_to_avoid=topics_to_avoid,
            additional_instructions=row["additional_instructions"],
            citation_style=row["citation_style"],
            outline=outline,
            outline_approved=bool(row["outline_approved"]),
            outline_approved_at=datetime.fromisoformat(row["outline_approved_at"]) if row["outline_approved_at"] else None,
            document_id=row["document_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
