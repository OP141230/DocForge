"""Authentication dependency for FastAPI."""
from fastapi import Request, HTTPException, status
from typing import Optional

from app.models.auth import User
from app.repositories.user_repository import UserRepository
from app.repositories.session_repository import SessionRepository
from app.core.database import get_database


async def get_current_user(request: Request) -> User:
    """
    Get current authenticated user from session cookie.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: 401 if not authenticated or session invalid/expired
    """
    # Get session token from cookie
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Get database and repositories
    db = await get_database()
    session_repo = SessionRepository(db)
    user_repo = UserRepository(db)
    
    # Get session
    session = await session_repo.get_by_token(session_token)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )
    
    # Check if session is expired
    if session_repo.is_expired(session):
        await session_repo.delete_by_token(session_token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )
    
    # Get user
    user = await user_repo.get_by_id(session.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


async def get_current_user_optional(request: Request) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    Used for endpoints that work for both authenticated and unauthenticated users.
    """
    try:
        return await get_current_user(request)
    except HTTPException:
        return None
