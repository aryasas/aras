from fastapi import status
from typing import Optional


class ArasException(Exception):
    def __init__(self, message: str, detail: Optional[dict] = None, status: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.detail = detail
        self.status = status
        super().__init__(self.message)


class ValidationException(ArasException):
    def __init__(self, message: str = "Validation error", detail: Optional[dict] = None):
        super().__init__(message, detail, status.HTTP_422_UNPROCESSABLE_ENTITY)


class ResourceNotFoundException(ArasException):
    def __init__(self, message: str = "Resource not found", detail: Optional[dict] = None):
        super().__init__(message, detail, status.HTTP_404_NOT_FOUND)


class PermissionDeniedException(ArasException):
    def __init__(self, message: str = "Permission denied", detail: Optional[dict] = None):
        super().__init__(message, detail, status.HTTP_403_FORBIDDEN)


class ConflictException(ArasException):
    def __init__(self, message: str = "Conflict", detail: Optional[dict] = None):
        super().__init__(message, detail, status.HTTP_409_CONFLICT)
