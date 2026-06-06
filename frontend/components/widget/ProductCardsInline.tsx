import { ProductCard } from "@/components/catalog/ProductCard";
import type { Product } from "@/lib/types";

type ProductCardsInlineProps = {
  products: Product[];
};

export function ProductCardsInline({ products }: ProductCardsInlineProps) {
  return (
    <div className="mt-3 flex flex-col gap-2">
      {products.map((product) => (
        <ProductCard key={product.code} product={product} compact />
      ))}
    </div>
  );
}
