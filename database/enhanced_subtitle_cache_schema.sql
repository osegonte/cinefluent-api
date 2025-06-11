-- Enhanced Multi-Language Subtitle System Database Schema
-- Add these tables to your existing Supabase database for the enhanced subtitle functionality

-- =====================================================
-- SUBTITLE CACHING SYSTEM
-- =====================================================

-- Table for caching external subtitle search results
CREATE TABLE IF NOT EXISTS subtitle_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key VARCHAR(32) NOT NULL UNIQUE, -- MD5 hash of movie_id:language:title
    movie_id UUID NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    language VARCHAR(10) NOT NULL,
    movie_title VARCHAR(255) NOT NULL,
    subtitles_data JSONB NOT NULL, -- Cached subtitle metadata as JSON
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for tracking subtitle download/processing jobs
CREATE TABLE IF NOT EXISTS subtitle_processing_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id UUID NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    language VARCHAR(10) NOT NULL,
    external_subtitle_id VARCHAR(255) NOT NULL,
    source VARCHAR(50) NOT NULL, -- opensubtitles, subscene, etc.
    file_url TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'queued', -- queued, processing, completed, failed
    priority INTEGER DEFAULT 5, -- 1 (highest) to 10 (lowest)
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for tracking external API usage and rate limits
CREATE TABLE IF NOT EXISTS external_api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_name VARCHAR(50) NOT NULL, -- opensubtitles, subscene, etc.
    endpoint VARCHAR(100) NOT NULL,
    request_count INTEGER DEFAULT 1,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    rate_limit_remaining INTEGER,
    rate_limit_reset TIMESTAMP WITH TIME ZONE,
    request_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(api_name, endpoint, request_date)
);

-- Enhanced subtitles table with external API tracking
-- Add columns to existing subtitles table
ALTER TABLE subtitles ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'upload';
ALTER TABLE subtitles ADD COLUMN IF NOT EXISTS external_id VARCHAR(255);
ALTER TABLE subtitles ADD COLUMN IF NOT EXISTS external_url TEXT;
ALTER TABLE subtitles ADD COLUMN IF NOT EXISTS download_count INTEGER DEFAULT 0;
ALTER TABLE subtitles ADD COLUMN IF NOT EXISTS rating DECIMAL(3,2) DEFAULT 0.0;
ALTER TABLE subtitles ADD COLUMN IF NOT EXISTS release_info TEXT;
ALTER TABLE subtitles ADD COLUMN IF NOT EXISTS encoding VARCHAR(20) DEFAULT 'utf-8';
ALTER TABLE subtitles ADD COLUMN IF NOT EXISTS hash_value VARCHAR(64); -- For subtitle file hash

-- Table for user subtitle search history and preferences
CREATE TABLE IF NOT EXISTS user_subtitle_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    preferred_languages TEXT[] DEFAULT ARRAY['en'], -- Array of language codes
    auto_download BOOLEAN DEFAULT FALSE,
    quality_preference VARCHAR(20) DEFAULT 'balanced', -- quality, speed, balanced
    external_apis_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Table for tracking user subtitle searches and downloads
CREATE TABLE IF NOT EXISTS user_subtitle_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    movie_id UUID NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    language VARCHAR(10) NOT NULL,
    activity_type VARCHAR(20) NOT NULL, -- search, download, process
    source VARCHAR(50), -- database, cache, opensubtitles, etc.
    subtitle_id UUID REFERENCES subtitles(id) ON DELETE SET NULL,
    metadata JSONB, -- Additional activity metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- PERFORMANCE INDEXES
-- =====================================================

-- Indexes for subtitle cache
CREATE INDEX IF NOT EXISTS idx_subtitle_cache_key ON subtitle_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_subtitle_cache_movie_lang ON subtitle_cache(movie_id, language);
CREATE INDEX IF NOT EXISTS idx_subtitle_cache_expires ON subtitle_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_subtitle_cache_created ON subtitle_cache(created_at DESC);

-- Indexes for processing queue
CREATE INDEX IF NOT EXISTS idx_processing_queue_status ON subtitle_processing_queue(status);
CREATE INDEX IF NOT EXISTS idx_processing_queue_priority ON subtitle_processing_queue(priority, created_at);
CREATE INDEX IF NOT EXISTS idx_processing_queue_movie_lang ON subtitle_processing_queue(movie_id, language);
CREATE INDEX IF NOT EXISTS idx_processing_queue_source ON subtitle_processing_queue(source);

-- Indexes for API usage tracking
CREATE INDEX IF NOT EXISTS idx_api_usage_date ON external_api_usage(api_name, request_date);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON external_api_usage(api_name, endpoint);

-- Enhanced indexes for subtitles table
CREATE INDEX IF NOT EXISTS idx_subtitles_source ON subtitles(source);
CREATE INDEX IF NOT EXISTS idx_subtitles_external_id ON subtitles(external_id);
CREATE INDEX IF NOT EXISTS idx_subtitles_rating ON subtitles(rating DESC);
CREATE INDEX IF NOT EXISTS idx_subtitles_movie_lang_source ON subtitles(movie_id, language, source);

