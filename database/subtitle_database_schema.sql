-- CineFluent Subtitle and Learning Database Schema
-- Add these tables to your existing Supabase database

-- =====================================================
-- SUBTITLE MANAGEMENT TABLES
-- =====================================================

-- Table for subtitle files metadata
CREATE TABLE IF NOT EXISTS subtitles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id UUID NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    language VARCHAR(10) NOT NULL, -- ISO language code (en, es, fr, etc.)
    title VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL, -- srt, vtt
    total_cues INTEGER NOT NULL DEFAULT 0,
    total_segments INTEGER NOT NULL DEFAULT 0,
    duration DECIMAL(10,2) NOT NULL DEFAULT 0, -- Total duration in seconds
    avg_difficulty DECIMAL(3,2) NOT NULL DEFAULT 0, -- Average difficulty score
    vocabulary_count INTEGER NOT NULL DEFAULT 0,
    uploaded_by UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for individual subtitle cues
CREATE TABLE IF NOT EXISTS subtitle_cues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subtitle_id UUID NOT NULL REFERENCES subtitles(id) ON DELETE CASCADE,
    cue_index INTEGER NOT NULL, -- Order within subtitle file
    start_time DECIMAL(10,3) NOT NULL, -- Start time in seconds
    end_time DECIMAL(10,3) NOT NULL, -- End time in seconds
    text TEXT NOT NULL,
    words JSONB, -- Enriched word data with definitions, translations, etc.
    difficulty_score DECIMAL(3,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for learning segments (grouped cues for learning)
CREATE TABLE IF NOT EXISTS learning_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subtitle_id UUID NOT NULL REFERENCES subtitles(id) ON DELETE CASCADE,
    start_time DECIMAL(10,3) NOT NULL,
    end_time DECIMAL(10,3) NOT NULL,
    difficulty_score DECIMAL(3,2) DEFAULT 0,
    vocabulary_words JSONB, -- Key vocabulary words for this segment
    cue_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- USER PROGRESS TRACKING TABLES
-- =====================================================

-- Table for user progress on learning segments
CREATE TABLE IF NOT EXISTS user_segment_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    segment_id UUID NOT NULL REFERENCES learning_segments(id) ON DELETE CASCADE,
    time_spent INTEGER NOT NULL DEFAULT 0, -- Time spent in seconds
    words_learned TEXT[] DEFAULT '{}', -- Array of learned words
    completed BOOLEAN DEFAULT FALSE,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, segment_id)
);

-- Table for tracking user interactions with individual words
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

-- =====================================================
-- QUIZ AND ASSESSMENT TABLES
-- =====================================================

-- Table for quiz sessions
CREATE TABLE IF NOT EXISTS quiz_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    segment_id UUID NOT NULL REFERENCES learning_segments(id) ON DELETE CASCADE,
    questions JSONB NOT NULL, -- Quiz questions and metadata
    score DECIMAL(5,2), -- Final score percentage
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Table for individual quiz question submissions
CREATE TABLE IF NOT EXISTS quiz_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_session_id UUID NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
    question_id UUID NOT NULL, -- References question ID within the quiz
    word VARCHAR(100) NOT NULL,
    selected_answer TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    time_taken INTEGER NOT NULL DEFAULT 0, -- Time taken in seconds
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- VOCABULARY AND LEARNING ANALYTICS
-- =====================================================

-- Table for user vocabulary mastery levels
CREATE TABLE IF NOT EXISTS user_vocabulary_mastery (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    word VARCHAR(100) NOT NULL,
    lemma VARCHAR(100) NOT NULL, -- Base form of the word
    language VARCHAR(10) NOT NULL,
    mastery_level INTEGER DEFAULT 0, -- 0=unknown, 1=seen, 2=recognized, 3=mastered
    first_encountered TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_reviewed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    review_count INTEGER DEFAULT 0,
    correct_count INTEGER DEFAULT 0,
    next_review TIMESTAMP WITH TIME ZONE, -- For spaced repetition
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, word, language)
);

