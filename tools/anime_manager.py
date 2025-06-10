#!/usr/bin/env python3
"""
CineFluent Anime Management Tool
Comprehensive tool for managing anime content and subtitles
"""

import os
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database import supabase, supabase_admin
    DATABASE_AVAILABLE = True
    print("✅ Database connection available")
except ImportError as e:
    print(f"⚠️ Database not available: {e}")
    DATABASE_AVAILABLE = False

class AnimeManager:
    """Comprehensive anime content management"""
    
    def __init__(self):
        self.anime_series = {
            "my_hero_academia": {
                "name": "My Hero Academia",
                "total_episodes": 13,
                "difficulty": "beginner",
                "languages": ["en", "ja", "es"],
                "is_premium": False
            },
            "jujutsu_kaisen": {
                "name": "Jujutsu Kaisen",
                "total_episodes": 24,
                "difficulty": "beginner", 
                "languages": ["en", "ja", "es"],
                "is_premium": False
            },
            "attack_on_titan": {
                "name": "Attack on Titan",
                "total_episodes": 25,
                "difficulty": "advanced",
                "languages": ["en", "ja", "es", "fr", "de"],
                "is_premium": True
            },
            "demon_slayer": {
                "name": "Demon Slayer",
                "total_episodes": 26,
                "difficulty": "intermediate",
                "languages": ["en", "ja", "es", "fr"],
                "is_premium": False
            }
        }
    
    def show_database_stats(self):
        """Show current database statistics"""
        if not DATABASE_AVAILABLE:
            print("❌ Database not available")
            return
        
        try:
            print("📊 Database Statistics:")
            
            # Movies/Episodes
            movies_response = supabase.table("movies").select("*", count="exact").execute()
            total_episodes = movies_response.count
            print(f"  📺 Total Episodes: {total_episodes}")
            
            if total_episodes > 0:
                # Breakdown by difficulty
                for difficulty in ["beginner", "intermediate", "advanced"]:
                    diff_response = supabase.table("movies")\
                        .select("*", count="exact")\
                        .eq("difficulty_level", difficulty)\
                        .execute()
                    print(f"    {difficulty.capitalize()}: {diff_response.count}")
                
                # Premium vs Free
                premium_response = supabase.table("movies")\
                    .select("*", count="exact")\
                    .eq("is_premium", True)\
                    .execute()
                free_count = total_episodes - premium_response.count
                print(f"    Premium: {premium_response.count} | Free: {free_count}")
            
            # Subtitles
            subtitles_response = supabase.table("subtitles").select("*", count="exact").execute()
            print(f"  📄 Total Subtitles: {subtitles_response.count}")
            
            # Learning segments
            segments_response = supabase.table("learning_segments").select("*", count="exact").execute()
            print(f"  🧠 Learning Segments: {segments_response.count}")
            
        except Exception as e:
            print(f"❌ Failed to get stats: {e}")
    
    def verify_subtitle_structure(self):
        """Verify subtitle directory structure"""
        print("📁 Subtitle Directory Analysis:")
        
        subtitle_dir = Path("subtitles")
        if not subtitle_dir.exists():
            print("  ❌ Subtitles directory not found")
            return
        
        organized_dir = subtitle_dir / "organized"
        if organized_dir.exists():
            print(f"  ✅ Organized structure exists: {organized_dir}")
            
            for series_key, series_info in self.anime_series.items():
                series_dir = organized_dir / series_key
                if series_dir.exists():
                    print(f"    📺 {series_info['name']}: {series_dir}")
                    
                    # Count subtitle files
                    subtitle_count = 0
                    for lang in series_info['languages']:
                        lang_dir = series_dir / lang
                        if lang_dir.exists():
                            files = list(lang_dir.glob("*.srt")) + list(lang_dir.glob("*.vtt"))
                            subtitle_count += len(files)
                            if files:
                                print(f"      🌍 {lang}: {len(files)} files")
                    
                    if subtitle_count == 0:
                        print(f"      💡 No subtitle files found - ready for upload")
        else:
            print("  💡 Run subtitle structure creation first")

def main():
    """Main execution function"""
    if len(sys.argv) < 2:
        print("""
🎌 CineFluent Anime Manager

Usage:
    python3 anime_manager.py stats              # Show database statistics
    python3 anime_manager.py verify             # Verify project structure
    python3 anime_manager.py subtitles          # Analyze subtitle structure
    python3 anime_manager.py info               # Show complete project info

Examples:
    python3 tools/anime_manager.py stats
    python3 tools/anime_manager.py verify
        """)
        return
    
    manager = AnimeManager()
    command = sys.argv[1]
    
    if command == "stats":
        manager.show_database_stats()
    
    elif command == "verify":
        manager.show_database_stats()
        print()
        manager.verify_subtitle_structure()
    
    elif command == "subtitles":
        manager.verify_subtitle_structure()
    
    elif command == "info":
        print("🎌 CineFluent Project Information")
        print("=" * 50)
        manager.show_database_stats()
        print()
        manager.verify_subtitle_structure()
        
        print(f"\n📈 Next Steps:")
        print("  1. Add subtitle files to subtitles/organized/[anime]/[language]/")
        print("  2. Process subtitles through learning pipeline")
        print("  3. Test frontend with populated content")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
