"""Tests for storage service."""

import io
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app.services.storage_service import (
    StorageResult,
    MockStorageService,
    LocalStorageService,
    generate_file_hash,
    generate_storage_path,
    validate_file_size,
    validate_file_type,
    get_storage_service,
)


class TestStorageResult:
    """Tests for StorageResult class."""

    def test_successful_result(self):
        """Test creating a successful storage result."""
        result = StorageResult(
            success=True,
            file_path="2025/01/01/PGRS-001/abc123.pdf",
            file_url="/uploads/2025/01/01/PGRS-001/abc123.pdf",
            file_hash="abc123hash",
            file_size_bytes=1024,
            file_name="document.pdf",
            file_type="application/pdf",
        )

        assert result.success is True
        assert result.file_path == "2025/01/01/PGRS-001/abc123.pdf"
        assert result.file_url == "/uploads/2025/01/01/PGRS-001/abc123.pdf"
        assert result.file_hash == "abc123hash"
        assert result.file_size_bytes == 1024
        assert result.file_name == "document.pdf"
        assert result.file_type == "application/pdf"
        assert result.error is None

    def test_failed_result(self):
        """Test creating a failed storage result."""
        result = StorageResult(
            success=False,
            error="File type not allowed",
        )

        assert result.success is False
        assert result.error == "File type not allowed"
        assert result.file_path is None

    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = StorageResult(
            success=True,
            file_path="test/path.pdf",
            file_size_bytes=500,
        )

        data = result.to_dict()

        assert isinstance(data, dict)
        assert data["success"] is True
        assert data["file_path"] == "test/path.pdf"
        assert data["file_size_bytes"] == 500


class TestValidationHelpers:
    """Tests for validation helper functions."""

    @patch('app.services.storage_service.settings')
    def test_validate_file_type_allowed(self, mock_settings):
        """Test validating allowed file types."""
        mock_settings.ALLOWED_FILE_TYPES = ["application/pdf", "image/jpeg", "image/png"]

        assert validate_file_type("application/pdf") is True
        assert validate_file_type("image/jpeg") is True
        assert validate_file_type("image/png") is True

    @patch('app.services.storage_service.settings')
    def test_validate_file_type_not_allowed(self, mock_settings):
        """Test validating disallowed file types."""
        mock_settings.ALLOWED_FILE_TYPES = ["application/pdf", "image/jpeg"]

        assert validate_file_type("application/exe") is False
        assert validate_file_type("text/plain") is False

    @patch('app.services.storage_service.settings')
    def test_validate_file_size_within_limit(self, mock_settings):
        """Test validating file size within limit."""
        mock_settings.MAX_FILE_SIZE_MB = 10  # 10MB

        assert validate_file_size(1024) is True  # 1KB
        assert validate_file_size(5 * 1024 * 1024) is True  # 5MB
        assert validate_file_size(10 * 1024 * 1024) is True  # 10MB exactly

    @patch('app.services.storage_service.settings')
    def test_validate_file_size_exceeds_limit(self, mock_settings):
        """Test validating file size exceeds limit."""
        mock_settings.MAX_FILE_SIZE_MB = 10  # 10MB

        assert validate_file_size(11 * 1024 * 1024) is False  # 11MB


class TestGenerateFileHash:
    """Tests for file hash generation."""

    def test_generate_hash(self):
        """Test generating SHA-256 hash."""
        content = b"test content"
        hash_value = generate_file_hash(content)

        assert len(hash_value) == 64  # SHA-256 hex length
        assert hash_value.isalnum()

    def test_same_content_same_hash(self):
        """Test same content produces same hash."""
        content = b"identical content"

        hash1 = generate_file_hash(content)
        hash2 = generate_file_hash(content)

        assert hash1 == hash2

    def test_different_content_different_hash(self):
        """Test different content produces different hash."""
        content1 = b"content one"
        content2 = b"content two"

        hash1 = generate_file_hash(content1)
        hash2 = generate_file_hash(content2)

        assert hash1 != hash2


class TestGenerateStoragePath:
    """Tests for storage path generation."""

    def test_path_format(self):
        """Test generated path has correct format."""
        path = generate_storage_path("PGRS-2025-01-12345", "document.pdf")

        parts = path.split(os.sep)
        assert len(parts) == 5  # YYYY/MM/DD/grievance_id/filename

        # Check year/month/day parts are numeric
        assert parts[0].isdigit()
        assert parts[1].isdigit()
        assert parts[2].isdigit()

        # Check grievance ID
        assert parts[3] == "PGRS-2025-01-12345"

        # Check filename has extension
        assert parts[4].endswith(".pdf")

    def test_unique_filenames(self):
        """Test generates unique filenames."""
        path1 = generate_storage_path("PGRS-001", "doc.pdf")
        path2 = generate_storage_path("PGRS-001", "doc.pdf")

        # Same original name but different generated names
        assert path1 != path2


