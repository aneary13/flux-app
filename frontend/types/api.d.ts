// --- 1. Global Enums & Literals ---
export type Archetype = 'PERFORMANCE' | 'RECOVERY'; 
export type BiologicalState = 'GREEN' | 'ORANGE' | 'RED';
export type MovementPattern = 'SQUAT' | 'HINGE' | 'PUSH' | 'PULL'; 
export type ConditioningProtocol = 'HIIT' | 'SIT' | 'SS'; 
export type BlockType = 'PREP' | 'POWER' | 'MAIN' | 'ACCESSORY' | 'CONDITIONING'; 

// Updated based on your live JSON payload
export type TrackingUnit = 'REPS' | 'SECS' | 'DISTANCE' | 'WEIGHT' | 'CHECKLIST' | 'WATTS'; 
export type LoadType = 'BODYWEIGHT' | 'WEIGHTED';

// --- 2. User State Management ---
export interface UserState {
  pattern_debts: Record<MovementPattern, number>; 
  conditioning_levels: Record<ConditioningProtocol, number>; 
}

// --- 3. Exercise & Block Architecture ---
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

// --- 4. Session Generation Payloads ---
export interface GenerateSessionRequest {
  knee_pain: number; 
  energy: number; 
  pattern_debts: Record<MovementPattern, number>; 
  conditioning_levels: Record<ConditioningProtocol, number>; 
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

// --- 5. Session Execution Payloads ---
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
