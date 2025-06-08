# Add these new imports to your main.py
import pysrt
import webvtt
from typing import Optional, List, Dict, Union
import re
from datetime import datetime, timedelta
import json

# Add these new Pydantic models
class SubtitleUpload(BaseModel):
    movie_id: str
    language: str
    subtitle_type: str = "srt"  # srt or vtt
    file_content: str  # Base64 encoded content

class SubtitleSegment(BaseModel):
    id: str
    start_time: float
    end_time: float
    text: str
    translation: Optional[str] = None
    words: List[Dict[str, any]] = []
    difficulty_level: str = "intermediate"

class WordDefinition(BaseModel):
    word: str
    language: str
    definition: str
    pronunciation: Optional[str] = None
    part_of_speech: Optional[str] = None
    difficulty_level: str = "intermediate"
    example_sentence: Optional[str] = None

class VocabularyProgress(BaseModel):
    word_id: str
    mastery_level: int = 0  # 0-5 scale
    times_seen: int = 0
    times_correct: int = 0

# ===== SUBTITLE PROCESSING ENDPOINTS =====

@app.post("/api/v1/subtitles/upload")
async def upload_subtitles(
    subtitle_data: SubtitleUpload,
    current_user: User = Depends(get_current_user)
):
    """Upload and process subtitle files (SRT/VTT)"""
    try:
        # Verify movie exists
        movie_response = supabase.table("movies").select("id").eq("id", subtitle_data.movie_id).execute()
        if not movie_response.data:
            raise HTTPException(status_code=404, detail="Movie not found")

        # Decode file content
        import base64
        file_content = base64.b64decode(subtitle_data.file_content).decode('utf-8')
        
        # Create subtitle file record
        subtitle_file_data = {
            "movie_id": subtitle_data.movie_id,
            "language": subtitle_data.language,
            "subtitle_type": subtitle_data.subtitle_type,
            "file_content": file_content,
            "uploaded_by": current_user.id,
            "processing_status": "processing"
        }
        
        file_response = supabase.table("subtitle_files").insert(subtitle_file_data).execute()
        if not file_response.data:
            raise HTTPException(status_code=400, detail="Failed to create subtitle file")
        
        subtitle_file_id = file_response.data[0]["id"]
        
        # Process subtitle file
        segments = await process_subtitle_file(file_content, subtitle_data.subtitle_type, subtitle_data.language)
        
        # Store segments in database
        for segment in segments:
            segment_data = {
                "subtitle_file_id": subtitle_file_id,
                "start_time": segment["start_time"],
                "end_time": segment["end_time"],
                "text": segment["text"],
                "sequence_order": segment["sequence_order"],
                "words_data": json.dumps(segment["words"]),
                "difficulty_level": segment["difficulty_level"]
            }
            
            supabase.table("subtitle_segments").insert(segment_data).execute()
        
        # Update processing status
        supabase.table("subtitle_files").update({
            "processing_status": "completed",
            "segments_count": len(segments)
        }).eq("id", subtitle_file_id).execute()
        
        return {
            "message": "Subtitles uploaded and processed successfully",
            "subtitle_file_id": subtitle_file_id,
            "segments_processed": len(segments)
        }
        
    except Exception as e:
        # Update processing status to failed
        if 'subtitle_file_id' in locals():
            supabase.table("subtitle_files").update({
                "processing_status": "failed",
                "error_message": str(e)
            }).eq("id", subtitle_file_id).execute()
        
        raise HTTPException(status_code=500, detail=f"Subtitle processing failed: {str(e)}")

