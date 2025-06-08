-- CineFluent Complete Database Schema - FIXED VERSION
-- Run this in your Supabase SQL Editor to set up all required tables

-- =====================================================
-- CORE TABLES
-- =====================================================

-- Movies table
CREATE TABLE IF NOT EXISTS movies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    duration INTEGER NOT NULL DEFAULT 0, -- minutes
    release_year INTEGER,
    difficulty_level VARCHAR(20) DEFAULT 'beginner', -- beginner, intermediate, advanced
    languages JSONB DEFAULT '[]'::jsonb, -- Array of language codes as JSONB
    genres JSONB DEFAULT '[]'::jsonb, -- Array of genres as JSONB
    thumbnail_url TEXT,
    video_url TEXT,
    is_premium BOOLEAN DEFAULT FALSE,
    vocabulary_count INTEGER DEFAULT 0,
    imdb_rating DECIMAL(3,1),
    tmdb_id INTEGER UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User profiles table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username VARCHAR(50) UNIQUE,
    full_name VARCHAR(255),
    avatar_url TEXT,
    native_language VARCHAR(10) DEFAULT 'en',
    learning_languages JSONB DEFAULT '[]'::jsonb,
    learning_goals JSONB DEFAULT '{}'::jsonb,
    subscription_type VARCHAR(20) DEFAULT 'free', -- free, premium
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User progress tracking
CREATE TABLE IF NOT EXISTS user_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    movie_id UUID NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    time_watched INTEGER DEFAULT 0, -- seconds
    vocabulary_learned INTEGER DEFAULT 0,
    last_watched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, movie_id)
);

-- Categories/Genres lookup
CREATE TABLE IF NOT EXISTS categories (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    plan_type VARCHAR(20) NOT NULL DEFAULT 'free', -- free, premium, pro
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, cancelled, expired
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    stripe_subscription_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- =====================================================
-- SUBTITLE AND LEARNING TABLES  
-- =====================================================

-- Subtitle files metadata
CREATE TABLE IF NOT EXISTS subtitles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id UUID NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    language VARCHAR(10) NOT NULL,
    title VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL, -- srt, vtt
    total_cues INTEGER NOT NULL DEFAULT 0,
    total_segments INTEGER NOT NULL DEFAULT 0,
    duration DECIMAL(10,2) NOT NULL DEFAULT 0,
    avg_difficulty DECIMAL(3,2) NOT NULL DEFAULT 0,
    vocabulary_count INTEGER NOT NULL DEFAULT 0,
    uploaded_by UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Individual subtitle cues
CREATE TABLE IF NOT EXISTS subtitle_cues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subtitle_id UUID NOT NULL REFERENCES subtitles(id) ON DELETE CASCADE,
    cue_index INTEGER NOT NULL,
    start_time DECIMAL(10,3) NOT NULL,
    end_time DECIMAL(10,3) NOT NULL,
    text TEXT NOT NULL,
    words JSONB,
    difficulty_score DECIMAL(3,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Learning segments (grouped cues)
CREATE TABLE IF NOT EXISTS learning_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subtitle_id UUID NOT NULL REFERENCES subtitles(id) ON DELETE CASCADE,
    start_time DECIMAL(10,3) NOT NULL,
    end_time DECIMAL(10,3) NOT NULL,
    difficulty_score DECIMAL(3,2) DEFAULT 0,
    vocabulary_words JSONB,
    cue_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User progress on learning segments
CREATE TABLE IF NOT EXISTS user_segment_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    segment_id UUID NOT NULL REFERENCES learning_segments(id) ON DELETE CASCADE,
    time_spent INTEGER NOT NULL DEFAULT 0,
    words_learned JSONB DEFAULT '[]'::jsonb, -- Changed from TEXT[] to JSONB
    completed BOOLEAN DEFAULT FALSE,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, segment_id)
);

-- User word interactions
CREATE TABLE IF NOT EXISTS user_word_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    segment_id UUID NOT NULL REFERENCES learning_segments(id) ON DELETE CASCADE,
    cue_id UUID REFERENCES subtitle_cues(id) ON DELETE CASCADE,
    word VARCHAR(100) NOT NULL,
    definition_viewed BOOLEAN DEFAULT FALSE,
    marked_learned BOOLEAN DEFAULT FALSE,
    quiz_attempted BOOLEAN DEFAULT FALSE,
    quiz_correct BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Quiz sessions
CREATE TABLE IF NOT EXISTS quiz_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    segment_id UUID NOT NULL REFERENCES learning_segments(id) ON DELETE CASCADE,
    questions JSONB NOT NULL,
    score DECIMAL(5,2),
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Quiz submissions
CREATE TABLE IF NOT EXISTS quiz_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_session_id UUID NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
    question_id UUID NOT NULL,
    word VARCHAR(100) NOT NULL,
    selected_answer TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    time_taken INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vocabulary mastery tracking