class TestMockStorageService:
    """Tests for MockStorageService."""

    @pytest.fixture
    def mock_service(self):
        """Create mock storage service instance."""
        return MockStorageService()

    @pytest.mark.asyncio
    @patch('app.services.storage_service.settings')
    async def test_upload_file_success(self, mock_settings, mock_service):
        """Test successful file upload."""
        mock_settings.ALLOWED_FILE_TYPES = ["application/pdf"]
        mock_settings.MAX_FILE_SIZE_MB = 10

        file_content = b"test pdf content"
        file_obj = io.BytesIO(file_content)

        result = await mock_service.upload_file(
            file=file_obj,
            file_name="test.pdf",
            file_type="application/pdf",
            grievance_id="PGRS-2025-01-12345",
        )

        assert result.success is True
        assert result.file_name == "test.pdf"
        assert result.file_type == "application/pdf"
        assert result.file_size_bytes == len(file_content)
        assert len(mock_service.uploaded_files) == 1

    @pytest.mark.asyncio
    @patch('app.services.storage_service.settings')
    async def test_upload_file_invalid_type(self, mock_settings, mock_service):
        """Test upload fails for invalid file type."""
        mock_settings.ALLOWED_FILE_TYPES = ["application/pdf"]

        file_obj = io.BytesIO(b"test content")

        result = await mock_service.upload_file(
            file=file_obj,
            file_name="test.exe",
            file_type="application/exe",  # Not allowed
            grievance_id="PGRS-001",
        )

        assert result.success is False
        assert "not allowed" in result.error.lower()

    @pytest.mark.asyncio
    @patch('app.services.storage_service.settings')
    async def test_upload_file_too_large(self, mock_settings, mock_service):
        """Test upload fails for file too large."""
        mock_settings.ALLOWED_FILE_TYPES = ["application/pdf"]
        mock_settings.MAX_FILE_SIZE_MB = 1  # 1MB limit

        # Create content larger than 1MB
        large_content = b"x" * (2 * 1024 * 1024)  # 2MB
        file_obj = io.BytesIO(large_content)

        result = await mock_service.upload_file(
            file=file_obj,
            file_name="large.pdf",
            file_type="application/pdf",
            grievance_id="PGRS-001",
        )

        assert result.success is False
        assert "too large" in result.error.lower()

    @pytest.mark.asyncio
    @patch('app.services.storage_service.settings')
    async def test_get_file_url(self, mock_settings, mock_service):
        """Test getting file URL."""
        mock_settings.ALLOWED_FILE_TYPES = ["application/pdf"]
        mock_settings.MAX_FILE_SIZE_MB = 10

        file_obj = io.BytesIO(b"test content")

        # Upload first
        result = await mock_service.upload_file(
            file=file_obj,
            file_name="test.pdf",
            file_type="application/pdf",
            grievance_id="PGRS-001",
        )

        # Get URL
        url = await mock_service.get_file_url(result.file_path)

        assert url is not None
        assert url == result.file_url

    @pytest.mark.asyncio
    async def test_get_file_url_not_found(self, mock_service):
        """Test getting URL for non-existent file."""
        url = await mock_service.get_file_url("non/existent/path.pdf")

        assert url is None

    @pytest.mark.asyncio
    async def test_delete_file(self, mock_service):
        """Test deleting file."""
        result = await mock_service.delete_file("test/path.pdf")

        assert result is True
        assert "test/path.pdf" in mock_service.deleted_files

    @pytest.mark.asyncio
    async def test_health_check(self, mock_service):
        """Test health check."""
        health = await mock_service.health_check()

        assert health["status"] == "healthy"
        assert health["mock"] is True


