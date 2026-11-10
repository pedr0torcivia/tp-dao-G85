import { test, expect } from "@playwright/test";

const username = process.env.E2E_USERNAME || "biblioteca";
const password = process.env.E2E_PASSWORD || "demo";

test("protege rutas, rechaza clave incorrecta, restaura sesión y la cierra", async ({
  page,
}) => {
  await page.goto("/catalogo");
  await expect(page).toHaveURL(/\/acceso$/);
  const anonymous = await page.request.get("/api/libros/");
  expect(anonymous.status()).toBe(403);
  await page.getByLabel("Usuario", { exact: true }).fill(username);
  await page.getByLabel("Contraseña", { exact: true }).fill("incorrecta");
  await page.getByRole("button", { name: "Ingresar", exact: true }).click();
  await expect(
    page.getByText("Usuario o contraseña incorrectos.", { exact: true }),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/acceso$/);
  await page.getByLabel("Contraseña", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Ingresar", exact: true }).click();
  await expect(page).toHaveURL(/\/catalogo$/);
  await expect(page.getByRole("button", { name: "Menú de usuario" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("button", { name: "Menú de usuario" })).toBeVisible();
  expect((await page.request.get("/api/libros/")).status()).toBe(200);
  await page.getByRole("button", { name: "Menú de usuario" }).click();
  await page.getByRole("menuitem", { name: "Cerrar sesión" }).click();
  await expect(page).toHaveURL(/\/acceso$/);
  expect((await page.request.get("/api/libros/")).status()).toBe(403);
  await page.goto("/inicio");
  await expect(page).toHaveURL(/\/acceso$/);
});

test("una sesión vencida vuelve al acceso sin mostrar datos anteriores", async ({
  page,
}) => {
  await page.goto("/acceso");
  await page.getByLabel("Usuario", { exact: true }).fill(username);
  await page.getByLabel("Contraseña", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Ingresar", exact: true }).click();
  await expect(page).toHaveURL(/\/inicio$/);
  await page.context().clearCookies();
  await page.getByRole("link", { name: "Informes", exact: true }).click();
  // Informes ya consulta la API al abrirse: según quién llegue primero, la
  // sesión vencida redirige antes o después de elegir un reporte.
  await page
    .getByRole("link", { name: /Préstamos vencidos/ })
    .click({ timeout: 3_000 })
    .catch(() => undefined);
  await expect(page).toHaveURL(/\/acceso$/);
  await expect(
    page.getByRole("heading", { name: "Ingresá a tu biblioteca" }),
  ).toBeVisible();
});
