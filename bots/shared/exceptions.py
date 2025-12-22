"""
Shared exception classes for all bots.
"""


class BotException(Exception):
    """Base exception for all bot errors."""
    pass


class AuthenticationError(BotException):
    """Raised when authentication fails."""
    pass


class ConfigurationError(BotException):
    """Raised when configuration is invalid."""
    pass


class DownloadError(BotException):
    """Raised when download fails."""
    pass
