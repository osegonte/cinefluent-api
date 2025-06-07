from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import os

# Import our modules
from database import supabase, test_connection
from auth import (
    get_current_user, get_current_user_profile, get_optional_user, 
    require_premium_user, create_user_account, sign_in_user,
    refresh_token, sign_out_user, security,
    User, UserProfile
)

app = FastAPI(
    title="CineFluent API", 
    version="0.1.0",
    description="Language learning through movies"
)

# Enhanced CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # React development
        "http://localhost:8080",      # Expo web
        "http://localhost:8081",      # Expo alternative port
        "http://localhost:19006",     # Expo web default
        "https://*.vercel.app",       # Vercel deployments
        "https://*.railway.app",      # Railway deployments
        "https://cinefluent.com",     # Production domain (when ready)
        # Add your custom domains here
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "User-Agent",
        "X-Requested-With",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=["*"],
)

# Pydantic Models
class Movie(BaseModel):
    id: str
    title: str
    description: str
    duration: int  # minutes
    release_year: int
    difficulty_level: str
    languages: List[str]
    genres: List[str]
    thumbnail_url: str
    video_url: Optional[str] = None
    is_premium: bool = False
    vocabulary_count: int
    imdb_rating: Optional[float] = None

class MovieResponse(BaseModel):
    movies: List[Movie]
    total: int
    page: int
    per_page: int

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenRefresh(BaseModel):
    refresh_token: str

class ProgressUpdate(BaseModel):
    movie_id: str
    progress_percentage: int
    time_watched: int  # seconds
    vocabulary_learned: Optional[int] = 0

class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    native_language: Optional[str] = None
    learning_languages: Optional[List[str]] = None
    learning_goals: Optional[Dict[str, Any]] = None

# Startup event
@app.on_event("startup")
async def startup_event():
    print("🚀 Starting CineFluent API...")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")
    if test_connection():
        print("✅ Database connection established")
    else:
        print("❌ Database connection failed")

# Health Check
@app.get("/")
async def health_check():
    return {
        "status": "healthy", 
        "service": "CineFluent API",
        "version": "0.1.0",
        "database": "connected" if test_connection() else "disconnected",
        "environment": os.getenv("ENVIRONMENT", "production")
    }

