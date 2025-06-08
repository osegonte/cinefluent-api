from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import os
import json

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
    description="Language learning through movies - Railway Deployment"
)

# Enhanced CORS configuration for Railway
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # React development
        "http://localhost:8080",      # Expo web
        "http://localhost:8081",      # Expo alternative port
        "http://localhost:19006",     # Expo web default
        "https://*.vercel.app",       # Vercel deployments
        "https://*.railway.app",      # Railway deployments
        "https://*.up.railway.app",   # Railway custom domains
        "https://cinefluent.com",     # Production domain
        "https://www.cinefluent.com", # Production domain with www
        "*"  # Allow all for now - restrict in production
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
    languages: List[str]  # Will be converted from JSONB
    genres: List[str]     # Will be converted from JSONB
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

# Helper function to convert JSONB to Python lists
def convert_movie_data(movie_data: Dict) -> Dict:
    """Convert JSONB fields to Python lists for Movie model"""
    # Convert languages and genres from JSONB to lists
    if isinstance(movie_data.get('languages'), str):
        try:
            movie_data['languages'] = json.loads(movie_data['languages'])
        except:
            movie_data['languages'] = []
    elif movie_data.get('languages') is None:
        movie_data['languages'] = []
    
    if isinstance(movie_data.get('genres'), str):
        try:
            movie_data['genres'] = json.loads(movie_data['genres'])
        except:
            movie_data['genres'] = []
    elif movie_data.get('genres') is None:
        movie_data['genres'] = []
    
    return movie_data

# Startup event
@app.on_event("startup")
async def startup_event():
    print("🚀 Starting CineFluent API on Railway...")
    print(f"Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'development')}")
    print(f"Service: {os.getenv('RAILWAY_SERVICE_NAME', 'cinefluent-api')}")
    
    if test_connection():
        print("✅ Database connection established")
    else:
        print("❌ Database connection failed - check environment variables")

# Health Check
@app.get("/")
async def root():
    return {
        "status": "healthy", 
        "service": "CineFluent API",
        "version": "0.1.0",
        "environment": os.getenv('RAILWAY_ENVIRONMENT', 'development'),
        "database": "connected" if test_connection() else "disconnected",
        "deployment": "railway"
    }

