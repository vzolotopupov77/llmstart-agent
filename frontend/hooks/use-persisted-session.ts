"use client";

import { useSyncExternalStore } from "react";

import { getSessionId } from "@/lib/session";

function subscribe(onStoreChange: () => void): () => void {
  void onStoreChange;
  return () => {};
}

export function usePersistedSessionId(): string | null {
  return useSyncExternalStore(
    subscribe,
    () => getSessionId(),
    () => null,
  );
}
