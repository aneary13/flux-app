-- 1. Scrub 'user_configs' (State Document)
-- We use the JSONB deletion operator (-) to drop the rogue key,
-- and the concatenation operator (||) to merge the correct HIIT level.
UPDATE user_configs
SET
    data = jsonb_set(
        data,
        '{conditioning_levels}',
        (data -> 'conditioning_levels') - 'TRAINING' || '{"HIIT": 2}'::jsonb
    )
WHERE slug = 'state'
-- Safety check: Ensure we only target documents actually affected by the bug
AND data -> 'conditioning_levels' ? 'TRAINING';

-- 2. Scrub 'workout_sets' (Atomic Tracking)
-- We surgically target the specific corrupted set ID you provided and overwrite
-- the nested 'protocol' value using jsonb_set.
UPDATE workout_sets
SET
    metadata = jsonb_set(
        metadata,
        '{protocol}',
        '"HIIT"'::jsonb
    )
WHERE
    id = '3dde3fb7-ecde-466e-a429-c187cafee9b7'
    AND metadata ->> 'protocol' = 'TRAINING';
