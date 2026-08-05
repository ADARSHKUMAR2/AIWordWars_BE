"""
Custom exception classes for the application
"""
from fastapi import HTTPException, status


class ResumeNotFoundError(HTTPException):
    """Raised when a resume is not found"""
    def __init__(self, user_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume not found for user: {user_id}"
        )


class InvalidFileTypeError(HTTPException):
    """Raised when uploaded file is not a valid type"""
    def __init__(self, file_type: str, allowed_types: list = None):
        allowed = allowed_types or ["application/pdf"]
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file_type}. Allowed types: {', '.join(allowed)}"
        )


class FileSizeLimitError(HTTPException):
    """Raised when file size exceeds limit"""
    def __init__(self, size_mb: float, limit_mb: float):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({size_mb:.2f}MB) exceeds limit ({limit_mb}MB)"
        )


class LLMProcessingError(HTTPException):
    """Raised when LLM processing fails"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM processing failed: {detail}"
        )


class CacheError(HTTPException):
    """Raised when Redis cache operation fails"""
    def __init__(self, operation: str, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache {operation} failed: {detail}"
        )


class DatabaseError(HTTPException):
    """Raised when database operation fails"""
    def __init__(self, operation: str, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database {operation} failed: {detail}"
        )
