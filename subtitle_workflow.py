#!/usr/bin/env python3
"""
CineFluent - Subtitle Processing Workflow
Process subtitle files and create learning content
"""

import os
import json
import glob
from typing import List, Dict, Optional
from pathlib import Path
import requests
from datetime import datetime

# Import our subtitle processor
try:
    from subtitle_processor import process_subtitle_file
    from database import supabase, test_connection
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the project directory and dependencies are installed")
    exit(1)

class SubtitleWorkflow:
    """Manages the complete subtitle processing workflow"""
    
    def __init__(self):
        self.base_dir = Path(".")
        self.subtitles_dir = self.base_dir / "subtitles" / "organized"
        self.processed_dir = self.base_dir / "subtitles" / "processed"
        
        # Create directories if they don't exist
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Anime series mapping
        self.anime_series = {
            "my_hero_academia": "My Hero Academia",
            "jujutsu_kaisen": "Jujutsu Kaisen", 
            "attack_on_titan": "Attack on Titan",
            "demon_slayer": "Demon Slayer"
        }
    
    def find_subtitle_files(self) -> Dict[str, List[str]]:
        """Find all subtitle files in organized directories"""
        subtitle_files = {}
        
        for series_dir in self.anime_series.keys():
            series_path = self.subtitles_dir / series_dir
            if series_path.exists():
                # Find SRT and VTT files
                srt_files = list(series_path.glob("*.srt"))
                vtt_files = list(series_path.glob("*.vtt"))
                webvtt_files = list(series_path.glob("*.webvtt"))
                
                all_files = srt_files + vtt_files + webvtt_files
                subtitle_files[series_dir] = [str(f) for f in all_files]
            else:
                subtitle_files[series_dir] = []
        
        return subtitle_files
    
    def get_anime_episodes_from_db(self) -> Dict[str, List[Dict]]:
        """Get anime episodes from database"""
        print("📊 Fetching anime episodes from database...")
        
        try:
            response = supabase.table("movies").select("*").execute()
            
            if not response.data:
                print("❌ No episodes found in database")
                return {}
            
            # Group by series
            episodes_by_series = {}
            for episode in response.data:
                title = episode.get("title", "")
                
                # Determine series based on title
                series_key = None
                if "My Hero Academia" in title or "Boku no Hero" in title:
                    series_key = "my_hero_academia"
                elif "Jujutsu Kaisen" in title:
                    series_key = "jujutsu_kaisen"
                elif "Attack on Titan" in title or "Shingeki no Kyojin" in title:
                    series_key = "attack_on_titan"
                elif "Demon Slayer" in title or "Kimetsu no Yaiba" in title:
                    series_key = "demon_slayer"
                
                if series_key:
                    if series_key not in episodes_by_series:
                        episodes_by_series[series_key] = []
                    episodes_by_series[series_key].append(episode)
            
            # Print summary
            total_episodes = sum(len(episodes) for episodes in episodes_by_series.values())
            print(f"✅ Found {total_episodes} episodes across {len(episodes_by_series)} series")
            
            for series, episodes in episodes_by_series.items():
                series_name = self.anime_series.get(series, series)
                print(f"  📺 {series_name}: {len(episodes)} episodes")
            
            return episodes_by_series
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return {}
    
    def create_sample_subtitle_files(self):
        """Create sample subtitle files for testing"""
        print("📝 Creating sample subtitle files for testing...")
        
        sample_srt_content = """1
00:00:01,000 --> 00:00:04,000
Welcome to the world of heroes!

2
00:00:04,500 --> 00:00:08,000
My name is Izuku Midoriya, and this is my story.

3
00:00:08,500 --> 00:00:12,000
I want to become the greatest hero, just like All Might.

4
00:00:12,500 --> 00:00:16,000
But there's one problem - I was born without a quirk.

5
00:00:16,500 --> 00:00:20,000
In a world where 80% of people have superpowers, I'm completely ordinary.
"""
        
        # Create sample files for each series
        for series_dir in self.anime_series.keys():
            series_path = self.subtitles_dir / series_dir
            series_path.mkdir(parents=True, exist_ok=True)
            
            # Create a sample subtitle file
            sample_file = series_path / f"{series_dir}_episode_01_en.srt"
            
            if not sample_file.exists():
                with open(sample_file, 'w', encoding='utf-8') as f:
                    # Customize content for each series
                    if series_dir == "my_hero_academia":
                        f.write(sample_srt_content)
                    elif series_dir == "jujutsu_kaisen":
                        content = sample_srt_content.replace("heroes", "sorcerers")
                        content = content.replace("Izuku Midoriya", "Yuji Itadori")
                        content = content.replace("All Might", "Gojo Sensei")
                        content = content.replace("quirk", "cursed energy")
                        f.write(content)
                    elif series_dir == "attack_on_titan":
                        content = sample_srt_content.replace("heroes", "soldiers")
                        content = content.replace("Izuku Midoriya", "Eren Yeager")
                        content = content.replace("All Might", "Captain Levi")
                        content = content.replace("quirk", "titan power")
                        f.write(content)
                    elif series_dir == "demon_slayer":
                        content = sample_srt_content.replace("heroes", "demon slayers")
                        content = content.replace("Izuku Midoriya", "Tanjiro Kamado")
                        content = content.replace("All Might", "Hashira")
                        content = content.replace("quirk", "breathing technique")
                        f.write(content)
                
                print(f"  ✅ Created sample: {sample_file}")
    
    def process_subtitle_file_wrapper(self, file_path: str, episode_id: str) -> Optional[Dict]:
        """Process a single subtitle file"""
        try:
            print(f"    📝 Processing: {Path(file_path).name}")
            
            # Read file
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Determine file type
            file_extension = Path(file_path).suffix.lower()
            file_type = file_extension[1:]  # Remove the dot
            
            if file_type == 'webvtt':
                file_type = 'vtt'
            
            # Process with our subtitle processor
            result = process_subtitle_file(file_content, file_type, episode_id)
            
            print(f"      ✅ Processed {result['total_cues']} cues into {result['total_segments']} segments")
            print(f"      📚 Found {result['vocabulary_count']} vocabulary words")
            print(f"      🎯 Average difficulty: {result['avg_difficulty']:.2f}")
            
            # Convert any remaining objects to dictionaries for JSON serialization
            def convert_to_serializable(obj):
                """Recursively convert objects to JSON-serializable format"""
                if hasattr(obj, '__dict__'):
                    return obj.__dict__
                elif isinstance(obj, list):
                    return [convert_to_serializable(item) for item in obj]
                elif isinstance(obj, dict):
                    return {key: convert_to_serializable(value) for key, value in obj.items()}
                else:
                    return obj
            
            # Ensure all data is serializable
            serializable_result = convert_to_serializable(result)
            
            return serializable_result
            
        except Exception as e:
            print(f"      ❌ Error processing {file_path}: {e}")
            return None
    
    def match_subtitles_to_episodes(self, subtitle_files: Dict[str, List[str]], 
                                   episodes: Dict[str, List[Dict]]) -> List[Dict]:
        """Match subtitle files to episodes in database"""
        matches = []
        
        for series, files in subtitle_files.items():
            if series in episodes and files:
                series_episodes = episodes[series]
                
                print(f"\n📺 {self.anime_series[series]}:")
                print(f"  Subtitle files: {len(files)}")
                print(f"  Episodes in DB: {len(series_episodes)}")
                
                # Simple matching - match first N files to first N episodes
                for i, file_path in enumerate(files):
                    if i < len(series_episodes):
                        episode = series_episodes[i]
                        matches.append({
                            'file_path': file_path,
                            'episode_id': episode['id'],
                            'episode_title': episode['title'],
                            'series': series
                        })
                        print(f"    ✅ Matched: {Path(file_path).name} → {episode['title']}")
                    else:
                        print(f"    ⚠️  No episode match for: {Path(file_path).name}")
        
        return matches
    
    def process_all_subtitles(self):
        """Process all subtitle files"""
        print("🎌 CineFluent - Subtitle Processing Workflow")
        print("=" * 50)
        
        # Check database connection
        if not test_connection():
            print("❌ Database connection failed")
            return False
        
        # Get episodes from database
        episodes = self.get_anime_episodes_from_db()
        if not episodes:
            print("❌ No episodes found in database")
            return False
        
        # Find subtitle files
        subtitle_files = self.find_subtitle_files()
        total_files = sum(len(files) for files in subtitle_files.values())
        
        if total_files == 0:
            print("📝 No subtitle files found. Creating samples...")
            self.create_sample_subtitle_files()
            subtitle_files = self.find_subtitle_files()
            total_files = sum(len(files) for files in subtitle_files.values())
        
        print(f"\n📊 Found {total_files} subtitle files")
        
        # Match files to episodes
        matches = self.match_subtitles_to_episodes(subtitle_files, episodes)
        
        if not matches:
            print("❌ No subtitle-episode matches found")
            return False
        
        print(f"\n🔄 Processing {len(matches)} subtitle files...")
        
        # Process each match
        processed_count = 0
        failed_count = 0
        
        for match in matches:
            print(f"\n📝 Processing: {match['episode_title']}")
            
            result = self.process_subtitle_file_wrapper(
                match['file_path'], 
                match['episode_id']
            )
            
            if result:
                # Save processed data
                output_file = self.processed_dir / f"{match['episode_id']}_processed.json"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                processed_count += 1
            else:
                failed_count += 1
        
        # Summary
        print(f"\n📋 Processing Summary:")
        print(f"✅ Processed: {processed_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📁 Results saved to: {self.processed_dir}")
        
        return processed_count > 0
    
    def get_processing_status(self):
        """Get current processing status"""
        print("📊 Current Processing Status")
        print("=" * 30)
        
        # Check database
        db_connected = test_connection()
        print(f"Database: {'✅ Connected' if db_connected else '❌ Disconnected'}")
        
        # Check subtitle files
        subtitle_files = self.find_subtitle_files()
        total_files = sum(len(files) for files in subtitle_files.values())
        print(f"Subtitle files: {total_files}")
        
        # Check processed files
        processed_files = list(self.processed_dir.glob("*_processed.json"))
        print(f"Processed files: {len(processed_files)}")
        
        # Check episodes in database
        if db_connected:
            try:
                response = supabase.table("movies").select("id").execute()
                episode_count = len(response.data) if response.data else 0
                print(f"Episodes in DB: {episode_count}")
            except:
                print("Episodes in DB: Error fetching")
        
        return {
            'db_connected': db_connected,
            'subtitle_files': total_files,
            'processed_files': len(processed_files),
            'ready_for_processing': db_connected and total_files > 0
        }

def main():
    """Main function"""
    import sys
    
    workflow = SubtitleWorkflow()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "status":
            workflow.get_processing_status()
        elif command == "samples":
            workflow.create_sample_subtitle_files()
            print("✅ Sample subtitle files created")
        elif command == "process":
            workflow.process_all_subtitles()
        else:
            print("Usage: python subtitle_workflow.py [status|samples|process]")
    else:
        # Default: show status and process if ready
        status = workflow.get_processing_status()
        
        if status['ready_for_processing']:
            print("\n🚀 Ready for processing! Run with 'process' argument to start")
        else:
            print("\n⚠️  Not ready for processing. Check database connection and subtitle files.")

if __name__ == "__main__":
    main()