-- Indexes for user activity tracking
CREATE INDEX IF NOT EXISTS idx_user_subtitle_activity_user ON user_subtitle_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subtitle_activity_movie ON user_subtitle_activity(movie_id);
CREATE INDEX IF NOT EXISTS idx_user_subtitle_activity_type ON user_subtitle_activity(activity_type);
CREATE INDEX IF NOT EXISTS idx_user_subtitle_activity_created ON user_subtitle_activity(created_at DESC);

-- =====================================================
-- ROW LEVEL SECURITY (RLS)
-- =====================================================

-- Enable RLS on new tables
ALTER TABLE subtitle_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE subtitle_processing_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE external_api_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subtitle_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subtitle_activity ENABLE ROW LEVEL SECURITY;

-- Cache policies (readable by all authenticated users, manageable by system)
CREATE POLICY "Users can view subtitle cache" ON subtitle_cache
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "System can manage subtitle cache" ON subtitle_cache
    FOR ALL USING (auth.role() = 'service_role');

-- Processing queue policies (users can view their requests, system manages all)
CREATE POLICY "Users can view processing queue" ON subtitle_processing_queue
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "System can manage processing queue" ON subtitle_processing_queue
    FOR ALL USING (auth.role() = 'service_role');

-- API usage policies (admin only)
CREATE POLICY "System can manage API usage" ON external_api_usage
    FOR ALL USING (auth.role() = 'service_role');

-- User preferences policies (users can manage their own)
CREATE POLICY "Users can view their own subtitle preferences" ON user_subtitle_preferences
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own subtitle preferences" ON user_subtitle_preferences
    FOR ALL USING (auth.uid() = user_id);

-- User activity policies (users can view their own activity)
CREATE POLICY "Users can view their own subtitle activity" ON user_subtitle_activity
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own subtitle activity" ON user_subtitle_activity
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "System can manage all subtitle activity" ON user_subtitle_activity
    FOR ALL USING (auth.role() = 'service_role');

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_subtitle_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM subtitle_cache WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Also clean up old processing queue entries
    DELETE FROM subtitle_processing_queue 
    WHERE status IN ('completed', 'failed') 
    AND updated_at < NOW() - INTERVAL '7 days';
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to update API usage statistics
CREATE OR REPLACE FUNCTION update_api_usage_stats(
    p_api_name VARCHAR(50),
    p_endpoint VARCHAR(100),
    p_success BOOLEAN DEFAULT TRUE,
    p_rate_limit_remaining INTEGER DEFAULT NULL,
    p_rate_limit_reset TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO external_api_usage (
        api_name,
        endpoint,
        request_count,
        success_count,
        error_count,
        rate_limit_remaining,
        rate_limit_reset,
        request_date
    )
    VALUES (
        p_api_name,
        p_endpoint,
        1,
        CASE WHEN p_success THEN 1 ELSE 0 END,
        CASE WHEN p_success THEN 0 ELSE 1 END,
        p_rate_limit_remaining,
        p_rate_limit_reset,
        CURRENT_DATE
    )
    ON CONFLICT (api_name, endpoint, request_date)
    DO UPDATE SET
        request_count = external_api_usage.request_count + 1,
        success_count = external_api_usage.success_count + CASE WHEN p_success THEN 1 ELSE 0 END,
        error_count = external_api_usage.error_count + CASE WHEN p_success THEN 0 ELSE 1 END,
        rate_limit_remaining = COALESCE(p_rate_limit_remaining, external_api_usage.rate_limit_remaining),
        rate_limit_reset = COALESCE(p_rate_limit_reset, external_api_usage.rate_limit_reset),
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Function to get cache statistics
CREATE OR REPLACE FUNCTION get_subtitle_cache_stats()
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_entries', COUNT(*),
        'expired_entries', COUNT(*) FILTER (WHERE expires_at < NOW()),
        'active_entries', COUNT(*) FILTER (WHERE expires_at >= NOW()),
        'languages_cached', COUNT(DISTINCT language),
        'movies_cached', COUNT(DISTINCT movie_id),
        'cache_size_mb', ROUND(
            (pg_total_relation_size('subtitle_cache')::NUMERIC / 1024 / 1024), 2
        ),
        'oldest_entry', MIN(created_at),
        'newest_entry', MAX(created_at),
        'avg_entries_per_movie', CASE 
            WHEN COUNT(DISTINCT movie_id) > 0 
            THEN ROUND(COUNT(*)::NUMERIC / COUNT(DISTINCT movie_id), 2)
            ELSE 0 
        END
    )
    INTO result
    FROM subtitle_cache;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to record user subtitle activity
