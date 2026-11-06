"""File storage service with abstraction for local and future cloud storage."""
import os
import hashlib
import uuid
from pathlib import Path
from typing import Optional, BinaryIO
from abc import ABC, abstractmethod


class StorageService(ABC):
    """Abstract storage interface for file operations."""
    
    @abstractmethod
    async def save_file(self, file_data: bytes, user_id: str, original_filename: str) -> tuple[str, str, str]:
        """
        Save uploaded file.
        
        Args:
            file_data: File bytes
            user_id: ID of uploading user
            original_filename: Original filename from user
            
        Returns:
            Tuple of (stored_filename, storage_path, content_hash)
        """
        pass
    
    @abstractmethod
    async def get_file(self, storage_path: str) -> bytes:
        """
        Retrieve file by storage path.
        
        Args:
            storage_path: Path where file is stored
            
        Returns:
            File bytes
        """
        pass
    
    @abstractmethod
    async def delete_file(self, storage_path: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            storage_path: Path where file is stored
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    def file_exists(self, storage_path: str) -> bool:
        """Check if file exists in storage."""
        pass


class LocalFileStorage(StorageService):
    """Local filesystem storage implementation."""
    
    def __init__(self, base_path: str = "./uploads"):
        """
        Initialize local storage.
        
        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and other attacks.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename with UUID prefix
        """
        # Extract extension
        ext = Path(filename).suffix.lower()
        
        # Remove dangerous characters
        safe_name = "".join(c for c in filename if c.isalnum() or c in ".-_")
        
        # Generate UUID-based filename
        unique_id = uuid.uuid4().hex[:12]
        
        return f"{unique_id}_{safe_name}"
    
    def _compute_hash(self, data: bytes) -> str:
        """Compute SHA-256 hash of file data."""
        return hashlib.sha256(data).hexdigest()
    
    def _get_user_directory(self, user_id: str) -> Path:
        """Get user-specific directory."""
        user_dir = self.base_path / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    async def save_file(self, file_data: bytes, user_id: str, original_filename: str) -> tuple[str, str, str]:
        """
        Save uploaded file to local filesystem.
        
        Security measures:
        - UUID-prefixed filenames prevent collisions
        - User-specific directories prevent access to other users' files
        - Path sanitization prevents directory traversal
        - SHA-256 hashing enables deduplication
        
        Args:
            file_data: File bytes
            user_id: ID of uploading user
            original_filename: Original filename from user
            
        Returns:
            Tuple of (stored_filename, storage_path, content_hash)
        """
        # Sanitize filename
        stored_filename = self._sanitize_filename(original_filename)
        
        # Compute hash for deduplication
        content_hash = self._compute_hash(file_data)
        
        # Get user directory
        user_dir = self._get_user_directory(user_id)
        
        # Full path
        full_path = user_dir / stored_filename
        
        # Ensure no path traversal
        if not str(full_path.resolve()).startswith(str(self.base_path.resolve())):
            raise ValueError("Invalid file path - possible path traversal attempt")
        
        # Write file
        with open(full_path, 'wb') as f:
            f.write(file_data)
        
        # Return relative storage path (relative to base_path)
        storage_path = f"{user_id}/{stored_filename}"
        
        return stored_filename, storage_path, content_hash
    
    async def get_file(self, storage_path: str) -> bytes:
        """
        Retrieve file from local filesystem.
        
        Args:
            storage_path: Relative path from base_path
            
        Returns:
            File bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        full_path = self.base_path / storage_path
        
        # Security: ensure path is within base_path
        if not str(full_path.resolve()).startswith(str(self.base_path.resolve())):
            raise ValueError("Invalid file path - possible path traversal attempt")
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {storage_path}")
        
        with open(full_path, 'rb') as f:
            return f.read()
    
    async def delete_file(self, storage_path: str) -> bool:
        """
        Delete file from local filesystem.
        
        Args:
            storage_path: Relative path from base_path
            
        Returns:
            True if deleted, False if not found
        """
        try:
            full_path = self.base_path / storage_path
            
            # Security: ensure path is within base_path
            if not str(full_path.resolve()).startswith(str(self.base_path.resolve())):
                raise ValueError("Invalid file path - possible path traversal attempt")
            
            if full_path.exists():
                full_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    def file_exists(self, storage_path: str) -> bool:
        """Check if file exists."""
        try:
            full_path = self.base_path / storage_path
            
            # Security: ensure path is within base_path
            if not str(full_path.resolve()).startswith(str(self.base_path.resolve())):
                return False
            
            return full_path.exists()
        except Exception:
            return False


# Global storage instance
_storage: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get or create global storage service instance."""
    global _storage
    if _storage is None:
        # Get storage path from environment
        storage_path = os.getenv("UPLOAD_STORAGE_PATH", "./uploads")
        _storage = LocalFileStorage(storage_path)
    return _storage