CREATE TABLE IF NOT EXISTS user_vocabulary_mastery (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    word VARCHAR(100) NOT NULL,
    lemma VARCHAR(100) NOT NULL,
    language VARCHAR(10) NOT NULL,
    mastery_level INTEGER DEFAULT 0, -- 0=unknown, 1=seen, 2=recognized, 3=mastered
    first_encountered TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_reviewed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    review_count INTEGER DEFAULT 0,
    correct_count INTEGER DEFAULT 0,
    next_review TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, word, language)
);

-- Daily learning statistics
CREATE TABLE IF NOT EXISTS user_learning_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    stat_date DATE NOT NULL DEFAULT CURRENT_DATE,
    segments_completed INTEGER DEFAULT 0,
    words_learned INTEGER DEFAULT 0,
    quiz_questions_answered INTEGER DEFAULT 0,
    quiz_questions_correct INTEGER DEFAULT 0,
    time_spent INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, stat_date)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Movies indexes
CREATE INDEX IF NOT EXISTS idx_movies_difficulty ON movies(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_movies_premium ON movies(is_premium);
CREATE INDEX IF NOT EXISTS idx_movies_languages ON movies USING GIN(languages);
CREATE INDEX IF NOT EXISTS idx_movies_genres ON movies USING GIN(genres);

-- Progress indexes  
CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_progress_movie_id ON user_progress(movie_id);
CREATE INDEX IF NOT EXISTS idx_user_progress_completed ON user_progress(completed_at);

-- Subtitle indexes
CREATE INDEX IF NOT EXISTS idx_subtitles_movie_id ON subtitles(movie_id);
CREATE INDEX IF NOT EXISTS idx_subtitles_language ON subtitles(language);
CREATE INDEX IF NOT EXISTS idx_subtitle_cues_subtitle_id ON subtitle_cues(subtitle_id);
CREATE INDEX IF NOT EXISTS idx_subtitle_cues_timing ON subtitle_cues(start_time, end_time);

-- Learning indexes
CREATE INDEX IF NOT EXISTS idx_learning_segments_subtitle_id ON learning_segments(subtitle_id);
CREATE INDEX IF NOT EXISTS idx_user_segment_progress_user_id ON user_segment_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_word_interactions_user_id ON user_word_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_vocabulary_mastery_user_id ON user_vocabulary_mastery(user_id);

-- =====================================================
-- ROW LEVEL SECURITY (RLS)
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE movies ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE subtitles ENABLE ROW LEVEL SECURITY;
ALTER TABLE subtitle_cues ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_segments ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_segment_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_word_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_vocabulary_mastery ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_learning_stats ENABLE ROW LEVEL SECURITY;

-- Movies policies (public read)
CREATE POLICY "Anyone can view movies" ON movies FOR SELECT USING (true);
CREATE POLICY "Admin can manage movies" ON movies FOR ALL USING (auth.role() = 'service_role');

-- Profiles policies (users can manage their own)
CREATE POLICY "Users can view all profiles" ON profiles FOR SELECT USING (true);
CREATE POLICY "Users can update their own profile" ON profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can insert their own profile" ON profiles FOR INSERT WITH CHECK (auth.uid() = id);

-- User progress policies (private to user)
CREATE POLICY "Users can view their own progress" ON user_progress FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update their own progress" ON user_progress FOR ALL USING (auth.uid() = user_id);

-- Subscription policies
CREATE POLICY "Users can view their own subscription" ON subscriptions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update their own subscription" ON subscriptions FOR UPDATE USING (auth.uid() = user_id);

-- Subtitle policies (public read, authenticated upload)
CREATE POLICY "Anyone can view subtitles" ON subtitles FOR SELECT USING (true);
CREATE POLICY "Authenticated users can upload subtitles" ON subtitles FOR INSERT WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Users can update their own subtitles" ON subtitles FOR UPDATE USING (auth.uid() = uploaded_by);

-- Subtitle cues policies (public read)
CREATE POLICY "Anyone can view subtitle cues" ON subtitle_cues FOR SELECT USING (true);
CREATE POLICY "System can manage subtitle cues" ON subtitle_cues FOR ALL USING (true);

-- Learning segments policies (public read)
CREATE POLICY "Anyone can view learning segments" ON learning_segments FOR SELECT USING (true);
CREATE POLICY "System can manage learning segments" ON learning_segments FOR ALL USING (true);

-- User learning data policies (private to user)
CREATE POLICY "Users can view their own segment progress" ON user_segment_progress FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can manage their own segment progress" ON user_segment_progress FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own word interactions" ON user_word_interactions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can manage their own word interactions" ON user_word_interactions FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own quiz sessions" ON quiz_sessions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can manage their own quiz sessions" ON quiz_sessions FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own quiz submissions" ON quiz_submissions FOR SELECT USING (
    auth.uid() = (SELECT user_id FROM quiz_sessions WHERE id = quiz_session_id)
);
CREATE POLICY "Users can create their own quiz submissions" ON quiz_submissions FOR INSERT WITH CHECK (
    auth.uid() = (SELECT user_id FROM quiz_sessions WHERE id = quiz_session_id)
);

CREATE POLICY "Users can view their own vocabulary mastery" ON user_vocabulary_mastery FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can manage their own vocabulary mastery" ON user_vocabulary_mastery FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own learning stats" ON user_learning_stats FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can manage their own learning stats" ON user_learning_stats FOR ALL USING (auth.uid() = user_id);

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add update triggers
CREATE TRIGGER update_movies_updated_at BEFORE UPDATE ON movies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_progress_updated_at BEFORE UPDATE ON user_progress FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subtitles_updated_at BEFORE UPDATE ON subtitles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_segment_progress_updated_at BEFORE UPDATE ON user_segment_progress FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_word_interactions_updated_at BEFORE UPDATE ON user_word_interactions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_vocabulary_mastery_updated_at BEFORE UPDATE ON user_vocabulary_mastery FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_learning_stats_updated_at BEFORE UPDATE ON user_learning_stats FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- SAMPLE DATA
-- =====================================================

-- Insert categories
INSERT INTO categories (id, name, description, sort_order) VALUES
('action', 'Action', 'High-energy movies with adventure and excitement', 1),
('drama', 'Drama', 'Character-driven stories with emotional depth', 2),
('comedy', 'Comedy', 'Light-hearted movies designed to entertain', 3),
('thriller', 'Thriller', 'Suspenseful movies that keep you on edge', 4),
('romance', 'Romance', 'Love stories and romantic relationships', 5),
('sci-fi', 'Science Fiction', 'Futuristic and speculative fiction', 6),
('documentary', 'Documentary', 'Non-fiction educational content', 7),
('animation', 'Animation', 'Animated movies for all ages', 8),
('horror', 'Horror', 'Scary movies and supernatural themes', 9),
('fantasy', 'Fantasy', 'Magical and mythological adventures', 10)
ON CONFLICT (id) DO NOTHING;

-- Insert sample movies (FIXED - using JSONB format)
INSERT INTO movies (id, title, description, duration, release_year, difficulty_level, languages, genres, thumbnail_url, is_premium, vocabulary_count, imdb_rating) VALUES
(gen_random_uuid(), 'The Shawshank Redemption', 'Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.', 142, 1994, 'intermediate', '["en"]'::jsonb, '["drama"]'::jsonb, 'https://m.media-amazon.com/images/M/MV5BMDFkYTc0MGEtZmNhMC00ZDIzLWFmNTEtODM1ZmRlYWMwMWFmXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_.jpg', false, 850, 9.3),
(gen_random_uuid(), 'Forrest Gump', 'The presidencies of Kennedy and Johnson through the events of Vietnam, Watergate and other historical events unfold from the perspective of an Alabama man.', 142, 1994, 'beginner', '["en"]'::jsonb, '["drama", "romance"]'::jsonb, 'https://m.media-amazon.com/images/M/MV5BNWIwODRlZTUtY2U3ZS00Yzg1LWJhNzYtMmZiYmEyNmU1NjMzXkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_.jpg', false, 650, 8.8),
(gen_random_uuid(), 'The Dark Knight', 'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests.', 152, 2008, 'advanced', '["en"]'::jsonb, '["action", "thriller"]'::jsonb, 'https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_.jpg', true, 950, 9.0),
(gen_random_uuid(), 'Amélie', 'Amélie is an innocent and naive girl in Paris with her own sense of justice. She decides to help those around her and, along the way, discovers love.', 122, 2001, 'intermediate', '["fr", "en"]'::jsonb, '["romance", "comedy"]'::jsonb, 'https://m.media-amazon.com/images/M/MV5BNDg4NjM1YjMtYmNhZC00MjM0LWFiZmYtNGY1YjA3MzZmODc5XkEyXkFqcGdeQXVyNDk3NzU2MTQ@._V1_.jpg', false, 720, 8.3),
(gen_random_uuid(), 'Spirited Away', 'During her familys move to the suburbs, a sullen 10-year-old girl wanders into a world ruled by gods and witches where humans are changed into beasts.', 125, 2001, 'beginner', '["ja", "en"]'::jsonb, '["animation", "fantasy"]'::jsonb, 'https://m.media-amazon.com/images/M/MV5BMjlmZmI5MDctNDE2YS00YWE0LWE5ZWItZDBhYWQ0NTcxNWRhXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_.jpg', false, 580, 9.2),
(gen_random_uuid(), 'The Godfather', 'The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.', 175, 1972, 'advanced', '["en"]'::jsonb, '["drama", "crime"]'::jsonb, 'https://m.media-amazon.com/images/M/MV5BM2MyNjYxNmUtYTAwNi00MTYxLWJmNWYtYzZlODY3ZTk3OTFlXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_.jpg', false, 920, 9.2),
(gen_random_uuid(), 'Pulp Fiction', 'The lives of two mob hitmen, a boxer, a gangster and his wife intertwine in four tales of violence and redemption.', 154, 1994, 'advanced', '["en"]'::jsonb, '["drama", "crime"]'::jsonb, 'https://m.media-amazon.com/images/M/MV5BNGNhMDIzZTUtNTBlZi00MTRlLWFjM2ItYzViMjE3YzI5MjljXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_.jpg', true, 880, 8.9)
ON CONFLICT DO NOTHING;

-- Success message
SELECT 'Database schema setup completed successfully! 🎉' as status;
