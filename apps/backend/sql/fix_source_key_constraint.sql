-- Quick fix: Remove the NOT NULL constraint on source_key
-- This allows our new code to work without requiring source_key

-- Step 1: Make source_key optional
ALTER TABLE work_cache ALTER COLUMN source_key DROP NOT NULL;

-- Step 2: Test that the constraint is removed
INSERT INTO work_cache (
    title, 
    author, 
    work_type, 
    source_api, 
    source_id, 
    raw_data, 
    processed_data, 
    expires_at,
    public_domain_year,
    confidence_score
) VALUES (
    'Test Work',
    'Test Author',
    'literary',
    'test_api',
    'test_123',
    '{}',
    '{}',
    NOW() + INTERVAL '7 days',
    2023,
    0.95
);

-- Step 3: Verify the insert worked and check generated fields
SELECT 
    id,
    title,
    title_normalized,
    author,
    author_normalized, 
    content_hash,
    source_key,
    public_domain_year,
    confidence_score
FROM work_cache 
WHERE title = 'Test Work';

-- Step 4: Clean up test record
DELETE FROM work_cache WHERE title = 'Test Work';

-- Summary
SELECT 'source_key constraint fixed - new inserts should work now' as status;