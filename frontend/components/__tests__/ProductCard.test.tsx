import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProductCard } from "@/components/catalog/ProductCard";
import { formatPrice } from "@/lib/format";

describe("ProductCard", () => {
  it("renders title and formatted price", () => {
    render(
      <ProductCard
        product={{
          code: "agents",
          title: "Базовый курс по ИИ-агентам",
          price: 3_990_000,
          currency: "RUB",
        }}
      />,
    );

    expect(screen.getByText("Базовый курс по ИИ-агентам")).toBeInTheDocument();
    expect(
      screen.getByText(formatPrice(3_990_000, "RUB")),
    ).toBeInTheDocument();
    expect(screen.getByText("agents")).toBeInTheDocument();
  });
});
