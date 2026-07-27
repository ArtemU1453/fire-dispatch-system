import { expect, test } from "@playwright/test";

// Unauthenticated users are redirected to the login screen.
test("redirects to login and shows the form", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole("button", { name: /Войти/ })).toBeVisible();
});
