import re
import json
import spacy
import nltk
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid
import webvtt
import pysrt
from io import StringIO

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

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
    translations: Dict[str, str]  # language_code -> translation
    difficulty_level: str  # beginner, intermediate, advanced
    frequency_rank: int
    context: str
    audio_url: Optional[str] = None

class SubtitleProcessor:
    """Processes subtitle files and enriches them with learning data"""
    
    def __init__(self):
        # Load language models
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: English spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
            
        # Common word frequencies (simplified - in production, use comprehensive datasets)
        self.word_frequencies = self._load_word_frequencies()
        
        # Difficulty thresholds
        self.difficulty_thresholds = {
            'beginner': 3000,      # Most common 3000 words
            'intermediate': 7000,   # Words ranked 3001-7000
            'advanced': float('inf')  # All other words
        }
    
    def _load_word_frequencies(self) -> Dict[str, int]:
        """Load word frequency data - simplified version"""
        # In production, load from comprehensive frequency lists
        common_words = {
            'the': 1, 'of': 2, 'and': 3, 'a': 4, 'to': 5, 'in': 6, 'is': 7,
            'you': 8, 'that': 9, 'it': 10, 'he': 11, 'was': 12, 'for': 13,
            'on': 14, 'are': 15, 'as': 16, 'with': 17, 'his': 18, 'they': 19,
            'i': 20, 'at': 21, 'be': 22, 'this': 23, 'have': 24, 'from': 25,
            'or': 26, 'one': 27, 'had': 28, 'by': 29, 'word': 30, 'but': 31,
            'not': 32, 'what': 33, 'all': 34, 'were': 35, 'we': 36, 'when': 37,
            'your': 38, 'can': 39, 'said': 40, 'there': 41, 'each': 42,
            'which': 43, 'she': 44, 'do': 45, 'how': 46, 'their': 47,
            'if': 48, 'will': 49, 'up': 50, 'other': 51, 'about': 52,
            'out': 53, 'many': 54, 'then': 55, 'them': 56, 'these': 57,
            'so': 58, 'some': 59, 'her': 60, 'would': 61, 'make': 62,
            'like': 63, 'into': 64, 'him': 65, 'time': 66, 'has': 67,
            'two': 68, 'more': 69, 'very': 70, 'after': 71, 'words': 72,
            'here': 73, 'should': 74, 'way': 75, 'its': 76, 'only': 77,
            'new': 78, 'work': 79, 'part': 80, 'take': 81, 'get': 82,
            'place': 83, 'made': 84, 'live': 85, 'where': 86, 'much': 87,
            'too': 88, 'any': 89, 'may': 90, 'say': 91, 'small': 92,
            'every': 93, 'found': 94, 'still': 95, 'between': 96, 'name': 97,
            'should': 98, 'home': 99, 'big': 100
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
                # Convert time to seconds
                start_time = self._time_to_seconds(sub.start)
                end_time = self._time_to_seconds(sub.end)
                
                # Clean text
                text = self._clean_subtitle_text(sub.text)
                
                # Create cue
                cue = SubtitleCue(
                    id=str(uuid.uuid4()),
                    start_time=start_time,
                    end_time=end_time,
                    text=text,
                    words=[],  # Will be enriched later
                    difficulty_score=0.0
                )
                cues.append(cue)
            
            return cues
            
        except Exception as e:
            raise ValueError(f"Failed to parse SRT: {str(e)}")
    
    def _parse_vtt(self, content: str) -> List[SubtitleCue]:
        """Parse WebVTT format subtitles"""
        try:
            # Create a file-like object from string
            vtt_file = StringIO(content)
            captions = webvtt.read_buffer(vtt_file)
            
            cues = []
            for caption in captions:
                # Convert time to seconds
                start_time = self._webvtt_time_to_seconds(caption.start)
                end_time = self._webvtt_time_to_seconds(caption.end)
                
                # Clean text
                text = self._clean_subtitle_text(caption.text)
                
                # Create cue
                cue = SubtitleCue(
                    id=str(uuid.uuid4()),
                    start_time=start_time,
                    end_time=end_time,
                    text=text,
                    words=[],  # Will be enriched later
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
        # Format: HH:MM:SS.mmm or MM:SS.mmm
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
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove speaker names in brackets
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\(.*?\)', '', text)
        
        # Remove music notes and sound effects
        text = re.sub(r'♪.*?♪', '', text)
        text = re.sub(r'♫.*?♫', '', text)
        
        # Clean whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def enrich_subtitles(self, cues: List[SubtitleCue], target_language: str = "en") -> List[SubtitleCue]:
        """Enrich subtitle cues with learning data"""
        if not self.nlp:
            print("Warning: spaCy model not available. Skipping enrichment.")
            return cues
        
        for cue in cues:
            # Process text with spaCy
            doc = self.nlp(cue.text)
            enriched_words = []
            
            for token in doc:
                # Skip punctuation and whitespace
                if token.is_punct or token.is_space:
                    continue
                
                # Create enriched word
                enriched_word = self._create_enriched_word(token, cue.text)
                if enriched_word:
                    enriched_words.append(enriched_word.__dict__)
            
            cue.words = enriched_words
            cue.difficulty_score = self._calculate_difficulty_score(enriched_words)
        
        return cues
    
    def _create_enriched_word(self, token, context: str) -> Optional[EnrichedWord]:
        """Create an enriched word object from a spaCy token"""
        word = token.text.lower()
        
        # Skip very short words and common stop words
        if len(word) < 2 or token.is_stop:
            return None
        
        # Get frequency rank
        frequency_rank = self.word_frequencies.get(word, 10000)
        
        # Determine difficulty level
        difficulty_level = self._get_difficulty_level(frequency_rank)
        
        # Get definition (simplified - in production, use dictionary API)
        definition = self._get_word_definition(word, token.pos_)
        
        # Get translations (placeholder - in production, use translation API)
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
        # In production, integrate with dictionary APIs like Oxford, Merriam-Webster
        definitions = {
            'NOUN': f"A noun: {word}",
            'VERB': f"A verb: {word}",
            'ADJ': f"An adjective: {word}",
            'ADV': f"An adverb: {word}",
        }
        
        return definitions.get(pos, f"A word: {word}")
    
    def _get_translations(self, word: str) -> Dict[str, str]:
        """Get word translations - placeholder"""
        # In production, integrate with translation APIs like Google Translate
        return {
            'es': f"{word}_es",  # Spanish
            'fr': f"{word}_fr",  # French
            'de': f"{word}_de",  # German
            'it': f"{word}_it",  # Italian
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
            # Start new segment if duration exceeded
            if (current_segment['cues'] and 
                cue.start_time - current_segment['start_time'] > segment_duration):
                
                # Finalize current segment
                current_segment['end_time'] = current_segment['cues'][-1].end_time
                current_segment['difficulty_score'] = self._calculate_segment_difficulty(current_segment['cues'])
                current_segment['vocabulary_words'] = self._extract_vocabulary_words(current_segment['cues'])
                
                segments.append(current_segment)
                
                # Start new segment
                current_segment = {
                    'id': str(uuid.uuid4()),
                    'start_time': cue.start_time,
                    'end_time': 0,
                    'cues': [],
                    'vocabulary_words': [],
                    'difficulty_score': 0.0
                }
            
            # Set start time for first cue
            if not current_segment['cues']:
                current_segment['start_time'] = cue.start_time
            
            current_segment['cues'].append(cue)
        
        # Add final segment
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
        
        # Sort by difficulty (advanced first for challenge)
        vocabulary.sort(key=lambda x: {'advanced': 3, 'intermediate': 2, 'beginner': 1}.get(x.get('difficulty_level', 'beginner'), 1), reverse=True)
        
        return vocabulary[:10]  # Limit to top 10 vocabulary words per segment

# Example usage and utility functions
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

if __name__ == "__main__":
    # Test the processor
    processor = SubtitleProcessor()
    
    # Example SRT content
    srt_content = """1
00:00:01,000 --> 00:00:04,000
Hello, welcome to our language learning adventure.

2
00:00:04,500 --> 00:00:08,000
Today we'll explore fascinating vocabulary through cinema.

3
00:00:08,500 --> 00:00:12,000
This sophisticated approach enhances comprehension significantly.
"""
    
    # Test processing
    try:
        result = process_subtitle_file(srt_content.encode('utf-8'), 'srt', 'test-movie-123')
        print("✅ Subtitle processing test successful!")
        print(f"Processed {result['total_cues']} cues into {result['total_segments']} segments")
        print(f"Average difficulty: {result['avg_difficulty']:.2f}")
        print(f"Total vocabulary words: {result['vocabulary_count']}")
    except Exception as e:
        print(f"❌ Test failed: {e}")