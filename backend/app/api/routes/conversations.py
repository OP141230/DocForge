"""Conversation and message management endpoints."""
from fastapi import APIRouter, HTTPException, Response, Depends

from app.models.auth import (
    User, 
    Conversation, 
    Message,
    CreateConversationRequest, 
    UpdateConversationRequest,
    CreateMessageRequest,
)
from app.core.database import get_database
from app.core.auth import get_current_user
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository


router = APIRouter()


@router.post("/conversations", response_model=Conversation, status_code=201)
async def create_conversation(
    request: CreateConversationRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation (requires authentication)."""
    try:
        db = await get_database()
        repo = ConversationRepository(db)
        conversation = await repo.create(user_id=current_user.id, title=request.title)
        return conversation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")


@router.get("/conversations")
async def list_conversations(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """List user's conversations with pagination (requires authentication)."""
    try:
        db = await get_database()
        repo = ConversationRepository(db)
        conversations, total = await repo.list_by_user(current_user.id, limit, offset)
        return {
            "conversations": conversations,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a conversation by ID (requires authentication and ownership)."""
    try:
        db = await get_database()
        repo = ConversationRepository(db)
        conversation = await repo.get_by_id(conversation_id, user_id=current_user.id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation: {str(e)}")


@router.put("/conversations/{conversation_id}", response_model=Conversation)
async def update_conversation(
    conversation_id: str,
    request: UpdateConversationRequest,
    current_user: User = Depends(get_current_user)
):
    """Update a conversation title (requires authentication and ownership)."""
    try:
        db = await get_database()
        repo = ConversationRepository(db)
        conversation = await repo.update_title(conversation_id, request.title, user_id=current_user.id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update conversation: {str(e)}")


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a conversation (requires authentication and ownership)."""
    try:
        db = await get_database()
        repo = ConversationRepository(db)
        deleted = await repo.delete(conversation_id, user_id=current_user.id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return Response(status_code=204)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")


@router.post("/conversations/{conversation_id}/messages", response_model=Message, status_code=201)
async def create_message(
    conversation_id: str,
    request: CreateMessageRequest,
    current_user: User = Depends(get_current_user)
):
    """Add a message to a conversation (requires authentication and ownership)."""
    try:
        db = await get_database()
        conv_repo = ConversationRepository(db)
        msg_repo = MessageRepository(db)
        
        # Verify conversation exists and user owns it
        conversation = await conv_repo.get_by_id(conversation_id, user_id=current_user.id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get next sequence number
        latest_sequence = await msg_repo.get_latest_sequence(conversation_id)
        next_sequence = latest_sequence + 1
        
        # Create message with role 'user'
        message = await msg_repo.create(
            conversation_id=conversation_id,
            role="user",
            content=request.content,
            sequence_number=next_sequence
        )
        
        return message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create message: {str(e)}")


@router.get("/conversations/{conversation_id}/messages")
async def list_messages(
    conversation_id: str,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """List messages for a conversation (requires authentication and ownership)."""
    try:
        db = await get_database()
        conv_repo = ConversationRepository(db)
        msg_repo = MessageRepository(db)
        
        # Verify conversation exists and user owns it
        conversation = await conv_repo.get_by_id(conversation_id, user_id=current_user.id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get messages
        messages, total = await msg_repo.list_by_conversation(conversation_id, limit, offset)
        
        return {
            "messages": messages,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list messages: {str(e)}")
