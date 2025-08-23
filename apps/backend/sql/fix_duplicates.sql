-- Fix existing duplicates and improve deduplication

-- Step 1: Show current duplicate situation
SELECT 
    'Current Duplicates' as status,
    content_hash,
    COUNT(*) as duplicate_count,
    MIN(created_at) as first_created,
    MAX(created_at) as last_created,
    ARRAY_AGG(id ORDER BY created_at) as all_ids,
    ARRAY_AGG(source_api ORDER BY created_at) as sources
FROM work_cache 
GROUP BY content_hash
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- Step 2: Create a function to merge duplicate records
CREATE OR REPLACE FUNCTION merge_duplicate_works()
RETURNS INTEGER AS $$
DECLARE
    duplicate_hash TEXT;
    record_ids UUID[];
    keep_id UUID;
    merge_count INTEGER := 0;
BEGIN
    -- Process each group of duplicates
    FOR duplicate_hash, record_ids IN
        SELECT 
            content_hash, 
            ARRAY_AGG(id ORDER BY 
                -- Prefer LOC over MusicBrainz, then by creation time
                CASE WHEN source_api = 'library_of_congress' THEN 1 ELSE 2 END,
                created_at
            )
        FROM work_cache 
        GROUP BY content_hash
        HAVING COUNT(*) > 1
    LOOP
        -- Keep the first record (highest priority)
        keep_id := record_ids[1];
        
        -- Merge processed_data from other records
        UPDATE work_cache 
        SET 
            processed_data = (
                SELECT jsonb_agg(DISTINCT processed_data)
                FROM work_cache 
                WHERE id = ANY(record_ids)
            )[0], -- Take the first one for now, could be more sophisticated
            raw_data = (
                CASE 
                    WHEN source_api = 'library_of_congress' THEN raw_data
                    ELSE (
                        SELECT raw_data 
                        FROM work_cache 
                        WHERE id = ANY(record_ids) AND source_api = 'library_of_congress'
                        LIMIT 1
                    )
                END
            ),
            updated_at = NOW()
        WHERE id = keep_id;
        
        -- Delete the duplicate records (keep only the first one)
        DELETE FROM work_cache 
        WHERE id = ANY(record_ids[2:array_length(record_ids, 1)]);
        
        merge_count := merge_count + array_length(record_ids, 1) - 1;
    END LOOP;
    
    RETURN merge_count;
END;
$$ LANGUAGE plpgsql;

-- Step 3: Run the deduplication
SELECT 
    'Duplicates Merged' as status,
    merge_duplicate_works() as records_removed;

-- Step 4: Add a unique constraint to prevent future duplicates
-- ALTER TABLE work_cache ADD CONSTRAINT unique_content_hash UNIQUE (content_hash);

-- Step 5: Verify the cleanup worked
SELECT 
    'After Cleanup' as status,
    COUNT(*) as total_records,
    COUNT(DISTINCT content_hash) as unique_works,
    COUNT(*) - COUNT(DISTINCT content_hash) as remaining_duplicates
FROM work_cache;

-- Step 6: Show any remaining duplicates (should be 0)
SELECT 
    'Remaining Duplicates' as status,
    content_hash,
    COUNT(*) as duplicate_count
FROM work_cache 
GROUP BY content_hash
HAVING COUNT(*) > 1;