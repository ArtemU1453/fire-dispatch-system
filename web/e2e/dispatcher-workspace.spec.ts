import { expect, test } from "@playwright/test";

// The dispatcher workspace lives at /dashboard and is protected: an
// unauthenticated visitor is sent to the login screen (the workspace itself
// requires a live backend + session and is covered by unit/integration tests).
test("dispatcher workspace route is protected", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByLabel(/Логин/i)).toBeVisible();
});

// The login form is the entry point to the workspace.
test("login screen exposes credentials form", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("button", { name: /Войти/ })).toBeVisible();
});
