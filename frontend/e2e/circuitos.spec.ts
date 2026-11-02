import {
  test as base,
  expect,
  type Page,
  type APIRequestContext,
} from "@playwright/test";

const api = process.env.E2E_API_URL || "http://127.0.0.1:8000/api";
// Las preparaciones y verificaciones usan la misma sesión real del navegador.
const test = base.extend({
  request: async ({ page }, use) => {
    await use(page.request);
  },
});
async function post(request: APIRequestContext, path: string, data: object) {
  const sesion = await (await request.get(`${api}/auth/sesion/`)).json();
  const res = await request.post(`${api}/${path}/`, {
    data,
    headers: { "X-CSRFToken": sesion.csrfToken },
  });
  expect(res.ok(), await res.text()).toBeTruthy();
  return res.json();
}
test.beforeEach(async ({ page }) => {
  const username = process.env.E2E_USERNAME || "biblioteca";
  const password = process.env.E2E_PASSWORD || "demo";
  await page.goto("/acceso");
  await page.getByLabel("Usuario", { exact: true }).fill(username);
  await page.getByLabel("Contraseña", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Ingresar", exact: true }).click();
  await expect(page).toHaveURL(/\/inicio$/);
});
async function datos(request: APIRequestContext) {
  const code = `${Date.now()}-${Math.random().toString(16).slice(2, 7)}`;
  const sede = async (name: string) =>
    post(request, "sedes", {
      nombre: `${name} ${code}`,
      direccion: "Calle 85",
      contacto: "test@example.test",
      horarios: "8 a 18",
    });
  const origen = await sede("Prueba Central"),
    destino = await sede("Prueba Norte");
  const socio = await post(request, "socios", {
    numero_socio: code,
    documento: code,
    nombre: "Lector de prueba",
    contacto: "lector@example.test",
  });
  const libro = await post(request, "libros", {
    titulo: `Libro ${code}`,
    autor: "Autor de prueba",
    editorial: "Editorial",
    edicion: "1",
  });
  const ejemplar = await post(request, "ejemplares", {
    codigo_inventario: code,
    libro_id: libro.id,
    sede_propietaria_id: origen.id,
    condicion_fisica: "APTO",
  });
  return { origen, destino, socio, libro, ejemplar };
}
async function comando(page: Page, label: string, fill?: () => Promise<void>) {
  await page.getByRole("button", { name: label, exact: true }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  if (fill) await fill();
  await dialog.getByRole("button", { name: "Confirmar", exact: true }).click();
  await expect(dialog).not.toBeVisible();
}
async function entrega(page: Page) {
  await comando(page, "Registrar entrega", async () => {
    await page
      .getByLabel("Fecha de entrega", { exact: true })
      .fill("2026-11-01T12:00");
    await page
      .getByLabel("Fecha de vencimiento", { exact: true })
      .fill("2026-11-15T12:00");
  });
}
async function devolver(
  page: Page,
  request: APIRequestContext,
  solicitudId: number,
) {
  const response = await request.get(`${api}/prestamos/`);
  let data = await response.json();
  const rows = Array.isArray(data) ? data : data.results;
  let prestamo = rows.find(
    (p: { solicitud_id: number }) => p.solicitud_id === solicitudId,
  );
  while (!prestamo && data.next) {
    data = await (await request.get(data.next)).json();
    prestamo = data.results.find(
      (p: { solicitud_id: number }) => p.solicitud_id === solicitudId,
    );
  }
  expect(prestamo).toBeTruthy();
  await page.goto(`/prestamos/${prestamo.id}`);
  await comando(page, "Registrar devolución", async () => {
    await page
      .getByLabel("Fecha de devolución", { exact: true })
      .fill("2026-11-02T12:00");
  });
}
async function remito(page: Page, ejemplarId: number) {
  await page
    .getByLabel("Número de remito", { exact: true })
    .fill(`ENV-${Date.now()}`);
  await page
    .getByRole("button", { name: "Guardar preparación", exact: true })
    .click();
  await expect(page).toHaveURL(/\/remitos\/\d+$/);
  await comando(page, "Agregar ejemplar", async () => {
    await page
      .getByLabel("Ejemplar disponible", { exact: true })
      .selectOption(String(ejemplarId));
  });
  for (const label of ["Empaquetar", "Despachar", "Registrar salida"])
    await comando(page, label);
  await comando(page, "Registrar recepción", async () => {
    await page.getByRole("dialog").getByRole("checkbox").check();
  });
  await expect(
    page.getByRole("heading", { name: "Historial del remito" }),
  ).toBeVisible();
}

test("alta de libro guarda autor y sobrevive a recargar", async ({ page }) => {
  const titulo = `Catálogo ${Date.now()}`;
  await page.goto("/catalogo/nuevo");
  await page.getByLabel("Título", { exact: true }).fill(titulo);
  await page
    .getByLabel("Autor o autores", { exact: true })
    .fill("Autora de integración");
  await page.getByLabel("Editorial", { exact: true }).fill("Editorial");
  await page.getByLabel("Edición", { exact: true }).fill("1");
  await page
    .getByRole("button", { name: "Guardar libro", exact: true })
    .click();
  await expect(page).toHaveURL(/\/catalogo\/\d+$/);
  await page.reload();
  await expect(
    page.getByRole("heading", { name: titulo, exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Autora de integración", { exact: true }).first(),
  ).toBeVisible();
});

test("préstamo local desde asignación hasta devolución", async ({
  page,
  request,
}) => {
  const d = await datos(request);
  const s = await post(request, "solicitudes", {
    socio_id: d.socio.id,
    libro_id: d.libro.id,
    sede_origen_id: d.origen.id,
    sede_destino_id: d.origen.id,
    tipo: "LOCAL",
  });
  await page.goto(`/solicitudes/${s.id}`);
  await comando(page, "Asignar ejemplar", async () => {
    await page
      .getByLabel("Ejemplar disponible")
      .selectOption(String(d.ejemplar.id));
  });
  await comando(page, "Preparar entrega local");
  await entrega(page);
  await devolver(page, request, s.id);
  await page.goto(`/ejemplares/${d.ejemplar.id}`);
  await comando(page, "Aprobar disponibilidad");
  expect(
    (await (await request.get(`${api}/ejemplares/${d.ejemplar.id}/`)).json())
      .estado,
  ).toBe("DISPONIBLE");
});

test("interbibliotecario con remito de ida, entrega, devolución y retorno", async ({
  page,
  request,
}) => {
  const d = await datos(request);
  const s = await post(request, "solicitudes", {
    socio_id: d.socio.id,
    libro_id: d.libro.id,
    sede_origen_id: d.origen.id,
    sede_destino_id: d.destino.id,
    tipo: "INTERBIBLIOTECARIO",
  });
  await page.goto(`/solicitudes/${s.id}`);
  await comando(page, "Asignar ejemplar", async () => {
    await page
      .getByLabel("Ejemplar disponible")
      .selectOption(String(d.ejemplar.id));
  });
  await page
    .getByRole("link", { name: "Preparar remito", exact: true })
    .click();
  await remito(page, d.ejemplar.id);
  await page.goto(`/solicitudes/${s.id}`);
  await entrega(page);
  await devolver(page, request, s.id);
  await page.goto(`/ejemplares/${d.ejemplar.id}`);
  await page
    .getByRole("link", { name: "Preparar retorno a sede propietaria" })
    .click();
  await remito(page, d.ejemplar.id);
  await page.goto(`/ejemplares/${d.ejemplar.id}`);
  await comando(page, "Aprobar disponibilidad");
  const e = await (
    await request.get(`${api}/ejemplares/${d.ejemplar.id}/`)
  ).json();
  expect(e.sede_actual_id).toBe(d.origen.id);
  expect(e.estado).toBe("DISPONIBLE");
});

test("reserva asignada y cumplida desde su ficha", async ({
  page,
  request,
}) => {
  const d = await datos(request);
  const r = await post(request, "reservas", {
    socio_id: d.socio.id,
    libro_id: d.libro.id,
    sede_retiro_id: d.origen.id,
  });
  await page.goto(`/reservas/${r.id}`);
  await comando(page, "Asignar y preparar ejemplar", async () => {
    await page
      .getByLabel("Ejemplar disponible")
      .selectOption(String(d.ejemplar.id));
    const limite = new Date(Date.now() + 3 * 86400000)
      .toISOString()
      .slice(0, 16);
    await page.getByLabel("Fecha límite de retiro").fill(limite);
  });
  await page
    .getByRole("link", { name: "Registrar entrega", exact: true })
    .click();
  await entrega(page);
  expect(
    (await (await request.get(`${api}/reservas/${r.id}/`)).json()).estado,
  ).toBe("CUMPLIDA");
});

test("los cinco reportes consultan la API y exportan CSV", async ({ page }) => {
  for (const [tipo, endpoint] of [
    ["vencidos", "prestamos-vencidos"],
    ["demanda", "demanda-interbibliotecaria"],
    ["movimientos", "movimientos"],
    ["disponibilidad", "disponibilidad"],
    ["operaciones", "operaciones"],
  ]) {
    const response = page.waitForResponse(
      (r) =>
        r.url().includes(endpoint) && r.request().resourceType() === "fetch",
    );
    await page.goto(`/reportes/${tipo}`);
    expect((await response).ok()).toBeTruthy();
    const boton = page.getByRole("button", { name: "Exportar CSV" });
    await expect(boton).toBeEnabled();
    const descarga = page.waitForEvent("download");
    await boton.click();
    expect((await descarga).suggestedFilename()).toContain(
      `entrelibros-${tipo}`,
    );
  }
});

test("ABMC de ejemplar queda evidenciado en bitácora y disponibilidad", async ({
  page,
  request,
}) => {
  const d = await datos(request);
  const inventario = `ABMC-${Date.now()}`;
  await page.goto("/ejemplares/nuevo");
  await page
    .getByLabel("Código de inventario", { exact: true })
    .fill(inventario);
  await page
    .getByLabel("Libro", { exact: true })
    .selectOption(String(d.libro.id));
  await page
    .getByLabel("Sede propietaria", { exact: true })
    .selectOption(String(d.origen.id));
  await page
    .getByRole("button", { name: "Guardar ejemplar", exact: true })
    .click();
  await expect(page).toHaveURL(/\/ejemplares\/\d+$/);
  const id = Number(page.url().split("/").pop());
  await page.getByRole("link", { name: "Editar ejemplar", exact: true }).click();
  await page
    .getByLabel("Condición física", { exact: true })
    .selectOption("NO_APTO");
  await page
    .getByRole("button", { name: "Guardar ejemplar", exact: true })
    .click();
  await expect(page).toHaveURL(new RegExp(`/ejemplares/${id}$`));
  await comando(page, "Dar de baja");
  const response = page.waitForResponse((r) =>
    r.url().includes("/api/reportes/operaciones/"),
  );
  await page.goto("/reportes/operaciones");
  const reporte = await (await response).json();
  const eventos = reporte.filas.filter(
    (f: { entidad: string; registro_id: number }) =>
      f.entidad === "ejemplares" && f.registro_id === id,
  );
  expect(eventos.map((f: { accion: string }) => f.accion)).toEqual([
    "ALTA",
    "MODIFICACION",
    "BAJA",
  ]);
  await expect(page.getByText(inventario, { exact: false })).toBeVisible();
  const filas = page
    .locator("tbody tr")
    .filter({ has: page.getByRole("cell", { name: String(id), exact: true }) })
    .filter({ hasText: "ejemplares" });
  await expect(filas).toHaveCount(3);
  const data = await (
    await request.get(
      `${api}/reportes/disponibilidad/?desde=2000-01-01&hasta=2100-01-01`,
    )
  ).json();
  const fila = data.filas.find(
    (f: { libro_id: number; sede_propietaria_id: number }) =>
      f.libro_id === d.libro.id && f.sede_propietaria_id === d.origen.id,
  );
  expect(fila.total).toBe(2);
  expect(fila.disponibles).toBe(1);
  expect(fila.por_estado.BAJA).toBe(1);
});
