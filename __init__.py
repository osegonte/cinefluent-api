"""
CineFluent API - Language learning through movies
"""

__version__ = "0.1.0"
__author__ = "CineFluent Team"
__description__ = "FastAPI backend for CineFluent language learning platform"

# Make key components available at package level
from .main import app
from .database import supabase, test_connection
from .auth import get_current_user, User

__all__ = [
    "app",
    "supabase", 
    "test_connection",
    "get_current_user",
    "User"
]
