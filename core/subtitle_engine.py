"""
CineFluent Unified Subtitle Engine
Consolidates subtitle processing, API endpoints, and workflow management
"""

import re
import json
import spacy
import nltk
import uuid
import webvtt
import pysrt
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import database and auth from project root
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import supabase, supabase_admin
from auth import get_current_user, get_optional_user, User

@dataclass
class SubtitleCue:
    """Represents a single subtitle cue with timing and text"""
    id: str
    start_time: float  # seconds
    end_time: float    # seconds
    text: str
    words: List[Dict[str, Any]]  # Enriched word data
    difficulty_score: float

@dataclass
class EnrichedWord:
    """Represents a word with learning metadata"""
    word: str
    lemma: str
    pos_tag: str
    definition: str
    translations: Dict[str, str]
    difficulty_level: str
    frequency_rank: int
    context: str
    audio_url: Optional[str] = None

class SubtitleProcessor:
    """Core subtitle processing engine"""
    
    def __init__(self):
        # Load language models
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: English spaCy model not found")
            self.nlp = None
            
        # Word frequency data (simplified)
        self.word_frequencies = self._load_word_frequencies()
        
        # Difficulty thresholds
        self.difficulty_thresholds = {
            'beginner': 3000,
            'intermediate': 7000,
            'advanced': float('inf')
        }
    
    def _load_word_frequencies(self) -> Dict[str, int]:
        """Load word frequency data"""
        # Simplified frequency list - in production, use comprehensive datasets
        common_words = {
            'the': 1, 'of': 2, 'and': 3, 'a': 4, 'to': 5, 'in': 6, 'is': 7,
            'you': 8, 'that': 9, 'it': 10, 'he': 11, 'was': 12, 'for': 13,
            'on': 14, 'are': 15, 'as': 16, 'with': 17, 'his': 18, 'they': 19,
            'i': 20, 'at': 21, 'be': 22, 'this': 23, 'have': 24, 'from': 25,
            # Add more common words...
        }
        return common_words
    
    def parse_subtitle_file(self, file_content: bytes, file_type: str) -> List[SubtitleCue]:
        """Parse SRT or VTT subtitle files"""
        try:
            content_str = file_content.decode('utf-8')
            
            if file_type.lower() == 'srt':
                return self._parse_srt(content_str)
            elif file_type.lower() in ['vtt', 'webvtt']:
                return self._parse_vtt(content_str)
            else:
                raise ValueError(f"Unsupported subtitle format: {file_type}")
                
        except Exception as e:
            raise ValueError(f"Failed to parse subtitle file: {str(e)}")
    
    def _parse_srt(self, content: str) -> List[SubtitleCue]:
        """Parse SRT format subtitles"""
        try:
            subs = pysrt.from_string(content)
            cues = []
            
            for i, sub in enumerate(subs):
                start_time = self._time_to_seconds(sub.start)
                end_time = self._time_to_seconds(sub.end)
                text = self._clean_subtitle_text(sub.text)
                
                cue = SubtitleCue(
                    id=str(uuid.uuid4()),
                    start_time=start_time,
                    end_time=end_time,
                    text=text,
                    words=[],
                    difficulty_score=0.0
                )
                cues.append(cue)
            
            return cues
            
        except Exception as e:
            raise ValueError(f"Failed to parse SRT: {str(e)}")
    
    def _parse_vtt(self, content: str) -> List[SubtitleCue]:
        """Parse WebVTT format subtitles"""
        try:
            vtt_file = StringIO(content)
            captions = webvtt.read_buffer(vtt_file)
            
            cues = []
            for caption in captions:
                start_time = self._webvtt_time_to_seconds(caption.start)
                end_time = self._webvtt_time_to_seconds(caption.end)
                text = self._clean_subtitle_text(caption.text)
                
                cue = SubtitleCue(
                    id=str(uuid.uuid4()),
                    start_time=start_time,
                    end_time=end_time,
                    text=text,
                    words=[],
                    difficulty_score=0.0
                )
                cues.append(cue)
            
            return cues
            
        except Exception as e:
            raise ValueError(f"Failed to parse VTT: {str(e)}")
    
    def _time_to_seconds(self, time_obj) -> float:
        """Convert pysrt time object to seconds"""
        return (time_obj.hours * 3600 + 
                time_obj.minutes * 60 + 
                time_obj.seconds + 
                time_obj.milliseconds / 1000.0)
    
    def _webvtt_time_to_seconds(self, time_str: str) -> float:
        """Convert WebVTT time string to seconds"""
        parts = time_str.split(':')
        
        if len(parts) == 3:  # HH:MM:SS.mmm
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        elif len(parts) == 2:  # MM:SS.mmm
            minutes, seconds = parts
            return int(minutes) * 60 + float(seconds)
        else:
            raise ValueError(f"Invalid time format: {time_str}")
    
    def _clean_subtitle_text(self, text: str) -> str:
        """Clean subtitle text of formatting and artifacts"""
        text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
        text = re.sub(r'\[.*?\]', '', text)  # Remove brackets
        text = re.sub(r'\(.*?\)', '', text)  # Remove parentheses
        text = re.sub(r'♪.*?♪', '', text)   # Remove music notes
        text = ' '.join(text.split())       # Clean whitespace
        return text.strip()
    
    def enrich_subtitles(self, cues: List[SubtitleCue], target_language: str = "en") -> List[SubtitleCue]:
        """Enrich subtitle cues with learning data"""
        if not self.nlp:
            print("Warning: spaCy model not available. Skipping enrichment.")
            return cues
        
        for cue in cues:
            doc = self.nlp(cue.text)
            enriched_words = []
            
            for token in doc:
                if token.is_punct or token.is_space:
                    continue
                
                enriched_word = self._create_enriched_word(token, cue.text)
                if enriched_word:
                    enriched_words.append(enriched_word.__dict__)
            
            cue.words = enriched_words
            cue.difficulty_score = self._calculate_difficulty_score(enriched_words)
        
        return cues
    
    def _create_enriched_word(self, token, context: str) -> Optional[EnrichedWord]:
        """Create an enriched word object from a spaCy token"""
        word = token.text.lower()
        
        if len(word) < 2 or token.is_stop:
            return None
        
        frequency_rank = self.word_frequencies.get(word, 10000)
        difficulty_level = self._get_difficulty_level(frequency_rank)
        definition = self._get_word_definition(word, token.pos_)
        translations = self._get_translations(word)
        
        return EnrichedWord(
            word=word,
            lemma=token.lemma_.lower(),
            pos_tag=token.pos_,
            definition=definition,
            translations=translations,
            difficulty_level=difficulty_level,
            frequency_rank=frequency_rank,
            context=context
        )
    
    def _get_difficulty_level(self, frequency_rank: int) -> str:
        """Determine difficulty level based on word frequency"""
        if frequency_rank <= self.difficulty_thresholds['beginner']:
            return 'beginner'
        elif frequency_rank <= self.difficulty_thresholds['intermediate']:
            return 'intermediate'
        else:
            return 'advanced'
    
    def _get_word_definition(self, word: str, pos: str) -> str:
        """Get word definition - simplified version"""
        definitions = {
            'NOUN': f"A noun: {word}",
            'VERB': f"A verb: {word}",
            'ADJ': f"An adjective: {word}",
            'ADV': f"An adverb: {word}",
        }
        return definitions.get(pos, f"A word: {word}")
    
    def _get_translations(self, word: str) -> Dict[str, str]:
        """Get word translations - placeholder"""
        return {
            'es': f"{word}_es",
            'fr': f"{word}_fr", 
            'de': f"{word}_de",
            'it': f"{word}_it",
        }
    
    def _calculate_difficulty_score(self, words: List[Dict]) -> float:
        """Calculate overall difficulty score for a subtitle cue"""
        if not words:
            return 0.0
        
        difficulty_scores = {
            'beginner': 1.0,
            'intermediate': 2.0,
            'advanced': 3.0
        }
        
        total_score = sum(difficulty_scores.get(word.get('difficulty_level', 'beginner'), 1.0) for word in words)
        return total_score / len(words)
    
    def create_learning_segments(self, cues: List[SubtitleCue], segment_duration: int = 30) -> List[Dict[str, Any]]:
        """Group subtitle cues into learning segments"""
        segments = []
        current_segment = {
            'id': str(uuid.uuid4()),
            'start_time': 0,
            'end_time': 0,
            'cues': [],
            'vocabulary_words': [],
            'difficulty_score': 0.0
        }
        
        for cue in cues:
            if (current_segment['cues'] and 
                cue.start_time - current_segment['start_time'] > segment_duration):
                
                current_segment['end_time'] = current_segment['cues'][-1].end_time
                current_segment['difficulty_score'] = self._calculate_segment_difficulty(current_segment['cues'])
                current_segment['vocabulary_words'] = self._extract_vocabulary_words(current_segment['cues'])
                
                segments.append(current_segment)
                
                current_segment = {
                    'id': str(uuid.uuid4()),
                    'start_time': cue.start_time,
                    'end_time': 0,
                    'cues': [],
                    'vocabulary_words': [],
                    'difficulty_score': 0.0
                }
            
            if not current_segment['cues']:
                current_segment['start_time'] = cue.start_time
            
            current_segment['cues'].append(cue)
        
        if current_segment['cues']:
            current_segment['end_time'] = current_segment['cues'][-1].end_time
            current_segment['difficulty_score'] = self._calculate_segment_difficulty(current_segment['cues'])
            current_segment['vocabulary_words'] = self._extract_vocabulary_words(current_segment['cues'])
            segments.append(current_segment)
        
        return segments
    
    def _calculate_segment_difficulty(self, cues: List[SubtitleCue]) -> float:
        """Calculate difficulty score for a segment"""
        if not cues:
            return 0.0
        
        total_score = sum(cue.difficulty_score for cue in cues)
        return total_score / len(cues)
    
    def _extract_vocabulary_words(self, cues: List[SubtitleCue]) -> List[Dict[str, Any]]:
        """Extract unique vocabulary words from segment cues"""
        words_seen = set()
        vocabulary = []
        
        for cue in cues:
            for word_data in cue.words:
                word = word_data.get('word', '')
                if word and word not in words_seen and word_data.get('difficulty_level') != 'beginner':
                    words_seen.add(word)
                    vocabulary.append(word_data)
        
        vocabulary.sort(key=lambda x: {'advanced': 3, 'intermediate': 2, 'beginner': 1}.get(x.get('difficulty_level', 'beginner'), 1), reverse=True)
        
        return vocabulary[:10]


