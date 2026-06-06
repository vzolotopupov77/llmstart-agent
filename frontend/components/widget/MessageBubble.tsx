import type { ChatMessage } from "@/lib/types";

import { PaymentLinkCard } from "@/components/widget/PaymentLinkCard";
import { ProductCardsInline } from "@/components/widget/ProductCardsInline";
import { ThinkingBlock } from "@/components/widget/ThinkingBlock";

type MessageBubbleProps = {
  message: ChatMessage;
};

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[90%] rounded-2xl bg-cyan-500/20 px-4 py-3 text-sm leading-relaxed text-cyan-50 shadow-[0_0_20px_rgba(34,211,238,0.12)]">
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="flex w-full max-w-[90%] flex-col gap-3">
        {message.thinking ? (
          <ThinkingBlock thinking={message.thinking} />
        ) : null}

        {message.content ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm leading-relaxed text-zinc-100">
            <p className="whitespace-pre-wrap">{message.content}</p>

            {message.products && message.products.length > 0 ? (
              <ProductCardsInline products={message.products} />
            ) : null}

            {message.paymentLink ? (
              <PaymentLinkCard url={message.paymentLink} />
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
