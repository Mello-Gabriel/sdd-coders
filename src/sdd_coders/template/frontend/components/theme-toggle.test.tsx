import { ThemeToggle } from "@/components/theme-toggle";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

const setThemeMock = vi.fn();

vi.mock("next-themes", () => ({
  useTheme: vi.fn(() => ({ theme: "light", setTheme: setThemeMock })),
}));

afterEach(() => {
  vi.clearAllMocks();
});

describe("ThemeToggle", () => {
  it("renders the moon icon in light mode and switches to dark on click", async () => {
    const user = userEvent.setup();
    render(<ThemeToggle />);

    const btn = screen.getByRole("button", { name: /modo escuro/i });
    expect(btn).toBeInTheDocument();

    await user.click(btn);
    expect(setThemeMock).toHaveBeenCalledWith("dark");
  });

  it("renders the sun icon in dark mode and switches to light on click", async () => {
    const { useTheme } = await import("next-themes");
    vi.mocked(useTheme).mockReturnValue({
      theme: "dark",
      setTheme: setThemeMock,
      themes: [],
      systemTheme: undefined,
      resolvedTheme: "dark",
      forcedTheme: undefined,
    });

    const user = userEvent.setup();
    render(<ThemeToggle />);

    const btn = screen.getByRole("button", { name: /modo claro/i });
    await user.click(btn);
    expect(setThemeMock).toHaveBeenCalledWith("light");
  });
});
