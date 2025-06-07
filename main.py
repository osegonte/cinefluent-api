from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

# Import our modules
from database import supabase, test_connection
from auth import (
    get_current_user, get_current_user_profile, get_optional_user, 
    require_premium_user, create_user_account, sign_in_user,
    User, UserProfile
)

app = FastAPI(title="CineFluent API", version="0.1.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080", 
        "http://localhost:8081",
        "http://localhost:3000",
        "https://*.vercel.app",
        # Add your production domains here
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
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

class ProgressUpdate(BaseModel):
    movie_id: str
    progress_percentage: int
    time_watched: int  # seconds
    vocabulary_learned: Optional[int] = 0

# Startup event
@app.on_event("startup")
async def startup_event():
    print("🚀 Starting CineFluent API...")
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
        "database": "connected" if test_connection() else "disconnected"
    }

# Authentication Endpoints
@app.post("/api/v1/auth/register")
async def register(user_data: UserRegister):
    """Register a new user"""
    return await create_user_account(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )

@app.post("/api/v1/auth/login")
async def login(user_data: UserLogin):
    """Login user"""
    return await sign_in_user(
        email=user_data.email,
        password=user_data.password
    )

@app.get("/api/v1/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    profile = await get_current_user_profile(current_user)
    return {
        "user": current_user,
        "profile": profile
    }

@app.put("/api/v1/auth/profile")
async def update_profile(
    profile_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Update user profile"""
    try:
        response = supabase.table("profiles")\
            .update(profile_data)\
            .eq("id", current_user.id)\
            .execute()
        
        if response.data:
            return {"message": "Profile updated successfully", "profile": response.data[0]}
        else:
            raise HTTPException(status_code=400, detail="Failed to update profile")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

# Movies API with Database Integration
@app.get("/api/v1/movies", response_model=MovieResponse)
async def get_movies(
    page: int = 1,
    limit: int = 20,
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
        
        # Get total count
        count_response = query.execute()
        total = len(count_response.data) if count_response.data else 0
        
        # Apply pagination
        start = (page - 1) * limit
        end = start + limit - 1
        
        paginated_query = query.range(start, end)
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
        
        response = query.limit(6).execute()
        movies = [Movie(**movie_data) for movie_data in response.data] if response.data else []
        
        return {"movies": movies}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch featured movies: {str(e)}")

@app.get("/api/v1/movies/search")
async def search_movies(
    q: str = Query(..., min_length=1),
    limit: int = 10,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Search movies by title or description"""
    try:
        # Use Supabase full-text search
        query = supabase.table("movies")\
            .select("*")\
            .or_(f"title.ilike.%{q}%,description.ilike.%{q}%")
        
        # Filter premium content for non-premium users
        if not current_user:
            query = query.eq("is_premium", False)
        
        response = query.limit(limit).execute()
        movies = [Movie(**movie_data) for movie_data in response.data] if response.data else []
        
        return {"movies": movies, "query": q}
        
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
            progress_response = supabase.table("user_progress")\
                .select("*")\
                .eq("user_id", current_user.id)\
                .eq("movie_id", movie_id)\
                .execute()
            
            if progress_response.data:
                user_progress = progress_response.data[0]
        
        return {
            "movie": movie,
            "user_progress": user_progress
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch movie: {str(e)}")

# Progress Tracking
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
        
        # Upsert progress
        progress_update = {
            "user_id": current_user.id,
            "movie_id": progress_data.movie_id,
            "progress_percentage": progress_data.progress_percentage,
            "time_watched": progress_data.time_watched,
            "vocabulary_learned": progress_data.vocabulary_learned,
            "last_watched_at": datetime.utcnow().isoformat(),
        }
        
        # Mark as completed if 100%
        if progress_data.progress_percentage >= 100:
            progress_update["completed_at"] = datetime.utcnow().isoformat()
        
        response = supabase.table("user_progress")\
            .upsert(progress_update, on_conflict="user_id,movie_id")\
            .execute()
        
        return {"message": "Progress updated successfully", "progress": response.data[0]}
        
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
        
        # Get streak info
        streak_response = supabase.table("user_streaks")\
            .select("*")\
            .eq("user_id", current_user.id)\
            .execute()
        
        streak_data = streak_response.data[0] if streak_response.data else {
            "current_streak": 0,
            "longest_streak": 0
        }
        
        return {
            "total_movies_watched": total_movies_watched,
            "completed_movies": completed_movies,
            "total_time_watched": total_time_watched,  # in seconds
            "total_vocabulary_learned": total_vocabulary,
            "current_streak": streak_data.get("current_streak", 0),
            "longest_streak": streak_data.get("longest_streak", 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get progress stats: {str(e)}")

# Premium content endpoint
@app.get("/api/v1/movies/premium")
async def get_premium_movies(current_user: User = Depends(require_premium_user)):
    """Get premium movies (requires premium subscription)"""
    try:
        response = supabase.table("movies").select("*").eq("is_premium", True).execute()
        movies = [Movie(**movie_data) for movie_data in response.data] if response.data else []
        
        return {"movies": movies}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch premium movies: {str(e)}")

# Categories endpoint
@app.get("/api/v1/categories")
async def get_categories():
    """Get all movie categories"""
    try:
        response = supabase.table("categories").select("*").order("sort_order").execute()
        return {"categories": response.data if response.data else []}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch categories: {str(e)}")

# Available languages endpoint
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
        
        return {"languages": sorted(list(all_languages))}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch languages: {str(e)}")

# Add explicit OPTIONS handlers for CORS
@app.options("/")
async def options_root():
    return {"message": "OK"}

@app.options("/api/v1/{path:path}")
async def options_api(path: str):
    return {"message": "OK"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)