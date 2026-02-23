-- ==========================================
-- 1. EXERCISES TABLE (Relational Catalog)
-- ==========================================
CREATE TABLE exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    is_unilateral BOOLEAN NOT NULL DEFAULT FALSE,
    load_type TEXT NOT NULL,       -- e.g., 'WEIGHTED', 'BODYWEIGHT'
    tracking_unit TEXT NOT NULL,   -- e.g., 'REPS', 'SECS', 'CHECKLIST'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- 2. USER CONFIGS TABLE (The Dynamic Brain)
-- ==========================================
CREATE TABLE user_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,         -- We will use a dummy UUID string in Phase 2
    slug TEXT NOT NULL,            -- e.g., 'logic', 'sessions', 'selections', 'conditioning'
    data JSONB NOT NULL,           -- The actual configuration rules
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, slug)          -- Ensures one type of config per user
);

-- ==========================================
-- 3. WORKOUT SESSIONS TABLE (Session Metadata)
-- ==========================================
CREATE TABLE workout_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    archetype TEXT NOT NULL,       -- 'PERFORMANCE' or 'RECOVERY'
    readiness JSONB NOT NULL,      -- e.g., {"pain": 2, "energy": 8}
    exercise_notes JSONB DEFAULT '{}'::jsonb, -- e.g., {"Back Squat": "Felt heavy"}
    summary_notes TEXT,
    status TEXT DEFAULT 'IN_PROGRESS', -- 'IN_PROGRESS' or 'COMPLETED'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- ==========================================
-- 4. WORKOUT SETS TABLE (Atomic Tracking)
-- ==========================================
CREATE TABLE workout_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    exercise_name TEXT NOT NULL REFERENCES exercises(name) ON DELETE CASCADE,
    weight DECIMAL,
    reps INTEGER,
    seconds INTEGER,
    is_warmup BOOLEAN DEFAULT FALSE,
    is_benchmark BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- 5. PERFORMANCE INDEXES
-- ==========================================
CREATE INDEX idx_workout_sets_session_id ON workout_sets(session_id);
CREATE INDEX idx_workout_sets_exercise_name ON workout_sets(exercise_name);
CREATE INDEX idx_user_configs_user_id ON user_configs(user_id);
