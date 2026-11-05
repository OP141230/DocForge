"""Authentication endpoints."""
from fastapi import APIRouter, HTTPException, status, Response, Depends, Request
from fastapi.responses import JSONResponse

from app.models.auth import (
    RegisterRequest,
    LoginRequest,
    UserPublic,
    User
)
from app.repositories.user_repository import UserRepository
from app.repositories.session_repository import SessionRepository
from app.core.database import get_database
from app.core.security import (
    hash_password,
    verify_password,
    generate_session_token,
    create_session_expiry,
    validate_password_strength
)
from app.core.auth import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, response: Response):
    """
    Register a new user account and automatically log them in.
    
    Validates email uniqueness, password strength, creates user account, and creates session.
    """
    # Validate passwords match
    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Validate password strength
    is_valid, error_message = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # Get database and repositories
    db = await get_database()
    user_repo = UserRepository(db)
    session_repo = SessionRepository(db)
    
    # Check if email already exists
    if await user_repo.email_exists(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = hash_password(request.password)
    
    # Create user
    user = await user_repo.create(
        full_name=request.full_name,
        email=request.email,
        password_hash=password_hash
    )
    
    # Generate session token and create session (auto-login)
    session_token = generate_session_token()
    expires_at = create_session_expiry(days=30)
    
    await session_repo.create(
        user_id=user.id,
        session_token=session_token,
        expires_at=expires_at
    )
    
    # Set session cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,           # Prevent JavaScript access
        secure=False,            # Set to True in production with HTTPS
        samesite="lax",          # CSRF protection
        max_age=30 * 24 * 60 * 60,  # 30 days in seconds
    )
    
    # Return public user data (without password_hash)
    return UserPublic(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.post("/login")
async def login(request: LoginRequest, response: Response):
    """
    Login and create session.
    
    Validates credentials and creates session cookie.
    """
    # Get database and repositories
    db = await get_database()
    user_repo = UserRepository(db)
    session_repo = SessionRepository(db)
    
    # Get user by email
    user = await user_repo.get_by_email(request.email)
    
    # Check user exists and password is correct
    # Use same error message for both to avoid email enumeration
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate session token
    session_token = generate_session_token()
    expires_at = create_session_expiry(days=30)
    
    # Create session
    await session_repo.create(
        user_id=user.id,
        session_token=session_token,
        expires_at=expires_at
    )
    
    # Set session cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,           # Prevent JavaScript access
        secure=False,            # Set to True in production with HTTPS
        samesite="lax",          # CSRF protection
        max_age=30 * 24 * 60 * 60,  # 30 days in seconds
    )
    
    # Return user data
    return {
        "message": "Login successful",
        "user": UserPublic(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    }


@router.post("/logout")
async def logout(request: Request, response: Response):
    """
    Logout and destroy session.
    
    Clears session cookie and removes session from database.
    """
    # Get session token from cookie
    session_token = request.cookies.get("session_token")
    
    if session_token:
        # Delete session from database
        db = await get_database()
        session_repo = SessionRepository(db)
        await session_repo.delete_by_token(session_token)
    
    # Clear cookie
    response.delete_cookie(key="session_token")
    
    return {"message": "Logout successful"}


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Requires authentication.
    """
    return UserPublic(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )
