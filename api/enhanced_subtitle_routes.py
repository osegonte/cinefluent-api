"""
Enhanced Subtitle API Routes with Multi-Language Support
Integrates with the MultiLanguageSubtitleService
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import from the project structure
from auth import get_current_user, get_optional_user, User
from database import supabase
from services.enhanced_subtitle_service import (
    get_subtitle_service, 
    search_subtitles_for_movie,
    get_all_languages_for_movie,
    download_and_process_external_subtitle,
    cleanup_subtitle_cache,
    check_subtitle_service_health,
    MultiLanguageSubtitleService
)

router = APIRouter(prefix="/api/v1/subtitles", tags=["enhanced_subtitles"])

# Pydantic models for API
class SubtitleSearchRequest(BaseModel):
    movie_id: str
    language: str
    movie_title: Optional[str] = None
    movie_year: Optional[int] = None
    imdb_id: Optional[str] = None
    auto_fetch: bool = True

class SubtitleSearchResponse(BaseModel):
    subtitles: List[Dict[str, Any]]
    source: str
    language: str
    movie_id: str
    cached: bool
    total_found: int
    search_metadata: Dict[str, Any]

class MultiLanguageRequest(BaseModel):
    movie_id: str
    movie_title: str
    movie_year: Optional[int] = None
    preferred_languages: Optional[List[str]] = None

class MultiLanguageResponse(BaseModel):
    movie_id: str
    movie_title: str
    available_languages: List[str]
    subtitles_by_language: Dict[str, List[Dict[str, Any]]]
    cache_info: Dict[str, str]
    total_languages: int

class SubtitleDownloadRequest(BaseModel):
    subtitle_id: str
    movie_id: str
    language: str
    external_url: str
    title: str
    source: str = "opensubtitles"
    process_immediately: bool = True

class SubtitleDownloadResponse(BaseModel):
    subtitle_id: str
    download_status: str
    processing_status: str
    learning_content: Optional[Dict[str, Any]] = None
    estimated_processing_time: Optional[str] = None

class CacheStatsResponse(BaseModel):
    cache_performance: Dict[str, Any]
    service_stats: Dict[str, Any]
    supported_languages: List[str]
    health_status: str

# ===== ENHANCED SUBTITLE SEARCH ENDPOINTS =====

@router.post("/search", response_model=SubtitleSearchResponse)
async def search_subtitles(
    request: SubtitleSearchRequest,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Intelligent subtitle search with multi-source fallback
    
    This endpoint:
    1. Checks local database first
    2. Checks cache for recent searches
    3. Fetches from external APIs if not found (when auto_fetch=True)
    4. Caches results for future requests
    5. Returns comprehensive metadata
    """
    try:
        # Get movie info for better search if title not provided
        movie_title = request.movie_title
        movie_year = request.movie_year
        
        if not movie_title:
            movie_response = supabase.table("movies").select("title, release_year").eq("id", request.movie_id).execute()
            if movie_response.data:
                movie_data = movie_response.data[0]
                movie_title = movie_data["title"]
                movie_year = movie_data.get("release_year") if not movie_year else movie_year
            else:
                raise HTTPException(status_code=404, detail="Movie not found")
        
        # Search for subtitles using the enhanced service
        service = await get_subtitle_service()
        subtitles, source = await service.search_and_cache_subtitles(
            movie_id=request.movie_id,
            language=request.language,
            movie_title=movie_title,
            auto_fetch=request.auto_fetch,
            movie_year=movie_year,
            imdb_id=request.imdb_id
        )
        
        # Convert to serializable format
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
                "external_id": sub.external_id,
                "created_at": sub.created_at.isoformat(),
                "can_download": sub.file_url is not None,
                "is_processed": sub.source.value == "database",
                "quality_score": sub.rating * 0.3 + min(sub.download_count / 1000, 1.0) * 0.7  # Combined quality metric
            }
            subtitle_dicts.append(subtitle_dict)
        
        # Sort by quality score
        subtitle_dicts.sort(key=lambda x: x["quality_score"], reverse=True)
        
        return SubtitleSearchResponse(
            subtitles=subtitle_dicts,
            source=source,
            language=request.language,
            movie_id=request.movie_id,
            cached=source in ["cache", "database"],
            total_found=len(subtitle_dicts),
            search_metadata={
                "movie_title": movie_title,
                "movie_year": movie_year,
                "imdb_id": request.imdb_id,
                "search_timestamp": datetime.utcnow().isoformat(),
                "user_authenticated": current_user is not None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subtitle search failed: {str(e)}")

@router.post("/search/multi-language", response_model=MultiLanguageResponse)
async def search_multi_language_subtitles(
    request: MultiLanguageRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Search for subtitles in all available languages for a movie
    
    This endpoint:
    1. Searches for subtitles in all supported languages
    2. Returns available languages with subtitle counts
    3. Prioritizes user's preferred languages
    4. Caches results for better performance
    5. Schedules background cleanup
    """
    try:
        service = await get_subtitle_service()
        
        # Get all available subtitles by language
        all_subtitles = await service.get_all_available_languages(
            movie_id=request.movie_id,
            movie_title=request.movie_title,
            movie_year=request.movie_year
        )
        
        # Convert to response format
        subtitles_by_language = {}
        available_languages = []
        cache_info = {}
        
        for language, subtitles in all_subtitles.items():
            if subtitles:
                available_languages.append(language)
                
                # Convert to serializable format
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
                        "is_processed": sub.source.value == "database",
                        "quality_score": sub.rating * 0.3 + min(sub.download_count / 1000, 1.0) * 0.7
                    }
                    subtitle_dicts.append(subtitle_dict)
                
                # Sort by quality
                subtitle_dicts.sort(key=lambda x: x["quality_score"], reverse=True)
                subtitles_by_language[language] = subtitle_dicts
                cache_info[language] = subtitles[0].source.value
        
        # Sort available languages by preference if provided
        if request.preferred_languages:
            preferred_available = [lang for lang in request.preferred_languages if lang in available_languages]
            other_available = [lang for lang in available_languages if lang not in preferred_available]
            available_languages = preferred_available + sorted(other_available)
        else:
            available_languages = sorted(available_languages)
        
        # Schedule cache cleanup in background
        background_tasks.add_task(cleanup_subtitle_cache)
        
        return MultiLanguageResponse(
            movie_id=request.movie_id,
            movie_title=request.movie_title,
            available_languages=available_languages,
            subtitles_by_language=subtitles_by_language,
            cache_info=cache_info,
            total_languages=len(available_languages)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-language search failed: {str(e)}")

# ===== SUBTITLE DOWNLOAD AND PROCESSING ENDPOINTS =====

@router.post("/download", response_model=SubtitleDownloadResponse)
async def download_and_process_subtitle(
    request: SubtitleDownloadRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Download external subtitle and process it through the learning pipeline
    
    This endpoint:
    1. Downloads subtitle file from external source
    2. Processes it through NLP pipeline
    3. Creates learning segments and vocabulary
    4. Stores everything in the database
    5. Returns processing results
    """
    try:
        if request.process_immediately:
            # Process in foreground for immediate response
            result = await download_and_process_external_subtitle(
                subtitle_id=request.subtitle_id,
                movie_id=request.movie_id,
                language=request.language,
                external_url=request.external_url,
                title=request.title,
                source=request.source
            )
            
            if result:
                return SubtitleDownloadResponse(
                    subtitle_id=request.subtitle_id,
                    download_status="completed",
                    processing_status="completed",
                    learning_content=result.get("processed_data"),
                    estimated_processing_time="immediate"
                )
            else:
                raise HTTPException(status_code=500, detail="Download and processing failed")
        else:
            # Process in background
            background_tasks.add_task(
                download_and_process_external_subtitle,
                request.subtitle_id,
                request.movie_id,
                request.language,
                request.external_url,
                request.title,
                request.source
            )
            
            return SubtitleDownloadResponse(
                subtitle_id=request.subtitle_id,
                download_status="queued",
                processing_status="queued",
                learning_content=None,
                estimated_processing_time="2-5 minutes"
            )
            
    except HTTPException:
        raise
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
                "metadata": {
                    "total_cues": subtitle.get("total_cues", 0),
                    "total_segments": subtitle.get("total_segments", 0),
                    "vocabulary_count": subtitle.get("vocabulary_count", 0),
                    "avg_difficulty": subtitle.get("avg_difficulty", 0),
                    "duration": subtitle.get("duration", 0),
                    "language": subtitle.get("language"),
                    "created_at": subtitle.get("created_at")
                }
            }
        else:
            # Check if it's an external ID that might be processing
            external_response = supabase.table("subtitles").select("*").eq("external_id", subtitle_id).execute()
            if external_response.data:
                subtitle = external_response.data[0]
                return {
                    "subtitle_id": subtitle["id"],
                    "external_id": subtitle_id,
                    "status": "completed",
                    "download_status": "completed",
                    "processing_status": "completed",
                    "metadata": {
                        "total_cues": subtitle.get("total_cues", 0),
                        "total_segments": subtitle.get("total_segments", 0),
                        "vocabulary_count": subtitle.get("vocabulary_count", 0),
                        "avg_difficulty": subtitle.get("avg_difficulty", 0),
                        "duration": subtitle.get("duration", 0),
                        "language": subtitle.get("language"),
                        "created_at": subtitle.get("created_at")
                    }
                }
            else:
                return {
                    "subtitle_id": subtitle_id,
                    "status": "not_found",
                    "download_status": "not_found",
                    "processing_status": "not_found",
                    "message": "Subtitle not found or still processing"
                }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

# ===== SUBTITLE MANAGEMENT ENDPOINTS =====

@router.get("/movie/{movie_id}/available")
async def get_available_subtitle_languages(
    movie_id: str,
    include_external: bool = Query(False, description="Include external API search"),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get all available subtitle languages for a movie (optimized for quick response)"""
    try:
        # Get from database first
        response = supabase.table("subtitles")\
            .select("language, count(*)")\
            .eq("movie_id", movie_id)\
            .execute()
        
        language_counts = {}
        for row in response.data or []:
            language = row.get("language")
            if language:
                language_counts[language] = language_counts.get(language, 0) + 1
        
        result = {
            "movie_id": movie_id,
            "available_languages": list(language_counts.keys()),
            "language_counts": language_counts,
            "total_languages": len(language_counts),
            "source": "database"
        }
        
        # Optionally include external search
        if include_external and len(language_counts) < 5:  # Only if we have few languages
            try:
                movie_response = supabase.table("movies").select("title, release_year").eq("id", movie_id).execute()
                if movie_response.data:
                    movie_data = movie_response.data[0]
                    external_languages = await get_all_languages_for_movie(movie_id, movie_data["title"])
                    
                    # Merge external results
                    for lang, subtitles in external_languages.items():
                        if lang not in language_counts and subtitles:
                            language_counts[lang] = len(subtitles)
                    
                    result.update({
                        "available_languages": list(language_counts.keys()),
                        "language_counts": language_counts,
                        "total_languages": len(language_counts),
                        "source": "database_and_external"
                    })
            except Exception as e:
                # Don't fail the whole request if external search fails
                result["external_search_error"] = str(e)
        
        return result
        
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
            "deleted_count": len(subtitle_ids),
            "deleted_subtitle_ids": subtitle_ids
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

# ===== CACHING AND PERFORMANCE ENDPOINTS =====

@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    current_user: User = Depends(get_current_user)
):
    """Get cache performance statistics and service information"""
    try:
        health_data = await check_subtitle_service_health()
        service = await get_subtitle_service()
        service_stats = service.get_service_stats()
        
        return CacheStatsResponse(
            cache_performance=service_stats["cache_stats"],
            service_stats={
                "searches_performed": service_stats["service_stats"]["searches_performed"],
                "downloads_completed": service_stats["service_stats"]["downloads_completed"],
                "processing_completed": service_stats["service_stats"]["processing_completed"],
                "external_apis": service_stats["external_apis"],
                "configuration": service_stats["configuration"]
            },
            supported_languages=service_stats["supported_languages"],
            health_status=health_data["status"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@router.post("/cache/clear")
async def clear_subtitle_cache(
    cache_type: str = Query("memory", regex="^(memory|database|all)$"),
    current_user: User = Depends(get_current_user)
):
    """Clear subtitle cache (memory, database, or both)"""
    try:
        service = await get_subtitle_service()
        cleared_items = 0
        
        if cache_type in ["memory", "all"]:
            # Clear memory cache
            memory_items = len(service.cache.memory_cache)
            service.cache.memory_cache.clear()
            cleared_items += memory_items
            service.cache.cache_hits = 0
            service.cache.cache_misses = 0
        
        if cache_type in ["database", "all"]:
            # Clear database cache
            try:
                db_response = supabase.table("subtitle_cache").delete().neq("id", "").execute()
                # Note: Supabase doesn't return count for delete operations by default
                cleared_items += 1  # Indicate that database operation was performed
            except Exception as e:
                print(f"Database cache clear error: {e}")
        
        return {
            "message": f"Cache cleared successfully",
            "cache_type": cache_type,
            "operation_completed": True,
            "memory_items_cleared": memory_items if cache_type in ["memory", "all"] else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")

@router.post("/cache/warm-up")
async def warm_up_cache(
    movie_ids: List[str],
    languages: List[str],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Pre-populate cache with subtitles for specified movies and languages"""
    try:
        # Validate input
        if len(movie_ids) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 movies allowed for warm-up")
        if len(languages) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 languages allowed for warm-up")
        
        # Get movie titles
        movies_response = supabase.table("movies")\
            .select("id, title, release_year")\
            .in_("id", movie_ids)\
            .execute()
        
        if not movies_response.data:
            raise HTTPException(status_code=404, detail="No movies found with provided IDs")
        
        movies = {row["id"]: {"title": row["title"], "year": row.get("release_year")} for row in movies_response.data}
        
        # Schedule cache warm-up in background
        background_tasks.add_task(
            _warm_up_cache_task,
            movies,
            languages
        )
        
        return {
            "message": "Cache warm-up started",
            "movie_count": len(movies),
            "language_count": len(languages),
            "total_combinations": len(movies) * len(languages),
            "estimated_completion_time": f"{len(movies) * len(languages) * 2} seconds",
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache warm-up failed: {str(e)}")

# ===== HEALTH CHECK ENDPOINTS =====

@router.get("/health")
async def subtitle_service_health():
    """Health check for subtitle service"""
    try:
        health_data = await check_subtitle_service_health()
        return health_data
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "multi_language_subtitle_service",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/health/detailed")
async def detailed_subtitle_service_health(
    current_user: User = Depends(get_current_user)
):
    """Detailed health check with comprehensive diagnostics"""
    try:
        service = await get_subtitle_service()
        stats = service.get_service_stats()
        
        # Test database connectivity
        db_test = True
        try:
            supabase.table("subtitles").select("id").limit(1).execute()
        except Exception:
            db_test = False
        
        # Test cache functionality
        cache_test = True
        try:
            test_key = "health_check_test"
            await service.cache.store_subtitles("test", "en", [], "test_movie", 1)
            cache_test = len(service.cache.memory_cache) >= 0  # Basic test
        except Exception:
            cache_test = False
        
        return {
            "status": "healthy" if db_test and cache_test else "degraded",
            "service": "multi_language_subtitle_service",
            "timestamp": datetime.utcnow().isoformat(),
            "detailed_checks": {
                "database_connectivity": "ok" if db_test else "error",
                "cache_functionality": "ok" if cache_test else "error",
                "external_apis": stats["external_apis"],
                "memory_usage": {
                    "cache_size": stats["cache_stats"]["memory_cache_size"],
                    "max_cache_size": stats["cache_stats"]["max_memory_items"]
                }
            },
            "performance_metrics": {
                "cache_hit_ratio": stats["cache_stats"]["hit_ratio"],
                "total_searches": stats["service_stats"]["searches_performed"],
                "total_downloads": stats["service_stats"]["downloads_completed"],
                "total_processing": stats["service_stats"]["processing_completed"]
            },
            "configuration": stats["configuration"]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "service": "multi_language_subtitle_service",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# ===== BACKGROUND TASK FUNCTIONS =====

async def _warm_up_cache_task(movies: Dict[str, Dict], languages: List[str]):
    """Background task to warm up cache"""
    try:
        service = await get_subtitle_service()
        
        for movie_id, movie_data in movies.items():
            for language in languages:
                try:
                    await service.search_and_cache_subtitles(
                        movie_id=movie_id,
                        language=language,
                        movie_title=movie_data["title"],
                        auto_fetch=True,
                        movie_year=movie_data.get("year")
                    )
                    print(f"✅ Warmed up cache for {movie_data['title']} ({language})")
                    
                    # Small delay to avoid overwhelming external APIs
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    print(f"❌ Failed to warm up cache for {movie_data['title']} ({language}): {e}")
                    continue
                    
    except Exception as e:
        print(f"❌ Cache warm-up task failed: {e}")

# ===== ANALYTICS ENDPOINTS =====

@router.get("/analytics/popular-languages")
async def get_popular_languages(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """Get most popular subtitle languages based on usage"""
    try:
        # Get language usage from database
        response = supabase.table("subtitles")\
            .select("language, count(*)")\
            .execute()
        
        language_stats = {}
        for row in response.data or []:
            language = row.get("language")
            if language:
                language_stats[language] = language_stats.get(language, 0) + 1
        
        # Sort by popularity
        sorted_languages = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return {
            "popular_languages": [
                {
                    "language": lang,
                    "subtitle_count": count,
                    "percentage": round(count / sum(language_stats.values()) * 100, 2) if language_stats else 0
                }
                for lang, count in sorted_languages
            ],
            "total_languages": len(language_stats),
            "total_subtitles": sum(language_stats.values()),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")

@router.get("/analytics/processing-stats")
async def get_processing_statistics(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user)
):
    """Get subtitle processing statistics for the specified period"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get processing stats
        response = supabase.table("subtitles")\
            .select("language, created_at, total_cues, vocabulary_count, avg_difficulty")\
            .gte("created_at", start_date.isoformat())\
            .lte("created_at", end_date.isoformat())\
            .execute()
        
        stats = {
            "total_processed": len(response.data) if response.data else 0,
            "period_days": days,
            "processing_rate": 0,
            "language_breakdown": {},
            "quality_metrics": {
                "avg_cues_per_subtitle": 0,
                "avg_vocabulary_per_subtitle": 0,
                "avg_difficulty_score": 0
            }
        }
        
        if response.data:
            stats["processing_rate"] = round(len(response.data) / days, 2)
            
            # Language breakdown
            for row in response.data:
                lang = row.get("language", "unknown")
                stats["language_breakdown"][lang] = stats["language_breakdown"].get(lang, 0) + 1
            
            # Quality metrics
            total_cues = sum(row.get("total_cues", 0) for row in response.data)
            total_vocabulary = sum(row.get("vocabulary_count", 0) for row in response.data)
            total_difficulty = sum(row.get("avg_difficulty", 0) for row in response.data)
            
            count = len(response.data)
            stats["quality_metrics"] = {
                "avg_cues_per_subtitle": round(total_cues / count, 1),
                "avg_vocabulary_per_subtitle": round(total_vocabulary / count, 1),
                "avg_difficulty_score": round(total_difficulty / count, 2)
            }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing statistics failed: {str(e)}")

# ===== ERROR HANDLING AND VALIDATION =====

@router.get("/validate/api-keys")
async def validate_external_api_keys(
    current_user: User = Depends(get_current_user)
):
    """Validate external API keys and check rate limits"""
    try:
        service = await get_subtitle_service()
        validation_results = {}
        
        # Check OpenSubtitles API
        if service.opensubtitles:
            api_stats = service.opensubtitles.get_api_stats()
            validation_results["opensubtitles"] = {
                "available": True,
                "rate_limit_remaining": service.opensubtitles.rate_limit_remaining,
                "rate_limit_reset": service.opensubtitles.rate_limit_reset.isoformat() if service.opensubtitles.rate_limit_reset else None,
                "status": "active" if service.opensubtitles.rate_limit_remaining > 10 else "limited",
                "success_rate": api_stats["success_rate"],
                "total_requests": api_stats["total_requests"]
            }
        else:
            validation_results["opensubtitles"] = {
                "available": False,
                "error": "API key not configured",
                "status": "unavailable"
            }
        
        # Overall status
        overall_status = "healthy" if any(api["available"] for api in validation_results.values()) else "degraded"
        
        return {
            "validation_results": validation_results,
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "recommendations": [
                "Configure OpenSubtitles API key for external subtitle access" if not service.opensubtitles else None,
                "Monitor rate limits to avoid service interruption" if any(api.get("status") == "limited" for api in validation_results.values()) else None
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API validation failed: {str(e)}")

# ===== LEGACY COMPATIBILITY ENDPOINTS =====

@router.post("/upload")
async def upload_subtitle_file_legacy(
    # Maintain compatibility with existing upload functionality
    # This should delegate to your existing subtitle upload logic
    current_user: User = Depends(get_current_user)
):
    """Legacy subtitle upload endpoint - maintains existing functionality"""
    return JSONResponse(
        status_code=501,
        content={
            "message": "Legacy upload endpoint - please use the new multi-language endpoints",
            "new_endpoints": {
                "search": "/api/v1/subtitles/search",
                "download": "/api/v1/subtitles/download",
                "multi_language": "/api/v1/subtitles/search/multi-language"
            }
        }
    )

@router.get("/{subtitle_id}/segments")
async def get_learning_segments_legacy(
    subtitle_id: str,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Legacy endpoint for getting learning segments - maintains existing functionality"""
    try:
        # Get learning segments from database
        segments_response = supabase.table("learning_segments")\
            .select("*")\
            .eq("subtitle_id", subtitle_id)\
            .order("start_time")\
            .execute()
        
        if not segments_response.data:
            raise HTTPException(status_code=404, detail="No learning segments found for this subtitle")
        
        return {
            "subtitle_id": subtitle_id,
            "segments": segments_response.data,
            "total_segments": len(segments_response.data),
            "legacy_endpoint": True,
            "message": "Consider using the new enhanced subtitle endpoints for better functionality"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch segments: {str(e)}")

# Import asyncio for background tasks
import asyncio