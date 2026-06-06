"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { CatalogTabs, type CatalogTab } from "@/components/catalog/CatalogTabs";
import { ProductCard } from "@/components/catalog/ProductCard";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, getProducts } from "@/lib/api";
import type { Product } from "@/lib/types";

const beginnerCodes = new Set(["agents", "ai-agents-combo", "consultation"]);
const newCodes = new Set(["vibe-coding-intensive", "fullstack-aidd"]);

function filterByTab(products: Product[], tab: CatalogTab): Product[] {
  switch (tab) {
    case "beginner":
      return products.filter((product) => beginnerCodes.has(product.code));
    case "new":
      return products.filter((product) => newCodes.has(product.code));
    default:
      return products;
  }
}

export function ProductGrid() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<CatalogTab>("popular");

  const loadProducts = useCallback(async (showLoading = true) => {
    if (showLoading) {
      setLoading(true);
    }
    setError(null);
    try {
      const response = await getProducts();
      setProducts(response.items);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Не удалось загрузить каталог";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const response = await getProducts();
        if (!cancelled) {
          setProducts(response.items);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof ApiError
              ? err.message
              : "Не удалось загрузить каталог";
          setError(message);
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const visibleProducts = useMemo(
    () => filterByTab(products, activeTab),
    [products, activeTab],
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-50">
            Курсы по ИИ
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            Каталог программ LLMStart — выберите курс или спросите консультанта
          </p>
        </div>
        <CatalogTabs active={activeTab} onChange={setActiveTab} />
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <Skeleton key={index} className="h-32 rounded-xl" />
          ))}
        </div>
      ) : null}

      {!loading && error ? (
        <div className="flex flex-col items-center gap-4 rounded-xl border border-red-500/20 bg-red-500/5 p-8 text-center">
          <p className="text-sm text-red-200">{error}</p>
          <Button variant="outline" onClick={() => void loadProducts(true)}>
            Повторить
          </Button>
        </div>
      ) : null}

      {!loading && !error ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {visibleProducts.map((product) => (
            <ProductCard key={product.code} product={product} />
          ))}
        </div>
      ) : null}
    </div>
  );
}