CREATE OR REPLACE FUNCTION record_subtitle_activity(
    p_user_id UUID,
    p_movie_id UUID,
    p_language VARCHAR(10),
    p_activity_type VARCHAR(20),
    p_source VARCHAR(50) DEFAULT NULL,
    p_subtitle_id UUID DEFAULT NULL,
    p_metadata JSONB DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO user_subtitle_activity (
        user_id, movie_id, language, activity_type, 
        source, subtitle_id, metadata
    )
    VALUES (
        p_user_id, p_movie_id, p_language, p_activity_type,
        p_source, p_subtitle_id, p_metadata
    );
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at timestamps
CREATE TRIGGER update_subtitle_cache_updated_at 
    BEFORE UPDATE ON subtitle_cache 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_processing_queue_updated_at 
    BEFORE UPDATE ON subtitle_processing_queue 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_usage_updated_at 
    BEFORE UPDATE ON external_api_usage 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_subtitle_preferences_updated_at 
    BEFORE UPDATE ON user_subtitle_preferences 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- VIEWS FOR ANALYTICS
-- =====================================================

-- View for cache performance analytics
CREATE OR REPLACE VIEW subtitle_cache_analytics AS
SELECT 
    DATE(created_at) as cache_date,
    language,
    COUNT(*) as entries_created,
    COUNT(*) FILTER (WHERE expires_at >= NOW()) as active_entries,
    AVG(EXTRACT(EPOCH FROM (expires_at - created_at))) / 3600 as avg_ttl_hours,
    COUNT(DISTINCT movie_id) as unique_movies
FROM subtitle_cache
GROUP BY DATE(created_at), language
ORDER BY cache_date DESC, language;

-- View for API usage analytics
CREATE OR REPLACE VIEW api_usage_analytics AS
SELECT 
    api_name,
    endpoint,
    request_date,
    request_count,
    success_count,
    error_count,
    ROUND((success_count::DECIMAL / NULLIF(request_count, 0)) * 100, 2) as success_rate,
    rate_limit_remaining
FROM external_api_usage
ORDER BY request_date DESC, api_name, endpoint;

-- View for processing queue analytics
CREATE OR REPLACE VIEW processing_queue_analytics AS
SELECT 
    DATE(created_at) as processing_date,
    language,
    source,
    status,
    COUNT(*) as job_count,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) / 60 as avg_processing_time_minutes,
    MAX(retry_count) as max_retries
FROM subtitle_processing_queue
GROUP BY DATE(created_at), language, source, status
ORDER BY processing_date DESC, language, source;

-- View for user activity summary
CREATE OR REPLACE VIEW user_subtitle_activity_summary AS
SELECT 
    user_id,
    COUNT(*) as total_activities,
    COUNT(DISTINCT movie_id) as unique_movies_accessed,
    COUNT(DISTINCT language) as languages_used,
    COUNT(*) FILTER (WHERE activity_type = 'search') as searches_performed,
    COUNT(*) FILTER (WHERE activity_type = 'download') as downloads_initiated,
    COUNT(*) FILTER (WHERE activity_type = 'process') as processings_completed,
    MAX(created_at) as last_activity,
    MIN(created_at) as first_activity
FROM user_subtitle_activity
GROUP BY user_id;

-- View for popular subtitle languages
CREATE OR REPLACE VIEW popular_subtitle_languages AS
SELECT 
    language,
    COUNT(*) as subtitle_count,
    COUNT(DISTINCT movie_id) as movie_count,
    AVG(rating) as avg_rating,
    COUNT(*) FILTER (WHERE source = 'database') as local_count,
    COUNT(*) FILTER (WHERE source != 'database') as external_count,
    ROUND((COUNT(*)::DECIMAL / (SELECT COUNT(*) FROM subtitles)) * 100, 2) as percentage
FROM subtitles
GROUP BY language
ORDER BY subtitle_count DESC;

-- =====================================================
-- SAMPLE QUERIES FOR MONITORING
-- =====================================================

-- Get cache statistics
-- SELECT get_subtitle_cache_stats();

-- Get top cached languages
-- SELECT language, COUNT(*) as cache_entries
-- FROM subtitle_cache 
-- WHERE expires_at >= NOW()
-- GROUP BY language 
-- ORDER BY cache_entries DESC;

-- Get API usage summary for last 7 days
-- SELECT api_name, 
--        SUM(request_count) as total_requests,
--        SUM(success_count) as successful_requests,
--        ROUND(AVG(success_count::DECIMAL / NULLIF(request_count, 0)) * 100, 2) as avg_success_rate
-- FROM external_api_usage 
-- WHERE request_date >= CURRENT_DATE - INTERVAL '7 days'
-- GROUP BY api_name;

-- Get processing queue status
-- SELECT status, COUNT(*) as job_count, 
--        MIN(created_at) as oldest_job,
--        MAX(created_at) as newest_job
-- FROM subtitle_processing_queue 
-- GROUP BY status;

-- Get user activity trends
-- SELECT DATE(created_at) as activity_date,
--        activity_type,
--        COUNT(*) as activity_count,
--        COUNT(DISTINCT user_id) as unique_users
-- FROM user_subtitle_activity
-- WHERE created_at >= NOW() - INTERVAL '30 days'
-- GROUP BY DATE(created_at), activity_type
-- ORDER BY activity_date DESC;

-- Success message
SELECT 'Enhanced multi-language subtitle system schema created successfully! 🌐' as status;