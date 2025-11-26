"""Storage Service for file uploads.

Provides file upload handling with local storage (and S3-ready interface).
Includes file validation, hash generation, and secure storage.
"""

import hashlib
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional
from uuid import uuid4

import aiofiles  # type: ignore[import-untyped]
import aiofiles.os  # type: ignore[import-untyped]

from app.config import settings

logger = logging.getLogger(__name__)


class StorageResult:
    """Result of file storage operation."""

    def __init__(
        self,
        success: bool,
        file_path: Optional[str] = None,
        file_url: Optional[str] = None,
        file_hash: Optional[str] = None,
        file_size_bytes: int = 0,
        file_name: Optional[str] = None,
        file_type: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.success = success
        self.file_path = file_path
        self.file_url = file_url
        self.file_hash = file_hash
        self.file_size_bytes = file_size_bytes
        self.file_name = file_name
        self.file_type = file_type
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "file_path": self.file_path,
            "file_url": self.file_url,
            "file_hash": self.file_hash,
            "file_size_bytes": self.file_size_bytes,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "error": self.error,
        }


class IStorageService(ABC):
    """Interface for file storage service."""

    @abstractmethod
    async def upload_file(
        self,
        file: BinaryIO,
        file_name: str,
        file_type: str,
        grievance_id: str,
    ) -> StorageResult:
        """Upload a file.

        Args:
            file: File object to upload
            file_name: Original file name
            file_type: MIME type
            grievance_id: Associated grievance ID

        Returns:
            StorageResult with file path and URL
        """
        pass

    @abstractmethod
    async def get_file_url(self, file_path: str) -> Optional[str]:
        """Get URL for accessing a file.

        Args:
            file_path: Stored file path

        Returns:
            URL to access the file
        """
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file.

        Args:
            file_path: Path to file to delete

        Returns:
            True if deleted, False otherwise
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check storage service health."""
        pass


def validate_file_type(file_type: str) -> bool:
    """Validate file MIME type is allowed.

    Args:
        file_type: MIME type to validate

    Returns:
        True if allowed, False otherwise
    """
    return file_type in settings.ALLOWED_FILE_TYPES


def validate_file_size(size_bytes: int) -> bool:
    """Validate file size is within limit.

    Args:
        size_bytes: File size in bytes

    Returns:
        True if within limit, False otherwise
    """
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    return size_bytes <= max_bytes


def generate_file_hash(content: bytes) -> str:
    """Generate SHA-256 hash of file content.

    Args:
        content: File content bytes

    Returns:
        Hex-encoded SHA-256 hash
    """
    return hashlib.sha256(content).hexdigest()


def generate_storage_path(grievance_id: str, file_name: str) -> str:
    """Generate organized storage path.

    Format: YYYY/MM/DD/grievance_id/uuid_filename

    Args:
        grievance_id: Grievance ID for organization
        file_name: Original file name

    Returns:
        Storage path string
    """
    now = datetime.utcnow()
    file_ext = Path(file_name).suffix
    unique_name = f"{uuid4().hex}{file_ext}"

    return os.path.join(
        str(now.year),
        f"{now.month:02d}",
        f"{now.day:02d}",
        grievance_id,
        unique_name,
    )


class LocalStorageService(IStorageService):
    """Local filesystem storage service.

    Stores files in the local filesystem with organized directory structure.
    """

    def __init__(self, upload_dir: Optional[str] = None):
        self.upload_dir = upload_dir or settings.UPLOAD_DIR
        self._ensure_upload_dir()

    def _ensure_upload_dir(self) -> None:
        """Ensure upload directory exists."""
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        file: BinaryIO,
        file_name: str,
        file_type: str,
        grievance_id: str,
    ) -> StorageResult:
        """Upload file to local storage.

        Args:
            file: File object
            file_name: Original name
            file_type: MIME type
            grievance_id: Grievance ID

        Returns:
            StorageResult
        """
        # Validate file type
        if not validate_file_type(file_type):
            return StorageResult(
                success=False,
                error=f"File type not allowed: {file_type}. Allowed: {settings.ALLOWED_FILE_TYPES}",
            )

        try:
            # Read file content
            content = file.read()
            file_size = len(content)

            # Validate file size
            if not validate_file_size(file_size):
                return StorageResult(
                    success=False,
                    error=f"File too large: {file_size} bytes. Max: {settings.MAX_FILE_SIZE_MB}MB",
                )

            # Generate storage path and hash
            storage_path = generate_storage_path(grievance_id, file_name)
            full_path = os.path.join(self.upload_dir, storage_path)
            file_hash = generate_file_hash(content)

            # Create directory structure
            await aiofiles.os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # Write file
            async with aiofiles.open(full_path, 'wb') as f:
                await f.write(content)

            # Generate URL (for local, it's the relative path)
            file_url = f"/uploads/{storage_path}"

            logger.info(f"File uploaded: {storage_path} ({file_size} bytes)")

            return StorageResult(
                success=True,
                file_path=storage_path,
                file_url=file_url,
                file_hash=file_hash,
                file_size_bytes=file_size,
                file_name=file_name,
                file_type=file_type,
            )

        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return StorageResult(
                success=False,
                error=str(e),
            )

    async def get_file_url(self, file_path: str) -> Optional[str]:
        """Get URL for local file.

        Args:
            file_path: Stored file path

        Returns:
            URL path
        """
        full_path = os.path.join(self.upload_dir, file_path)
        if os.path.exists(full_path):
            return f"/uploads/{file_path}"
        return None

    async def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage.

        Args:
            file_path: Path to delete

        Returns:
            True if deleted
        """
        try:
            full_path = os.path.join(self.upload_dir, file_path)
            if os.path.exists(full_path):
                await aiofiles.os.remove(full_path)
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"File delete failed: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Check local storage health."""
        try:
            # Check directory exists and is writable
            test_file = os.path.join(self.upload_dir, ".health_check")
            async with aiofiles.open(test_file, 'w') as f:
                await f.write("ok")
            await aiofiles.os.remove(test_file)

            return {
                "status": "healthy",
                "backend": "local",
                "upload_dir": self.upload_dir,
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "local",
                "error": str(e),
            }


