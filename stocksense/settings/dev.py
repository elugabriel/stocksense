from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]