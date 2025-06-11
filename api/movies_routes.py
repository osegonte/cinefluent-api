"""
CineFluent Movies Routes
Handles movie catalog, search, and metadata
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json

# Import from project root
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import supabase
from auth import get_optional_user, User

router = APIRouter(prefix="/api/v1/movies", tags=["movies"])

# Pydantic models
class Movie(BaseModel):
    id: str
    title: str
    description: str
    duration: int
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

def convert_movie_data(movie_data: Dict) -> Dict:
    """Convert JSONB fields to Python lists for Movie model"""
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

@router.get("", response_model=MovieResponse)
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
        query = supabase.table("movies").select("*")
        
        # Apply filters
        if language:
            query = query.contains("languages", [language])
        if difficulty:
            query = query.eq("difficulty_level", difficulty)
        if genre:
            query = query.contains("genres", [genre])
        
        # Handle premium content
        if not current_user:
            query = query.eq("is_premium", False)
        
        # Get total count
        count_response = query.execute()
        total = len(count_response.data) if count_response.data else 0
        
        # Apply pagination
        start = (page - 1) * limit
        end = start + limit - 1
        
        paginated_query = query.range(start, end).order("created_at", desc=True)
        response = paginated_query.execute()
        
        # Convert JSONB fields
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

@router.get("/featured")
async def get_featured_movies(current_user: Optional[User] = Depends(get_optional_user)):
    """Get featured movies for the homepage"""
    try:
        query = supabase.table("movies").select("*")
        
        if not current_user:
            query = query.eq("is_premium", False)
        
        response = query.order("imdb_rating", desc=True).limit(6).execute()
        
        movies = []
        for movie_data in response.data or []:
            converted_data = convert_movie_data(movie_data)
            movies.append(Movie(**converted_data))
        
        return {"movies": movies}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch featured movies: {str(e)}")

@router.get("/search")
async def search_movies(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Search movies by title or description"""
    try:
        query = supabase.table("movies")\
            .select("*")\
            .or_(f"title.ilike.%{q}%,description.ilike.%{q}%")
        
        if not current_user:
            query = query.eq("is_premium", False)
        
        response = query.limit(limit).execute()
        
        movies = []
        for movie_data in response.data or []:
            converted_data = convert_movie_data(movie_data)
            movies.append(Movie(**converted_data))
        
        return {"movies": movies, "query": q, "total": len(movies)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/{movie_id}")
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
        
        if movie_data["is_premium"] and not current_user:
            raise HTTPException(status_code=403, detail="Premium subscription required")
        
        movie = Movie(**movie_data)
        
        # Include user progress if authenticated
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
