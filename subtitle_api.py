from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import json

from database import supabase, supabase_admin
from auth import get_current_user, get_optional_user, User
from subtitle_processor import SubtitleProcessor, process_subtitle_file

# Create router
router = APIRouter(prefix="/api/v1/subtitles", tags=["subtitles"])

# Pydantic models
class SubtitleUpload(BaseModel):
    movie_id: str
    language: str
    title: Optional[str] = None
    
class SubtitleCueResponse(BaseModel):
    id: str
    start_time: float
    end_time: float
    text: str
    words: List[Dict[str, Any]]
    difficulty_score: float

class LearningSegmentResponse(BaseModel):
    id: str
    start_time: float
    end_time: float
    cues: List[SubtitleCueResponse]
    vocabulary_words: List[Dict[str, Any]]
    difficulty_score: float

class WordInteraction(BaseModel):
    word: str
    definition_viewed: bool = False
    marked_learned: bool = False
    quiz_attempted: bool = False
    quiz_correct: bool = False

class ProgressUpdate(BaseModel):
    segment_id: str
    time_spent: int  # seconds
    words_learned: List[str] = []
    interactions: List[WordInteraction] = []
    completed: bool = False

class QuizQuestion(BaseModel):
    id: str
    word: str
    question_type: str  # "definition", "translation", "context"
    question: str
    options: List[str]
    correct_answer: str
    context: Optional[str] = None

class QuizSubmission(BaseModel):
    question_id: str
    selected_answer: str
    time_taken: int  # seconds

# ===== SUBTITLE UPLOAD AND MANAGEMENT =====

@router.post("/upload")
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
        file_type = file_extension[1:]  # Remove the dot
        if file_type == 'webvtt':
            file_type = 'vtt'
        
        # Process subtitle file
        print(f"Processing subtitle file for movie {movie_id} ({file_type})")
        processed_data = process_subtitle_file(file_content, file_type, movie_id)
        
        # Generate subtitle record ID
        subtitle_id = str(uuid.uuid4())
        
        # Store subtitle metadata in database
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
        
        # Insert subtitle record
        subtitle_response = supabase.table("subtitles").insert(subtitle_record).execute()
        
        if not subtitle_response.data:
            raise HTTPException(status_code=500, detail="Failed to save subtitle metadata")
        
        # Store processed cues in database
        cues_data = []
        for cue_dict in processed_data["cues"]:
            cue_record = {
                "id": str(uuid.uuid4()),
                "subtitle_id": subtitle_id,
                "cue_index": len(cues_data),
                "start_time": cue_dict["start_time"],
                "end_time": cue_dict["end_time"],
                "text": cue_dict["text"],
                "words": json.dumps(cue_dict["words"]),  # Store as JSON
                "difficulty_score": cue_dict["difficulty_score"]
            }
            cues_data.append(cue_record)
        
        # Batch insert cues
        if cues_data:
            cues_response = supabase.table("subtitle_cues").insert(cues_data).execute()
            if not cues_response.data:
                print("Warning: Failed to insert subtitle cues")
        
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
        
        # Batch insert segments
        if segments_data:
            segments_response = supabase.table("learning_segments").insert(segments_data).execute()
            if not segments_response.data:
                print("Warning: Failed to insert learning segments")
        
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
        print(f"Subtitle processing error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process subtitle file: {str(e)}"
        )

@router.get("/movie/{movie_id}")
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

# ===== INTERACTIVE LEARNING ENDPOINTS =====

