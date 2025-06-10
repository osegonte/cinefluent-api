#!/usr/bin/env python3
"""
CineFluent Anime Subtitle Processing Pipeline
Downloads, processes, and feeds subtitle files into the learning system
"""

import os
import json
import uuid
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import your existing modules
try:
    from database import supabase
    from subtitle_processor import process_subtitle_file
    print("✅ Imported existing modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the project directory and have dependencies installed")
    exit(1)

class AnimeSubtitlePipeline:
    """Pipeline for processing anime subtitles and feeding them to CineFluent"""
    
    def __init__(self):
        self.supported_languages = ['en', 'ja', 'es', 'fr', 'de', 'pt', 'it', 'ko', 'zh']
        self.subtitle_formats = ['.srt', '.vtt', '.ass', '.ssa']
        
        # Create directories for subtitle storage
        self.subtitle_dir = Path("subtitles")
        self.subtitle_dir.mkdir(exist_ok=True)
        
        # Popular anime series for subtitle sourcing
        self.anime_series = {
            "my_hero_academia": {
                "name": "My Hero Academia",
                "languages": ["en", "ja", "es"],
            },
            "demon_slayer": {
                "name": "Demon Slayer",
                "languages": ["en", "ja", "es", "fr"],
            },
            "jujutsu_kaisen": {
                "name": "Jujutsu Kaisen", 
                "languages": ["en", "ja", "es"],
            },
            "attack_on_titan": {
                "name": "Attack on Titan",
                "languages": ["en", "ja", "es", "fr", "de"],
            }
        }
    
    def detect_language_from_filename(self, filename: str) -> str:
        """Detect language from subtitle filename"""
        filename_lower = filename.lower()
        
        language_patterns = {
            'en': ['english', 'eng', '.en.', 'en_'],
            'ja': ['japanese', 'jpn', '.ja.', 'jp_'],
            'es': ['spanish', 'spa', '.es.', 'es_'],
            'fr': ['french', 'fra', '.fr.', 'fr_'],
            'de': ['german', 'ger', '.de.', 'de_'],
        }
        
        for lang_code, patterns in language_patterns.items():
            for pattern in patterns:
                if pattern in filename_lower:
                    return lang_code
        
        return 'en'  # Default to English
    
    def get_movie_id_by_title(self, title_pattern: str) -> Optional[str]:
        """Get movie ID from database by title pattern"""
        try:
            response = supabase.table("movies")\
                .select("id, title")\
                .ilike("title", f"%{title_pattern}%")\
                .limit(1)\
                .execute()
            
            if response.data:
                return response.data[0]["id"]
            return None
        except Exception as e:
            print(f"❌ Error getting movie ID: {e}")
            return None
    
    def process_subtitle_file_pipeline(self, subtitle_path: Path, movie_id: str, language: str, title: str) -> bool:
        """Process a subtitle file through the CineFluent pipeline"""
        try:
            print(f"�� Processing subtitle: {subtitle_path}")
            
            # Read subtitle file
            with open(subtitle_path, 'rb') as f:
                file_content = f.read()
            
            # Determine file type
            file_extension = subtitle_path.suffix.lower()
            if file_extension == '.srt':
                file_type = 'srt'
            elif file_extension in ['.vtt', '.webvtt']:
                file_type = 'vtt'
            else:
                print(f"⚠️ Unsupported file type: {file_extension}")
                return False
            
            # Process through your existing pipeline
            print(f"🧠 Running NLP processing for {file_type} file...")
            processed_data = process_subtitle_file(file_content, file_type, movie_id)
            
            # Store subtitle metadata in database
            subtitle_id = str(uuid.uuid4())
            subtitle_record = {
                "id": subtitle_id,
                "movie_id": movie_id,
                "language": language,
                "title": title,
                "file_type": file_type,
                "total_cues": processed_data["total_cues"],
                "total_segments": processed_data["total_segments"],
                "duration": processed_data["duration"],
                "avg_difficulty": processed_data["avg_difficulty"],
                "vocabulary_count": processed_data["vocabulary_count"],
                "uploaded_by": "system",
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Insert subtitle record
            supabase.table("subtitles").insert(subtitle_record).execute()
            print(f"✅ Saved subtitle metadata: {subtitle_id}")
            
            # Store processed cues
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
                print(f"✅ Inserted {len(cues_data)} subtitle cues")
            
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
                print(f"✅ Inserted {len(segments_data)} learning segments")
            
            print(f"🎉 Successfully processed subtitle with {processed_data['vocabulary_count']} vocabulary words")
            return True
            
        except Exception as e:
            print(f"❌ Subtitle processing failed: {e}")
            return False
    
    def process_local_subtitle_directory(self, directory_path: str) -> Dict[str, Any]:
        """Process all subtitle files in a local directory"""
        subtitle_dir = Path(directory_path)
        
        if not subtitle_dir.exists():
            print(f"❌ Directory not found: {directory_path}")
            return {"error": "Directory not found"}
        
        print(f"📁 Processing subtitles from: {subtitle_dir}")
        
        results = {
            "processed": 0,
            "failed": 0,
            "files": []
        }
        
        # Find all subtitle files
        subtitle_files = []
        for ext in self.subtitle_formats:
            subtitle_files.extend(subtitle_dir.glob(f"**/*{ext}"))
        
        print(f"📊 Found {len(subtitle_files)} subtitle files")
        
        for subtitle_file in subtitle_files:
            try:
                # Extract info from filename
                filename = subtitle_file.stem
                language = self.detect_language_from_filename(filename)
                
                # Try to match to anime series
                movie_id = None
                series_name = None
                
                for series_key, series_info in self.anime_series.items():
                    series_name_lower = series_info["name"].lower().replace(" ", "").replace("-", "")
                    filename_lower = filename.lower().replace(" ", "").replace("-", "")
                    
                    if series_name_lower in filename_lower or any(word in filename_lower for word in series_name_lower.split()):
                        # Find movie in database
                        movie_id = self.get_movie_id_by_title(series_info["name"])
                        series_name = series_info["name"]
                        break
                
                if not movie_id:
                    print(f"⚠️ Could not match subtitle to anime series: {filename}")
                    results["failed"] += 1
                    continue
                
                # Process the subtitle
                title = f"{series_name} - {language.upper()} Subtitles"
                
                if self.process_subtitle_file_pipeline(subtitle_file, movie_id, language, title):
                    results["processed"] += 1
                    results["files"].append({
                        "file": str(subtitle_file),
                        "series": series_name,
                        "language": language,
                        "status": "success"
                    })
                else:
                    results["failed"] += 1
                    results["files"].append({
                        "file": str(subtitle_file),
                        "series": series_name,
                        "language": language,
                        "status": "failed"
                    })
                
                # Small delay to avoid overwhelming the database
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error processing {subtitle_file}: {e}")
                results["failed"] += 1
        
        return results
    
    def create_sample_subtitle_structure(self) -> None:
        """Create sample directory structure for organizing subtitles"""
        sample_dir = self.subtitle_dir / "sample_structure"
        sample_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for each anime
        for series_key, series_info in self.anime_series.items():
            series_dir = sample_dir / series_key
            series_dir.mkdir(exist_ok=True)
            
            # Create language subdirectories
            for lang in series_info["languages"]:
                lang_dir = series_dir / lang
                lang_dir.mkdir(exist_ok=True)
        
        # Create README
        readme_content = """# CineFluent Subtitle Organization Guide

## Directory Structure
subtitles/
├── my_hero_academia/
│   ├── en/
│   ├── ja/
│   └── es/
├── demon_slayer/
│   ├── en/
│   ├── ja/
│   ├── es/
│   └── fr/
└── [other_anime]/
└── [languages]/

## File Naming Convention
- `SeriesName_S01E01_Language.srt`
- `MyHeroAcademia_S01E01_English.srt`
- `DemonSlayer_S01E01_Japanese.srt`

## Supported Formats
- .srt (SubRip)
- .vtt (WebVTT)
- .ass (Advanced SubStation Alpha)
- .ssa (SubStation Alpha)

## Supported Languages
- en (English)
- ja (Japanese)
- es (Spanish)
- fr (French)
- de (German)
- pt (Portuguese)
- it (Italian)
- ko (Korean)
- zh (Chinese)

## Usage
1. Place subtitle files in appropriate directories
2. Run: `python3 subtitle_pipeline.py process-local subtitles/`
3. The system will automatically:
   - Detect language from filename
   - Match to anime series
   - Process with NLP
   - Extract vocabulary
   - Create learning segments
   - Generate quizzes
"""
        
        with open(sample_dir / "README.md", "w") as f:
            f.write(readme_content)
        
        print(f"📁 Created sample structure at: {sample_dir}")
        print("📖 See README.md for organization guidelines")

def main():
    """Main execution function"""
    import sys
    
    pipeline = AnimeSubtitlePipeline()
    
    if len(sys.argv) < 2:
        print("""
🎬 CineFluent Anime Subtitle Pipeline

Usage:
    python3 subtitle_pipeline.py process-local <directory>    # Process local subtitle directory
    python3 subtitle_pipeline.py create-structure            # Create sample directory structure
    python3 subtitle_pipeline.py verify                      # Verify existing subtitles in database

Examples:
    python3 subtitle_pipeline.py process-local subtitles/
    python3 subtitle_pipeline.py create-structure
        """)
        return
    
    command = sys.argv[1]
    
    if command == "process-local":
        if len(sys.argv) < 3:
            print("❌ Please specify directory path")
            return
        
        directory = sys.argv[2]
        print(f"🚀 Processing subtitles from: {directory}")
        
        start_time = datetime.now()
        results = pipeline.process_local_subtitle_directory(directory)
        end_time = datetime.now()
        
        print("\n" + "="*60)
        print("🎬 SUBTITLE PROCESSING COMPLETE")
        print("="*60)
        print(f"⏰ Duration: {end_time - start_time}")
        print(f"✅ Processed: {results['processed']} files")
        print(f"❌ Failed: {results['failed']} files")
        
        if results.get("files"):
            print("\n📁 File Details:")
            for file_info in results["files"]:
                status_icon = "✅" if file_info["status"] == "success" else "❌"
                print(f"   {status_icon} {file_info['series']} ({file_info['language']})")
    
    elif command == "create-structure":
        pipeline.create_sample_subtitle_structure()
        print("✅ Sample structure created! Check subtitles/sample_structure/")
    
    elif command == "verify":
        print("🔍 Verifying subtitles in database...")
        try:
            response = supabase.table("subtitles").select("*", count="exact").execute()
            print(f"📊 Total subtitles in database: {response.count}")
            
            if response.data:
                print("\n📋 Recent subtitles:")
                for subtitle in response.data[:5]:
                    print(f"   📺 {subtitle['title']} ({subtitle['language']}) - {subtitle['total_cues']} cues")
        except Exception as e:
            print(f"❌ Verification failed: {e}")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
