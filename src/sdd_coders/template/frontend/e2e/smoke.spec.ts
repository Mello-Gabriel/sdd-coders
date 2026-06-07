import { expect, test } from "@playwright/test";

test("home shows navigation and the cookie banner", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Bem-vindo" })).toBeVisible();
  await expect(page.getByRole("dialog", { name: "Consentimento de cookies" })).toBeVisible();
});

test("rejecting cookies hides the banner and persists", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Recusar" }).click();
  await expect(page.getByRole("dialog")).toBeHidden();

  await page.reload();
  await expect(page.getByRole("dialog")).toBeHidden();
});
