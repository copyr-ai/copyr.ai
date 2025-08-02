-- Create tables for caching system and user authentication
-- Run these commands in your Supabase SQL editor

-- Table for user profiles (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for user search history
CREATE TABLE IF NOT EXISTS user_search_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE NOT NULL,
    query_text TEXT NOT NULL,
    filters JSONB DEFAULT '{}', -- store category, country, status filters
    results JSONB DEFAULT '[]', -- store search results
    result_count INTEGER DEFAULT 0,
    searched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for caching individual work records
CREATE TABLE IF NOT EXISTS work_cache (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    source_key TEXT UNIQUE NOT NULL, -- format: "source_api:source_id"
    title TEXT NOT NULL,
    author TEXT,
    publication_year INTEGER,
    work_type TEXT NOT NULL,
    copyright_status TEXT,
    public_domain_date TEXT,
    source_api TEXT NOT NULL,
    source_id TEXT NOT NULL,
    raw_data JSONB NOT NULL DEFAULT '{}',
    processed_data JSONB NOT NULL DEFAULT '{}',
    cache_status TEXT NOT NULL DEFAULT 'fresh' CHECK (cache_status IN ('fresh', 'stale', 'expired')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Table for caching search query results
CREATE TABLE IF NOT EXISTS cache_search_queries (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    query_hash TEXT UNIQUE NOT NULL,
    query_text TEXT NOT NULL,
    work_type TEXT NOT NULL,
    results UUID[] NOT NULL DEFAULT '{}', -- array of work_cache IDs
    total_results INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_work_cache_source_key ON work_cache(source_key);
CREATE INDEX IF NOT EXISTS idx_work_cache_expires_at ON work_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_work_cache_cache_status ON work_cache(cache_status);
CREATE INDEX IF NOT EXISTS idx_work_cache_source_api ON work_cache(source_api);
CREATE INDEX IF NOT EXISTS idx_work_cache_title ON work_cache USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_work_cache_author ON work_cache USING gin(to_tsvector('english', author));

CREATE INDEX IF NOT EXISTS idx_search_queries_hash ON cache_search_queries(query_hash);
CREATE INDEX IF NOT EXISTS idx_search_queries_expires_at ON cache_search_queries(expires_at);
CREATE INDEX IF NOT EXISTS idx_search_queries_work_type ON cache_search_queries(work_type);

-- Indexes for user tables
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_search_history_user_id ON user_search_history(user_id);
CREATE INDEX IF NOT EXISTS idx_user_search_history_searched_at ON user_search_history(searched_at DESC);

-- Enable Row Level Security (RLS) - optional but recommended
ALTER TABLE work_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE cache_search_queries ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_search_history ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (adjust as needed for your security requirements)
CREATE POLICY "Public read access on work_cache" ON work_cache FOR SELECT USING (true);
CREATE POLICY "Public insert access on work_cache" ON work_cache FOR INSERT WITH CHECK (true);
CREATE POLICY "Public update access on work_cache" ON work_cache FOR UPDATE USING (true);
CREATE POLICY "Public delete access on work_cache" ON work_cache FOR DELETE USING (true);

CREATE POLICY "Public read access on cache_search_queries" ON cache_search_queries FOR SELECT USING (true);
CREATE POLICY "Public insert access on cache_search_queries" ON cache_search_queries FOR INSERT WITH CHECK (true);
CREATE POLICY "Public update access on cache_search_queries" ON cache_search_queries FOR UPDATE USING (true);
CREATE POLICY "Public delete access on cache_search_queries" ON cache_search_queries FOR DELETE USING (true);

-- User-specific policies
CREATE POLICY "Users can view own profile" ON user_profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON user_profiles FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON user_profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can delete own profile" ON user_profiles FOR DELETE USING (auth.uid() = id);

CREATE POLICY "Users can view own search history" ON user_search_history FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own search history" ON user_search_history FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own search history" ON user_search_history FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own search history" ON user_search_history FOR DELETE USING (auth.uid() = user_id);

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_work_cache_updated_at 
    BEFORE UPDATE ON work_cache 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at 
    BEFORE UPDATE ON user_profiles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Optional: Create a function to clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete work cache entries older than 30 days past expiration
    DELETE FROM work_cache 
    WHERE expires_at < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Delete search query cache entries older than 7 days past expiration
    DELETE FROM cache_search_queries 
    WHERE expires_at < NOW() - INTERVAL '7 days';
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to handle new user profile creation
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name',
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to automatically create user profile on signup
CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();