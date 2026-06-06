"use client";

import { cn } from "@/lib/utils";

export type CatalogTab = "popular" | "new" | "beginner";

const tabs: { id: CatalogTab; label: string }[] = [
  { id: "popular", label: "Популярные" },
  { id: "new", label: "Новые" },
  { id: "beginner", label: "Для начинающих" },
];

type CatalogTabsProps = {
  active: CatalogTab;
  onChange: (tab: CatalogTab) => void;
};

export function CatalogTabs({ active, onChange }: CatalogTabsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => onChange(tab.id)}
          className={cn(
            "rounded-full border px-4 py-1.5 text-sm transition-colors",
            active === tab.id
              ? "border-cyan-400/60 bg-cyan-500/15 text-cyan-200 shadow-[0_0_16px_rgba(34,211,238,0.2)]"
              : "border-white/10 bg-white/5 text-zinc-400 hover:text-zinc-200",
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
