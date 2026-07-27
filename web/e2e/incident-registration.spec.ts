import { expect, test } from "@playwright/test";

// The registration workflow lives at /incidents/new and is protected: an
// unauthenticated visitor is redirected to login. The end-to-end workflow
// (address → recommendation → confirm → dispatch) requires a live backend and
// session, and is covered by the Vitest integration test.
test("new-incident route is protected", async ({ page }) => {
  await page.goto("/incidents/new");
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole("button", { name: /Войти/ })).toBeVisible();
});
