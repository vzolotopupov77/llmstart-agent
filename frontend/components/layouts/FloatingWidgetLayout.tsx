"use client";

import { useState } from "react";
import { MessageCircle } from "lucide-react";

import { ProductGrid } from "@/components/catalog/ProductGrid";
import { ChatPanel } from "@/components/widget/ChatPanel";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export function FloatingWidgetLayout() {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative min-h-screen">
      <div className="mx-auto max-w-7xl px-4 py-8">
        <ProductGrid />
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button
            size="icon"
            className="fixed bottom-6 right-6 z-30 size-14 rounded-full shadow-[0_0_32px_rgba(34,211,238,0.35)]"
            aria-label="Открыть чат"
          >
            <MessageCircle className="size-6" />
          </Button>
        </DialogTrigger>
        <DialogContent className="max-h-[90vh] max-w-md overflow-hidden p-0">
          <DialogHeader className="sr-only">
            <DialogTitle>ИИ-Консультант</DialogTitle>
          </DialogHeader>
          <ChatPanel className="max-h-[85vh] border-0 bg-transparent shadow-none" />
        </DialogContent>
      </Dialog>
    </div>
  );
}
