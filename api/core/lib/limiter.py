# claude-sonnet-4-6
from slowapi import Limiter
from slowapi.util import get_remote_address

# gemini-3-flash-preview: Centralized rate limiter instance
limiter = Limiter(key_func=get_remote_address)
