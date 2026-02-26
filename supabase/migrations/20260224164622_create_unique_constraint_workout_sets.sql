ALTER TABLE workout_sets 
ADD CONSTRAINT unique_set_per_session 
UNIQUE (session_id, exercise_name, set_index);
