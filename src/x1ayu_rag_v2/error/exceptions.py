class RAGError(Exception):
    """Base exception for RAG application errors."""
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.message = message
        self.original_error = original_error

class NotInitializedError(RAGError):
    """Raised when the application is not initialized."""
    pass

class ConfigurationError(RAGError):
    """Raised when configuration is missing or invalid."""
    pass

class ModelConnectionError(RAGError):
    """Raised when connection to the model fails."""
    pass

class DatabaseError(RAGError):
    """Raised when a database operation fails."""
    pass