@app.get("/api/v1/health")
async def api_health():
    """Detailed health check for monitoring"""
    try:
        # Test database connection
        db_status = test_connection()
        
        # Test Supabase auth (basic check)
        auth_status = True
        try:
            # This won't actually authenticate, but checks if Supabase client works
            supabase.auth.get_session()
        except:
            auth_status = False
        
        return {
            "status": "healthy" if db_status and auth_status else "degraded",
            "checks": {
                "database": "ok" if db_status else "error",
                "auth": "ok" if auth_status else "error"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

# ===== AUTHENTICATION ENDPOINTS =====

@app.post("/api/v1/auth/register")
async def register(user_data: UserRegister):
    """Register a new user account"""
    print(f"Registration attempt for: {user_data.email}")
    
    try:
        result = await create_user_account(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        print(f"Registration successful for: {user_data.email}")
        return result
    except HTTPException as e:
        print(f"Registration failed for {user_data.email}: {e.detail}")
        raise e
    except Exception as e:
        print(f"Registration error for {user_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/api/v1/auth/login")
async def login(user_data: UserLogin):
    """Login user and return access token"""
    print(f"Login attempt for: {user_data.email}")
    
    try:
        result = await sign_in_user(
            email=user_data.email,
            password=user_data.password
        )
        print(f"Login successful for: {user_data.email}")
        return result
    except HTTPException as e:
        print(f"Login failed for {user_data.email}: {e.detail}")
        raise e
    except Exception as e:
        print(f"Login error for {user_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

@app.post("/api/v1/auth/refresh")
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

@app.post("/api/v1/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout user and invalidate session"""
    try:
        if credentials:
            result = await sign_out_user(credentials.credentials)
            return result
        else:
            return {"message": "Successfully signed out"}
    except Exception as e:
        # Always return success for logout
        return {"message": "Successfully signed out"}

@app.get("/api/v1/auth/me")
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

@app.put("/api/v1/auth/profile")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user profile"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in profile_data.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data provided for update")
        
        # Add timestamp
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        response = supabase.table("profiles")\
            .update(update_data)\
            .eq("id", current_user.id)\
            .execute()
        
        if response.data:
            return {"message": "Profile updated successfully", "profile": response.data[0]}
        else:
            # If no rows affected, the profile might not exist
            # Try to create it
            profile_data_with_id = {
                "id": current_user.id,
                "username": current_user.email.split("@")[0],
                **update_data
            }
            
            create_response = supabase.table("profiles")\
                .insert(profile_data_with_id)\
                .execute()
            
            if create_response.data:
                return {"message": "Profile created successfully", "profile": create_response.data[0]}
            else:
                raise HTTPException(status_code=400, detail="Failed to update profile")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Profile update failed: {str(e)}"
        )

# ===== MOVIES API =====

@app.get("/api/v1/movies", response_model=MovieResponse)
async def get_movies(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    language: Optional[str] = None,
    difficulty: Optional[str] = None,
    genre: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get paginated list of movies with optional filters"""
    try:
        # Build query
        query = supabase.table("movies").select("*")
        
        # Apply filters
        if language:
            query = query.contains("languages", [language])
        if difficulty:
            query = query.eq("difficulty_level", difficulty)
        if genre:
            query = query.contains("genres", [genre])
        
        # Handle premium content based on user subscription
        if not current_user:
            query = query.eq("is_premium", False)
        else:
            # Check if user has premium access
            try:
                subscription_response = supabase.table("subscriptions")\
                    .select("plan_type")\
                    .eq("user_id", current_user.id)\
                    .eq("status", "active")\
                    .execute()
                
                has_premium = (subscription_response.data and 
                             subscription_response.data[0]["plan_type"] != "free")
                
                if not has_premium:
                    query = query.eq("is_premium", False)
            except:
                # If subscription check fails, show only free content
                query = query.eq("is_premium", False)
        
        # Get total count first
        count_response = query.execute()
        total = len(count_response.data) if count_response.data else 0
        
        # Apply pagination
        start = (page - 1) * limit
        end = start + limit - 1
        
        paginated_query = query.range(start, end).order("created_at", desc=True)
        response = paginated_query.execute()
        
        movies = [Movie(**movie_data) for movie_data in response.data] if response.data else []
        
        return MovieResponse(
            movies=movies,
            total=total,
            page=page,
            per_page=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch movies: {str(e)}")

@app.get("/api/v1/movies/featured")
async def get_featured_movies(current_user: Optional[User] = Depends(get_optional_user)):
    """Get featured movies for the homepage"""
    try:
        query = supabase.table("movies").select("*")
        
        # Show only free content for non-premium users
        if not current_user:
            query = query.eq("is_premium", False)
        
        response = query.order("imdb_rating", desc=True).limit(6).execute()
        movies = [Movie(**movie_data) for movie_data in response.data] if response.data else []
        
        return {"movies": movies}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch featured movies: {str(e)}")

@app.get("/api/v1/movies/search")
async def search_movies(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Search movies by title or description"""
    try:
        # Use Supabase full-text search
        search_query = f"%{q}%"
        query = supabase.table("movies")\
            .select("*")\
            .or_(f"title.ilike.{search_query},description.ilike.{search_query}")
        
        # Filter premium content for non-premium users
        if not current_user:
            query = query.eq("is_premium", False)
        
        response = query.limit(limit).execute()
        movies = [Movie(**movie_data) for movie_data in response.data] if response.data else []
        
        return {"movies": movies, "query": q, "total": len(movies)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/api/v1/movies/{movie_id}")
async def get_movie(
    movie_id: str,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get detailed information about a specific movie"""
    try:
        response = supabase.table("movies").select("*").eq("id", movie_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        movie_data = response.data[0]
        
        # Check if user can access premium content
        if movie_data["is_premium"] and not current_user:
            raise HTTPException(status_code=403, detail="Premium subscription required")
        
        movie = Movie(**movie_data)
        
        # If user is authenticated, include their progress
        user_progress = None
        if current_user:
            try:
                progress_response = supabase.table("user_progress")\
                    .select("*")\
                    .eq("user_id", current_user.id)\
                    .eq("movie_id", movie_id)\
                    .execute()
                
                if progress_response.data:
                    user_progress = progress_response.data[0]
            except:
                # Don't fail if progress lookup fails
                pass
        
        return {
            "movie": movie,
            "user_progress": user_progress
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch movie: {str(e)}")

# ===== PROGRESS TRACKING =====

@app.post("/api/v1/progress/update")
async def update_progress(
    progress_data: ProgressUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user's learning progress"""
    try:
        # Check if movie exists
        movie_response = supabase.table("movies").select("id").eq("id", progress_data.movie_id).execute()
        if not movie_response.data:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        # Prepare progress update
        progress_update = {
            "user_id": current_user.id,
            "movie_id": progress_data.movie_id,
            "progress_percentage": min(progress_data.progress_percentage, 100),  # Cap at 100%
            "time_watched": progress_data.time_watched,
            "vocabulary_learned": progress_data.vocabulary_learned or 0,
            "last_watched_at": datetime.utcnow().isoformat(),
        }
        
        # Mark as completed if 100%
        if progress_data.progress_percentage >= 100:
            progress_update["completed_at"] = datetime.utcnow().isoformat()
        
        response = supabase.table("user_progress")\
            .upsert(progress_update, on_conflict="user_id,movie_id")\
            .execute()
        
        return {"message": "Progress updated successfully", "progress": response.data[0] if response.data else None}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update progress: {str(e)}")

@app.get("/api/v1/progress/stats")
async def get_progress_stats(current_user: User = Depends(get_current_user)):
    """Get user's learning statistics"""
    try:
        # Get total progress
        progress_response = supabase.table("user_progress")\
            .select("*")\
            .eq("user_id", current_user.id)\
            .execute()
        
        progress_data = progress_response.data if progress_response.data else []
        
        # Calculate stats
        total_movies_watched = len(progress_data)
        completed_movies = len([p for p in progress_data if p.get("completed_at")])
        total_time_watched = sum(p.get("time_watched", 0) for p in progress_data)
        total_vocabulary = sum(p.get("vocabulary_learned", 0) for p in progress_data)
        
        # Calculate average progress
        avg_progress = 0
        if progress_data:
            avg_progress = sum(p.get("progress_percentage", 0) for p in progress_data) / len(progress_data)
        
        return {
            "total_movies_watched": total_movies_watched,
            "completed_movies": completed_movies,
            "total_time_watched": total_time_watched,  # in seconds
            "total_vocabulary_learned": total_vocabulary,
            "average_progress": round(avg_progress, 1),
            "recent_activity": progress_data[-5:] if progress_data else []  # Last 5 activities
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get progress stats: {str(e)}")

# ===== PREMIUM CONTENT =====

@app.get("/api/v1/movies/premium")
async def get_premium_movies(current_user: User = Depends(require_premium_user)):
    """Get premium movies (requires premium subscription)"""
    try:
        response = supabase.table("movies").select("*").eq("is_premium", True).order("created_at", desc=True).execute()
        movies = [Movie(**movie_data) for movie_data in response.data] if response.data else []
        
        return {"movies": movies, "total": len(movies)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch premium movies: {str(e)}")

# ===== METADATA ENDPOINTS =====

@app.get("/api/v1/categories")
async def get_categories():
    """Get all movie categories"""
    try:
        response = supabase.table("categories").select("*").order("sort_order").execute()
        return {"categories": response.data if response.data else []}
        
    except Exception as e:
        # Fallback to hardcoded categories if table doesn't exist
        fallback_categories = [
            {"id": "action", "name": "Action", "sort_order": 1},
            {"id": "drama", "name": "Drama", "sort_order": 2},
            {"id": "comedy", "name": "Comedy", "sort_order": 3},
            {"id": "thriller", "name": "Thriller", "sort_order": 4},
            {"id": "romance", "name": "Romance", "sort_order": 5},
            {"id": "sci-fi", "name": "Science Fiction", "sort_order": 6},
            {"id": "documentary", "name": "Documentary", "sort_order": 7}
        ]
        return {"categories": fallback_categories}

@app.get("/api/v1/languages")
async def get_languages():
    """Get all available languages from movies"""
    try:
        response = supabase.table("movies").select("languages").execute()
        
        all_languages = set()
        if response.data:
            for movie in response.data:
                if movie.get("languages"):
                    all_languages.update(movie["languages"])
        
        # If no languages found, provide fallback
        if not all_languages:
            all_languages = {"en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"}
        
        return {"languages": sorted(list(all_languages))}
        
    except Exception as e:
        # Fallback languages
        fallback_languages = ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
        return {"languages": fallback_languages}

# ===== CORS PREFLIGHT HANDLERS =====

@app.options("/")
async def options_root():
    return {"message": "OK"}

@app.options("/api/v1/{path:path}")
async def options_api(path: str):
    return {"message": "OK"}

# ===== APPLICATION STARTUP =====

if __name__ == "__main__":
    import uvicorn
    
    # Railway provides PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 Starting CineFluent API on port {port}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")
    print(f"CORS origins configured for local development and production")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )