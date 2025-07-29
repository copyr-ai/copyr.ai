-- Create tables for caching system
-- Run these commands in your Supabase SQL editor

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

-- Enable Row Level Security (RLS) - optional but recommended
ALTER TABLE work_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE cache_search_queries ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (adjust as needed for your security requirements)
CREATE POLICY "Public read access on work_cache" ON work_cache FOR SELECT USING (true);
CREATE POLICY "Public insert access on work_cache" ON work_cache FOR INSERT WITH CHECK (true);
CREATE POLICY "Public update access on work_cache" ON work_cache FOR UPDATE USING (true);
CREATE POLICY "Public delete access on work_cache" ON work_cache FOR DELETE USING (true);

CREATE POLICY "Public read access on cache_search_queries" ON cache_search_queries FOR SELECT USING (true);
CREATE POLICY "Public insert access on cache_search_queries" ON cache_search_queries FOR INSERT WITH CHECK (true);
CREATE POLICY "Public update access on cache_search_queries" ON cache_search_queries FOR UPDATE USING (true);
CREATE POLICY "Public delete access on cache_search_queries" ON cache_search_queries FOR DELETE USING (true);

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