-- Remap all logged sets from "Assault Bike" to "Rowing Machine"
-- Prerequisite: start the backend first so system_init.py seeds "Rowing Machine" into exercises
UPDATE workout_sets
SET exercise_name = 'Rowing Machine'
WHERE exercise_name = 'Assault Bike';
