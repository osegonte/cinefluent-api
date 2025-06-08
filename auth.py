from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any, Union
from datetime import datetime
import os
from database import supabase

# JWT Configuration
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)

class User(BaseModel):
    id: str
    email: str
    role: str = "authenticated"
    email_confirmed_at: Optional[str] = None
    
    @field_validator('email_confirmed_at', mode='before')
    @classmethod
    def validate_email_confirmed_at(cls, v):
        """Convert datetime objects to ISO string format"""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)
    
class UserProfile(BaseModel):
    id: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    native_language: str = "en"
    learning_languages: list = []
    learning_goals: dict = {}
    created_at: Optional[str] = None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Extract and validate user from JWT token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
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
        
        # Convert datetime fields properly
        email_confirmed_at = None
        if hasattr(user, 'email_confirmed_at') and user.email_confirmed_at:
            if isinstance(user.email_confirmed_at, datetime):
                email_confirmed_at = user.email_confirmed_at.isoformat()
            else:
                email_confirmed_at = str(user.email_confirmed_at)
        
        return User(
            id=user.id,
            email=user.email,
            role=getattr(user, 'role', "authenticated"),
            email_confirmed_at=email_confirmed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Auth error: {str(e)}")
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
            
            insert_response = supabase.table("profiles").insert(default_profile).execute()
            if insert_response.data:
                return UserProfile(**insert_response.data[0])
            else:
                return UserProfile(**default_profile)
        
        profile_data = profile_response.data[0]
        return UserProfile(**profile_data)
        
    except Exception as e:
        print(f"Profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve user profile: {str(e)}"
        )

def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """Get user if authenticated, but don't require authentication"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user_response = supabase.auth.get_user(token)
        
        if user_response.user:
            user = user_response.user
            
            # Convert datetime fields properly
            email_confirmed_at = None
            if hasattr(user, 'email_confirmed_at') and user.email_confirmed_at:
                if isinstance(user.email_confirmed_at, datetime):
                    email_confirmed_at = user.email_confirmed_at.isoformat()
                else:
                    email_confirmed_at = str(user.email_confirmed_at)
            
            return User(
                id=user.id,
                email=user.email,
                role=getattr(user, 'role', "authenticated"),
                email_confirmed_at=email_confirmed_at
            )
        return None
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

# Enhanced auth functions with better error handling
async def create_user_account(email: str, password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
    """Create new user account with improved error handling"""
    try:
        print(f"Attempting to create user: {email}")
        
        # Prepare signup data
        signup_data = {
            "email": email,
            "password": password
        }
        
        if full_name:
            signup_data["options"] = {
                "data": {
                    "full_name": full_name
                }
            }
        
        print(f"Calling Supabase signup for: {email}")
        
        # Create user with Supabase Auth
        auth_response = supabase.auth.sign_up(signup_data)
        
        print(f"Supabase response: user={auth_response.user is not None}, session={auth_response.session is not None}")
        
        if auth_response.user:
            print(f"User created successfully: {auth_response.user.id}")
            
            # Create profile record
            try:
                profile_data = {
                    "id": auth_response.user.id,
                    "username": email.split("@")[0],
                    "full_name": full_name,
                    "native_language": "en",
                    "learning_languages": [],
                    "learning_goals": {}
                }
                
                print(f"Creating profile for user: {auth_response.user.id}")
                profile_response = supabase.table("profiles").insert(profile_data).execute()
                print(f"Profile created: {profile_response.data is not None}")
                
            except Exception as profile_error:
                print(f"Profile creation warning: {profile_error}")
                # Don't fail registration if profile creation fails
            
            return {
                "user": {
                    "id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "email_confirmed_at": auth_response.user.email_confirmed_at.isoformat() if auth_response.user.email_confirmed_at else None
                },
                "session": auth_response.session,
                "access_token": auth_response.session.access_token if auth_response.session else None,
                "token_type": "bearer",
                "message": "User created successfully"
            }
        else:
            print(f"Supabase signup failed for: {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        print(f"Registration exception for {email}: {str(e)}")
        
        if "already registered" in error_msg or "already exists" in error_msg or "user_already_exists" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        elif "invalid email" in error_msg or "email" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        elif "password" in error_msg and ("weak" in error_msg or "short" in error_msg):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet requirements (minimum 6 characters)"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {str(e)}"
            )

async def sign_in_user(email: str, password: str) -> Dict[str, Any]:
    """Sign in user with enhanced error handling"""
    try:
        print(f"Attempting login for: {email}")
        
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        print(f"Login response: user={auth_response.user is not None}, session={auth_response.session is not None}")
        
        if auth_response.user and auth_response.session:
            print(f"Login successful for: {email}")
            
            # Get or create user profile
            profile_response = supabase.table("profiles").select("*").eq("id", auth_response.user.id).execute()
            
            profile = None
            if profile_response.data:
                profile = profile_response.data[0]
                print(f"Profile found for user: {auth_response.user.id}")
            else:
                # Create profile if it doesn't exist
                try:
                    default_profile = {
                        "id": auth_response.user.id,
                        "username": email.split("@")[0],
                        "full_name": None,
                        "native_language": "en",
                        "learning_languages": [],
                        "learning_goals": {}
                    }
                    
                    insert_response = supabase.table("profiles").insert(default_profile).execute()
                    if insert_response.data:
                        profile = insert_response.data[0]
                        print(f"Profile created during login for: {auth_response.user.id}")
                except Exception as profile_error:
                    print(f"Profile creation warning during login: {profile_error}")
            
            return {
                "user": {
                    "id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "email_confirmed_at": auth_response.user.email_confirmed_at.isoformat() if auth_response.user.email_confirmed_at else None
                },
                "profile": profile,
                "session": auth_response.session,
                "access_token": auth_response.session.access_token,
                "refresh_token": auth_response.session.refresh_token,
                "token_type": "bearer",
                "expires_in": auth_response.session.expires_in,
                "message": "Login successful"
            }
        else:
            print(f"Login failed for {email}: Invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        print(f"Login exception for {email}: {str(e)}")
        
        if "invalid login credentials" in error_msg or "email not confirmed" in error_msg or "invalid_credentials" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}"
            )

async def refresh_token(refresh_token: str) -> Dict[str, Any]:
    """Refresh user session token"""
    try:
        auth_response = supabase.auth.refresh_session(refresh_token)
        
        if auth_response.session:
            return {
                "access_token": auth_response.session.access_token,
                "refresh_token": auth_response.session.refresh_token,
                "token_type": "bearer",
                "expires_in": auth_response.session.expires_in
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )

async def sign_out_user(token: str) -> Dict[str, Any]:
    """Sign out user and invalidate session"""
    try:
        supabase.auth.sign_out()
        return {"message": "Successfully signed out"}
    except Exception as e:
        # Even if signout fails on server, we'll return success
        # since the client will remove the token anyway
        return {"message": "Successfully signed out"}