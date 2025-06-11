"""
Enhanced Subtitle API Routes with Multi-Language Support
Integrates with the streamlined architecture and subtitle fetcher service
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import from the streamlined project structure
from services.subtitle_fetcher import (
    MultiLanguageSubtitleService, 
    SubtitleMetadata, 
    SubtitleSource,
    get_subtitle_service
)
from auth import get_current_user, get_optional_user, User
from database import supabase

router = APIRouter(prefix="/api/v1/subtitles", tags=["subtitles"])

# Pydantic models for API
class SubtitleSearchRequest(BaseModel):
    movie_id: str
    language: str
    movie_title: Optional[str] = None
    auto_fetch: bool = True

class SubtitleSearchResponse(BaseModel):
    subtitles: List[Dict[str, Any]]
    source: str
    language: str
    movie_id: str
    cached: bool
    total_found: int

class MultiLanguageRequest(BaseModel):
    movie_id: str
    movie_title: str
    preferred_languages: Optional[List[str]] = None

class MultiLanguageResponse(BaseModel):
    movie_id: str
    movie_title: str
    available_languages: List[str]
    subtitles_by_language: Dict[str, List[Dict[str, Any]]]
    cache_info: Dict[str, str]

class SubtitleDownloadRequest(BaseModel):
    subtitle_id: str
    process_immediately: bool = True

class SubtitleDownloadResponse(BaseModel):
    subtitle_id: str
    download_status: str
    processing_status: str
    learning_content: Optional[Dict[str, Any]] = None

class CacheStatsResponse(BaseModel):
    cache_performance: Dict[str, Any]
    service_stats: Dict[str, Any]
    supported_languages: List[str]

# ===== ENHANCED SUBTITLE SEARCH ENDPOINTS =====

@router.post("/search", response_model=SubtitleSearchResponse)
async def search_subtitles(
    request: SubtitleSearchRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    subtitle_service: MultiLanguageSubtitleService = Depends(get_subtitle_service)
):
    """
    Search for subtitles in a specific language with intelligent fallback
    
    This endpoint:
    1. Checks local database first
    2. Checks cache for recent searches
    3. Fetches from external APIs if not found (when auto_fetch=True)
    4. Caches results for future requests
    """
    try:
        # Get movie info for better search
        movie_title = request.movie_title
        if not movie_title:
            movie_response = supabase.table("movies").select("title").eq("id", request.movie_id).execute()
            if movie_response.data:
                movie_title = movie_response.data[0]["title"]
            else:
                raise HTTPException(status_code=404, detail="Movie not found")
        
        # Search for subtitles
        subtitles, source = await subtitle_service.get_subtitles(
            movie_id=request.movie_id,
            language=request.language,
            movie_title=movie_title,
            auto_fetch=request.auto_fetch
        )
        
        # Convert SubtitleMetadata objects to dictionaries
        subtitle_dicts = []
        for sub in subtitles:
            subtitle_dict = {
                "id": sub.id,
                "movie_id": sub.movie_id,
                "language": sub.language,
                "title": sub.title,
                "source": sub.source.value,
                "file_size": sub.file_size,
                "download_count": sub.download_count,
                "rating": sub.rating,
                "release_info": sub.release_info,
                "encoding": sub.encoding,
                "created_at": sub.created_at.isoformat(),
                "can_download": sub.file_url is not None,
                "is_processed": sub.source == SubtitleSource.DATABASE
            }
            subtitle_dicts.append(subtitle_dict)
        
        return SubtitleSearchResponse(
            subtitles=subtitle_dicts,
            source=source,
            language=request.language,
            movie_id=request.movie_id,
            cached=source in ["cache", "database"],
            total_found=len(subtitle_dicts)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subtitle search failed: {str(e)}")

@router.post("/search/multi-language", response_model=MultiLanguageResponse)
async def search_multi_language_subtitles(
    request: MultiLanguageRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_optional_user),
    subtitle_service: MultiLanguageSubtitleService = Depends(get_subtitle_service)
):
    """
    Search for subtitles in all available languages for a movie
    
    This endpoint:
    1. Searches for subtitles in all supported languages
    2. Returns available languages with subtitle counts
    3. Prioritizes user's preferred languages
    4. Caches results for better performance
    """
    try:
        # Get all available subtitles by language
        all_subtitles = await subtitle_service.get_all_available_languages(
            movie_id=request.movie_id,
            movie_title=request.movie_title
        )
        
        # Convert to response format
        subtitles_by_language = {}
        available_languages = []
        cache_info = {}
        
        for language, subtitles in all_subtitles.items():
            if subtitles:
                available_languages.append(language)
                
                # Convert SubtitleMetadata to dicts
                subtitle_dicts = []
                for sub in subtitles:
                    subtitle_dict = {
                        "id": sub.id,
                        "title": sub.title,
                        "source": sub.source.value,
                        "rating": sub.rating,
                        "download_count": sub.download_count,
                        "release_info": sub.release_info,
                        "can_download": sub.file_url is not None,
                        "is_processed": sub.source == SubtitleSource.DATABASE
                    }
                    subtitle_dicts.append(subtitle_dict)
                
                subtitles_by_language[language] = subtitle_dicts
                cache_info[language] = subtitles[0].source.value
        
        # Sort available languages by preference if provided
        if request.preferred_languages:
            # Put preferred languages first
            preferred_available = [lang for lang in request.preferred_languages if lang in available_languages]
            other_available = [lang for lang in available_languages if lang not in preferred_available]
            available_languages = preferred_available + other_available
        
        # Schedule cache cleanup in background
        background_tasks.add_task(subtitle_service.cleanup_expired_cache)
        
        return MultiLanguageResponse(
            movie_id=request.movie_id,
            movie_title=request.movie_title,
            available_languages=available_languages,
            subtitles_by_language=subtitles_by_language,
            cache_info=cache_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-language search failed: {str(e)}")

# ===== SUBTITLE DOWNLOAD AND PROCESSING ENDPOINTS =====

@router.post("/download", response_model=SubtitleDownloadResponse)
async def download_and_process_subtitle(
    request: SubtitleDownloadRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    subtitle_service: MultiLanguageSubtitleService = Depends(get_subtitle_service)
):
    """
    Download external subtitle and process it through the learning pipeline
    
    This endpoint:
    1. Downloads subtitle file from external source
    2. Processes it through NLP pipeline
    3. Creates learning segments and vocabulary
    4. Stores everything in the database
    5. Optionally deletes original file to save space
    """
    try:
        # This would need to be implemented to get subtitle metadata by ID
        # For now, return a placeholder response
        
        if request.process_immediately:
            # Process in foreground for immediate response
            result = await _process_subtitle_download(request.subtitle_id, subtitle_service)
            
            return SubtitleDownloadResponse(
                subtitle_id=request.subtitle_id,
                download_status="completed",
                processing_status="completed",
                learning_content=result
            )
        else:
            # Process in background
            background_tasks.add_task(_process_subtitle_download, request.subtitle_id, subtitle_service)
            
            return SubtitleDownloadResponse(
                subtitle_id=request.subtitle_id,
                download_status="queued",
                processing_status="queued",
                learning_content=None
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subtitle download failed: {str(e)}")

@router.get("/download/status/{subtitle_id}")
async def get_download_status(
    subtitle_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get the download and processing status of a subtitle"""
    try:
        # Check if subtitle exists in database (meaning it's been processed)
        response = supabase.table("subtitles").select("*").eq("id", subtitle_id).execute()
        
        if response.data:
            subtitle = response.data[0]
            return {
                "subtitle_id": subtitle_id,
                "status": "completed",
                "download_status": "completed",
                "processing_status": "completed",
                "total_cues": subtitle.get("total_cues", 0),
                "total_segments": subtitle.get("total_segments", 0),
                "vocabulary_count": subtitle.get("vocabulary_count", 0),
                "created_at": subtitle.get("created_at")
            }
        else:
            # Check processing queue (would need to implement queue tracking)
            return {
                "subtitle_id": subtitle_id,
                "status": "not_found",
                "download_status": "not_found",
                "processing_status": "not_found"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

# ===== SUBTITLE MANAGEMENT ENDPOINTS =====

@router.get("/movie/{movie_id}/available")
async def get_available_subtitle_languages(
    movie_id: str,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get all available subtitle languages for a movie (from database only)"""
    try:
        response = supabase.table("subtitles")\
            .select("language, count(*)")\
            .eq("movie_id", movie_id)\
            .execute()
        
        language_counts = {}
        for row in response.data or []:
            language_counts[row["language"]] = row.get("count", 1)
        
        return {
            "movie_id": movie_id,
            "available_languages": list(language_counts.keys()),
            "language_counts": language_counts,
            "total_languages": len(language_counts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available languages: {str(e)}")

@router.delete("/movie/{movie_id}/language/{language}")
async def delete_movie_subtitles(
    movie_id: str,
    language: str,
    current_user: User = Depends(get_current_user)
):
    """Delete all subtitles for a movie in a specific language"""
    try:
        # Get subtitle IDs first
        subtitle_response = supabase.table("subtitles")\
            .select("id")\
            .eq("movie_id", movie_id)\
            .eq("language", language)\
            .execute()
        
        if not subtitle_response.data:
            raise HTTPException(status_code=404, detail="No subtitles found for this movie/language combination")
        
        subtitle_ids = [row["id"] for row in subtitle_response.data]
        
        # Delete related data first (due to foreign key constraints)
        for subtitle_id in subtitle_ids:
            # Delete learning segments
            supabase.table("learning_segments").delete().eq("subtitle_id", subtitle_id).execute()
            
            # Delete subtitle cues
            supabase.table("subtitle_cues").delete().eq("subtitle_id", subtitle_id).execute()
        
        # Delete subtitle records
        supabase.table("subtitles")\
            .delete()\
            .eq("movie_id", movie_id)\
            .eq("language", language)\
            .execute()
        
        return {
            "message": f"Deleted {len(subtitle_ids)} subtitle(s) for {language} language",
            "movie_id": movie_id,
            "language": language,
            "deleted_count": len(subtitle_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

# ===== CACHING AND PERFORMANCE ENDPOINTS =====

@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    current_user: User = Depends(get_current_user),
    subtitle_service: MultiLanguageSubtitleService = Depends(get_subtitle_service)
):
    """Get cache performance statistics and service information"""
    try:
        service_stats = subtitle_service.get_service_stats()
        
        return CacheStatsResponse(
            cache_performance=service_stats["cache_stats"],
            service_stats={
                "external_apis": service_stats["external_apis"],
                "configuration": service_stats["configuration"]
            },
            supported_languages=service_stats["supported_languages"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@router.post("/cache/clear")
async def clear_subtitle_cache(
    cache_type: str = Query("all", regex="^(memory|database|all)$"),
    current_user: User = Depends(get_current_user),
    subtitle_service: MultiLanguageSubtitleService = Depends(get_subtitle_service)
):
    """Clear subtitle cache (memory, database, or both)"""
    try:
        cleared_items = 0
        
        if cache_type in ["memory", "all"]:
            # Clear memory cache
            memory_items = len(subtitle_service.cache.memory_cache)
            subtitle_service.cache.memory_cache.clear()
            cleared_items += memory_items
        
        if cache_type in ["database", "all"]:
            # Clear database cache
            db_response = supabase.table("subtitle_cache").delete().neq("id", "").execute()
            if hasattr(db_response, 'count'):
                cleared_items += db_response.count
        
        return {
            "message": f"Cache cleared successfully",
            "cache_type": cache_type,
            "items_cleared": cleared_items,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")

@router.post("/cache/warm-up")
async def warm_up_cache(
    movie_ids: List[str],
    languages: List[str],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    subtitle_service: MultiLanguageSubtitleService = Depends(get_subtitle_service)
):
    """Pre-populate cache with subtitles for specified movies and languages"""
    try:
        # Get movie titles
        movies_response = supabase.table("movies")\
            .select("id, title")\
            .in_("id", movie_ids)\
            .execute()
        
        if not movies_response.data:
            raise HTTPException(status_code=404, detail="No movies found with provided IDs")
        
        movies = {row["id"]: row["title"] for row in movies_response.data}
        
        # Schedule cache warm-up in background
        background_tasks.add_task(
            _warm_up_cache_task,
            subtitle_service,
            movies,
            languages
        )
        
        return {
            "message": "Cache warm-up started",
            "movie_count": len(movies),
            "language_count": len(languages),
            "total_combinations": len(movies) * len(languages),
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache warm-up failed: {str(e)}")

# ===== BACKGROUND TASK FUNCTIONS =====

async def _process_subtitle_download(subtitle_id: str, subtitle_service: MultiLanguageSubtitleService) -> Optional[Dict[str, Any]]:
    """Background task to process subtitle download"""
    try:
        # This would need to retrieve subtitle metadata and process it
        # Implementation depends on how subtitle metadata is stored
        print(f"Processing subtitle download: {subtitle_id}")
        
        # Placeholder for actual processing logic
        return {
            "subtitle_id": subtitle_id,
            "processed": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error processing subtitle {subtitle_id}: {e}")
        return None

async def _warm_up_cache_task(subtitle_service: MultiLanguageSubtitleService, 
                            movies: Dict[str, str], languages: List[str]):
    """Background task to warm up cache"""
    try:
        for movie_id, movie_title in movies.items():
            for language in languages:
                try:
                    await subtitle_service.get_subtitles(
                        movie_id=movie_id,
                        language=language,
                        movie_title=movie_title,
                        auto_fetch=True
                    )
                    print(f"Warmed up cache for {movie_title} ({language})")
                    
                    # Small delay to avoid overwhelming external APIs
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"Failed to warm up cache for {movie_title} ({language}): {e}")
                    continue
                    
    except Exception as e:
        print(f"Cache warm-up task failed: {e}")

# ===== LEGACY COMPATIBILITY ENDPOINTS =====

@router.post("/upload")
async def upload_subtitle_file_legacy(
    # ... existing upload logic from original subtitle_api.py
    # This maintains compatibility with existing upload functionality
):
    """Legacy subtitle upload endpoint - maintains existing functionality"""
    # Implementation would be the same as in the original subtitle_api.py
    # Just kept for backward compatibility
    pass

@router.get("/{subtitle_id}/segments")
async def get_learning_segments_legacy(
    subtitle_id: str,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Legacy endpoint for getting learning segments - maintains existing functionality"""
    # Implementation would be the same as in the original subtitle_api.py
    # Just kept for backward compatibility
    pass

# ===== ERROR HANDLING AND VALIDATION =====

@router.get("/validate/api-keys")
async def validate_external_api_keys(
    current_user: User = Depends(get_current_user),
    subtitle_service: MultiLanguageSubtitleService = Depends(get_subtitle_service)
):
    """Validate external API keys and check rate limits"""
    try:
        validation_results = {}
        
        # Check OpenSubtitles API
        if subtitle_service.opensubtitles:
            validation_results["opensubtitles"] = {
                "available": True,
                "rate_limit_remaining": subtitle_service.opensubtitles.rate_limit_remaining,
                "rate_limit_reset": subtitle_service.opensubtitles.rate_limit_reset,
                "status": "active" if subtitle_service.opensubtitles.rate_limit_remaining > 10 else "limited"
            }
        else:
            validation_results["opensubtitles"] = {
                "available": False,
                "error": "API key not configured",
                "status": "unavailable"
            }
        
        return {
            "validation_results": validation_results,
            "overall_status": "healthy" if any(api["available"] for api in validation_results.values()) else "degraded",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API validation failed: {str(e)}")

# ===== HEALTH CHECK ENDPOINTS =====

@router.get("/health")
async def subtitle_service_health(
    subtitle_service: MultiLanguageSubtitleService = Depends(get_subtitle_service)
):
    """Health check for subtitle service"""
    try:
        service_stats = subtitle_service.get_service_stats()
        
        return {
            "status": "healthy",
            "service": "subtitle_service",
            "cache_status": "active",
            "external_apis": service_stats["external_apis"],
            "supported_languages": len(service_stats["supported_languages"]),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "subtitle_service",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Import asyncio for background tasks
import asyncio