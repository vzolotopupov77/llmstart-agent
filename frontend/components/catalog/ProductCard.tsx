import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatPrice } from "@/lib/format";
import type { Product } from "@/lib/types";

type ProductCardProps = {
  product: Product;
  compact?: boolean;
};

export function ProductCard({ product, compact = false }: ProductCardProps) {
  return (
    <Card
      className={
        compact
          ? "border-cyan-500/20 bg-cyan-500/5"
          : "transition-colors hover:border-cyan-500/30 hover:bg-white/[0.07]"
      }
    >
      <CardHeader className={compact ? "p-3" : undefined}>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className={compact ? "text-sm" : "text-base"}>
            {product.title}
          </CardTitle>
          <Badge variant="secondary">{product.code}</Badge>
        </div>
      </CardHeader>
      <CardContent className={compact ? "p-3 pt-0" : undefined}>
        <p className="text-lg font-semibold text-cyan-300">
          {formatPrice(product.price, product.currency)}
        </p>
      </CardContent>
    </Card>
  );
}
