-- Clean up unused/redundant columns from work_cache table
-- These columns are always NULL and serve no purpose

-- Step 1: Remove the redundant columns
ALTER TABLE work_cache DROP COLUMN IF EXISTS source_key;
ALTER TABLE work_cache DROP COLUMN IF EXISTS public_domain_date;

-- Step 2: Keep work_subtype for now (we might use it later for "novel", "song", etc.)
-- ALTER TABLE work_cache DROP COLUMN IF EXISTS work_subtype;  -- Commented out - might be useful later

-- Step 3: Verify the cleanup worked
SELECT 
    'Cleanup completed' as status,
    COUNT(*) as total_records
FROM work_cache;

-- Step 4: Show the cleaned schema (remaining columns)
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'work_cache' 
    AND table_schema = 'public'
ORDER BY ordinal_position;