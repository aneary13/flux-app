import { components } from './api';

// --- 1. Base API Type Extraction ---
export type UserStateResponse = components['schemas']['UserStateResponse'];
export type PatternState = components['schemas']['PatternState'];
export type GeneratedSessionResponse = components['schemas']['GeneratedSessionResponse'];
export type GeneratedBlock = components['schemas']['GeneratedBlock'];
export type GeneratedExercise = components['schemas']['GeneratedExercise'];
export type SessionMetadata = components['schemas']['SessionMetadata'];
export type StartSessionRequest = components['schemas']['StartSessionRequest'];
export type GenerateSessionRequest = components['schemas']['GenerateSessionRequest'];
export type LogSetRequest = components['schemas']['LogSetRequest'];
export type CompleteSessionRequest = components['schemas']['CompleteSessionRequest'];
export type AIResponse = components['schemas']['AIResponse'];

// --- 2. Frontend Strict Literals ---
// We redefine these strictly here because OpenAPI string types often compile down
// to generic `string` rather than specific unions, and our UI needs these for conditional rendering.

export type Archetype = 'PERFORMANCE' | 'RECOVERY';
export type BiologicalState = 'GREEN' | 'ORANGE' | 'RED';
export type MovementPattern = 'SQUAT' | 'HINGE' | 'PUSH' | 'PULL';
export type ConditioningProtocol = 'HIIT' | 'SIT' | 'SS';
export type BlockType = 'PREP' | 'POWER' | 'MAIN' | 'ACCESSORY' | 'CONDITIONING';
export type TrackingUnit = 'REPS' | 'SECS' | 'DISTANCE' | 'WEIGHT' | 'CHECKLIST' | 'WATTS';
export type LoadType = 'BODYWEIGHT' | 'WEIGHTED';

// --- 3. Frontend-Specific Utility Types ---
// For ephemeral local state that doesn't exist on the backend API schema

export interface LoggedSet {
  weight?: number;
  reps?: number;
  seconds?: number;
  completed?: boolean;
  is_warmup?: boolean;
  is_benchmark?: boolean;
  rpe?: number;
  avg_watts?: number;
  peak_watts?: number;
  avg_hr?: number;
  peak_hr?: number;
  metadata?: Record<string, unknown>;
}
