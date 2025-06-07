from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

app = FastAPI(title="CineFluent API", version="0.1.0")

# CORS configuration - Fixed for better browser compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:8081"],
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
    difficulty_level: str  # "Beginner", "Intermediate", "Advanced"
    languages: List[str]
    genres: List[str]
    thumbnail_url: str
    video_url: Optional[str] = None
    is_premium: bool = False
    vocabulary_count: int

class MovieResponse(BaseModel):
    movies: List[Movie]
    total: int
    page: int
    per_page: int

# Sample data
SAMPLE_MOVIES = [
    {
        "id": "1",
        "title": "Amélie",
        "description": "A whimsical French film about a shy waitress who decides to help those around her find happiness.",
        "duration": 122,
        "release_year": 2001,
        "difficulty_level": "Intermediate",
        "languages": ["French", "English"],
        "genres": ["Romance", "Comedy"],
        "thumbnail_url": "https://via.placeholder.com/300x400?text=Amélie",
        "is_premium": False,
        "vocabulary_count": 450
    },
    {
        "id": "2",
        "title": "Roma",
        "description": "A semi-autobiographical film about a domestic worker in 1970s Mexico City.",
        "duration": 135,
        "release_year": 2018,
        "difficulty_level": "Advanced",
        "languages": ["Spanish", "Mixtec"],
        "genres": ["Drama"],
        "thumbnail_url": "https://via.placeholder.com/300x400?text=Roma",
        "is_premium": True,
        "vocabulary_count": 680
    },
    {
        "id": "3",
        "title": "Cinema Paradiso",
        "description": "A filmmaker recalls his childhood when he and the village projectionist formed a deep friendship.",
        "duration": 155,
        "release_year": 1988,
        "difficulty_level": "Intermediate",
        "languages": ["Italian", "English"],
        "genres": ["Drama", "Romance"],
        "thumbnail_url": "https://via.placeholder.com/300x400?text=Cinema+Paradiso",
        "is_premium": False,
        "vocabulary_count": 520
    },
    {
        "id": "4",
        "title": "Your Name",
        "description": "Two teenagers share a profound, magical connection upon discovering they are swapping bodies.",
        "duration": 106,
        "release_year": 2016,
        "difficulty_level": "Beginner",
        "languages": ["Japanese", "English"],
        "genres": ["Animation", "Romance"],
        "thumbnail_url": "https://via.placeholder.com/300x400?text=Your+Name",
        "is_premium": False,
        "vocabulary_count": 320
    }
]

# Health Check
@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "CineFluent API"}

# Movies API
@app.get("/api/v1/movies", response_model=MovieResponse)
async def get_movies(
    page: int = 1,
    limit: int = 20,
    language: Optional[str] = None,
    difficulty: Optional[str] = None,
    genre: Optional[str] = None
):
    """Get paginated list of movies with optional filters"""
    filtered_movies = SAMPLE_MOVIES.copy()
    
    # Apply filters
    if language:
        filtered_movies = [m for m in filtered_movies if language in m["languages"]]
    if difficulty:
        filtered_movies = [m for m in filtered_movies if m["difficulty_level"] == difficulty]
    if genre:
        filtered_movies = [m for m in filtered_movies if genre in m["genres"]]
    
    # Pagination
    start = (page - 1) * limit
    end = start + limit
    paginated_movies = filtered_movies[start:end]
    
    # Convert to Movie objects
    movies = [Movie(**movie_data) for movie_data in paginated_movies]
    
    return MovieResponse(
        movies=movies,
        total=len(filtered_movies),
        page=page,
        per_page=limit
    )

@app.get("/api/v1/movies/featured")
async def get_featured_movies():
    """Get featured movies for the homepage"""
    # Return first 3 movies as featured
    featured_data = SAMPLE_MOVIES[:3]
    movies = [Movie(**movie_data) for movie_data in featured_data]
    return {"movies": movies}

@app.get("/api/v1/movies/search")
async def search_movies(q: str, limit: int = 10):
    """Search movies by title or description"""
    if not q:
        return {"movies": [], "query": ""}
    
    query = q.lower()
    results = []
    
    for movie_data in SAMPLE_MOVIES:
        if query in movie_data["title"].lower() or query in movie_data["description"].lower():
            results.append(Movie(**movie_data))
    
    return {"movies": results[:limit], "query": q}

@app.get("/api/v1/movies/{movie_id}")
async def get_movie(movie_id: str):
    """Get detailed information about a specific movie"""
    movie_data = next((m for m in SAMPLE_MOVIES if m["id"] == movie_id), None)
    if not movie_data:
        raise HTTPException(status_code=404, detail="Movie not found")
    return Movie(**movie_data)

# Add explicit OPTIONS handlers to fix CORS
@app.options("/")
async def options_root():
    return {"message": "OK"}

@app.options("/api/v1/{path:path}")
async def options_api(path: str):
    return {"message": "OK"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)