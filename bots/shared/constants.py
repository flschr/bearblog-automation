"""
Centralized constants for all bots.
"""

# Request settings
REQUEST_TIMEOUT = 15  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds

# Size limits
MAX_IMAGE_SIZE = 10_000_000  # 10MB
MAX_CSV_SIZE = 50_000_000  # 50MB

# Concurrency
MAX_WORKERS = 5  # Concurrent operations