@app.get("/api/v1/movies/{movie_id}/subtitles")
async def get_movie_subtitles(
    movie_id: str,
    language: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get subtitles for a specific movie"""
    try:
        # Build query
        query = supabase.table("subtitle_files").select("""
            id,
            language,
            subtitle_type,
            processing_status,
            segments_count,
            created_at,
            subtitle_segments (
                id,
                start_time,
                end_time,
                text,
                sequence_order,
                words_data,
                difficulty_level
            )
        """).eq("movie_id", movie_id).eq("processing_status", "completed")
        
        if language:
            query = query.eq("language", language)
        
        response = query.execute()
        
        if not response.data:
            return {"subtitles": [], "message": "No subtitles found for this movie"}
        
        # Format response
        subtitles = []
        for subtitle_file in response.data:
            segments = []
            if subtitle_file.get("subtitle_segments"):
                segments = [
                    {
                        "id": seg["id"],
                        "start_time": seg["start_time"],
                        "end_time": seg["end_time"],
                        "text": seg["text"],
                        "sequence_order": seg["sequence_order"],
                        "words": json.loads(seg["words_data"]) if seg["words_data"] else [],
                        "difficulty_level": seg["difficulty_level"]
                    }
                    for seg in subtitle_file["subtitle_segments"]
                ]
                segments.sort(key=lambda x: x["sequence_order"])
            
            subtitles.append({
                "id": subtitle_file["id"],
                "language": subtitle_file["language"],
                "subtitle_type": subtitle_file["subtitle_type"],
                "segments_count": subtitle_file["segments_count"],
                "segments": segments,
                "created_at": subtitle_file["created_at"]
            })
        
        return {"subtitles": subtitles}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch subtitles: {str(e)}")

@app.get("/api/v1/vocabulary/lookup/{word}")
async def lookup_word_definition(
    word: str,
    language: str = "es",  # Default to Spanish
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get definition for a specific word"""
    try:
        # First check if we have the definition in our database
        response = supabase.table("word_definitions").select("*").eq("word", word.lower()).eq("language", language).execute()
        
        if response.data:
            definition_data = response.data[0]
            
            # Track word lookup if user is authenticated
            if current_user:
                await track_vocabulary_interaction(current_user.id, definition_data["id"], "lookup")
            
            return {
                "word": definition_data["word"],
                "language": definition_data["language"],
                "definition": definition_data["definition"],
                "pronunciation": definition_data["pronunciation"],
                "part_of_speech": definition_data["part_of_speech"],
                "difficulty_level": definition_data["difficulty_level"],
                "example_sentence": definition_data["example_sentence"],
                "source": "database"
            }
        
        # If not in database, generate/fetch definition
        definition = await generate_word_definition(word, language)
        
        # Store in database for future use
        definition_data = {
            "word": word.lower(),
            "language": language,
            "definition": definition["definition"],
            "pronunciation": definition.get("pronunciation"),
            "part_of_speech": definition.get("part_of_speech"),
            "difficulty_level": definition.get("difficulty_level", "intermediate"),
            "example_sentence": definition.get("example_sentence")
        }
        
        store_response = supabase.table("word_definitions").insert(definition_data).execute()
        
        if current_user and store_response.data:
            await track_vocabulary_interaction(current_user.id, store_response.data[0]["id"], "lookup")
        
        return {**definition, "source": "generated"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Word lookup failed: {str(e)}")

@app.get("/api/v1/vocabulary/progress")
async def get_vocabulary_progress(
    current_user: User = Depends(get_current_user),
    language: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """Get user's vocabulary learning progress"""
    try:
        query = supabase.table("user_vocabulary").select("""
            id,
            mastery_level,
            times_seen,
            times_correct,
            last_reviewed_at,
            next_review_at,
            created_at,
            word_definitions (
                word,
                language,
                definition,
                part_of_speech,
                difficulty_level
            )
        """).eq("user_id", current_user.id)
        
        if language:
            # Note: This requires a join, might need to filter after fetch
            pass
        
        response = query.limit(limit).order("last_reviewed_at", desc=True).execute()
        
        progress_data = []
        for item in response.data or []:
            word_def = item.get("word_definitions")
            if word_def and (not language or word_def["language"] == language):
                progress_data.append({
                    "id": item["id"],
                    "word": word_def["word"],
                    "language": word_def["language"],
                    "definition": word_def["definition"],
                    "part_of_speech": word_def["part_of_speech"],
                    "difficulty_level": word_def["difficulty_level"],
                    "mastery_level": item["mastery_level"],
                    "times_seen": item["times_seen"],
                    "times_correct": item["times_correct"],
                    "accuracy": round((item["times_correct"] / max(item["times_seen"], 1)) * 100, 1),
                    "last_reviewed_at": item["last_reviewed_at"],
                    "next_review_at": item["next_review_at"],
                    "created_at": item["created_at"]
                })
        
        # Calculate summary stats
        total_words = len(progress_data)
        mastered_words = len([w for w in progress_data if w["mastery_level"] >= 4])
        average_accuracy = sum(w["accuracy"] for w in progress_data) / max(total_words, 1)
        
        return {
            "vocabulary": progress_data,
            "stats": {
                "total_words": total_words,
                "mastered_words": mastered_words,
                "learning_words": total_words - mastered_words,
                "average_accuracy": round(average_accuracy, 1),
                "mastery_rate": round((mastered_words / max(total_words, 1)) * 100, 1)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch vocabulary progress: {str(e)}")

@app.post("/api/v1/vocabulary/practice")
async def practice_vocabulary_word(
    word_id: str,
    correct: bool,
    current_user: User = Depends(get_current_user)
):
    """Record vocabulary practice result"""
    try:
        # Get current progress
        response = supabase.table("user_vocabulary").select("*").eq("user_id", current_user.id).eq("word_definition_id", word_id).execute()
        
        if response.data:
            # Update existing progress
            current_progress = response.data[0]
            new_times_seen = current_progress["times_seen"] + 1
            new_times_correct = current_progress["times_correct"] + (1 if correct else 0)
            
            # Calculate new mastery level (simple algorithm)
            accuracy = new_times_correct / new_times_seen
            if accuracy >= 0.9 and new_times_seen >= 3:
                new_mastery = min(5, current_progress["mastery_level"] + 1)
            elif accuracy < 0.5:
                new_mastery = max(0, current_progress["mastery_level"] - 1)
            else:
                new_mastery = current_progress["mastery_level"]
            
            # Calculate next review time (spaced repetition)
            next_review = datetime.utcnow() + timedelta(
                hours=2 ** new_mastery  # Exponential backoff
            )
            
            update_data = {
                "times_seen": new_times_seen,
                "times_correct": new_times_correct,
                "mastery_level": new_mastery,
                "last_reviewed_at": datetime.utcnow().isoformat(),
                "next_review_at": next_review.isoformat()
            }
            
            supabase.table("user_vocabulary").update(update_data).eq("id", current_progress["id"]).execute()
            
        else:
            # Create new progress entry
            new_progress = {
                "user_id": current_user.id,
                "word_definition_id": word_id,
                "times_seen": 1,
                "times_correct": 1 if correct else 0,
                "mastery_level": 1 if correct else 0,
                "last_reviewed_at": datetime.utcnow().isoformat(),
                "next_review_at": (datetime.utcnow() + timedelta(hours=2)).isoformat()
            }
            
            supabase.table("user_vocabulary").insert(new_progress).execute()
        
        # Track the practice session
        await track_vocabulary_interaction(current_user.id, word_id, "practice", {"correct": correct})
        
        return {
            "message": "Practice result recorded",
            "correct": correct,
            "next_review_in": "2 hours" if correct else "1 hour"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record practice: {str(e)}")

# ===== HELPER FUNCTIONS =====

async def process_subtitle_file(content: str, file_type: str, language: str) -> List[Dict]:
    """Process SRT or VTT file and extract segments with word analysis"""
    segments = []
    
    try:
        if file_type.lower() == "srt":
            # Parse SRT file
            import io
            srt_file = io.StringIO(content)
            subtitle_items = pysrt.stream(srt_file, encoding='utf-8')
            
            for i, item in enumerate(subtitle_items):
                start_time = item.start.hours * 3600 + item.start.minutes * 60 + item.start.seconds + item.start.milliseconds / 1000
                end_time = item.end.hours * 3600 + item.end.minutes * 60 + item.end.seconds + item.end.milliseconds / 1000
                text = item.text.replace('\n', ' ').strip()
                
                # Analyze words in the text
                words = await analyze_subtitle_text(text, language)
                
                segments.append({
                    "start_time": start_time,
                    "end_time": end_time,
                    "text": text,
                    "sequence_order": i + 1,
                    "words": words,
                    "difficulty_level": calculate_segment_difficulty(words)
                })
                
        elif file_type.lower() == "vtt":
            # Parse VTT file
            import io
            vtt_file = io.StringIO(content)
            captions = webvtt.read_buffer(vtt_file)
            
            for i, caption in enumerate(captions):
                start_time = time_to_seconds(caption.start)
                end_time = time_to_seconds(caption.end)
                text = caption.text.replace('\n', ' ').strip()
                
                words = await analyze_subtitle_text(text, language)
                
                segments.append({
                    "start_time": start_time,
                    "end_time": end_time,
                    "text": text,
                    "sequence_order": i + 1,
                    "words": words,
                    "difficulty_level": calculate_segment_difficulty(words)
                })
        
        return segments
        
    except Exception as e:
        raise Exception(f"Failed to process {file_type} file: {str(e)}")

async def analyze_subtitle_text(text: str, language: str) -> List[Dict]:
    """Analyze subtitle text and extract words with metadata"""
    words = []
    
    # Simple word extraction (you might want to use proper NLP libraries)
    word_pattern = re.compile(r'\b\w+\b', re.IGNORECASE)
    word_matches = word_pattern.findall(text)
    
    for word in word_matches:
        word_lower = word.lower()
        
        # Skip very short words and common stop words
        if len(word_lower) < 3 or word_lower in ['the', 'and', 'but', 'or', 'so', 'yet']:
            continue
        
        # Determine difficulty (simple heuristic - replace with proper algorithm)
        difficulty = "beginner" if len(word_lower) <= 4 else "intermediate" if len(word_lower) <= 7 else "advanced"
        
        words.append({
            "word": word_lower,
            "original_form": word,
            "difficulty_level": difficulty,
            "part_of_speech": None,  # Would need NLP library for this
            "position": text.lower().find(word_lower)
        })
    
    return words

def calculate_segment_difficulty(words: List[Dict]) -> str:
    """Calculate overall difficulty of a subtitle segment"""
    if not words:
        return "beginner"
    
    difficulty_scores = {"beginner": 1, "intermediate": 2, "advanced": 3}
    total_score = sum(difficulty_scores.get(word["difficulty_level"], 2) for word in words)
    average_score = total_score / len(words)
    
    if average_score <= 1.3:
        return "beginner"
    elif average_score <= 2.3:
        return "intermediate"
    else:
        return "advanced"

def time_to_seconds(time_str: str) -> float:
    """Convert VTT time format to seconds"""
    parts = time_str.replace(',', '.').split(':')
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
    elif len(parts) == 2:
        minutes, seconds = parts
        return float(minutes) * 60 + float(seconds)
    else:
        return float(parts[0])

async def generate_word_definition(word: str, language: str) -> Dict:
    """Generate word definition (placeholder - integrate with dictionary API)"""
    # This is a placeholder. In production, integrate with:
    # - Google Translate API
    # - Oxford Dictionary API
    # - Or other translation services
    
    return {
        "definition": f"Definition for '{word}' in {language}",
        "pronunciation": f"/{word}/",
        "part_of_speech": "noun",  # Placeholder
        "difficulty_level": "intermediate",
        "example_sentence": f"Example sentence with {word}."
    }

async def track_vocabulary_interaction(user_id: str, word_id: str, interaction_type: str, metadata: Dict = None):
    """Track vocabulary interactions for analytics"""
    try:
        interaction_data = {
            "user_id": user_id,
            "word_definition_id": word_id,
            "interaction_type": interaction_type,
            "metadata": json.dumps(metadata) if metadata else None,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Store in a vocabulary_interactions table (you might want to create this)
        # For now, we'll skip this to avoid additional table creation
        pass
        
    except Exception as e:
        # Don't fail the main operation if tracking fails
        print(f"Failed to track vocabulary interaction: {e}")
        pass