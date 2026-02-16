"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/auth-context";
import { useSession } from "@/lib/session/session-context";
import { api } from "@/lib/api/client";
import { BlockCard } from "@/components/session/BlockCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

function blockDisplayLabel(blockType: string): string {
  if (blockType === "MAIN") return "STRENGTH";
  if (blockType.startsWith("ACCESSORY")) return "ACCESSORIES";
  return blockType;
}

export default function SessionPage() {
  const { session, loading: authLoading } = useAuth();
  const { plan, logs, startedAt, updateLog, buildWorkoutPayload, clearSession, setLastCompletedSummary } = useSession();
  const [page, setPage] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !session) {
      router.replace("/login");
    }
  }, [session, authLoading, router]);

  useEffect(() => {
    if (!authLoading && session && !plan) {
      router.replace("/dashboard");
    }
  }, [plan, authLoading, session, router]);

  if (authLoading || !session || !plan) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-[#f7f6f3]">
        <p className="text-neutral-600">Loading…</p>
      </main>
    );
  }

  const blocks = plan.blocks;
  const total = blocks.length;
  const currentBlock = blocks[page];
  const currentLog = logs[page];
  const isLast = page === total - 1;

  async function handleComplete() {
    setError(null);
    setSubmitting(true);
    try {
      const payload = buildWorkoutPayload();
      await api.postWorkouts(payload);
      const completedAt = new Date();
      const start = startedAt ?? completedAt;
      const totalTimeMinutes = Math.max(
        1,
        Math.round((completedAt.getTime() - start.getTime()) / 60000)
      );
      let totalSets = 0;
      const blocks = plan.blocks.map((block, i) => {
        const count = logs[i]?.sets?.length ?? 0;
        totalSets += count;
        return {
          blockType: block.block_type,
          exerciseName: block.exercise_name,
          setsCount: count,
        };
      });
      setLastCompletedSummary({
        blocks,
        totalSets,
        totalExercises: plan.blocks.length,
        totalTimeMinutes: totalTimeMinutes || 1,
      });
      clearSession();
      router.push("/session/complete");
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save session");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen flex flex-col bg-[#f7f6f3] pb-24">
      <header className="sticky top-0 z-10 flex items-center justify-between p-4 bg-[#f7f6f3] border-b border-neutral-200">
        <Link href="/dashboard" className="text-neutral-600 hover:text-neutral-900">
          ← Back
        </Link>
        <div className="flex items-center gap-2">
          <Badge className="bg-neutral-800 text-white">
            {blockDisplayLabel(currentBlock.block_type)}
          </Badge>
          <span className="text-sm text-neutral-600">
            {page + 1}/{total}
          </span>
        </div>
      </header>

      <div className="flex-1 p-4 overflow-auto">
        {currentLog && (
          <BlockCard
            block={currentBlock}
            log={currentLog}
            onLogChange={(log) => updateLog(page, log)}
          />
        )}
      </div>

      {error && (
        <p className="px-4 py-2 text-sm text-red-600">{error}</p>
      )}

      <footer className="fixed bottom-0 left-0 right-0 flex items-center justify-between p-4 bg-[#f7f6f3] border-t border-neutral-200">
        <Button
          variant="outline"
          onClick={() => setPage((p) => Math.max(0, p - 1))}
          disabled={page === 0}
        >
          ← Previous
        </Button>
        {isLast ? (
          <Button
            onClick={handleComplete}
            disabled={submitting}
          >
            {submitting ? "Saving…" : "Complete Session"}
          </Button>
        ) : (
          <Button onClick={() => setPage((p) => p + 1)}>
            Next Block →
          </Button>
        )}
      </footer>
    </main>
  );
}
