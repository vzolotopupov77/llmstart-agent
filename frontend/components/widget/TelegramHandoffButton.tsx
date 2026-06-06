"use client";

import { Send } from "lucide-react";

import { Button } from "@/components/ui/button";
import { telegramBotUsername } from "@/lib/config";

type TelegramHandoffButtonProps = {
  sessionId: string | null;
};

export function TelegramHandoffButton({
  sessionId,
}: TelegramHandoffButtonProps) {
  const username = telegramBotUsername.trim();
  const hasBot = username.length > 0;
  const hasSession = Boolean(sessionId);
  const href =
    hasBot && hasSession
      ? `https://t.me/${username}?start=s_${sessionId}`
      : undefined;

  return (
    <div className="flex flex-col gap-1">
      <Button
        asChild={Boolean(href)}
        variant="secondary"
        className="w-full"
        disabled={!href}
        title={
          !hasBot
            ? "Бот не настроен (NEXT_PUBLIC_TELEGRAM_BOT_USERNAME)"
            : !hasSession
              ? "Отправьте сообщение, чтобы продолжить в Telegram"
              : undefined
        }
      >
        {href ? (
          <a href={href} target="_blank" rel="noopener noreferrer">
            <Send className="size-4" />
            Продолжить в Telegram
          </a>
        ) : (
          <span className="inline-flex items-center gap-2">
            <Send className="size-4" />
            Продолжить в Telegram
          </span>
        )}
      </Button>
      {!hasSession ? (
        <p className="text-center text-xs text-zinc-500">
          Начните диалог, чтобы получить ссылку с session_id
        </p>
      ) : null}
    </div>
  );
}
