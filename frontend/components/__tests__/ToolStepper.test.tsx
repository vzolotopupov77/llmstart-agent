import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ToolStepper } from "@/components/widget/ToolStepper";

describe("ToolStepper", () => {
  it("renders tool titles", () => {
    render(
      <ToolStepper
        tools={[
          {
            name: "search_knowledge_base",
            title: "Поиск в базе знаний",
            status: "done",
          },
        ]}
      />,
    );

    expect(screen.getByText("Поиск в базе знаний")).toBeInTheDocument();
  });

  it("renders empty list when tools are empty", () => {
    const { container } = render(<ToolStepper tools={[]} />);
    expect(container.querySelector("ol")).toBeInTheDocument();
    expect(container.querySelectorAll("li")).toHaveLength(0);
  });
});
