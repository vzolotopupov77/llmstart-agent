import { ExternalLink, Lock } from "lucide-react";

import { Button } from "@/components/ui/button";

type PaymentLinkCardProps = {
  url: string;
};

export function PaymentLinkCard({ url }: PaymentLinkCardProps) {
  return (
    <div className="mt-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3">
      <p className="mb-2 text-xs text-emerald-200">Ссылка на оплату готова</p>
      <Button asChild variant="default" className="w-full bg-emerald-500 hover:bg-emerald-400">
        <a href={url} target="_blank" rel="noopener noreferrer">
          <Lock className="size-4" />
          Перейти к оплате
          <ExternalLink className="size-4" />
        </a>
      </Button>
    </div>
  );
}