class MockStorageService(IStorageService):
    """Mock storage service for testing."""

    def __init__(self) -> None:
        self.uploaded_files: List[StorageResult] = []
        self.deleted_files: List[str] = []

    async def upload_file(
        self,
        file: BinaryIO,
        file_name: str,
        file_type: str,
        grievance_id: str,
    ) -> StorageResult:
        """Mock file upload."""
        if not validate_file_type(file_type):
            return StorageResult(
                success=False,
                error=f"File type not allowed: {file_type}",
            )

        content = file.read()
        file_size = len(content)

        if not validate_file_size(file_size):
            return StorageResult(
                success=False,
                error="File too large",
            )

        storage_path = generate_storage_path(grievance_id, file_name)
        file_hash = generate_file_hash(content)

        result = StorageResult(
            success=True,
            file_path=storage_path,
            file_url=f"/uploads/{storage_path}",
            file_hash=file_hash,
            file_size_bytes=file_size,
            file_name=file_name,
            file_type=file_type,
        )

        self.uploaded_files.append(result)
        return result

    async def get_file_url(self, file_path: str) -> Optional[str]:
        """Get mock file URL."""
        for result in self.uploaded_files:
            if result.file_path == file_path:
                return result.file_url
        return None

    async def delete_file(self, file_path: str) -> bool:
        """Mock file delete."""
        self.deleted_files.append(file_path)
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Return mock health status."""
        return {
            "status": "healthy",
            "mock": True,
            "files_uploaded": len(self.uploaded_files),
        }


# Singleton instance
_storage_service: Optional[IStorageService] = None


def get_storage_service() -> IStorageService:
    """Get storage service instance.

    Returns:
        IStorageService instance
    """
    global _storage_service

    if _storage_service is None:
        if settings.STORAGE_BACKEND == "local":
            _storage_service = LocalStorageService()
        else:
            # Default to local for now (S3 would be added here)
            _storage_service = LocalStorageService()

    return _storage_service
