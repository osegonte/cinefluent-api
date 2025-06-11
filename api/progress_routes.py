"""
CineFluent Progress Routes
Handles user learning progress and statistics
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Import from project root
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import supabase
from auth import get_current_user, User

router = APIRouter(prefix="/api/v1/progress", tags=["progress"])

class ProgressUpdate(BaseModel):
    movie_id: str
    progress_percentage: int
    time_watched: int  # seconds
    vocabulary_learned: Optional[int] = 0

@router.post("/update")
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
        
        return {
            "message": "Progress updated successfully", 
            "progress": response.data[0] if response.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update progress: {str(e)}")

@router.get("/stats")
async def get_progress_stats(current_user: User = Depends(get_current_user)):
    """Get user's learning statistics"""
    try:
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
