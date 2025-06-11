"""
CineFluent Multi-Language Subtitle Fetcher Service
Integrates with external APIs and manages subtitle caching/storage
"""

import os
import asyncio
import aiohttp
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json
import uuid
from dataclasses import dataclass
from enum import Enum

# For subtitle processing
import requests
from core.subtitle_engine import SubtitleProcessor, process_subtitle_file
from database import supabase, supabase_admin

class SubtitleSource(Enum):
    """Available subtitle sources"""
    OPENSUBTITLES = "opensubtitles"
    SUBSCENE = "subscene"
    YIFYSUBTITLES = "yifysubtitles"
    CACHE = "cache"
    DATABASE = "database"

@dataclass
class SubtitleMetadata:
    """Subtitle file metadata"""
    id: str
    movie_id: str
    language: str
    title: str
    source: SubtitleSource
    file_url: Optional[str]
    file_size: int
    download_count: int
    rating: float
    release_info: str
    encoding: str
    created_at: datetime
    expires_at: Optional[datetime] = None

class SubtitleCache:
    """In-memory and database caching for subtitles"""
    
    def __init__(self, max_memory_items: int = 100):
        self.memory_cache = {}
        self.max_memory_items = max_memory_items
        self.cache_hits = 0
        self.cache_misses = 0
    
    def _generate_cache_key(self, movie_id: str, language: str, movie_title: str = "") -> str:
        """Generate cache key for movie + language combination"""
        content = f"{movie_id}:{language}:{movie_title.lower()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get_cached_subtitles(self, movie_id: str, language: str, movie_title: str = "") -> Optional[List[SubtitleMetadata]]:
        """Get cached subtitle metadata"""
        cache_key = self._generate_cache_key(movie_id, language, movie_title)
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            cached_data = self.memory_cache[cache_key]
            if cached_data['expires_at'] > datetime.utcnow():
                self.cache_hits += 1
                return cached_data['subtitles']
            else:
                # Expired, remove from memory
                del self.memory_cache[cache_key]
        
        # Check database cache
        try:
            cache_response = supabase.table("subtitle_cache")\
                .select("*")\
                .eq("cache_key", cache_key)\
                .gt("expires_at", datetime.utcnow().isoformat())\
                .execute()
            
            if cache_response.data:
                cached_entry = cache_response.data[0]
                subtitles_data = json.loads(cached_entry["subtitles_data"])
                
                # Convert back to SubtitleMetadata objects
                subtitles = []
                for sub_dict in subtitles_data:
                    sub_dict['source'] = SubtitleSource(sub_dict['source'])
                    sub_dict['created_at'] = datetime.fromisoformat(sub_dict['created_at'])
                    if sub_dict.get('expires_at'):
                        sub_dict['expires_at'] = datetime.fromisoformat(sub_dict['expires_at'])
                    subtitles.append(SubtitleMetadata(**sub_dict))
                
                # Store in memory cache
                self._store_in_memory_cache(cache_key, subtitles, cached_entry["expires_at"])
                self.cache_hits += 1
                return subtitles
        
        except Exception as e:
            print(f"Cache lookup error: {e}")
        
        self.cache_misses += 1
        return None
    
    async def store_subtitles(self, movie_id: str, language: str, subtitles: List[SubtitleMetadata], 
                            movie_title: str = "", ttl_hours: int = 24):
        """Store subtitles in cache"""
        cache_key = self._generate_cache_key(movie_id, language, movie_title)
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        
        # Store in memory cache
        self._store_in_memory_cache(cache_key, subtitles, expires_at)
        
        # Store in database cache
        try:
            # Convert SubtitleMetadata objects to serializable format
            subtitles_data = []
            for sub in subtitles:
                sub_dict = {
                    'id': sub.id,
                    'movie_id': sub.movie_id,
                    'language': sub.language,
                    'title': sub.title,
                    'source': sub.source.value,
                    'file_url': sub.file_url,
                    'file_size': sub.file_size,
                    'download_count': sub.download_count,
                    'rating': sub.rating,
                    'release_info': sub.release_info,
                    'encoding': sub.encoding,
                    'created_at': sub.created_at.isoformat(),
                    'expires_at': sub.expires_at.isoformat() if sub.expires_at else None
                }
                subtitles_data.append(sub_dict)
            
            cache_entry = {
                "cache_key": cache_key,
                "movie_id": movie_id,
                "language": language,
                "movie_title": movie_title,
                "subtitles_data": json.dumps(subtitles_data),
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Upsert cache entry
            supabase.table("subtitle_cache").upsert(cache_entry, on_conflict="cache_key").execute()
            
        except Exception as e:
            print(f"Cache storage error: {e}")
    
    def _store_in_memory_cache(self, cache_key: str, subtitles: List[SubtitleMetadata], expires_at: datetime):
        """Store subtitles in memory cache with LRU eviction"""
        # Simple LRU eviction
        if len(self.memory_cache) >= self.max_memory_items:
            # Remove oldest entry
            oldest_key = min(self.memory_cache.keys(), 
                           key=lambda k: self.memory_cache[k]['accessed_at'])
            del self.memory_cache[oldest_key]
        
        self.memory_cache[cache_key] = {
            'subtitles': subtitles,
            'expires_at': expires_at,
            'accessed_at': datetime.utcnow()
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_ratio = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_ratio": round(hit_ratio, 2),
            "memory_cache_size": len(self.memory_cache),
            "max_memory_items": self.max_memory_items
        }

class OpenSubtitlesAPI:
    """OpenSubtitles API integration"""
    
    def __init__(self, api_key: str, user_agent: str = "CineFluent v1.0"):
        self.api_key = api_key
        self.user_agent = user_agent
        self.base_url = "https://api.opensubtitles.com/api/v1"
        self.session = None
        self.rate_limit_remaining = 200  # Default daily limit
        self.rate_limit_reset = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            headers = {
                "User-Agent": self.user_agent,
                "Api-Key": self.api_key,
                "Content-Type": "application/json"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def search_subtitles(self, movie_title: str, year: int = None, 
                             imdb_id: str = None, languages: List[str] = None) -> List[SubtitleMetadata]:
        """Search for subtitles"""
        if self.rate_limit_remaining <= 5:
            print("Rate limit approaching, skipping external API call")
            return []
        
        try:
            session = await self._get_session()
            
            # Build query parameters
            params = {
                "query": movie_title,
                "type": "movie"
            }
            
            if year:
                params["year"] = year
            if imdb_id:
                params["imdb_id"] = imdb_id
            if languages:
                params["languages"] = ",".join(languages)
            
            async with session.get(f"{self.base_url}/subtitles", params=params) as response:
                # Update rate limit info
                self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                
                if response.status == 200:
                    data = await response.json()
                    return self._parse_opensubtitles_response(data)
                else:
                    print(f"OpenSubtitles API error: {response.status}")
                    return []
                    
        except Exception as e:
            print(f"OpenSubtitles API request failed: {e}")
            return []
    
    def _parse_opensubtitles_response(self, data: Dict) -> List[SubtitleMetadata]:
        """Parse OpenSubtitles API response"""
        subtitles = []
        
        for item in data.get('data', []):
            try:
                subtitle = SubtitleMetadata(
                    id=str(uuid.uuid4()),
                    movie_id="",  # Will be set by caller
                    language=item['attributes']['language'],
                    title=f"{item['attributes']['release']} - {item['attributes']['language']}",
                    source=SubtitleSource.OPENSUBTITLES,
                    file_url=item['attributes']['url'],
                    file_size=item['attributes'].get('download_count', 0),
                    download_count=item['attributes'].get('download_count', 0),
                    rating=float(item['attributes'].get('rating', 0.0)),
                    release_info=item['attributes'].get('release', ''),
                    encoding=item['attributes'].get('encoding', 'utf-8'),
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(hours=48)
                )
                subtitles.append(subtitle)
            except Exception as e:
                print(f"Failed to parse subtitle item: {e}")
                continue
        
        return subtitles
    
    async def download_subtitle(self, file_url: str) -> Optional[bytes]:
        """Download subtitle file content"""
        if self.rate_limit_remaining <= 1:
            print("Rate limit reached, cannot download subtitle")
            return None
        
        try:
            session = await self._get_session()
            
            async with session.get(file_url) as response:
                self.rate_limit_remaining -= 1
                
                if response.status == 200:
                    return await response.read()
                else:
                    print(f"Subtitle download failed: {response.status}")
                    return None
                    
        except Exception as e:
            print(f"Subtitle download error: {e}")
            return None
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()

class MultiLanguageSubtitleService:
    """Main service for managing multi-language subtitles"""
    
    def __init__(self):
        self.cache = SubtitleCache()
        self.subtitle_processor = SubtitleProcessor()
        
        # Initialize external APIs
        opensubtitles_api_key = os.getenv("OPENSUBTITLES_API_KEY")
        self.opensubtitles = OpenSubtitlesAPI(opensubtitles_api_key) if opensubtitles_api_key else None
        
        # Configuration
        self.supported_languages = ["en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh", "ru", "ar"]
        self.max_external_requests_per_movie = 3
        self.auto_process_downloaded = True
    
    async def get_subtitles(self, movie_id: str, language: str, movie_title: str = "", 
                          auto_fetch: bool = True) -> Tuple[List[SubtitleMetadata], str]:
        """
        Get subtitles for a movie in specified language
        Returns: (subtitles_list, source_info)
        """
        
        # Step 1: Check local database first
        database_subtitles = await self._get_database_subtitles(movie_id, language)
        if database_subtitles:
            return database_subtitles, "database"
        
        # Step 2: Check cache
        cached_subtitles = await self.cache.get_cached_subtitles(movie_id, language, movie_title)
        if cached_subtitles:
            return cached_subtitles, "cache"
        
        # Step 3: Fetch from external APIs if auto_fetch is enabled
        if auto_fetch and movie_title:
            external_subtitles = await self._fetch_from_external_apis(movie_id, language, movie_title)
            if external_subtitles:
                # Cache the results
                await self.cache.store_subtitles(movie_id, language, external_subtitles, movie_title)
                return external_subtitles, "external_api"
        
        return [], "not_found"
    
    async def get_all_available_languages(self, movie_id: str, movie_title: str = "") -> Dict[str, List[SubtitleMetadata]]:
        """Get subtitles in all available languages for a movie"""
        all_subtitles = {}
        
        # Check database for all languages
        for language in self.supported_languages:
            subtitles, source = await self.get_subtitles(movie_id, language, movie_title, auto_fetch=False)
            if subtitles:
                all_subtitles[language] = subtitles
        
        # If we have some but not all languages, try to fetch missing ones
        if len(all_subtitles) < len(self.supported_languages) and movie_title:
            missing_languages = [lang for lang in self.supported_languages if lang not in all_subtitles]
            
            # Batch fetch missing languages
            if self.opensubtitles and len(missing_languages) > 0:
                external_results = await self._batch_fetch_languages(movie_id, movie_title, missing_languages)
                all_subtitles.update(external_results)
        
        return all_subtitles
    
    async def download_and_process_subtitle(self, subtitle_meta: SubtitleMetadata, 
                                          auto_delete_file: bool = True) -> Optional[Dict[str, Any]]:
        """Download subtitle file and process it through the learning pipeline"""
        if not subtitle_meta.file_url:
            return None
        
        try:
            # Download the subtitle file
            if subtitle_meta.source == SubtitleSource.OPENSUBTITLES and self.opensubtitles:
                file_content = await self.opensubtitles.download_subtitle(subtitle_meta.file_url)
            else:
                # Fallback to regular HTTP download
                async with aiohttp.ClientSession() as session:
                    async with session.get(subtitle_meta.file_url) as response:
                        if response.status == 200:
                            file_content = await response.read()
                        else:
                            return None
            
            if not file_content:
                return None
            
            # Determine file type from URL or content
            file_type = "srt"  # Default
            if subtitle_meta.file_url.endswith('.vtt'):
                file_type = "vtt"
            
            # Process through subtitle engine
            processed_data = process_subtitle_file(file_content, file_type, subtitle_meta.movie_id)
            
            # Store subtitle metadata in database
            subtitle_record = {
                "id": str(uuid.uuid4()),
                "movie_id": subtitle_meta.movie_id,
                "language": subtitle_meta.language,
                "title": subtitle_meta.title,
                "file_type": file_type,
                "total_cues": processed_data["total_cues"],
                "total_segments": processed_data["total_segments"],
                "duration": processed_data["duration"],
                "avg_difficulty": processed_data["avg_difficulty"],
                "vocabulary_count": processed_data["vocabulary_count"],
                "uploaded_by": "system",
                "source": subtitle_meta.source.value,
                "external_id": subtitle_meta.id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Insert subtitle record
            subtitle_response = supabase.table("subtitles").insert(subtitle_record).execute()
            
            if subtitle_response.data:
                subtitle_id = subtitle_response.data[0]["id"]
                
                # Store cues and segments (similar to existing logic)
                await self._store_processed_subtitle_data(subtitle_id, processed_data)
                
                return {
                    "subtitle_id": subtitle_id,
                    "processed_data": processed_data,
                    "source": subtitle_meta.source.value
                }
        
        except Exception as e:
            print(f"Error downloading/processing subtitle: {e}")
            return None
    
    async def _get_database_subtitles(self, movie_id: str, language: str) -> List[SubtitleMetadata]:
        """Get subtitles from local database"""
        try:
            response = supabase.table("subtitles")\
                .select("*")\
                .eq("movie_id", movie_id)\
                .eq("language", language)\
                .execute()
            
            subtitles = []
            for row in response.data or []:
                subtitle = SubtitleMetadata(
                    id=row["id"],
                    movie_id=row["movie_id"],
                    language=row["language"],
                    title=row["title"],
                    source=SubtitleSource.DATABASE,
                    file_url=None,  # Already processed
                    file_size=0,
                    download_count=0,
                    rating=5.0,  # Local files are high quality
                    release_info="Database",
                    encoding="utf-8",
                    created_at=datetime.fromisoformat(row["created_at"])
                )
                subtitles.append(subtitle)
            
            return subtitles
            
        except Exception as e:
            print(f"Database lookup error: {e}")
            return []
    
    async def _fetch_from_external_apis(self, movie_id: str, language: str, movie_title: str) -> List[SubtitleMetadata]:
        """Fetch subtitles from external APIs"""
        all_results = []
        
        # Try OpenSubtitles
        if self.opensubtitles:
            try:
                results = await self.opensubtitles.search_subtitles(
                    movie_title=movie_title,
                    languages=[language]
                )
                
                # Set movie_id for each result
                for result in results:
                    result.movie_id = movie_id
                
                all_results.extend(results[:5])  # Limit to top 5 results
                
            except Exception as e:
                print(f"OpenSubtitles fetch error: {e}")
        
        # TODO: Add other subtitle sources (Subscene, etc.)
        
        return all_results
    
    async def _batch_fetch_languages(self, movie_id: str, movie_title: str, 
                                   languages: List[str]) -> Dict[str, List[SubtitleMetadata]]:
        """Batch fetch subtitles for multiple languages"""
        results = {}
        
        if self.opensubtitles:
            try:
                # OpenSubtitles supports multiple languages in one request
                all_results = await self.opensubtitles.search_subtitles(
                    movie_title=movie_title,
                    languages=languages
                )
                
                # Group by language
                for subtitle in all_results:
                    subtitle.movie_id = movie_id
                    
                    if subtitle.language not in results:
                        results[subtitle.language] = []
                    results[subtitle.language].append(subtitle)
                
                # Cache all results
                for language, subtitles in results.items():
                    await self.cache.store_subtitles(movie_id, language, subtitles, movie_title)
                
            except Exception as e:
                print(f"Batch fetch error: {e}")
        
        return results
    
    async def _store_processed_subtitle_data(self, subtitle_id: str, processed_data: Dict[str, Any]):
        """Store processed subtitle cues and segments"""
        try:
            # Store cues
            cues_data = []
            for i, cue_dict in enumerate(processed_data["cues"]):
                cue_record = {
                    "id": str(uuid.uuid4()),
                    "subtitle_id": subtitle_id,
                    "cue_index": i,
                    "start_time": cue_dict["start_time"],
                    "end_time": cue_dict["end_time"],
                    "text": cue_dict["text"],
                    "words": json.dumps(cue_dict["words"]),
                    "difficulty_score": cue_dict["difficulty_score"]
                }
                cues_data.append(cue_record)
            
            # Batch insert cues
            if cues_data:
                batch_size = 50
                for i in range(0, len(cues_data), batch_size):
                    batch = cues_data[i:i + batch_size]
                    supabase.table("subtitle_cues").insert(batch).execute()
            
            # Store learning segments
            segments_data = []
            for segment in processed_data["segments"]:
                segment_record = {
                    "id": segment["id"],
                    "subtitle_id": subtitle_id,
                    "start_time": segment["start_time"],
                    "end_time": segment["end_time"],
                    "difficulty_score": segment["difficulty_score"],
                    "vocabulary_words": json.dumps(segment["vocabulary_words"]),
                    "cue_count": len(segment["cues"])
                }
                segments_data.append(segment_record)
            
            if segments_data:
                supabase.table("learning_segments").insert(segments_data).execute()
                
        except Exception as e:
            print(f"Error storing processed data: {e}")
    
    async def cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        try:
            # Remove expired entries from database
            supabase.table("subtitle_cache")\
                .delete()\
                .lt("expires_at", datetime.utcnow().isoformat())\
                .execute()
            
            # Clean memory cache
            expired_keys = []
            for key, data in self.memory_cache.items():
                if data['expires_at'] <= datetime.utcnow():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.memory_cache[key]
                
        except Exception as e:
            print(f"Cache cleanup error: {e}")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        cache_stats = self.cache.get_cache_stats()
        
        return {
            "cache_stats": cache_stats,
            "supported_languages": self.supported_languages,
            "external_apis": {
                "opensubtitles": {
                    "available": self.opensubtitles is not None,
                    "rate_limit_remaining": self.opensubtitles.rate_limit_remaining if self.opensubtitles else 0
                }
            },
            "configuration": {
                "max_external_requests_per_movie": self.max_external_requests_per_movie,
                "auto_process_downloaded": self.auto_process_downloaded
            }
        }
    
    async def close(self):
        """Clean up resources"""
        if self.opensubtitles:
            await self.opensubtitles.close()

# Global service instance
subtitle_service = MultiLanguageSubtitleService()

# Dependency for FastAPI
async def get_subtitle_service() -> MultiLanguageSubtitleService:
    """FastAPI dependency to get subtitle service"""
    return subtitle_service