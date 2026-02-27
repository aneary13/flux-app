// --- Global Enums & Literals ---
export type Archetype = 'PERFORMANCE' | 'RECOVERY';
export type BiologicalState = 'GREEN' | 'ORANGE' | 'RED';
export type MovementPattern = 'SQUAT' | 'HINGE' | 'PUSH' | 'PULL';
export type ConditioningProtocol = 'HIIT' | 'SIT' | 'SS';
export type BlockType = 'PREP' | 'POWER' | 'MAIN' | 'ACCESSORY' | 'CONDITIONING';

export type TrackingUnit = 'REPS' | 'SECS' | 'DISTANCE' | 'WEIGHT' | 'CHECKLIST' | 'WATTS';
export type LoadType = 'BODYWEIGHT' | 'WEIGHTED';

// --- Pattern Readiness View Model ---
export interface PatternReadiness {
  last_trained_datetime: string | null;
  days_since: number | null;
  status_text: 'Fully Primed' | 'Recovering' | 'Fatigued';
}

// --- User State Management ---
export interface UserState {
  patterns: Record<MovementPattern, PatternReadiness>; 
  conditioning_levels: Partial<Record<ConditioningProtocol, number>>; 
}

// --- Exercise & Block Architecture ---
export interface Exercise {
  id?: string; // Optional fallback for React keys
  name: string;
  is_unilateral: boolean; 
  tracking_unit: TrackingUnit;
  load_type: LoadType;
  
  // Conditioning-Specific Fields
  is_conditioning?: boolean;
  description?: string;
  rounds?: number;
  work_seconds?: number;
  rest_seconds?: number;
  is_benchmark?: boolean;
  target_intensity?: string | number;
}

export interface SessionBlock {
  id?: string;
  type: BlockType;
  label: string; // The backend uses "label" instead of "name" for the block
  exercises: Exercise[];
}

// --- Session Generation Payloads ---
export interface GenerateSessionRequest {
  knee_pain: number;
  energy: number;
  last_trained: Record<MovementPattern, string | null>;
  conditioning_levels: Partial<Record<ConditioningProtocol, number>>;
}

export interface SessionMetadata {
  session_id?: string;
  archetype: Archetype; 
  state: BiologicalState;
  anchor_pattern: MovementPattern; 
}

export interface GeneratedSessionResponse {
  metadata: SessionMetadata; 
  blocks: SessionBlock[]; 
}

// --- Session Execution Payloads ---
export interface StartSessionRequest {
  readiness: {
    knee_pain: number; 
    energy: number; 
  };
}

export interface CompleteSessionRequest {
  anchor_pattern: MovementPattern; 
  completed_conditioning_protocol?: ConditioningProtocol; 
  exercise_notes: Record<string, string>; // Maps exercise names/IDs to user notes
  summary_notes: string; 
}
