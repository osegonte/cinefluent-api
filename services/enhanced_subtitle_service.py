"""
CineFluent Enhanced Multi-Language Subtitle Service
Integrates with external APIs, caching, and auto-processing
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
import tempfile
import time

# For subtitle processing
from core.subtitle_engine import process_subtitle_file
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
    """Enhanced subtitle file metadata"""
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
    external_id: Optional[str]
    hash_value: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime] = None

class SubtitleCache:
    """Advanced caching system with memory and database layers"""
    
    def __init__(self, max_memory_items: int = 200, default_ttl_hours: int = 24):
        self.memory_cache = {}
        self.max_memory_items = max_memory_items
        self.default_ttl_hours = default_ttl_hours
        self.cache_hits = 0
        self.cache_misses = 0
        self.last_cleanup = datetime.utcnow()
    
    def _generate_cache_key(self, movie_id: str, language: str, movie_title: str = "") -> str:
        """Generate unique cache key"""
        content = f"{movie_id}:{language}:{movie_title.lower().strip()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get_cached_subtitles(self, movie_id: str, language: str, 
                                 movie_title: str = "") -> Optional[List[SubtitleMetadata]]:
        """Retrieve cached subtitles with intelligent fallback"""
        cache_key = self._generate_cache_key(movie_id, language, movie_title)
        
        # 1. Check memory cache first (fastest)
        memory_result = self._check_memory_cache(cache_key)
        if memory_result:
            self.cache_hits += 1
            return memory_result
        
        # 2. Check database cache (persistent)
        db_result = await self._check_database_cache(cache_key, movie_id, language)
        if db_result:
            # Store in memory for faster future access
            self._store_in_memory_cache(cache_key, db_result, 
                                      datetime.utcnow() + timedelta(hours=self.default_ttl_hours))
            self.cache_hits += 1
            return db_result
        
        self.cache_misses += 1
        return None
    
    def _check_memory_cache(self, cache_key: str) -> Optional[List[SubtitleMetadata]]:
        """Check memory cache for valid entries"""
        if cache_key in self.memory_cache:
            cached_data = self.memory_cache[cache_key]
            if cached_data['expires_at'] > datetime.utcnow():
                cached_data['accessed_at'] = datetime.utcnow()  # Update access time
                return cached_data['subtitles']
            else:
                # Expired, remove from memory
                del self.memory_cache[cache_key]
        return None
    
    async def _check_database_cache(self, cache_key: str, movie_id: str, 
                                  language: str) -> Optional[List[SubtitleMetadata]]:
        """Check database cache for persistent storage"""
        try:
            # Update the table name to match your schema
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
                
                return subtitles
        except Exception as e:
            print(f"Database cache lookup error: {e}")
        
        return None
    
    async def store_subtitles(self, movie_id: str, language: str, subtitles: List[SubtitleMetadata], 
                            movie_title: str = "", ttl_hours: int = None):
        """Store subtitles in both cache layers"""
        if ttl_hours is None:
            ttl_hours = self.default_ttl_hours
            
        cache_key = self._generate_cache_key(movie_id, language, movie_title)
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        
        # Store in memory cache
        self._store_in_memory_cache(cache_key, subtitles, expires_at)
        
        # Store in database cache for persistence
        await self._store_in_database_cache(cache_key, movie_id, language, 
                                          subtitles, movie_title, expires_at)
    
    def _store_in_memory_cache(self, cache_key: str, subtitles: List[SubtitleMetadata], 
                             expires_at: datetime):
        """Store subtitles in memory with LRU eviction"""
        # Implement LRU eviction
        if len(self.memory_cache) >= self.max_memory_items:
            # Remove oldest accessed item
            oldest_key = min(self.memory_cache.keys(), 
                           key=lambda k: self.memory_cache[k]['accessed_at'])
            del self.memory_cache[oldest_key]
        
        self.memory_cache[cache_key] = {
            'subtitles': subtitles,
            'expires_at': expires_at,
            'accessed_at': datetime.utcnow(),
            'created_at': datetime.utcnow()
        }
    
    async def _store_in_database_cache(self, cache_key: str, movie_id: str, language: str,
                                     subtitles: List[SubtitleMetadata], movie_title: str,
                                     expires_at: datetime):
        """Store subtitles in database cache"""
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
                    'external_id': sub.external_id,
                    'hash_value': sub.hash_value,
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
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Use upsert to handle duplicates
            supabase.table("subtitle_cache").upsert(cache_entry, on_conflict="cache_key").execute()
            
        except Exception as e:
            print(f"Database cache storage error: {e}")
    
    async def cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        current_time = datetime.utcnow()
        
        # Clean memory cache
        expired_keys = [
            key for key, data in self.memory_cache.items()
            if data['expires_at'] <= current_time
        ]
        for key in expired_keys:
            del self.memory_cache[key]
        
        # Clean database cache
        try:
            supabase.table("subtitle_cache")\
                .delete()\
                .lt("expires_at", current_time.isoformat())\
                .execute()
        except Exception as e:
            print(f"Database cache cleanup error: {e}")
        
        self.last_cleanup = current_time
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_ratio = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_ratio": round(hit_ratio, 2),
            "memory_cache_size": len(self.memory_cache),
            "max_memory_items": self.max_memory_items,
            "last_cleanup": self.last_cleanup.isoformat(),
            "total_requests": total_requests
        }

class OpenSubtitlesAPI:
    """Enhanced OpenSubtitles API integration with rate limiting"""
    
    def __init__(self, api_key: str, user_agent: str = "CineFluent v1.0"):
        self.api_key = api_key
        self.user_agent = user_agent
        self.base_url = "https://api.opensubtitles.com/api/v1"
        self.session = None
        
        # Rate limiting
        self.rate_limit_remaining = 200
        self.rate_limit_reset = None
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum seconds between requests
        
        # Statistics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with proper headers"""
        if self.session is None or self.session.closed:
            headers = {
                "User-Agent": self.user_agent,
                "Api-Key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self.session
    
    async def _rate_limit_check(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        if self.rate_limit_remaining <= 5:
            print(f"⚠️ OpenSubtitles rate limit low: {self.rate_limit_remaining} remaining")
            if self.rate_limit_remaining <= 1:
                print("🛑 Rate limit reached, skipping request")
                return False
        
        self.last_request_time = time.time()
        return True
    
    async def search_subtitles(self, movie_title: str, year: int = None, 
                             imdb_id: str = None, languages: List[str] = None,
                             episode_number: int = None) -> List[SubtitleMetadata]:
        """Enhanced subtitle search with better parameters"""
        
        if not await self._rate_limit_check():
            return []
        
        try:
            session = await self._get_session()
            
            # Build comprehensive query parameters
            params = {
                "query": movie_title.strip(),
                "type": "episode" if episode_number else "movie"
            }
            
            if year:
                params["year"] = year
            if imdb_id:
                params["imdb_id"] = imdb_id
            if languages:
                params["languages"] = ",".join(languages)
            if episode_number:
                params["episode_number"] = episode_number
            
            # Add additional search parameters for better results
            params.update({
                "moviehash_match": "include",
                "order_by": "download_count",
                "order_direction": "desc"
            })
            
            self.total_requests += 1
            
            async with session.get(f"{self.base_url}/subtitles", params=params) as response:
                # Update rate limit info
                self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                reset_time = response.headers.get('X-RateLimit-Reset')
                if reset_time:
                    self.rate_limit_reset = datetime.fromtimestamp(int(reset_time))
                
                if response.status == 200:
                    data = await response.json()
                    self.successful_requests += 1
                    return self._parse_opensubtitles_response(data)
                elif response.status == 429:
                    print("🛑 OpenSubtitles rate limit exceeded")
                    self.rate_limit_remaining = 0
                    self.failed_requests += 1
                    return []
                else:
                    print(f"❌ OpenSubtitles API error: {response.status}")
                    self.failed_requests += 1
                    return []
                    
        except Exception as e:
            print(f"❌ OpenSubtitles API request failed: {e}")
            self.failed_requests += 1
            return []
    
    def _parse_opensubtitles_response(self, data: Dict) -> List[SubtitleMetadata]:
        """Parse and enhance OpenSubtitles API response"""
        subtitles = []
        
        for item in data.get('data', []):
            try:
                attributes = item.get('attributes', {})
                
                # Extract comprehensive metadata
                subtitle = SubtitleMetadata(
                    id=str(uuid.uuid4()),
                    movie_id="",  # Will be set by caller
                    language=attributes.get('language', 'unknown'),
                    title=f"{attributes.get('release', 'Unknown')} - {attributes.get('language', 'Unknown')}",
                    source=SubtitleSource.OPENSUBTITLES,
                    file_url=attributes.get('url'),
                    file_size=attributes.get('file_size', 0),
                    download_count=attributes.get('download_count', 0),
                    rating=float(attributes.get('ratings', 0.0)),
                    release_info=attributes.get('release', ''),
                    encoding=attributes.get('encoding', 'utf-8'),
                    external_id=str(item.get('id', '')),
                    hash_value=attributes.get('moviehash'),
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(hours=48)  # External cache TTL
                )
                subtitles.append(subtitle)
                
            except Exception as e:
                print(f"⚠️ Failed to parse subtitle item: {e}")
                continue
        
        return subtitles
    
    async def download_subtitle(self, file_url: str) -> Optional[bytes]:
        """Download subtitle file with enhanced error handling"""
        if not await self._rate_limit_check():
            return None
        
        try:
            session = await self._get_session()
            
            async with session.get(file_url) as response:
                self.rate_limit_remaining -= 1
                
                if response.status == 200:
                    content = await response.read()
                    # Validate content
                    if len(content) > 0:
                        return content
                    else:
                        print("⚠️ Downloaded subtitle file is empty")
                        return None
                else:
                    print(f"❌ Subtitle download failed: {response.status}")
                    return None
                    
        except Exception as e:
            print(f"❌ Subtitle download error: {e}")
            return None
    
    async def close(self):
        """Clean up session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def get_api_stats(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(success_rate, 2),
            "rate_limit_remaining": self.rate_limit_remaining,
            "rate_limit_reset": self.rate_limit_reset.isoformat() if self.rate_limit_reset else None
        }

class MultiLanguageSubtitleService:
    """Comprehensive multi-language subtitle management service"""
    
    def __init__(self):
        self.cache = SubtitleCache()
        
        # Initialize external APIs
        opensubtitles_api_key = os.getenv("OPENSUBTITLES_API_KEY")
        self.opensubtitles = OpenSubtitlesAPI(opensubtitles_api_key) if opensubtitles_api_key else None
        
        # Configuration
        self.supported_languages = [
            "en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh", 
            "ru", "ar", "hi", "tr", "pl", "nl", "sv", "da", "no"
        ]
        self.max_external_requests_per_movie = 5
        self.auto_process_downloaded = True
        self.max_concurrent_downloads = 3
        
        # Statistics
        self.service_stats = {
            "searches_performed": 0,
            "downloads_completed": 0,
            "processing_completed": 0,
            "service_start_time": datetime.utcnow()
        }
    
    async def search_and_cache_subtitles(self, movie_id: str, language: str, 
                                       movie_title: str = "", auto_fetch: bool = True,
                                       movie_year: int = None, imdb_id: str = None) -> Tuple[List[SubtitleMetadata], str]:
        """
        Comprehensive subtitle search with intelligent caching
        
        Returns: (subtitles_list, source_info)
        """
        self.service_stats["searches_performed"] += 1
        
        # Step 1: Check local database first
        database_subtitles = await self._get_database_subtitles(movie_id, language)
        if database_subtitles:
            return database_subtitles, "database"
        
        # Step 2: Check cache
        cached_subtitles = await self.cache.get_cached_subtitles(movie_id, language, movie_title)
        if cached_subtitles:
            return cached_subtitles, "cache"
        
        # Step 3: Fetch from external APIs if enabled
        if auto_fetch and movie_title:
            external_subtitles = await self._fetch_from_external_apis(
                movie_id, language, movie_title, movie_year, imdb_id
            )
            if external_subtitles:
                # Cache the results
                await self.cache.store_subtitles(movie_id, language, external_subtitles, movie_title)
                return external_subtitles, "external_api"
        
        return [], "not_found"
    
    async def get_all_available_languages(self, movie_id: str, movie_title: str = "",
                                        movie_year: int = None) -> Dict[str, List[SubtitleMetadata]]:
        """Get subtitles in all available languages with batch optimization"""
        all_subtitles = {}
        
        # First check database for all languages
        for language in self.supported_languages:
            database_subtitles = await self._get_database_subtitles(movie_id, language)
            if database_subtitles:
                all_subtitles[language] = database_subtitles
        
        # If we have some languages but not all, try external APIs for missing ones
        if len(all_subtitles) < 5 and movie_title:  # Only fetch if we have few languages
            missing_languages = [
                lang for lang in self.supported_languages[:10]  # Focus on top 10 languages
                if lang not in all_subtitles
            ]
            
            if missing_languages and self.opensubtitles:
                external_results = await self._batch_fetch_languages(
                    movie_id, movie_title, missing_languages, movie_year
                )
                all_subtitles.update(external_results)
        
        return all_subtitles
    
    async def download_and_process_subtitle(self, subtitle_meta: SubtitleMetadata,
                                          auto_delete_file: bool = True,
                                          store_in_database: bool = True) -> Optional[Dict[str, Any]]:
        """Download and process subtitle through the learning pipeline"""
        
        if not subtitle_meta.file_url:
            print("❌ No file URL provided for subtitle")
            return None
        
        try:
            # Download the subtitle file
            file_content = await self._download_subtitle_content(subtitle_meta)
            if not file_content:
                return None
            
            # Determine file type
            file_type = self._determine_file_type(subtitle_meta.file_url, file_content)
            
            # Process through subtitle engine
            print(f"🧠 Processing subtitle: {subtitle_meta.title}")
            processed_data = process_subtitle_file(file_content, file_type, subtitle_meta.movie_id)
            
            if store_in_database:
                # Store in database
                result = await self._store_processed_subtitle(subtitle_meta, processed_data, file_type)
                if result:
                    self.service_stats["processing_completed"] += 1
                    return result
            
            return {
                "subtitle_id": subtitle_meta.id,
                "processed_data": processed_data,
                "source": subtitle_meta.source.value,
                "stored_in_database": store_in_database
            }
            
        except Exception as e:
            print(f"❌ Error downloading/processing subtitle: {e}")
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
                    external_id=row.get("external_id"),
                    hash_value=None,
                    created_at=datetime.fromisoformat(row["created_at"])
                )
                subtitles.append(subtitle)
            
            return subtitles
            
        except Exception as e:
            print(f"❌ Database lookup error: {e}")
            return []
    
    async def _fetch_from_external_apis(self, movie_id: str, language: str, 
                                      movie_title: str, movie_year: int = None,
                                      imdb_id: str = None) -> List[SubtitleMetadata]:
        """Fetch subtitles from external APIs with enhanced parameters"""
        all_results = []
        
        # Try OpenSubtitles
        if self.opensubtitles:
            try:
                results = await self.opensubtitles.search_subtitles(
                    movie_title=movie_title,
                    year=movie_year,
                    imdb_id=imdb_id,
                    languages=[language]
                )
                
                # Set movie_id for each result
                for result in results:
                    result.movie_id = movie_id
                
                # Limit and sort by quality
                sorted_results = sorted(results, key=lambda x: (x.rating, x.download_count), reverse=True)
                all_results.extend(sorted_results[:self.max_external_requests_per_movie])
                
            except Exception as e:
                print(f"❌ OpenSubtitles fetch error: {e}")
        
        return all_results
    
    async def _batch_fetch_languages(self, movie_id: str, movie_title: str, 
                                   languages: List[str], movie_year: int = None) -> Dict[str, List[SubtitleMetadata]]:
        """Batch fetch subtitles for multiple languages efficiently"""
        results = {}
        
        if self.opensubtitles:
            try:
                # OpenSubtitles supports multiple languages in one request
                all_results = await self.opensubtitles.search_subtitles(
                    movie_title=movie_title,
                    year=movie_year,
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
                    # Sort by quality
                    sorted_subtitles = sorted(subtitles, 
                                            key=lambda x: (x.rating, x.download_count), 
                                            reverse=True)[:5]  # Top 5 per language
                    results[language] = sorted_subtitles
                    
                    await self.cache.store_subtitles(movie_id, language, sorted_subtitles, movie_title)
                
            except Exception as e:
                print(f"❌ Batch fetch error: {e}")
        
        return results
    
    async def _download_subtitle_content(self, subtitle_meta: SubtitleMetadata) -> Optional[bytes]:
        """Download subtitle content with proper source handling"""
        if subtitle_meta.source == SubtitleSource.OPENSUBTITLES and self.opensubtitles:
            return await self.opensubtitles.download_subtitle(subtitle_meta.file_url)
        else:
            # Fallback to regular HTTP download
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(subtitle_meta.file_url) as response:
                        if response.status == 200:
                            return await response.read()
                        else:
                            print(f"❌ HTTP download failed: {response.status}")
                            return None
            except Exception as e:
                print(f"❌ HTTP download error: {e}")
                return None
    
    def _determine_file_type(self, file_url: str, file_content: bytes) -> str:
        """Determine subtitle file type from URL and content"""
        url_lower = file_url.lower()
        
        if url_lower.endswith('.vtt') or url_lower.endswith('.webvtt'):
            return "vtt"
        elif url_lower.endswith('.srt'):
            return "srt"
        else:
            # Try to detect from content
            try:
                content_str = file_content.decode('utf-8')[:200].lower()
                if 'webvtt' in content_str:
                    return "vtt"
                elif '-->' in content_str and '\n1\n' in content_str:
                    return "srt"
            except:
                pass
        
        return "srt"  # Default fallback
    
    async def _store_processed_subtitle(self, subtitle_meta: SubtitleMetadata, 
                                      processed_data: Dict[str, Any], file_type: str) -> Optional[Dict[str, Any]]:
        """Store processed subtitle data in database"""
        try:
            subtitle_id = str(uuid.uuid4())
            
            # Store subtitle metadata
            subtitle_record = {
                "id": subtitle_id,
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
                "external_id": subtitle_meta.external_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Insert subtitle record
            subtitle_response = supabase.table("subtitles").insert(subtitle_record).execute()
            
            if subtitle_response.data:
                # Store processed data
                await self._store_processed_subtitle_data(subtitle_id, processed_data)
                
                return {
                    "subtitle_id": subtitle_id,
                    "processed_data": processed_data,
                    "source": subtitle_meta.source.value,
                    "external_id": subtitle_meta.external_id
                }
            
        except Exception as e:
            print(f"❌ Error storing processed subtitle: {e}")
            return None
    
    async def _store_processed_subtitle_data(self, subtitle_id: str, processed_data: Dict[str, Any]):
        """Store processed subtitle cues and segments"""
        try:
            # Store cues in batches
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
            print(f"❌ Error storing processed data: {e}")
    
    async def cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        await self.cache.cleanup_expired_cache()
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        cache_stats = self.cache.get_cache_stats()
        
        stats = {
            "cache_stats": cache_stats,
            "supported_languages": self.supported_languages,
            "service_stats": self.service_stats,
            "external_apis": {},
            "configuration": {
                "max_external_requests_per_movie": self.max_external_requests_per_movie,
                "auto_process_downloaded": self.auto_process_downloaded,
                "max_concurrent_downloads": self.max_concurrent_downloads
            }
        }
        
        # Add API stats
        if self.opensubtitles:
            stats["external_apis"]["opensubtitles"] = {
                "available": True,
                **self.opensubtitles.get_api_stats()
            }
        else:
            stats["external_apis"]["opensubtitles"] = {
                "available": False,
                "error": "API key not configured"
            }
        
        return stats
    
    async def close(self):
        """Clean up resources"""
        if self.opensubtitles:
            await self.opensubtitles.close()

# Global service instance
subtitle_service = MultiLanguageSubtitleService()

# FastAPI dependency
async def get_subtitle_service() -> MultiLanguageSubtitleService:
    """FastAPI dependency to get subtitle service"""
    return subtitle_service

# Utility functions for easy integration
async def search_subtitles_for_movie(movie_id: str, language: str, 
                                   movie_title: str = "", auto_fetch: bool = True) -> Tuple[List[Dict], str]:
    """
    Simplified function to search subtitles for a movie
    Returns serializable data suitable for API responses
    """
    service = await get_subtitle_service()
    subtitles, source = await service.search_and_cache_subtitles(
        movie_id, language, movie_title, auto_fetch
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
            "is_processed": sub.source == SubtitleSource.DATABASE
        }
        subtitle_dicts.append(subtitle_dict)
    
    return subtitle_dicts, source

async def get_all_languages_for_movie(movie_id: str, movie_title: str = "") -> Dict[str, List[Dict]]:
    """
    Get all available subtitle languages for a movie
    Returns serializable data suitable for API responses
    """
    service = await get_subtitle_service()
    all_subtitles = await service.get_all_available_languages(movie_id, movie_title)
    
    # Convert to serializable format
    result = {}
    for language, subtitles in all_subtitles.items():
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
        result[language] = subtitle_dicts
    
    return result

async def download_and_process_external_subtitle(subtitle_id: str, 
                                               movie_id: str, language: str,
                                               external_url: str, title: str,
                                               source: str = "opensubtitles") -> Optional[Dict[str, Any]]:
    """
    Download and process an external subtitle
    Returns processing results
    """
    service = await get_subtitle_service()
    
    # Create subtitle metadata
    subtitle_meta = SubtitleMetadata(
        id=subtitle_id,
        movie_id=movie_id,
        language=language,
        title=title,
        source=SubtitleSource(source),
        file_url=external_url,
        file_size=0,
        download_count=0,
        rating=0.0,
        release_info=title,
        encoding="utf-8",
        external_id=subtitle_id,
        hash_value=None,
        created_at=datetime.utcnow()
    )
    
    return await service.download_and_process_subtitle(subtitle_meta)

# Background task for cache maintenance
async def cleanup_subtitle_cache():
    """Background task to clean up expired cache"""
    service = await get_subtitle_service()
    await service.cleanup_expired_cache()
    print("✅ Subtitle cache cleanup completed")

# Health check function
async def check_subtitle_service_health() -> Dict[str, Any]:
    """Check the health of the subtitle service"""
    service = await get_subtitle_service()
    stats = service.get_service_stats()
    
    health_status = {
        "status": "healthy",
        "service": "multi_language_subtitle_service",
        "timestamp": datetime.utcnow().isoformat(),
        "cache_health": {
            "memory_cache_size": stats["cache_stats"]["memory_cache_size"],
            "hit_ratio": stats["cache_stats"]["hit_ratio"],
            "total_requests": stats["cache_stats"]["total_requests"]
        },
        "external_apis": stats["external_apis"],
        "supported_languages_count": len(stats["supported_languages"])
    }
    
    # Check if any external APIs are available
    apis_available = any(api.get("available", False) for api in stats["external_apis"].values())
    if not apis_available:
        health_status["status"] = "degraded"
        health_status["warning"] = "No external subtitle APIs available"
    
    return health_status