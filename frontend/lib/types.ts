export type Product = {
  code: string;
  title: string;
  price: number;
  currency: string;
};

export type ProductListResponse = {
  items: Product[];
  total: number;
  limit: number;
  offset: number;
};

export type ToolStatus = "started" | "done" | "error";

export type ToolStep = {
  name: string;
  title: string;
  status: ToolStatus;
};

export type MessageThinking = {
  tools: ToolStep[];
  isStreaming: boolean;
  isResponding: boolean;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  products?: Product[];
  paymentLink?: string;
  thinking?: MessageThinking;
};

export type ChatStreamEvent =
  | { event: "reasoning"; data: { text: string } }
  | {
      event: "tool";
      data: { name: string; status: ToolStatus; title: string };
    }
  | { event: "products"; data: { items: Product[] } }
  | { event: "message"; data: { delta: string } }
  | { event: "payment_link"; data: { url: string } }
  | { event: "done"; data: { session_id: string; message: string } }
  | { event: "error"; data: { detail: string } };
