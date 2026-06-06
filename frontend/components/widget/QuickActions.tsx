import { Button } from "@/components/ui/button";
import { quickActions } from "@/lib/prompts";
import { cn } from "@/lib/utils";

type QuickActionsProps = {
  onSelect: (prompt: string) => void;
  disabled?: boolean;
  activePrompt?: string | null;
};

export function QuickActions({
  onSelect,
  disabled = false,
  activePrompt = null,
}: QuickActionsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {quickActions.map((action) => (
        <Button
          key={action.label}
          type="button"
          variant="outline"
          size="sm"
          disabled={disabled}
          onClick={() => onSelect(action.prompt)}
          className={cn(
            activePrompt === action.prompt &&
              "border-cyan-400 shadow-[0_0_16px_rgba(34,211,238,0.25)]",
          )}
        >
          {action.label}
        </Button>
      ))}
    </div>
  );
}
