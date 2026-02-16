"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/auth-context";
import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";

export default function CheckInPage() {
  const [kneePain, setKneePain] = useState(0);
  const [energy, setEnergy] = useState(5);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { session, loading: authLoading } = useAuth();
  const router = useRouter();

  if (authLoading) {
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

  async function handleBuildSession() {
    setError(null);
    setLoading(true);
    try {
      await api.postReadinessCheckIn({ knee_pain: kneePain, energy });
      router.push("/dashboard");
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to submit check-in");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen p-6 bg-[#f7f6f3]">
      <div className="max-w-lg mx-auto">
        <Link href="/dashboard" className="inline-flex items-center text-neutral-600 hover:text-neutral-900 mb-4">
          ← Back
        </Link>
        <h1 className="text-3xl font-bold text-neutral-900 mb-8">Check In</h1>

        <Card className="mb-6">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-lg">Knee Pain</CardTitle>
            <span className="text-2xl font-bold text-neutral-900">{kneePain}</span>
          </CardHeader>
          <CardContent>
            <Slider value={kneePain} onChange={setKneePain} min={0} max={10} />
            <div className="flex justify-between text-xs text-neutral-500 mt-1">
              <span>None</span>
              <span>Severe</span>
            </div>
          </CardContent>
        </Card>

        <Card className="mb-6">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-lg">Energy Level</CardTitle>
            <span className="text-2xl font-bold text-neutral-900">{energy}</span>
          </CardHeader>
          <CardContent>
            <Slider value={energy} onChange={setEnergy} min={0} max={10} />
            <div className="flex justify-between text-xs text-neutral-500 mt-1">
              <span>Exhausted</span>
              <span>Peak</span>
            </div>
          </CardContent>
        </Card>

        <div className="rounded-xl bg-neutral-100 p-4 mb-6">
          <p className="text-sm text-neutral-800">
            This data is used to tailor today&apos;s session to your current state.
          </p>
        </div>

        {error && (
          <p className="text-sm text-red-600 mb-4">{error}</p>
        )}

        <Button
          className="w-full"
          size="lg"
          onClick={handleBuildSession}
          disabled={loading}
        >
          {loading ? "Submitting…" : "Build Session"}
        </Button>
      </div>
    </main>
  );
}
