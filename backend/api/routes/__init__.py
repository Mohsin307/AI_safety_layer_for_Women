"""API routes module initialization"""
from .auth import router as auth_router
from .users import router as users_router
from .emergency import router as emergency_router
from .safety import router as safety_router

__all__ = [
    "auth_router",
    "users_router", 
    "emergency_router",
    "safety_router"
]
