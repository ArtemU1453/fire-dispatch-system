import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Button } from "@/components/ui/button";

describe("Button", () => {
  it("renders its label and reacts to clicks", async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Войти</Button>);
    const btn = screen.getByRole("button", { name: "Войти" });
    expect(btn).toBeInTheDocument();
    await userEvent.click(btn);
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("applies the destructive variant classes", () => {
    render(<Button variant="destructive">X</Button>);
    expect(screen.getByRole("button")).toHaveClass("bg-destructive");
  });
});
