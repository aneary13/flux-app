"use client";

import React from "react";
import type { ExerciseBlock } from "@/lib/api/types";
import type { ExerciseLog, SetLog } from "@/lib/session/session-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

type BlockCardProps = {
  block: ExerciseBlock;
  log: ExerciseLog;
  onLogChange: (log: ExerciseLog) => void;
};

type InputMode =
  | "WEIGHTED_REPS"
  | "WEIGHTED_TIME"
  | "BODYWEIGHT_REPS"
  | "BODYWEIGHT_TIME"
  | "CONDITIONING"
  | "CHECKLIST";

function getMode(block: ExerciseBlock): InputMode {
  if (block.block_type === "CONDITIONING") return "CONDITIONING";
  if (block.block_type === "PREP" && !block.tracking_unit) return "CHECKLIST";
  if (block.block_type === "PREP") return "CHECKLIST";
  const unit = block.tracking_unit ?? "REPS";
  const bw = block.is_bodyweight ?? false;
  if (unit === "WATTS") return "CONDITIONING";
  if (unit === "SECS" && !bw) return "WEIGHTED_TIME";
  if (unit === "SECS" && bw) return "BODYWEIGHT_TIME";
  if (unit === "REPS" && !bw) return "WEIGHTED_REPS";
  if (unit === "REPS" && bw) return "BODYWEIGHT_REPS";
  return "WEIGHTED_REPS";
}

export function BlockCard({ block, log, onLogChange }: BlockCardProps) {
  const mode = getMode(block);
  const rounds = block.rounds ?? 1;

  const updateSets = (sets: SetLog[]) => {
    onLogChange({ ...log, sets });
  };

  const updateSet = (index: number, upd: Partial<SetLog>) => {
    const next = [...log.sets];
    next[index] = { ...next[index], ...upd };
    updateSets(next);
  };

  const addSet = () => {
    updateSets([...log.sets, {}]);
  };

  if (mode === "CHECKLIST") {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">{block.exercise_name}</CardTitle>
        </CardHeader>
        <CardContent>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={log.sets[0]?.reps === 1}
              onChange={(e) =>
                updateSet(0, { reps: e.target.checked ? 1 : undefined })
              }
              className="rounded border-neutral-300"
            />
            <span className="text-sm text-neutral-700">Done</span>
          </label>
        </CardContent>
      </Card>
    );
  }

  if (mode === "CONDITIONING") {
    const rows = Array.from({ length: Math.max(1, rounds) }, (_, i) => i);
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">{block.exercise_name}</CardTitle>
          <p className="text-sm text-neutral-600 font-normal">
            Protocol: {block.exercise_name}
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          {rows.map((i) => (
            <div key={i} className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs text-neutral-500">Avg Watts</label>
                <Input
                  type="number"
                  placeholder="W"
                  value={log.sets[i]?.watts_avg ?? ""}
                  onChange={(e) =>
                    updateSet(i, {
                      watts_avg: e.target.value
                        ? parseInt(e.target.value, 10)
                        : undefined,
                    })
                  }
                />
              </div>
              <div>
                <label className="text-xs text-neutral-500">Distance (m)</label>
                <Input
                  type="number"
                  placeholder="m"
                  value={log.sets[i]?.distance_meters ?? ""}
                  onChange={(e) =>
                    updateSet(i, {
                      distance_meters: e.target.value
                        ? parseFloat(e.target.value)
                        : undefined,
                    })
                  }
                />
              </div>
            </div>
          ))}
          <div>
            <label className="text-xs text-neutral-500">Notes</label>
            <Textarea
              placeholder="Notes..."
              value={log.notes ?? ""}
              onChange={(e) => onLogChange({ ...log, notes: e.target.value })}
              className="mt-1"
            />
          </div>
        </CardContent>
      </Card>
    );
  }

  const repLabel = block.is_unilateral ? "Reps / side" : "Reps";
  const timeLabel = block.is_unilateral ? "Time / side (s)" : "Time (s)";
  const showWeight = mode === "WEIGHTED_REPS" || mode === "WEIGHTED_TIME";
  const showBodyweightPlus =
    mode === "BODYWEIGHT_REPS" || mode === "BODYWEIGHT_TIME";
  const showReps = mode === "WEIGHTED_REPS" || mode === "BODYWEIGHT_REPS";
  const showTime = mode === "WEIGHTED_TIME" || mode === "BODYWEIGHT_TIME";

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">{block.exercise_name}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {log.sets.map((set, i) => (
          <div key={i} className="space-y-2">
            <p className="text-sm font-medium text-neutral-700">Set {i + 1}</p>
            <div className="grid grid-cols-3 gap-2">
              {showWeight && (
                <div>
                  <label className="text-xs text-neutral-500">Weight (kg)</label>
                  <Input
                    type="number"
                    placeholder="kg"
                    value={set.weight_kg ?? ""}
                    onChange={(e) =>
                      updateSet(i, {
                        weight_kg: e.target.value
                          ? parseFloat(e.target.value)
                          : undefined,
                      })
                    }
                  />
                </div>
              )}
              {showBodyweightPlus && (
                <div>
                  <label className="text-xs text-neutral-500">
                    Bodyweight + (kg)
                  </label>
                  <Input
                    type="number"
                    placeholder="kg"
                    value={set.weight_kg ?? ""}
                    onChange={(e) =>
                      updateSet(i, {
                        weight_kg: e.target.value
                          ? parseFloat(e.target.value)
                          : undefined,
                      })
                    }
                  />
                </div>
              )}
              {showReps && (
                <div>
                  <label className="text-xs text-neutral-500">{repLabel}</label>
                  <Input
                    type="number"
                    placeholder="reps"
                    value={set.reps ?? ""}
                    onChange={(e) =>
                      updateSet(i, {
                        reps: e.target.value
                          ? parseInt(e.target.value, 10)
                          : undefined,
                      })
                    }
                  />
                </div>
              )}
              {showTime && (
                <div>
                  <label className="text-xs text-neutral-500">{timeLabel}</label>
                  <Input
                    type="number"
                    placeholder="s"
                    value={set.work_seconds ?? ""}
                    onChange={(e) =>
                      updateSet(i, {
                        work_seconds: e.target.value
                          ? parseInt(e.target.value, 10)
                          : undefined,
                      })
                    }
                  />
                </div>
              )}
              <div>
                <label className="text-xs text-neutral-500">RPE</label>
                <Input
                  type="number"
                  min={1}
                  max={10}
                  placeholder="RPE"
                  value={set.rpe ?? ""}
                  onChange={(e) =>
                    updateSet(i, {
                      rpe: e.target.value
                        ? parseFloat(e.target.value)
                        : undefined,
                    })
                  }
                />
              </div>
            </div>
          </div>
        ))}
        <Button type="button" variant="outline" size="sm" onClick={addSet}>
          + Add Set
        </Button>
        <div>
          <label className="text-xs text-neutral-500">Notes</label>
          <Textarea
            placeholder="Add notes about this exercise..."
            value={log.notes ?? ""}
            onChange={(e) => onLogChange({ ...log, notes: e.target.value })}
            className="mt-1"
          />
        </div>
      </CardContent>
    </Card>
  );
}
