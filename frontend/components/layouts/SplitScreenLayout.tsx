import { ProductGrid } from "@/components/catalog/ProductGrid";
import { ChatPanel } from "@/components/widget/ChatPanel";

export function SplitScreenLayout() {
  return (
    <div className="relative min-h-screen">
      <div className="mx-auto max-w-7xl px-4 py-8 pb-32 lg:pb-8">
        <ProductGrid />
      </div>

      <div className="pointer-events-none fixed inset-x-0 bottom-0 z-20 flex justify-center p-4 lg:inset-y-0 lg:left-auto lg:right-6 lg:items-center lg:justify-end lg:p-0">
        <div className="pointer-events-auto w-full max-w-md">
          <ChatPanel />
        </div>
      </div>
    </div>
  );
}
