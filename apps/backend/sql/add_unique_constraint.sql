-- Add unique constraint on content_hash to prevent future duplicates
-- Run this AFTER running fix_duplicates.sql

-- Step 1: Verify no duplicates remain
SELECT 
    'Pre-constraint Check' as status,
    COUNT(*) as total_records,
    COUNT(DISTINCT content_hash) as unique_hashes,
    COUNT(*) - COUNT(DISTINCT content_hash) as duplicates
FROM work_cache;

-- Step 2: Add the unique constraint (this will fail if duplicates still exist)
ALTER TABLE work_cache ADD CONSTRAINT unique_content_hash UNIQUE (content_hash);

-- Step 3: Verify constraint was added
SELECT 
    'Constraint Added' as status,
    constraint_name,
    constraint_type
FROM information_schema.table_constraints 
WHERE table_name = 'work_cache' 
    AND constraint_name = 'unique_content_hash';

-- Step 4: Test that duplicates are now prevented
-- This should fail with a constraint violation
-- INSERT INTO work_cache (title, author, work_type, source_api, source_id, raw_data, processed_data, expires_at)
-- VALUES ('Test Duplicate', 'Test Author', 'literary', 'test', 'test1', '{}', '{}', NOW() + INTERVAL '7 days');

SELECT 'Unique constraint successfully added - duplicates will now be prevented' as result;