-- Add anchor_pattern column to track which movement pattern each session was built around.
ALTER TABLE workout_sessions ADD COLUMN anchor_pattern TEXT;

-- Backfill historical sessions by inspecting which main-pattern exercise was logged
-- in workout_sets. Each completed session contains exactly one of these four main
-- movements, which unambiguously identifies the anchor pattern.
UPDATE workout_sessions ws
SET
    anchor_pattern = (
        SELECT
            CASE
                WHEN wset.exercise_name IN ('Back Squat', 'Box Squat (Vertical Shin)') THEN 'SQUAT'
                WHEN wset.exercise_name IN ('BB RDL') THEN 'HINGE'
                WHEN wset.exercise_name IN ('BB Bench Press') THEN 'PUSH'
                WHEN wset.exercise_name IN ('Chin Up') THEN 'PULL'
            END
        FROM workout_sets AS wset
        WHERE
            wset.session_id = ws.id
            AND wset.exercise_name IN (
                'Back Squat', 'Box Squat (Vertical Shin)',
                'BB RDL',
                'BB Bench Press',
                'Chin Up'
            )
        ORDER BY wset.created_at DESC
        LIMIT 1
    )
WHERE ws.status = 'COMPLETED';
