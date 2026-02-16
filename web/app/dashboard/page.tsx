"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/auth-context";
import { useSession } from "@/lib/session/session-context";
import { api } from "@/lib/api/client";
import type { ReadinessLatest, SessionPlan } from "@/lib/api/types";
import { buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const BLOCK_DESCRIPTIONS: Record<string, string> = {
  PREP: "Movement Preparation",
  POWER: "Explosive Movement",
  MAIN: "Primary Lift",
  STRENGTH: "Primary Lift",
  ACCESSORY_1: "Supplemental Work",
  ACCESSORY_2: "Supplemental Work",
  ACCESSORIES: "Supplemental Work",
  CONDITIONING: "Conditioning",
  ISOMETRICS: "Repair Isometrics",
};

function blockDisplayLabel(blockType: string): string {
  if (blockType === "MAIN") return "STRENGTH";
  if (blockType.startsWith("ACCESSORY")) return "ACCESSORIES";
  return blockType;
}

export default function DashboardPage() {
  const { session, loading: authLoading } = useAuth();
  const { startSession } = useSession();
  const router = useRouter();
  const [latest, setLatest] = useState<ReadinessLatest | null>(null);
  const [plan, setPlan] = useState<SessionPlan | null>(null);
  const [loadingLatest, setLoadingLatest] = useState(true);
  const [loadingPlan, setLoadingPlan] = useState(false);
  const [recommendError, setRecommendError] = useState<string | null>(null);

  useEffect(() => {
    if (!session) return;
    api
      .getReadinessLatest()
      .then(setLatest)
      .catch(() => setLatest(null))
      .finally(() => setLoadingLatest(false));
  }, [session]);

  useEffect(() => {
    if (!authLoading && !session) {
      router.replace("/login");
    }
  }, [session, authLoading, router]);

  useEffect(() => {
    if (!latest) return;
    setLoadingPlan(true);
    setRecommendError(null);
    api
      .postRecommend({ knee_pain: latest.knee_pain, energy: latest.energy_level })
      .then(setPlan)
      .catch((e) => setRecommendError(e instanceof Error ? e.message : "Failed to load plan"))
      .finally(() => setLoadingPlan(false));
  }, [latest?.date, latest?.knee_pain, latest?.energy_level]);

  async function handleLetsGo() {
    if (!plan) return;
    setRecommendError(null);
    const readiness =
      latest &&
      (latest.energy_level != null || latest.knee_pain != null)
        ? {
            readinessScore: latest.energy_level,
            computedState: latest.computed_state,
          }
        : undefined;
    startSession(plan, readiness);
    router.push("/session");
    router.refresh();
  }

  if (authLoading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-[#f7f6f3]">
        <p className="text-neutral-600">Loading…</p>
      </main>
    );
  }

  if (!session) return null;

  const state = latest?.computed_state ?? "GREEN";
  const stateLabel =
    state === "GREEN"
      ? "Full intensity training"
      : state === "ORANGE"
        ? "Reduced intensity"
        : "Recovery";

  return (
    <main className="min-h-screen p-6 bg-[#f7f6f3] max-w-lg mx-auto">
      <h1 className="text-2xl font-bold text-neutral-900">Today&apos;s Plan</h1>

      {loadingLatest ? (
        <p className="mt-4 text-neutral-600">Loading readiness…</p>
      ) : (
        <div
          className={cn(
            "mt-4 rounded-2xl p-4 flex items-center gap-3 shadow-sm",
            state === "GREEN" && "bg-[#e8ebe5]",
            state === "ORANGE" && "bg-amber-50",
            state === "RED" && "bg-red-50"
          )}
        >
          <div
            className={cn(
              "w-4 h-4 rounded-full shrink-0",
              state === "GREEN" && "bg-[#8DA887]",
              state === "ORANGE" && "bg-amber-500",
              state === "RED" && "bg-red-500"
            )}
          />
          <span className="text-neutral-800 font-medium">{stateLabel}</span>
        </div>
      )}

      {loadingPlan && latest && (
        <p className="mt-4 text-neutral-600">Loading your plan…</p>
      )}
      {plan && plan.blocks && plan.blocks.length > 0 && (
        <div className="mt-6 space-y-4">
          {plan.blocks.map((block, idx) => (
            <BlockCard key={idx} block={block} index={idx} />
          ))}
        </div>
      )}
      {latest && !loadingPlan && !plan?.blocks?.length && !recommendError && (
        <p className="mt-4 text-neutral-600">Complete a check-in to see your plan.</p>
      )}

      <div className="mt-8">
        <button
          onClick={handleLetsGo}
          disabled={!plan || loadingPlan}
          className={cn(
            "w-full rounded-xl py-3 font-semibold text-white bg-neutral-800 hover:bg-neutral-700 disabled:opacity-50"
          )}
        >
          {loadingPlan ? "Loading…" : "Let's Go"}
        </button>
        {recommendError && (
          <p className="mt-2 text-sm text-red-600">{recommendError}</p>
        )}
      </div>

      <div className="mt-6">
        <Link href="/check-in" className={buttonVariants({ variant: "outline" })}>
          Check In
        </Link>
      </div>
    </main>
  );
}

function BlockCard({
  block,
  index,
}: {
  block: { block_type: string; exercise_name: string };
  index: number;
}) {
  const label = blockDisplayLabel(block.block_type);
  const desc = BLOCK_DESCRIPTIONS[block.block_type] ?? block.block_type;
  return (
    <div className="rounded-2xl bg-white p-4 shadow-sm border border-neutral-200">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-full bg-neutral-800 text-white flex items-center justify-center text-sm font-semibold shrink-0">
          {index + 1}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-lg text-neutral-900">{label}</h3>
          <p className="text-sm text-neutral-600">{desc}</p>
          <div className="flex flex-wrap gap-1.5 mt-2">
            <Badge className="bg-neutral-100 text-neutral-800 font-normal border-0">
              {block.exercise_name}
            </Badge>
          </div>
        </div>
      </div>
    </div>
  );
}
