"""Authentication models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from uuid import uuid4


class User(BaseModel):
    """User model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    full_name: str
    email: EmailStr
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserPublic(BaseModel):
    """Public user model (without password_hash)."""
    id: str
    full_name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime


class Session(BaseModel):
    """Session model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RegisterRequest(BaseModel):
    """User registration request."""
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    confirm_password: str


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class Conversation(BaseModel):
    """Conversation model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Message(BaseModel):
    """Message model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: str
    role: str  # 'user' or 'assistant'
    content: str
    sequence_number: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CreateConversationRequest(BaseModel):
    """Request to create a conversation."""
    title: Optional[str] = "New Conversation"


class UpdateConversationRequest(BaseModel):
    """Request to update a conversation."""
    title: str


class CreateMessageRequest(BaseModel):
    """Request to create a message."""
    role: str = Field(pattern="^(user|assistant)$")
    content: str


class UpdateMessageRequest(BaseModel):
    """Request to update a message."""
    content: str