class TestLocalStorageService:
    """Tests for LocalStorageService."""

    @pytest.fixture
    def temp_upload_dir(self, tmp_path):
        """Create temporary upload directory."""
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        return str(upload_dir)

    @pytest.fixture
    def local_service(self, temp_upload_dir):
        """Create local storage service with temp directory."""
        return LocalStorageService(upload_dir=temp_upload_dir)

    @pytest.mark.asyncio
    @patch('app.services.storage_service.settings')
    async def test_upload_file_success(self, mock_settings, local_service, temp_upload_dir):
        """Test successful local file upload."""
        mock_settings.ALLOWED_FILE_TYPES = ["application/pdf"]
        mock_settings.MAX_FILE_SIZE_MB = 10

        file_content = b"test pdf content for local storage"
        file_obj = io.BytesIO(file_content)

        result = await local_service.upload_file(
            file=file_obj,
            file_name="document.pdf",
            file_type="application/pdf",
            grievance_id="PGRS-2025-01-00001",
        )

        assert result.success is True
        assert result.file_path is not None
        assert result.file_url.startswith("/uploads/")
        assert result.file_size_bytes == len(file_content)

        # Verify file exists
        full_path = os.path.join(temp_upload_dir, result.file_path)
        assert os.path.exists(full_path)

    @pytest.mark.asyncio
    @patch('app.services.storage_service.settings')
    async def test_upload_invalid_type(self, mock_settings, local_service):
        """Test upload with invalid file type."""
        mock_settings.ALLOWED_FILE_TYPES = ["application/pdf"]

        file_obj = io.BytesIO(b"test")

        result = await local_service.upload_file(
            file=file_obj,
            file_name="test.exe",
            file_type="application/x-executable",
            grievance_id="PGRS-001",
        )

        assert result.success is False
        assert "not allowed" in result.error.lower()

    @pytest.mark.asyncio
    @patch('app.services.storage_service.settings')
    async def test_get_file_url(self, mock_settings, local_service, temp_upload_dir):
        """Test getting URL for local file."""
        mock_settings.ALLOWED_FILE_TYPES = ["application/pdf"]
        mock_settings.MAX_FILE_SIZE_MB = 10

        # Upload first
        file_obj = io.BytesIO(b"test content")
        result = await local_service.upload_file(
            file=file_obj,
            file_name="test.pdf",
            file_type="application/pdf",
            grievance_id="PGRS-001",
        )

        # Get URL
        url = await local_service.get_file_url(result.file_path)

        assert url is not None
        assert url == f"/uploads/{result.file_path}"

    @pytest.mark.asyncio
    async def test_get_file_url_not_found(self, local_service):
        """Test getting URL for non-existent file."""
        url = await local_service.get_file_url("non/existent/file.pdf")

        assert url is None

    @pytest.mark.asyncio
    @patch('app.services.storage_service.settings')
    async def test_delete_file(self, mock_settings, local_service, temp_upload_dir):
        """Test deleting local file."""
        mock_settings.ALLOWED_FILE_TYPES = ["application/pdf"]
        mock_settings.MAX_FILE_SIZE_MB = 10

        # Upload first
        file_obj = io.BytesIO(b"delete me")
        result = await local_service.upload_file(
            file=file_obj,
            file_name="delete_me.pdf",
            file_type="application/pdf",
            grievance_id="PGRS-001",
        )

        # Verify file exists
        full_path = os.path.join(temp_upload_dir, result.file_path)
        assert os.path.exists(full_path)

        # Delete
        deleted = await local_service.delete_file(result.file_path)

        assert deleted is True
        assert not os.path.exists(full_path)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, local_service):
        """Test deleting non-existent file returns False."""
        deleted = await local_service.delete_file("does/not/exist.pdf")

        assert deleted is False

    @pytest.mark.asyncio
    async def test_health_check(self, local_service):
        """Test local storage health check."""
        health = await local_service.health_check()

        assert health["status"] == "healthy"
        assert health["backend"] == "local"


class TestGetStorageService:
    """Tests for storage service factory."""

    @patch('app.services.storage_service._storage_service', None)
    @patch('app.services.storage_service.settings')
    def test_get_local_storage_service(self, mock_settings, tmp_path):
        """Test getting local storage service."""
        mock_settings.STORAGE_BACKEND = "local"
        mock_settings.UPLOAD_DIR = str(tmp_path / "uploads")

        service = get_storage_service()

        assert isinstance(service, LocalStorageService)

    @patch('app.services.storage_service._storage_service', None)
    @patch('app.services.storage_service.settings')
    def test_get_default_storage_service(self, mock_settings, tmp_path):
        """Test getting default storage service when unknown backend."""
        mock_settings.STORAGE_BACKEND = "unknown"
        mock_settings.UPLOAD_DIR = str(tmp_path / "uploads")

        service = get_storage_service()

        # Defaults to local
        assert isinstance(service, LocalStorageService)
