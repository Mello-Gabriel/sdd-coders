"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

/** Light / dark mode toggle. Renders nothing during SSR to avoid hydration mismatch. */
export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  const isDark = theme === "dark";

  return (
    <button
      type="button"
      aria-label={isDark ? "Mudar para modo claro" : "Mudar para modo escuro"}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
    >
      {isDark ? "☀️" : "🌙"}
    </button>
  );
}
