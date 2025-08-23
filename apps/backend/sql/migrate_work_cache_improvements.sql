-- Migration Script: Work Cache Table Improvements
-- Run this in your Supabase SQL editor to fix the 4 main issues
-- This will update the existing work_cache table structure

-- Step 1: Add normalization functions
CREATE OR REPLACE FUNCTION normalize_title(input_title TEXT) 
RETURNS TEXT AS $$
BEGIN
    IF input_title IS NULL OR input_title = '' THEN
        RETURN '';
    END IF;
    
    RETURN LOWER(
        TRIM(
            regexp_replace(
                regexp_replace(
                    regexp_replace(input_title, '^(the|a|an)\s+', '', 'i'),  -- Remove leading articles
                    '[^a-zA-Z0-9\s]', '', 'g'                                -- Remove punctuation
                ),
                '\s+', ' ', 'g'                                               -- Normalize whitespace
            )
        )
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION normalize_author(input_author TEXT) 
RETURNS TEXT AS $$
BEGIN
    IF input_author IS NULL OR input_author = '' THEN
        RETURN '';
    END IF;
    
    -- Handle "Last, First" format and convert to "first last"
    RETURN LOWER(
        TRIM(
            regexp_replace(
                regexp_replace(
                    CASE 
                        WHEN input_author ~ '^[^,]+,\s*[^,]+$' THEN  -- "Last, First" format
                            TRIM(SPLIT_PART(input_author, ',', 2)) || ' ' || TRIM(SPLIT_PART(input_author, ',', 1))
                        ELSE 
                            input_author
                    END,
                    '[^a-zA-Z0-9\s]', '', 'g'                    -- Remove punctuation
                ),
                '\s+', ' ', 'g'                                  -- Normalize whitespace
            )
        )
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION generate_content_hash(title TEXT, author TEXT, pub_year INTEGER)
RETURNS TEXT AS $$
BEGIN
    RETURN encode(
        digest(
            COALESCE(normalize_title(title), '') || '|' || 
            COALESCE(normalize_author(author), '') || '|' ||
            COALESCE(pub_year::TEXT, ''),
            'sha256'
        ),
        'hex'
    );
END;
$$ LANGUAGE plpgsql;

-- Step 2: Add new columns to existing table
ALTER TABLE work_cache ADD COLUMN IF NOT EXISTS title_normalized TEXT;
ALTER TABLE work_cache ADD COLUMN IF NOT EXISTS author_normalized TEXT;
ALTER TABLE work_cache ADD COLUMN IF NOT EXISTS content_hash TEXT;
ALTER TABLE work_cache ADD COLUMN IF NOT EXISTS work_subtype TEXT;
ALTER TABLE work_cache ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(3,2) DEFAULT 0.80;

-- Step 3: Fix public_domain_date data type
-- First, create a temporary column with correct type
ALTER TABLE work_cache ADD COLUMN IF NOT EXISTS public_domain_year INTEGER;

-- Step 4: Populate new normalized fields and fix data types for existing records
UPDATE work_cache SET 
    title_normalized = normalize_title(title),
    author_normalized = normalize_author(author),
    public_domain_year = CASE 
        WHEN public_domain_date ~ '^\d{4}$' THEN public_domain_date::INTEGER
        WHEN public_domain_date ~ '^\d+$' THEN public_domain_date::INTEGER
        ELSE NULL
    END,
    confidence_score = COALESCE(
        (processed_data->>'confidence_score')::DECIMAL(3,2), 
        0.80
    )
WHERE title_normalized IS NULL OR author_normalized IS NULL OR public_domain_year IS NULL;

-- Step 5: Generate content hashes (this will help identify duplicates)
UPDATE work_cache SET 
    content_hash = generate_content_hash(title, author, publication_year)
WHERE content_hash IS NULL;

-- Step 6: Create better indexes
-- Drop old inefficient indexes if they exist
DROP INDEX IF EXISTS idx_work_cache_source_key;

-- Create new efficient indexes
CREATE INDEX IF NOT EXISTS idx_work_cache_content_hash ON work_cache(content_hash);
CREATE INDEX IF NOT EXISTS idx_work_cache_title_normalized_gin ON work_cache USING GIN(to_tsvector('english', title_normalized));
CREATE INDEX IF NOT EXISTS idx_work_cache_author_normalized_gin ON work_cache USING GIN(to_tsvector('english', author_normalized));
CREATE INDEX IF NOT EXISTS idx_work_cache_combined_search ON work_cache(title_normalized, author_normalized, publication_year);
CREATE INDEX IF NOT EXISTS idx_work_cache_source_lookup ON work_cache(source_api, source_id);
CREATE INDEX IF NOT EXISTS idx_work_cache_copyright_status ON work_cache(copyright_status, public_domain_year);

-- Step 7: Add constraints for data quality
-- Make normalized fields not null (after they're populated)
ALTER TABLE work_cache ALTER COLUMN title_normalized SET NOT NULL;
-- Don't make content_hash unique yet - we'll handle duplicates in application code first

-- Step 8: Create trigger to auto-populate normalized fields on insert/update
CREATE OR REPLACE FUNCTION update_normalized_fields()
RETURNS TRIGGER AS $$
BEGIN
    NEW.title_normalized := normalize_title(NEW.title);
    NEW.author_normalized := normalize_author(NEW.author);
    NEW.content_hash := generate_content_hash(NEW.title, NEW.author, NEW.publication_year);
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if it exists and recreate
DROP TRIGGER IF EXISTS trigger_update_normalized_fields ON work_cache;
CREATE TRIGGER trigger_update_normalized_fields
    BEFORE INSERT OR UPDATE ON work_cache
    FOR EACH ROW
    EXECUTE FUNCTION update_normalized_fields();

-- Step 9: Create a view to help identify duplicates (for analysis)
CREATE OR REPLACE VIEW work_cache_duplicates AS
SELECT 
    content_hash,
    COUNT(*) as duplicate_count,
    ARRAY_AGG(id) as record_ids,
    ARRAY_AGG(DISTINCT source_api) as sources,
    MIN(created_at) as first_created,
    MAX(updated_at) as last_updated,
    title_normalized,
    author_normalized,
    publication_year
FROM work_cache 
WHERE content_hash IS NOT NULL
GROUP BY content_hash, title_normalized, author_normalized, publication_year
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- Step 10: Add comments for documentation
COMMENT ON COLUMN work_cache.title_normalized IS 'Normalized title for deduplication and search (lowercase, no punctuation)';
COMMENT ON COLUMN work_cache.author_normalized IS 'Normalized author for deduplication and search (standardized format)';
COMMENT ON COLUMN work_cache.content_hash IS 'SHA256 hash of normalized title + author + year for duplicate detection';
COMMENT ON COLUMN work_cache.public_domain_year IS 'Year work enters public domain (replaces public_domain_date TEXT)';
COMMENT ON COLUMN work_cache.confidence_score IS 'Confidence in data accuracy (0.00 to 1.00)';

-- Step 11: Update the updated_at trigger to handle new fields
CREATE OR REPLACE FUNCTION update_work_cache_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    -- Ensure normalized fields are always updated
    NEW.title_normalized := normalize_title(NEW.title);
    NEW.author_normalized := normalize_author(NEW.author);
    NEW.content_hash := generate_content_hash(NEW.title, NEW.author, NEW.publication_year);
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Replace the existing trigger
DROP TRIGGER IF EXISTS update_work_cache_updated_at ON work_cache;
CREATE TRIGGER update_work_cache_updated_at 
    BEFORE UPDATE ON work_cache 
    FOR EACH ROW 
    EXECUTE FUNCTION update_work_cache_updated_at();

-- Step 12: Show summary of changes
SELECT 
    'Migration Summary' as status,
    COUNT(*) as total_records,
    COUNT(CASE WHEN title_normalized IS NOT NULL THEN 1 END) as records_with_normalized_title,
    COUNT(CASE WHEN content_hash IS NOT NULL THEN 1 END) as records_with_content_hash,
    COUNT(CASE WHEN public_domain_year IS NOT NULL THEN 1 END) as records_with_fixed_pd_year
FROM work_cache;

-- Show any potential duplicates found
SELECT 
    'Potential Duplicates Found' as info,
    COUNT(*) as duplicate_groups,
    SUM(duplicate_count) as total_duplicate_records
FROM work_cache_duplicates;