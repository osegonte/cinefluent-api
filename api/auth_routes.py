"""
CineFluent Authentication Routes
Handles user registration, login, and profile management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any

# Import from project root
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import (
    get_current_user, get_current_user_profile, security,
    create_user_account, sign_in_user, refresh_token, sign_out_user,
    User, UserProfile
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

# Pydantic models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenRefresh(BaseModel):
    refresh_token: str

class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    native_language: Optional[str] = None
    learning_languages: Optional[list] = None
    learning_goals: Optional[Dict[str, Any]] = None

@router.post("/register")
async def register(user_data: UserRegister):
    """Register a new user account"""
    try:
        result = await create_user_account(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login")
async def login(user_data: UserLogin):
    """Login user and return access token"""
    try:
        result = await sign_in_user(
            email=user_data.email,
            password=user_data.password
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information and profile"""
    try:
        profile = await get_current_user_profile(current_user)
        return {
            "user": current_user,
            "profile": profile
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )

@router.post("/refresh")
async def refresh_access_token(token_data: TokenRefresh):
    """Refresh access token using refresh token"""
    try:
        result = await refresh_token(token_data.refresh_token)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout user and invalidate session"""
    try:
        if credentials:
            result = await sign_out_user(credentials.credentials)
            return result
        else:
            return {"message": "Successfully signed out"}
    except Exception:
        return {"message": "Successfully signed out"}
