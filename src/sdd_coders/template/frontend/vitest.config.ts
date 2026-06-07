import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": fileURLToPath(new URL(".", import.meta.url)) },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      // The unit-coverage gate covers logic and components. Next.js route files
      // (app/**) are exercised end-to-end by Playwright, not unit tests.
      include: ["lib/**", "components/**"],
      exclude: ["**/*.test.{ts,tsx}", "**/*.d.ts", "lib/api/types.ts"],
      thresholds: { statements: 100, branches: 100, functions: 100, lines: 100 },
    },
  },
});
