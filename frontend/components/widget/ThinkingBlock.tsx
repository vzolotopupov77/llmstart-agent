import { ToolStepper } from "@/components/widget/ToolStepper";
import type { MessageThinking, ToolStep } from "@/lib/types";

type ThinkingBlockProps = {
  thinking: MessageThinking;
};

function buildThinkingSteps(thinking: MessageThinking): ToolStep[] {
  const steps: ToolStep[] = [];
  const hasTools = thinking.tools.length > 0;
  const analysisDone =
    !thinking.isStreaming || hasTools || thinking.isResponding;

  steps.push({
    name: "_analyze",
    title: "Анализ запроса пользователя",
    status: analysisDone ? "done" : "started",
  });

  steps.push(...thinking.tools);

  steps.push({
    name: "_recommend",
    title: hasTools ? "Формирование рекомендации" : "Формирование ответа",
    status: thinking.isStreaming ? "started" : "done",
  });

  return steps;
}

export function ThinkingBlock({ thinking }: ThinkingBlockProps) {
  const steps = buildThinkingSteps(thinking);

  return (
    <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-3">
      <p className="mb-2 text-xs font-medium uppercase tracking-wider text-cyan-300">
        Думает вслух
      </p>
      <ToolStepper tools={steps} />
    </div>
  );
}