@router.get("/{subtitle_id}/segments")
async def get_learning_segments(
    subtitle_id: str,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get learning segments for a subtitle file"""
    try:
        # Verify subtitle exists
        subtitle_response = supabase.table("subtitles").select("*").eq("id", subtitle_id).execute()
        if not subtitle_response.data:
            raise HTTPException(status_code=404, detail="Subtitle not found")
        
        subtitle = subtitle_response.data[0]
        
        # Get segments
        segments_response = supabase.table("learning_segments")\
            .select("*")\
            .eq("subtitle_id", subtitle_id)\
            .order("start_time")\
            .execute()
        
        segments = []
        for segment_data in segments_response.data or []:
            # Parse vocabulary words from JSON
            vocabulary_words = json.loads(segment_data["vocabulary_words"]) if segment_data["vocabulary_words"] else []
            
            segment = {
                "id": segment_data["id"],
                "start_time": segment_data["start_time"],
                "end_time": segment_data["end_time"],
                "difficulty_score": segment_data["difficulty_score"],
                "vocabulary_words": vocabulary_words,
                "cue_count": segment_data["cue_count"]
            }
            
            # Add user progress if authenticated
            if current_user:
                progress_response = supabase.table("user_segment_progress")\
                    .select("*")\
                    .eq("user_id", current_user.id)\
                    .eq("segment_id", segment_data["id"])\
                    .execute()
                
                if progress_response.data:
                    segment["user_progress"] = progress_response.data[0]
            
            segments.append(segment)
        
        return {
            "subtitle": subtitle,
            "segments": segments,
            "total_segments": len(segments)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch segments: {str(e)}")

@router.get("/segment/{segment_id}/cues")
async def get_segment_cues(
    segment_id: str,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get detailed cues for a learning segment"""
    try:
        # Verify segment exists
        segment_response = supabase.table("learning_segments").select("*").eq("id", segment_id).execute()
        if not segment_response.data:
            raise HTTPException(status_code=404, detail="Learning segment not found")
        
        segment = segment_response.data[0]
        
        # Get subtitle cues for this segment
        cues_response = supabase.table("subtitle_cues")\
            .select("*")\
            .eq("subtitle_id", segment["subtitle_id"])\
            .gte("start_time", segment["start_time"])\
            .lte("end_time", segment["end_time"])\
            .order("start_time")\
            .execute()
        
        cues = []
        for cue_data in cues_response.data or []:
            # Parse words from JSON
            words = json.loads(cue_data["words"]) if cue_data["words"] else []
            
            cue = {
                "id": cue_data["id"],
                "start_time": cue_data["start_time"],
                "end_time": cue_data["end_time"],
                "text": cue_data["text"],
                "words": words,
                "difficulty_score": cue_data["difficulty_score"]
            }
            
            # Add user interactions if authenticated
            if current_user:
                interactions_response = supabase.table("user_word_interactions")\
                    .select("*")\
                    .eq("user_id", current_user.id)\
                    .eq("cue_id", cue_data["id"])\
                    .execute()
                
                if interactions_response.data:
                    cue["user_interactions"] = interactions_response.data
            
            cues.append(cue)
        
        # Parse vocabulary words
        vocabulary_words = json.loads(segment["vocabulary_words"]) if segment["vocabulary_words"] else []
        
        return {
            "segment": {
                "id": segment["id"],
                "start_time": segment["start_time"],
                "end_time": segment["end_time"],
                "difficulty_score": segment["difficulty_score"],
                "vocabulary_words": vocabulary_words
            },
            "cues": cues,
            "total_cues": len(cues)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch segment cues: {str(e)}")

# ===== PROGRESS TRACKING =====

@router.post("/segment/{segment_id}/progress")
async def update_segment_progress(
    segment_id: str,
    progress_data: ProgressUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user progress for a learning segment"""
    try:
        # Verify segment exists
        segment_response = supabase.table("learning_segments").select("*").eq("id", segment_id).execute()
        if not segment_response.data:
            raise HTTPException(status_code=404, detail="Learning segment not found")
        
        # Prepare progress update
        progress_update = {
            "user_id": current_user.id,
            "segment_id": segment_id,
            "time_spent": progress_data.time_spent,
            "words_learned": progress_data.words_learned,
            "completed": progress_data.completed,
            "last_accessed": datetime.utcnow().isoformat()
        }
        
        # Update or insert progress
        existing_progress = supabase.table("user_segment_progress")\
            .select("*")\
            .eq("user_id", current_user.id)\
            .eq("segment_id", segment_id)\
            .execute()
        
        if existing_progress.data:
            # Update existing progress
            progress_update["updated_at"] = datetime.utcnow().isoformat()
            response = supabase.table("user_segment_progress")\
                .update(progress_update)\
                .eq("user_id", current_user.id)\
                .eq("segment_id", segment_id)\
                .execute()
        else:
            # Insert new progress
            progress_update["created_at"] = datetime.utcnow().isoformat()
            response = supabase.table("user_segment_progress").insert(progress_update).execute()
        
        # Record word interactions
        for interaction in progress_data.interactions:
            interaction_record = {
                "id": str(uuid.uuid4()),
                "user_id": current_user.id,
                "segment_id": segment_id,
                "word": interaction.word,
                "definition_viewed": interaction.definition_viewed,
                "marked_learned": interaction.marked_learned,
                "quiz_attempted": interaction.quiz_attempted,
                "quiz_correct": interaction.quiz_correct,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Insert interaction (ignore duplicates)
            try:
                supabase.table("user_word_interactions").insert(interaction_record).execute()
            except:
                pass  # Ignore duplicate interaction errors
        
        return {
            "message": "Progress updated successfully",
            "progress": response.data[0] if response.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update progress: {str(e)}")

@router.get("/user/progress")
async def get_user_subtitle_progress(
    current_user: User = Depends(get_current_user),
    movie_id: Optional[str] = Query(None)
):
    """Get user's subtitle learning progress"""
    try:
        query = supabase.table("user_segment_progress")\
            .select("*, learning_segments!inner(*, subtitles!inner(*))")\
            .eq("user_id", current_user.id)
        
        if movie_id:
            query = query.eq("learning_segments.subtitles.movie_id", movie_id)
        
        response = query.order("updated_at", desc=True).execute()
        
        progress_data = []
        total_time = 0
        words_learned = set()
        completed_segments = 0
        
        for progress in response.data or []:
            progress_data.append(progress)
            total_time += progress.get("time_spent", 0)
            words_learned.update(progress.get("words_learned", []))
            if progress.get("completed"):
                completed_segments += 1
        
        return {
            "progress": progress_data,
            "stats": {
                "total_segments_studied": len(progress_data),
                "completed_segments": completed_segments,
                "total_time_spent": total_time,
                "unique_words_learned": len(words_learned),
                "completion_rate": (completed_segments / len(progress_data) * 100) if progress_data else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch progress: {str(e)}")

# ===== QUIZ GENERATION AND MANAGEMENT =====

@router.get("/segment/{segment_id}/quiz")
async def generate_quiz(
    segment_id: str,
    question_count: int = Query(5, ge=1, le=20),
    difficulty: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Generate a quiz for a learning segment"""
    try:
        # Get segment data
        segment_response = supabase.table("learning_segments").select("*").eq("id", segment_id).execute()
        if not segment_response.data:
            raise HTTPException(status_code=404, detail="Learning segment not found")
        
        segment = segment_response.data[0]
        vocabulary_words = json.loads(segment["vocabulary_words"]) if segment["vocabulary_words"] else []
        
        # Filter by difficulty if specified
        if difficulty:
            vocabulary_words = [w for w in vocabulary_words if w.get("difficulty_level") == difficulty]
        
        if len(vocabulary_words) < question_count:
            question_count = len(vocabulary_words)
        
        if question_count == 0:
            return {"quiz": [], "message": "No vocabulary words available for quiz"}
        
        # Generate quiz questions
        quiz_questions = []
        used_words = set()
        
        import random
        random.shuffle(vocabulary_words)
        
        for i, word_data in enumerate(vocabulary_words[:question_count]):
            word = word_data["word"]
            if word in used_words:
                continue
            used_words.add(word)
            
            # Generate different types of questions
            question_types = ["definition", "translation", "context"]
            question_type = random.choice(question_types)
            
            question = self._generate_quiz_question(word_data, question_type, vocabulary_words)
            if question:
                quiz_questions.append(question)
        
        # Store quiz session
        quiz_session = {
            "id": str(uuid.uuid4()),
            "user_id": current_user.id,
            "segment_id": segment_id,
            "questions": json.dumps([q.__dict__ for q in quiz_questions]),
            "created_at": datetime.utcnow().isoformat(),
            "completed": False
        }
        
        supabase.table("quiz_sessions").insert(quiz_session).execute()
        
        return {
            "quiz_session_id": quiz_session["id"],
            "questions": [q.__dict__ for q in quiz_questions],
            "total_questions": len(quiz_questions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")

def _generate_quiz_question(word_data: Dict, question_type: str, all_words: List[Dict]) -> Optional[QuizQuestion]:
    """Generate a single quiz question"""
    import random
    
    word = word_data["word"]
    definition = word_data.get("definition", "")
    translations = word_data.get("translations", {})
    context = word_data.get("context", "")
    
    if question_type == "definition":
        # Definition question
        question = f"What does '{word}' mean?"
        correct_answer = definition
        
        # Generate wrong options from other words
        wrong_options = []
        for other_word in random.sample(all_words, min(3, len(all_words))):
            if other_word["word"] != word:
                wrong_options.append(other_word.get("definition", ""))
        
        options = [correct_answer] + wrong_options[:3]
        random.shuffle(options)
        
    elif question_type == "translation" and translations:
        # Translation question
        target_lang = random.choice(list(translations.keys()))
        question = f"How do you say '{word}' in {target_lang.upper()}?"
        correct_answer = translations[target_lang]
        
        # Generate wrong options
        wrong_options = []
        for other_word in random.sample(all_words, min(3, len(all_words))):
            if other_word["word"] != word:
                other_translations = other_word.get("translations", {})
                if target_lang in other_translations:
                    wrong_options.append(other_translations[target_lang])
        
        options = [correct_answer] + wrong_options[:3]
        random.shuffle(options)
        
    elif question_type == "context":
        # Context question
        question = f"Complete the sentence: '{context.replace(word, '_____')}'"
        correct_answer = word
        
        # Generate wrong options from similar words
        wrong_options = []
        for other_word in random.sample(all_words, min(3, len(all_words))):
            if other_word["word"] != word:
                wrong_options.append(other_word["word"])
        
        options = [correct_answer] + wrong_options[:3]
        random.shuffle(options)
        
    else:
        return None
    
    return QuizQuestion(
        id=str(uuid.uuid4()),
        word=word,
        question_type=question_type,
        question=question,
        options=options,
        correct_answer=correct_answer,
        context=context if question_type == "context" else None
    )

@router.post("/quiz/{quiz_session_id}/submit")
async def submit_quiz_answer(
    quiz_session_id: str,
    submission: QuizSubmission,
    current_user: User = Depends(get_current_user)
):
    """Submit an answer to a quiz question"""
    try:
        # Verify quiz session
        quiz_response = supabase.table("quiz_sessions")\
            .select("*")\
            .eq("id", quiz_session_id)\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not quiz_response.data:
            raise HTTPException(status_code=404, detail="Quiz session not found")
        
        quiz_session = quiz_response.data[0]
        questions = json.loads(quiz_session["questions"])
        
        # Find the question
        question = None
        for q in questions:
            if q["id"] == submission.question_id:
                question = q
                break
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Check if answer is correct
        is_correct = submission.selected_answer == question["correct_answer"]
        
        # Store submission
        submission_record = {
            "id": str(uuid.uuid4()),
            "quiz_session_id": quiz_session_id,
            "question_id": submission.question_id,
            "word": question["word"],
            "selected_answer": submission.selected_answer,
            "correct_answer": question["correct_answer"],
            "is_correct": is_correct,
            "time_taken": submission.time_taken,
            "created_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("quiz_submissions").insert(submission_record).execute()
        
        return {
            "correct": is_correct,
            "correct_answer": question["correct_answer"],
            "explanation": question.get("definition", "") if not is_correct else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")

@router.post("/quiz/{quiz_session_id}/complete")
async def complete_quiz(
    quiz_session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark quiz as completed and get results"""
    try:
        # Get quiz submissions
        submissions_response = supabase.table("quiz_submissions")\
            .select("*")\
            .eq("quiz_session_id", quiz_session_id)\
            .execute()
        
        submissions = submissions_response.data or []
        
        # Calculate results
        total_questions = len(submissions)
        correct_answers = sum(1 for s in submissions if s["is_correct"])
        score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        # Update quiz session
        supabase.table("quiz_sessions")\
            .update({
                "completed": True,
                "score": score,
                "completed_at": datetime.utcnow().isoformat()
            })\
            .eq("id", quiz_session_id)\
            .execute()
        
        return {
            "quiz_completed": True,
            "results": {
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "score": round(score, 1),
                "submissions": submissions
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete quiz: {str(e)}")

# ===== VOCABULARY MANAGEMENT =====

@router.get("/vocabulary/learned")
async def get_learned_vocabulary(
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200)
):
    """Get user's learned vocabulary words"""
    try:
        # Get words marked as learned
        interactions_response = supabase.table("user_word_interactions")\
            .select("word, created_at, segment_id")\
            .eq("user_id", current_user.id)\
            .eq("marked_learned", True)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        learned_words = []
        for interaction in interactions_response.data or []:
            # Get word details from segment
            segment_response = supabase.table("learning_segments")\
                .select("vocabulary_words")\
                .eq("id", interaction["segment_id"])\
                .execute()
            
            if segment_response.data:
                vocabulary = json.loads(segment_response.data[0]["vocabulary_words"])
                word_data = next((w for w in vocabulary if w["word"] == interaction["word"]), None)
                
                if word_data:
                    word_data["learned_at"] = interaction["created_at"]
                    learned_words.append(word_data)
        
        return {
            "learned_words": learned_words,
            "total": len(learned_words)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch learned vocabulary: {str(e)}")

@router.post("/vocabulary/{word}/mark-learned")
async def mark_word_learned(
    word: str,
    segment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a word as learned"""
    try:
        # Record the interaction
        interaction_record = {
            "id": str(uuid.uuid4()),
            "user_id": current_user.id,
            "segment_id": segment_id,
            "word": word,
            "marked_learned": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Insert or update interaction
        supabase.table("user_word_interactions").upsert(
            interaction_record,
            on_conflict="user_id,segment_id,word"
        ).execute()
        
        return {"message": f"Word '{word}' marked as learned"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark word as learned: {str(e)}")