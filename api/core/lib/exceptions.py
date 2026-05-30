# gemini-flash

class ArasException(Exception):
    """Base exception for Aras Framework."""
    status_code: int = 500
    message: str = "An internal error occurred."

    def __init__(self, message: str = None, status_code: int = None):
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)

class RequiredAppError(ArasException):
    """Raised when trying to uninstall a required app."""
    status_code: int = 409
    message: str = "This application is required and cannot be uninstalled."

class ValidationException(ArasException):
    """Raised during model validation."""
    status_code: int = 400
    message: str = "Validation failed."
