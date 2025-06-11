"""
CineFluent Database Manager
Consolidates database operations and anime population functionality
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Import from project root
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database import supabase, supabase_admin
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Database not available: {e}")
    DATABASE_AVAILABLE = False

@dataclass
class AnimeEpisode:
    """Represents a single anime episode"""
    title: str
    description: str
    duration: int
    release_year: int
    difficulty_level: str
    languages: List[str]
    genres: List[str]
    thumbnail_url: str
    video_url: str
    is_premium: bool
    vocabulary_count: int
    imdb_rating: float
    series_name: str
    episode_number: int
    season_number: int
    total_episodes_in_season: int

class DatabaseManager:
    """Manages database operations and content population"""
    
    def __init__(self):
        self.anime_series = self._define_anime_series()
        
    def _define_anime_series(self) -> Dict[str, Dict]:
        """Define the anime series with metadata"""
        return {
            "my_hero_academia": {
                "name": "My Hero Academia",
                "japanese_name": "Boku no Hero Academia",
                "season": 1,
                "total_episodes": 13,
                "difficulty": "beginner",
                "release_year": 2016,
                "genres": ["anime", "action", "school", "superhero"],
                "description_template": "In a world where superpowers called 'Quirks' are the norm, Izuku Midoriya dreams of becoming a hero despite being born without powers.",
                "base_imdb_rating": 8.7,
                "vocabulary_range": (300, 450),
                "thumbnail_base": "https://m.media-amazon.com/images/M/MV5BNTc0YmJkMTQtYjU0MS00NmM5LWJjMDUtZGQzMzRkNzM1ZjIzXkEyXkFqcGdeQXVyMzI2Mzc4OTY@._V1_.jpg",
                "video_base": "https://example.com/mha/s1",
                "is_premium": False
            },
            "demon_slayer": {
                "name": "Demon Slayer",
                "japanese_name": "Kimetsu no Yaiba",
                "season": 1,
                "total_episodes": 26,
                "difficulty": "intermediate",
                "release_year": 2019,
                "genres": ["anime", "action", "supernatural", "historical"],
                "description_template": "Tanjiro Kamado becomes a demon slayer to save his sister Nezuko and avenge his family.",
                "base_imdb_rating": 8.9,
                "vocabulary_range": (450, 600),
                "thumbnail_base": "https://m.media-amazon.com/images/M/MV5BZjZjNzI5MDctY2Y4YS00NmM4LWJjMjUtMGJjNzhkMzA5NTI1XkEyXkFqcGdeQXVyNjc3MjQzNTI@._V1_.jpg",
                "video_base": "https://example.com/demon-slayer/s1",
                "is_premium": False
            },
            "jujutsu_kaisen": {
                "name": "Jujutsu Kaisen",
                "japanese_name": "Jujutsu Kaisen",
                "season": 1,
                "total_episodes": 24,
                "difficulty": "beginner",
                "release_year": 2020,
                "genres": ["anime", "action", "supernatural", "school"],
                "description_template": "Yuji Itadori joins a secret organization of sorcerers to eliminate cursed spirits and find the remaining fingers of a powerful curse.",
                "base_imdb_rating": 8.8,
                "vocabulary_range": (350, 500),
                "thumbnail_base": "https://m.media-amazon.com/images/M/MV5BNjcyMjg0MjQtMDRjMC00NzI3LWE4MDQtYTVkN2RmODMxMDIwXkEyXkFqcGdeQXVyMTA4NjE0NjEy._V1_.jpg",
                "video_base": "https://example.com/jujutsu-kaisen/s1",
                "is_premium": False
            },
            "attack_on_titan": {
                "name": "Attack on Titan",
                "japanese_name": "Shingeki no Kyojin",
                "season": 1,
                "total_episodes": 25,
                "difficulty": "advanced",
                "release_year": 2013,
                "genres": ["anime", "action", "drama", "thriller"],
                "description_template": "Humanity fights for survival against giant humanoid Titans that threaten their existence.",
                "base_imdb_rating": 9.0,
                "vocabulary_range": (650, 800),
                "thumbnail_base": "https://m.media-amazon.com/images/M/MV5BNzUxNDU5NTItNDJhZi00NjlkLTlkY2YtNDBhM2E3YTY5ZjNmXkEyXkFqcGdeQXVyNjAwNDUxODI@._V1_.jpg",
                "video_base": "https://example.com/attack-on-titan/s1",
                "is_premium": True
            }
        }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            stats = {}
            
            # Movies/Episodes
            movies_response = supabase.table("movies").select("*", count="exact").execute()
            stats["total_episodes"] = movies_response.count
            
            # Breakdown by difficulty
            for difficulty in ["beginner", "intermediate", "advanced"]:
                diff_response = supabase.table("movies")\
                    .select("*", count="exact")\
                    .eq("difficulty_level", difficulty)\
                    .execute()
                stats[f"{difficulty}_episodes"] = diff_response.count
            
            # Premium vs Free
            premium_response = supabase.table("movies")\
                .select("*", count="exact")\
                .eq("is_premium", True)\
                .execute()
            stats["premium_episodes"] = premium_response.count
            stats["free_episodes"] = stats["total_episodes"] - premium_response.count
            
            # Subtitles
            subtitles_response = supabase.table("subtitles").select("*", count="exact").execute()
            stats["total_subtitles"] = subtitles_response.count
            
            # Learning segments
            segments_response = supabase.table("learning_segments").select("*", count="exact").execute()
            stats["learning_segments"] = segments_response.count
            
            return stats
            
        except Exception as e:
            return {"error": str(e)}
    
    def populate_anime_episodes(self, phase: int = 1) -> Dict[str, Any]:
        """Populate database with anime episodes"""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            start_time = datetime.now()
            results = {"episodes_added": 0, "series_processed": 0}
            
            if phase == 1:
                # Phase 1: Priority series
                target_series = ["my_hero_academia", "jujutsu_kaisen", "attack_on_titan", "demon_slayer"]
            else:
                # All series
                target_series = list(self.anime_series.keys())
            
            for series_key in target_series:
                series_info = self.anime_series[series_key]
                episodes_added = self._populate_single_series(series_key, series_info)
                results["episodes_added"] += episodes_added
                results["series_processed"] += 1
            
            end_time = datetime.now()
            results["duration"] = str(end_time - start_time)
            results["success"] = True
            
            return results
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _populate_single_series(self, series_key: str, series_info: Dict) -> int:
        """Populate episodes for a single series"""
        episodes_added = 0
        
        for episode_num in range(1, series_info["total_episodes"] + 1):
            episode = self._create_episode(series_key, series_info, episode_num)
            
            episode_data = {
                "id": str(uuid.uuid4()),
                "title": episode.title,
                "description": episode.description,
                "duration": episode.duration,
                "release_year": episode.release_year,
                "difficulty_level": episode.difficulty_level,
                "languages": json.dumps(episode.languages),
                "genres": json.dumps(episode.genres),
                "thumbnail_url": episode.thumbnail_url,
                "video_url": episode.video_url,
                "is_premium": episode.is_premium,
                "vocabulary_count": episode.vocabulary_count,
                "imdb_rating": episode.imdb_rating,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            try:
                response = supabase_admin.table("movies").insert(episode_data).execute()
                if response.data:
                    episodes_added += 1
            except Exception as e:
                print(f"Failed to insert episode {episode_num} of {series_key}: {e}")
        
        return episodes_added
    
    def _create_episode(self, series_key: str, series_info: Dict, episode_num: int) -> AnimeEpisode:
        """Create a single anime episode"""
        import random
        
        # Generate episode title
        title = f"{series_info['name']} - Episode {episode_num}"
        
        # Generate description
        description = f"{series_info['description_template']} Episode {episode_num} continues the epic journey."
        
        # Calculate episode rating with variation
        base_rating = series_info['base_imdb_rating']
        variation = random.uniform(-0.2, 0.3)
        episode_rating = round(min(10.0, max(1.0, base_rating + variation)), 1)
        
        # Calculate vocabulary count
        min_vocab, max_vocab = series_info['vocabulary_range']
        vocabulary_count = random.randint(min_vocab, max_vocab)
        
        # Standard languages
        languages = ["ja", "en"]
        if series_key in ["attack_on_titan", "demon_slayer"]:
            languages.extend(["es", "fr", "de"])
        elif series_key in ["my_hero_academia", "jujutsu_kaisen"]:
            languages.extend(["es"])
        
        return AnimeEpisode(
            title=title,
            description=description,
            duration=24,  # Standard anime episode duration
            release_year=series_info['release_year'],
            difficulty_level=series_info['difficulty'],
            languages=languages,
            genres=series_info['genres'],
            thumbnail_url=f"{series_info['thumbnail_base']}?ep={episode_num}",
            video_url=f"{series_info['video_base']}/episode-{episode_num:02d}.mp4",
            is_premium=series_info['is_premium'],
            vocabulary_count=vocabulary_count,
            imdb_rating=episode_rating,
            series_name=series_info['name'],
            episode_number=episode_num,
            season_number=series_info['season'],
            total_episodes_in_season=series_info['total_episodes']
        )

# Export main class
__all__ = ['DatabaseManager']