@app.get("/api/v1/health")
async def health_check():
    """Detailed health check for monitoring"""
    try:
        # Test database connection
        db_status = test_connection()
        
        # Test Supabase auth
        auth_status = True
        try:
            supabase.auth.get_session()
        except Exception as e:
            print(f"Auth test failed: {e}")
            auth_status = False
        
        return {
            "status": "healthy" if db_status and auth_status else "degraded",
            "service": "CineFluent API",
            "version": "0.1.0",
            "checks": {
                "database": "ok" if db_status else "error",
                "auth": "ok" if auth_status else "error"
            },
            "environment": {
                "railway_env": os.getenv('RAILWAY_ENVIRONMENT'),
                "service_name": os.getenv('RAILWAY_SERVICE_NAME'),
                "git_commit": os.getenv('RAILWAY_GIT_COMMIT_SHA', 'unknown')[:8]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"Health check error: {e}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

# Debug endpoint for Railway deployment
@app.get("/debug")
async def debug_info():
    """Debug endpoint to check Railway deployment"""
    return {
        "files": os.listdir("."),
        "current_time": datetime.utcnow().isoformat(),
        "environment_vars": {
            "RAILWAY_ENVIRONMENT": os.environ.get("RAILWAY_ENVIRONMENT"),
            "RAILWAY_SERVICE_NAME": os.environ.get("RAILWAY_SERVICE_NAME"),
            "RAILWAY_GIT_COMMIT_SHA": os.environ.get("RAILWAY_GIT_COMMIT_SHA", "unknown")[:8],
            "PORT": os.environ.get("PORT"),
            "SUPABASE_URL_SET": bool(os.environ.get("SUPABASE_URL")),
            "DATABASE_URL_SET": bool(os.environ.get("DATABASE_URL"))
        }
    }

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
        
        # Convert learning_languages to JSONB if provided
        if 'learning_languages' in update_data:
            update_data['learning_languages'] = json.dumps(update_data['learning_languages'])
        
        # Convert learning_goals to JSONB if provided
        if 'learning_goals' in update_data:
            update_data['learning_goals'] = json.dumps(update_data['learning_goals'])
        
        # Add timestamp
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        response = supabase.table("profiles")\
            .update(update_data)\
            .eq("id", current_user.id)\
            .execute()
        
        if response.data:
            return {"message": "Profile updated successfully", "profile": response.data[0]}
        else:
            # If no rows affected, create profile
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
        
        # Apply filters using JSONB operators
        if language:
            # Use JSONB contains operator for language filtering
            query = query.contains("languages", [language])
        if difficulty:
            query = query.eq("difficulty_level", difficulty)
        if genre:
            # Use JSONB contains operator for genre filtering
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
        
        # Convert JSONB fields to lists for Movie model
        movies = []
        for movie_data in response.data or []:
            converted_data = convert_movie_data(movie_data)
            movies.append(Movie(**converted_data))
        
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
        
        # Convert JSONB fields to lists
        movies = []
        for movie_data in response.data or []:
            converted_data = convert_movie_data(movie_data)
            movies.append(Movie(**converted_data))
        
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
            .or_(f"title.ilike.%{q}%,description.ilike.%{q}%")
        
        # Filter premium content for non-premium users
        if not current_user:
            query = query.eq("is_premium", False)
        
        response = query.limit(limit).execute()
        
        # Convert JSONB fields to lists
        movies = []
        for movie_data in response.data or []:
            converted_data = convert_movie_data(movie_data)
            movies.append(Movie(**converted_data))
        
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
        
        movie_data = convert_movie_data(response.data[0])
        
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
            "progress_percentage": min(progress_data.progress_percentage, 100),
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
            "total_time_watched": total_time_watched,
            "total_vocabulary_learned": total_vocabulary,
            "average_progress": round(avg_progress, 1),
            "recent_activity": progress_data[-5:] if progress_data else []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get progress stats: {str(e)}")

# ===== METADATA ENDPOINTS =====

@app.get("/api/v1/categories")
async def get_categories():
    """Get all movie categories"""
    try:
        response = supabase.table("categories").select("*").order("sort_order").execute()
        return {"categories": response.data if response.data else []}
        
    except Exception as e:
        # Fallback to hardcoded categories
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
                languages = movie.get("languages")
                if languages:
                    # Handle both JSONB and string formats
                    if isinstance(languages, str):
                        try:
                            languages = json.loads(languages)
                        except:
                            continue
                    if isinstance(languages, list):
                        all_languages.update(languages)
        
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

# ===== TEST ENDPOINTS FOR DEVELOPMENT =====

@app.get("/api/v1/test")
async def test_endpoint():
    """Test endpoint to verify deployment"""
    return {
        "message": "CineFluent API is working!",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "environment": os.getenv('RAILWAY_ENVIRONMENT', 'development')
    }

@app.get("/api/v1/test/database")
async def test_database():
    """Test database connectivity"""
    try:
        # Test basic query
        response = supabase.table("movies").select("id").limit(1).execute()
        
        return {
            "database": "connected",
            "tables_accessible": True,
            "sample_data": len(response.data) > 0 if response.data else False,
            "message": "Database is working correctly"
        }
    except Exception as e:
        return {
            "database": "error",
            "tables_accessible": False,
            "error": str(e),
            "message": "Database connection failed"
        }

@app.get("/api/v1/test/auth")
async def test_auth(current_user: Optional[User] = Depends(get_optional_user)):
    """Test authentication without requiring login"""
    if current_user:
        return {
            "authenticated": True,
            "user_id": current_user.id,
            "email": current_user.email,
            "message": "Authentication is working"
        }
    else:
        return {
            "authenticated": False,
            "message": "No authentication provided (this is expected for this test)"
        }

# ===== APPLICATION STARTUP =====

if __name__ == "__main__":
    import uvicorn
    
    # Railway provides PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"🚀 Starting CineFluent API")
    print(f"📍 Host: {host}:{port}")
    print(f"🌍 Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'development')}")
    print(f"🔧 Service: {os.getenv('RAILWAY_SERVICE_NAME', 'cinefluent-api')}")
    
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        log_level="info"
    )