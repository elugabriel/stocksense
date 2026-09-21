from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable login throttling locally so testing multiple accounts doesn't lock you out.
RATELIMIT_ENABLE = False

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://localhost:\d+$",
    r"^http://127\.0\.0\.1:\d+$",
]