# Pydantic models for API
class SubtitleUpload(BaseModel):
    movie_id: str
    language: str
    title: Optional[str] = None

class ProgressUpdate(BaseModel):
    segment_id: str
    time_spent: int
    words_learned: List[str] = []
    completed: bool = False


class SubtitleEngineAPI:
    """API endpoints for subtitle functionality"""
    
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1/subtitles", tags=["subtitles"])
        self.processor = SubtitleProcessor()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.router.post("/upload")
        async def upload_subtitle_file(
            file: UploadFile = File(...),
            movie_id: str = Form(...),
            language: str = Form(...),
            title: Optional[str] = Form(None),
            current_user: User = Depends(get_current_user)
        ):
            """Upload and process subtitle file"""
            
            # Validate file type
            allowed_extensions = ['.srt', '.vtt', '.webvtt']
            file_extension = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
            
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
                )
            
            # Check if movie exists
            try:
                movie_response = supabase.table("movies").select("id, title").eq("id", movie_id).execute()
                if not movie_response.data:
                    raise HTTPException(status_code=404, detail="Movie not found")
                
                movie = movie_response.data[0]
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to verify movie: {str(e)}")
            
            try:
                # Read file content
                file_content = await file.read()
                
                # Determine file type
                file_type = file_extension[1:]
                if file_type == 'webvtt':
                    file_type = 'vtt'
                
                # Process subtitle file
                processed_data = process_subtitle_file(file_content, file_type, movie_id)
                
                # Store in database
                subtitle_id = str(uuid.uuid4())
                subtitle_record = {
                    "id": subtitle_id,
                    "movie_id": movie_id,
                    "language": language,
                    "title": title or f"{movie['title']} - {language.upper()}",
                    "file_type": file_type,
                    "total_cues": processed_data["total_cues"],
                    "total_segments": processed_data["total_segments"],
                    "duration": processed_data["duration"],
                    "avg_difficulty": processed_data["avg_difficulty"],
                    "vocabulary_count": processed_data["vocabulary_count"],
                    "uploaded_by": current_user.id,
                    "created_at": datetime.utcnow().isoformat()
                }
                
                subtitle_response = supabase.table("subtitles").insert(subtitle_record).execute()
                
                if not subtitle_response.data:
                    raise HTTPException(status_code=500, detail="Failed to save subtitle metadata")
                
                return {
                    "message": "Subtitle uploaded and processed successfully",
                    "subtitle_id": subtitle_id,
                    "stats": {
                        "total_cues": processed_data["total_cues"],
                        "total_segments": processed_data["total_segments"],
                        "duration": processed_data["duration"],
                        "vocabulary_count": processed_data["vocabulary_count"],
                        "avg_difficulty": round(processed_data["avg_difficulty"], 2)
                    }
                }
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to process subtitle file: {str(e)}"
                )
        
        @self.router.get("/movie/{movie_id}")
        async def get_movie_subtitles(
            movie_id: str,
            language: Optional[str] = None,
            current_user: Optional[User] = Depends(get_optional_user)
        ):
            """Get all subtitles for a movie"""
            try:
                query = supabase.table("subtitles").select("*").eq("movie_id", movie_id)
                
                if language:
                    query = query.eq("language", language)
                
                response = query.order("created_at", desc=True).execute()
                
                return {
                    "subtitles": response.data if response.data else [],
                    "total": len(response.data) if response.data else 0
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to fetch subtitles: {str(e)}")


# Main processing function
def process_subtitle_file(file_content: bytes, file_type: str, movie_id: str) -> Dict[str, Any]:
    """Main function to process a subtitle file"""
    processor = SubtitleProcessor()
    
    try:
        # Parse subtitle file
        cues = processor.parse_subtitle_file(file_content, file_type)
        
        # Enrich with learning data
        enriched_cues = processor.enrich_subtitles(cues)
        
        # Create learning segments
        segments = processor.create_learning_segments(enriched_cues)
        
        # Prepare response
        result = {
            'movie_id': movie_id,
            'total_cues': len(enriched_cues),
            'total_segments': len(segments),
            'avg_difficulty': sum(cue.difficulty_score for cue in enriched_cues) / len(enriched_cues) if enriched_cues else 0,
            'duration': enriched_cues[-1].end_time if enriched_cues else 0,
            'cues': [cue.__dict__ for cue in enriched_cues],
            'segments': segments,
            'vocabulary_count': sum(len(segment['vocabulary_words']) for segment in segments),
            'created_at': datetime.utcnow().isoformat()
        }
        
        return result
        
    except Exception as e:
        raise ValueError(f"Subtitle processing failed: {str(e)}")


# Export the main components
__all__ = ['SubtitleProcessor', 'SubtitleEngineAPI', 'process_subtitle_file']