-- Table for tracking learning streaks and achievements
CREATE TABLE IF NOT EXISTS user_learning_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    stat_date DATE NOT NULL DEFAULT CURRENT_DATE,
    segments_completed INTEGER DEFAULT 0,
    words_learned INTEGER DEFAULT 0,
    quiz_questions_answered INTEGER DEFAULT 0,
    quiz_questions_correct INTEGER DEFAULT 0,
    time_spent INTEGER DEFAULT 0, -- Total time in seconds
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, stat_date)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Indexes for subtitles table
CREATE INDEX IF NOT EXISTS idx_subtitles_movie_id ON subtitles(movie_id);
CREATE INDEX IF NOT EXISTS idx_subtitles_language ON subtitles(language);
CREATE INDEX IF NOT EXISTS idx_subtitles_uploaded_by ON subtitles(uploaded_by);

-- Indexes for subtitle_cues table
CREATE INDEX IF NOT EXISTS idx_subtitle_cues_subtitle_id ON subtitle_cues(subtitle_id);
CREATE INDEX IF NOT EXISTS idx_subtitle_cues_timing ON subtitle_cues(start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_subtitle_cues_difficulty ON subtitle_cues(difficulty_score);

-- Indexes for learning_segments table
CREATE INDEX IF NOT EXISTS idx_learning_segments_subtitle_id ON learning_segments(subtitle_id);
CREATE INDEX IF NOT EXISTS idx_learning_segments_timing ON learning_segments(start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_learning_segments_difficulty ON learning_segments(difficulty_score);

-- Indexes for user progress tables
CREATE INDEX IF NOT EXISTS idx_user_segment_progress_user_id ON user_segment_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_segment_progress_segment_id ON user_segment_progress(segment_id);
CREATE INDEX IF NOT EXISTS idx_user_segment_progress_completed ON user_segment_progress(completed);

CREATE INDEX IF NOT EXISTS idx_user_word_interactions_user_id ON user_word_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_word_interactions_segment_id ON user_word_interactions(segment_id);
CREATE INDEX IF NOT EXISTS idx_user_word_interactions_word ON user_word_interactions(word);

-- Indexes for quiz tables
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user_id ON quiz_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_segment_id ON quiz_sessions(segment_id);
CREATE INDEX IF NOT EXISTS idx_quiz_submissions_session_id ON quiz_submissions(quiz_session_id);

-- Indexes for vocabulary mastery
CREATE INDEX IF NOT EXISTS idx_user_vocabulary_mastery_user_id ON user_vocabulary_mastery(user_id);
CREATE INDEX IF NOT EXISTS idx_user_vocabulary_mastery_word ON user_vocabulary_mastery(word);
CREATE INDEX IF NOT EXISTS idx_user_vocabulary_mastery_level ON user_vocabulary_mastery(mastery_level);
CREATE INDEX IF NOT EXISTS idx_user_vocabulary_mastery_next_review ON user_vocabulary_mastery(next_review);

-- Indexes for learning stats
CREATE INDEX IF NOT EXISTS idx_user_learning_stats_user_id ON user_learning_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_user_learning_stats_date ON user_learning_stats(stat_date);

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE subtitles ENABLE ROW LEVEL SECURITY;
ALTER TABLE subtitle_cues ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_segments ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_segment_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_word_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_vocabulary_mastery ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_learning_stats ENABLE ROW LEVEL SECURITY;

-- Policies for subtitles (public read, authenticated upload)
CREATE POLICY "Anyone can view subtitles" ON subtitles
    FOR SELECT USING (true);

CREATE POLICY "Authenticated users can upload subtitles" ON subtitles
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Users can update their own subtitles" ON subtitles
    FOR UPDATE USING (auth.uid() = uploaded_by);

CREATE POLICY "Users can delete their own subtitles" ON subtitles
    FOR DELETE USING (auth.uid() = uploaded_by);

-- Policies for subtitle_cues (public read)
CREATE POLICY "Anyone can view subtitle cues" ON subtitle_cues
    FOR SELECT USING (true);

CREATE POLICY "System can manage subtitle cues" ON subtitle_cues
    FOR ALL USING (true);

-- Policies for learning_segments (public read)
CREATE POLICY "Anyone can view learning segments" ON learning_segments
    FOR SELECT USING (true);

CREATE POLICY "System can manage learning segments" ON learning_segments
    FOR ALL USING (true);

-- Policies for user progress (users can only access their own data)
CREATE POLICY "Users can view their own segment progress" ON user_segment_progress
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own segment progress" ON user_segment_progress
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can modify their own segment progress" ON user_segment_progress
    FOR UPDATE USING (auth.uid() = user_id);

-- Policies for word interactions
CREATE POLICY "Users can view their own word interactions" ON user_word_interactions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own word interactions" ON user_word_interactions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own word interactions" ON user_word_interactions
    FOR UPDATE USING (auth.uid() = user_id);

-- Policies for quiz sessions
CREATE POLICY "Users can view their own quiz sessions" ON quiz_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own quiz sessions" ON quiz_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own quiz sessions" ON quiz_sessions
    FOR UPDATE USING (auth.uid() = user_id);

-- Policies for quiz submissions
CREATE POLICY "Users can view their own quiz submissions" ON quiz_submissions
    FOR SELECT USING (
        auth.uid() = (SELECT user_id FROM quiz_sessions WHERE id = quiz_session_id)
    );

CREATE POLICY "Users can create their own quiz submissions" ON quiz_submissions
    FOR INSERT WITH CHECK (
        auth.uid() = (SELECT user_id FROM quiz_sessions WHERE id = quiz_session_id)
    );

-- Policies for vocabulary mastery
CREATE POLICY "Users can view their own vocabulary mastery" ON user_vocabulary_mastery
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own vocabulary mastery" ON user_vocabulary_mastery
    FOR ALL USING (auth.uid() = user_id);

-- Policies for learning stats
CREATE POLICY "Users can view their own learning stats" ON user_learning_stats
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own learning stats" ON user_learning_stats
    FOR ALL USING (auth.uid() = user_id);

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$ language 'plpgsql';

-- Triggers for updating timestamps
CREATE TRIGGER update_subtitles_updated_at 
    BEFORE UPDATE ON subtitles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_segment_progress_updated_at 
    BEFORE UPDATE ON user_segment_progress 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_word_interactions_updated_at 
    BEFORE UPDATE ON user_word_interactions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_vocabulary_mastery_updated_at 
    BEFORE UPDATE ON user_vocabulary_mastery 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_learning_stats_updated_at 
    BEFORE UPDATE ON user_learning_stats 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update daily learning stats
CREATE OR REPLACE FUNCTION update_daily_learning_stats(
    p_user_id UUID,
    p_segments_completed INTEGER DEFAULT 0,
    p_words_learned INTEGER DEFAULT 0,
    p_quiz_questions_answered INTEGER DEFAULT 0,
    p_quiz_questions_correct INTEGER DEFAULT 0,
    p_time_spent INTEGER DEFAULT 0
)
RETURNS VOID AS $
DECLARE
    current_streak INTEGER;
    max_streak INTEGER;
BEGIN
    -- Insert or update today's stats
    INSERT INTO user_learning_stats (
        user_id, 
        stat_date, 
        segments_completed, 
        words_learned, 
        quiz_questions_answered, 
        quiz_questions_correct, 
        time_spent
    )
    VALUES (
        p_user_id, 
        CURRENT_DATE, 
        p_segments_completed, 
        p_words_learned, 
        p_quiz_questions_answered, 
        p_quiz_questions_correct, 
        p_time_spent
    )
    ON CONFLICT (user_id, stat_date) 
    DO UPDATE SET
        segments_completed = user_learning_stats.segments_completed + p_segments_completed,
        words_learned = user_learning_stats.words_learned + p_words_learned,
        quiz_questions_answered = user_learning_stats.quiz_questions_answered + p_quiz_questions_answered,
        quiz_questions_correct = user_learning_stats.quiz_questions_correct + p_quiz_questions_correct,
        time_spent = user_learning_stats.time_spent + p_time_spent,
        updated_at = NOW();

    -- Calculate and update streak
    SELECT 
        COALESCE(MAX(daily_streak), 0),
        COALESCE(MAX(max_streak), 0)
    INTO current_streak, max_streak
    FROM (
        SELECT 
            COUNT(*) as daily_streak,
            MAX(longest_streak) as max_streak
        FROM (
            SELECT 
                stat_date,
                longest_streak,
                stat_date - ROW_NUMBER() OVER (ORDER BY stat_date)::integer as streak_group
            FROM user_learning_stats 
            WHERE user_id = p_user_id 
                AND stat_date >= CURRENT_DATE - INTERVAL '365 days'
                AND (segments_completed > 0 OR words_learned > 0 OR quiz_questions_answered > 0)
            ORDER BY stat_date DESC
        ) grouped_dates
        GROUP BY streak_group
    ) streaks;

    -- Update current and longest streak
    UPDATE user_learning_stats 
    SET 
        current_streak = current_streak,
        longest_streak = GREATEST(longest_streak, current_streak)
    WHERE user_id = p_user_id AND stat_date = CURRENT_DATE;

END;
$ LANGUAGE plpgsql;

-- Function to calculate word mastery level
CREATE OR REPLACE FUNCTION calculate_word_mastery(
    p_user_id UUID,
    p_word VARCHAR(100),
    p_language VARCHAR(10),
    p_correct BOOLEAN
)
RETURNS INTEGER AS $
DECLARE
    current_level INTEGER;
    review_count INTEGER;
    correct_count INTEGER;
    new_level INTEGER;
BEGIN
    -- Get current mastery data
    SELECT 
        COALESCE(mastery_level, 0),
        COALESCE(review_count, 0),
        COALESCE(correct_count, 0)
    INTO current_level, review_count, correct_count
    FROM user_vocabulary_mastery
    WHERE user_id = p_user_id AND word = p_word AND language = p_language;

    -- Update counts
    review_count := review_count + 1;
    IF p_correct THEN
        correct_count := correct_count + 1;
    END IF;

    -- Calculate new mastery level
    IF review_count = 0 THEN
        new_level := 0; -- Unknown
    ELSIF correct_count = 0 THEN
        new_level := 1; -- Seen but not mastered
    ELSIF (correct_count::FLOAT / review_count) >= 0.8 AND review_count >= 3 THEN
        new_level := 3; -- Mastered
    ELSIF (correct_count::FLOAT / review_count) >= 0.6 THEN
        new_level := 2; -- Recognized
    ELSE
        new_level := 1; -- Seen
    END IF;

    -- Insert or update mastery record
    INSERT INTO user_vocabulary_mastery (
        user_id, word, language, mastery_level, 
        review_count, correct_count, last_reviewed
    )
    VALUES (
        p_user_id, p_word, p_language, new_level,
        review_count, correct_count, NOW()
    )
    ON CONFLICT (user_id, word, language)
    DO UPDATE SET
        mastery_level = new_level,
        review_count = review_count,
        correct_count = correct_count,
        last_reviewed = NOW(),
        updated_at = NOW();

    RETURN new_level;
END;
$ LANGUAGE plpgsql;

-- =====================================================
-- VIEWS FOR ANALYTICS AND REPORTING
-- =====================================================

-- View for subtitle analytics
CREATE OR REPLACE VIEW subtitle_analytics AS
SELECT 
    s.id,
    s.movie_id,
    s.language,
    s.title,
    s.total_cues,
    s.total_segments,
    s.duration,
    s.avg_difficulty,
    s.vocabulary_count,
    m.title as movie_title,
    COUNT(DISTINCT usp.user_id) as unique_learners,
    AVG(usp.time_spent) as avg_time_spent,
    COUNT(DISTINCT CASE WHEN usp.completed = true THEN usp.user_id END) as completions
FROM subtitles s
LEFT JOIN movies m ON s.movie_id = m.id
LEFT JOIN learning_segments ls ON s.id = ls.subtitle_id
LEFT JOIN user_segment_progress usp ON ls.id = usp.segment_id
GROUP BY s.id, m.title;

-- View for user learning progress summary
CREATE OR REPLACE VIEW user_learning_summary AS
SELECT 
    u.id as user_id,
    u.email,
    COUNT(DISTINCT usp.segment_id) as segments_studied,
    COUNT(DISTINCT CASE WHEN usp.completed = true THEN usp.segment_id END) as segments_completed,
    SUM(usp.time_spent) as total_time_spent,
    COUNT(DISTINCT uwi.word) as unique_words_encountered,
    COUNT(DISTINCT CASE WHEN uwi.marked_learned = true THEN uwi.word END) as words_learned,
    AVG(CASE WHEN qs.completed = true THEN qs.score END) as avg_quiz_score,
    MAX(uls.current_streak) as current_streak,
    MAX(uls.longest_streak) as longest_streak
FROM auth.users u
LEFT JOIN user_segment_progress usp ON u.id = usp.user_id
LEFT JOIN user_word_interactions uwi ON u.id = uwi.user_id
LEFT JOIN quiz_sessions qs ON u.id = qs.user_id
LEFT JOIN user_learning_stats uls ON u.id = uls.user_id
GROUP BY u.id, u.email;

-- View for vocabulary difficulty distribution
CREATE OR REPLACE VIEW vocabulary_difficulty_stats AS
SELECT 
    s.language,
    jsonb_array_elements(ls.vocabulary_words)->>'difficulty_level' as difficulty_level,
    COUNT(*) as word_count,
    AVG((jsonb_array_elements(ls.vocabulary_words)->>'frequency_rank')::INTEGER) as avg_frequency_rank
FROM subtitles s
JOIN learning_segments ls ON s.id = ls.subtitle_id
WHERE ls.vocabulary_words IS NOT NULL
GROUP BY s.language, jsonb_array_elements(ls.vocabulary_words)->>'difficulty_level';

-- =====================================================
-- SAMPLE DATA INSERTION (FOR TESTING)
-- =====================================================

-- Note: This sample data assumes you have movies in your movies table
-- You can uncomment and run this after setting up your movies

/*
-- Insert sample subtitle
INSERT INTO subtitles (id, movie_id, language, title, file_type, total_cues, total_segments, duration, avg_difficulty, vocabulary_count, uploaded_by)
SELECT 
    gen_random_uuid(),
    m.id,
    'en',
    m.title || ' - English Subtitles',
    'srt',
    100,
    10,
    7200.0,
    2.3,
    45,
    (SELECT id FROM auth.users LIMIT 1)
FROM movies m 
LIMIT 1;

-- Insert sample learning segment
INSERT INTO learning_segments (subtitle_id, start_time, end_time, difficulty_score, vocabulary_words, cue_count)
SELECT 
    s.id,
    0.0,
    720.0,
    2.5,
    '[{"word": "adventure", "difficulty_level": "intermediate", "definition": "An exciting experience"}, {"word": "fascinating", "difficulty_level": "advanced", "definition": "Very interesting"}]'::jsonb,
    10
FROM subtitles s
LIMIT 1;
*/

-- =====================================================
-- PERFORMANCE OPTIMIZATION QUERIES
-- =====================================================

-- Query to find most popular learning segments
/*
SELECT 
    ls.id,
    s.title as subtitle_title,
    ls.start_time,
    ls.end_time,
    ls.difficulty_score,
    COUNT(usp.user_id) as learner_count,
    AVG(usp.time_spent) as avg_time_spent
FROM learning_segments ls
JOIN subtitles s ON ls.subtitle_id = s.id
LEFT JOIN user_segment_progress usp ON ls.id = usp.segment_id
GROUP BY ls.id, s.title, ls.start_time, ls.end_time, ls.difficulty_score
ORDER BY learner_count DESC, avg_time_spent DESC;
*/

-- Query to find users who need vocabulary review
/*
SELECT 
    uvm.user_id,
    uvm.word,
    uvm.mastery_level,
    uvm.last_reviewed,
    uvm.next_review
FROM user_vocabulary_mastery uvm
WHERE uvm.next_review <= NOW()
    AND uvm.mastery_level < 3
ORDER BY uvm.last_reviewed ASC;
*/