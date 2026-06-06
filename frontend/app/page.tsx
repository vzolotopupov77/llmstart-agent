"use client";

import { useState } from "react";

import { FloatingWidgetLayout } from "@/components/layouts/FloatingWidgetLayout";
import { SplitScreenLayout } from "@/components/layouts/SplitScreenLayout";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type LayoutMode = "split" | "floating";

export default function Home() {
  const [mode, setMode] = useState<LayoutMode>("split");

  return (
    <main className="min-h-screen bg-[#0a0f1a] text-zinc-50">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.08),_transparent_45%)]" />

      <div className="relative z-10 border-b border-white/10 bg-zinc-950/60 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-3">
          <p className="text-sm text-zinc-400">LLMStart Agent · Web Widget</p>
          <div className="flex gap-2 rounded-full border border-white/10 bg-white/5 p-1">
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => setMode("split")}
              className={cn(
                mode === "split" && "bg-cyan-500/15 text-cyan-200",
              )}
            >
              Split-screen
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => setMode("floating")}
              className={cn(
                mode === "floating" && "bg-cyan-500/15 text-cyan-200",
              )}
            >
              Floating
            </Button>
          </div>
        </div>
      </div>

      {mode === "split" ? <SplitScreenLayout /> : <FloatingWidgetLayout />}
    </main>
  );
}
