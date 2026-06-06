import { Check, Loader2, X } from "lucide-react";

import type { ToolStep } from "@/lib/types";
import { cn } from "@/lib/utils";

type ToolStepperProps = {
  tools: ToolStep[];
};

export function ToolStepper({ tools }: ToolStepperProps) {
  return (
    <ol className="flex flex-col gap-2">
      {tools.map((tool, index) => (
        <li
          key={`${tool.name}-${index}`}
          className="step-enter flex items-center gap-3 rounded-lg border border-white/5 bg-black/20 px-3 py-2 text-sm"
        >
          <StatusIcon status={tool.status} />
          <span className="text-zinc-300">{tool.title}</span>
        </li>
      ))}
    </ol>
  );
}

function StatusIcon({ status }: { status: ToolStep["status"] }) {
  if (status === "started") {
    return <Loader2 className="size-4 shrink-0 animate-spin text-cyan-400" />;
  }

  if (status === "done") {
    return <Check className="size-4 shrink-0 text-emerald-400" />;
  }

  return <X className={cn("size-4 shrink-0 text-red-400")} />;
}
