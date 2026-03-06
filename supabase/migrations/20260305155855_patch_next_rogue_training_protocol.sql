-- 1. Scrub 'user_configs' (State Document)
-- We use the JSONB deletion operator (-) to drop the rogue key,
-- and the concatenation operator (||) to merge the correct HIIT level.
UPDATE user_configs
SET
    data = jsonb_set(
        data,
        '{conditioning_levels}',
        (data -> 'conditioning_levels') - 'TRAINING' || '{"SIT": 2}'::jsonb
    )
WHERE slug = 'state'

-- Safety check: Ensure we only target documents actually affected by the bug
AND data -> 'conditioning_levels' ? 'TRAINING';

-- 2. Scrub 'workout_sets' (Atomic Tracking)
-- Surgically updates the metadata protocol from "TRAINING" to "SIT" for BOTH sets.
UPDATE workout_sets
SET
    metadata = jsonb_set(
        metadata,
        '{protocol}',
        '"SIT"'::jsonb
    )
WHERE id IN (
    '13a90931-02cd-403e-b2a8-7fa4f86196d4',
    '036aa496-74cf-49d5-9dc8-70bd9ac7575a'
)
AND metadata ->> 'protocol' = 'TRAINING';
