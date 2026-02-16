"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/auth-context";
import { useSession } from "@/lib/session/session-context";
import { buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

function blockDisplayLabel(blockType: string): string {
  if (blockType === "MAIN") return "STRENGTH";
  if (blockType.startsWith("ACCESSORY")) return "ACCESSORIES";
  return blockType;
}

function CheckIcon({ className = "w-4 h-4 text-white" }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M5 13l4 4L19 7"
      />
    </svg>
  );
}

export default function SessionCompletePage() {
  const { session, loading } = useAuth();
  const { lastCompletedSummary } = useSession();
  const router = useRouter();

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-[#f7f6f3]">
        <p className="text-neutral-600">Loading…</p>
      </main>
    );
  }

  if (!session) {
    router.replace("/login");
    return null;
  }

  const summary = lastCompletedSummary ?? {
    blocks: [],
    totalSets: 0,
    totalExercises: 0,
    totalTimeMinutes: 0,
  };

  const blocksByType = summary.blocks.reduce(
    (acc, b) => {
      const type = blockDisplayLabel(b.blockType);
      if (!acc[type]) acc[type] = [];
      acc[type].push({ name: b.exerciseName, setsCount: b.setsCount });
      return acc;
    },
    {} as Record<string, { name: string; setsCount: number }[]>
  );

  return (
    <main className="min-h-screen p-6 bg-[#f7f6f3] max-w-lg mx-auto">
      <div className="flex flex-col items-center mb-8">
        <div className="w-14 h-14 rounded-full bg-[#8DA887] flex items-center justify-center mb-4">
          <CheckIcon className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-2xl font-bold text-neutral-900">Session Complete</h1>
      </div>

      <div className="space-y-4 mb-8">
        {Object.entries(blocksByType).map(([type, exercises]) => (
          <div
            key={type}
            className="rounded-2xl bg-white p-4 shadow-sm border border-neutral-200"
          >
            <div className="flex items-center justify-between mb-2">
              <Badge className="bg-neutral-800 text-white">{type}</Badge>
              <div className="w-6 h-6 rounded-full bg-[#8DA887] flex items-center justify-center">
                <CheckIcon />
              </div>
            </div>
            <ul className="text-sm text-neutral-800 space-y-0.5">
              {exercises.map((ex, i) => (
                <li key={i}>
                  {ex.name}
                  <span className="text-neutral-500 ml-1">
                    {ex.setsCount} set{ex.setsCount !== 1 ? "s" : ""}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="rounded-2xl bg-neutral-100 p-4 mb-8">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-neutral-900">
              {summary.totalTimeMinutes}m
            </p>
            <p className="text-sm text-neutral-600">Total Time</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-neutral-900">
              {summary.totalSets}
            </p>
            <p className="text-sm text-neutral-600">Total Sets</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-neutral-900">
              {summary.totalExercises}
            </p>
            <p className="text-sm text-neutral-600">Exercises</p>
          </div>
        </div>
      </div>

      <Link
        href="/dashboard"
        className={cn(
          "block w-full text-center rounded-xl py-3 font-semibold text-white bg-neutral-800 hover:bg-neutral-700",
          buttonVariants()
        )}
      >
        Back to Home
      </Link>
    </main>
  );
}
