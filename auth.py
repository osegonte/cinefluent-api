from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
from database import supabase, supabase_admin

# JWT Configuration
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "your-jwt-secret")
ALGORITHM = "HS256"

security = HTTPBearer()

class User(BaseModel):
    id: str
    email: str
    role: str = "authenticated"
    
class UserProfile(BaseModel):
    id: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    native_language: str = "en"
    learning_languages: list = []
    learning_goals: dict = {}

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Extract and validate user from JWT token"""
    token = credentials.credentials
    
    try:
        # Verify token with Supabase
        user_response = supabase.auth.get_user(token)
        
        if user_response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = user_response.user
        return User(
            id=user.id,
            email=user.email,
            role=user.role if hasattr(user, 'role') else "authenticated"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_profile(user: User = Depends(get_current_user)) -> UserProfile:
    """Get user profile from database"""
    try:
        profile_response = supabase.table("profiles").select("*").eq("id", user.id).execute()
        
        if not profile_response.data:
            # Create default profile if doesn't exist
            default_profile = {
                "id": user.id,
                "username": user.email.split("@")[0],
                "full_name": None,
                "native_language": "en",
                "learning_languages": [],
                "learning_goals": {}
            }
            
            supabase.table("profiles").insert(default_profile).execute()
            return UserProfile(**default_profile)
        
        profile_data = profile_response.data[0]
        return UserProfile(**profile_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve user profile: {str(e)}"
        )

def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[User]:
    """Get user if authenticated, but don't require authentication"""
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials)
    except:
        return None

def require_premium_user(user: User = Depends(get_current_user)) -> User:
    """Require user to have premium subscription"""
    try:
        # Check user subscription
        subscription_response = supabase.table("subscriptions")\
            .select("*")\
            .eq("user_id", user.id)\
            .eq("status", "active")\
            .execute()
        
        if not subscription_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Premium subscription required"
            )
        
        subscription = subscription_response.data[0]
        if subscription["plan_type"] == "free":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Premium subscription required"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not verify subscription status"
        )

# Auth endpoints
async def create_user_account(email: str, password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
    """Create new user account"""
    try:
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name
                }
            }
        })
        
        if auth_response.user:
            return {
                "user": auth_response.user,
                "session": auth_response.session,
                "message": "User created successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )

async def sign_in_user(email: str, password: str) -> Dict[str, Any]:
    """Sign in user with email and password"""
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if auth_response.user and auth_response.session:
            return {
                "user": auth_response.user,
                "session": auth_response.session,
                "access_token": auth_response.session.access_token,
                "token_type": "bearer"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )