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
async function get(request: APIRequestContext, path: string) {
  return (await request.get(`${api}/${path}/`)).json();
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
/** Abre la operación desde su botón, completa el diálogo y lo confirma. */
async function comando(page: Page, label: string, fill?: () => Promise<void>) {
  await page.getByRole("button", { name: label, exact: true }).first().click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  if (fill) await fill();
  await dialog.locator('button[type="submit"]').click();
  await expect(dialog).not.toBeVisible();
}
const elegirEjemplar = (page: Page, id: number) => async () => {
  await page
    .getByRole("dialog")
    .getByLabel("Ejemplar", { exact: true })
    .selectOption(String(id));
};
async function prestamoDe(request: APIRequestContext, solicitudId: number) {
  let data = await get(request, "prestamos");
  let rows = Array.isArray(data) ? data : data.results;
  let prestamo = rows.find((p: { solicitud_id: number }) => p.solicitud_id === solicitudId);
  while (!prestamo && data.next) {
    data = await (await request.get(data.next)).json();
    rows = data.results;
    prestamo = rows.find((p: { solicitud_id: number }) => p.solicitud_id === solicitudId);
  }
  expect(prestamo).toBeTruthy();
  return prestamo;
}
async function devolver(page: Page, request: APIRequestContext, solicitudId: number) {
  const prestamo = await prestamoDe(request, solicitudId);
  await page.goto(`/prestamos/${prestamo.id}`);
  await comando(page, "Registrar devolución");
}
/** Recorre el remito abierto en pantalla: empaquetar → despachar → recibir. */
async function recorrerRemito(page: Page) {
  await expect(page).toHaveURL(/\/remitos\/\d+$/);
  await comando(page, "Empaquetar");
  await comando(page, "Despachar");
  await comando(page, "Recibir envío", async () => {
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Marcar todo como recibido" })
      .click();
  });
  await expect(page.getByRole("heading", { name: "Trazabilidad" })).toBeVisible();
  await expect(page.getByText("En tránsito → Recibido")).toBeVisible();
}

test("alta de libro guarda autor y sobrevive a recargar", async ({ page }) => {
  const titulo = `Catálogo ${Date.now()}`;
  await page.goto("/catalogo/nuevo");
  await page.getByLabel("Título", { exact: true }).fill(titulo);
  await page.getByLabel("Autor o autores", { exact: true }).fill("Autora de integración");
  await page.getByLabel("Editorial", { exact: true }).fill("Editorial");
  await page.getByLabel("Edición", { exact: true }).fill("1");
  await page.getByRole("button", { name: "Guardar libro", exact: true }).click();
  await expect(page).toHaveURL(/\/catalogo\/\d+$/);
  await page.reload();
  await expect(page.getByRole("heading", { name: titulo, exact: true })).toBeVisible();
  await expect(page.getByText("Autora de integración", { exact: true }).first()).toBeVisible();
});

test("préstamo local: asignar y preparar en un paso, entregar, devolver y habilitar", async ({
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
  await expect(page.getByText("TramitacionLocal")).toBeVisible();
  await comando(page, "Asignar ejemplar", elegirEjemplar(page, d.ejemplar.id));
  expect((await get(request, `solicitudes/${s.id}`)).estado).toBe("LISTA_PARA_ENTREGA");
  await comando(page, "Entregar al socio");
  await devolver(page, request, s.id);
  await page.goto(`/ejemplares/${d.ejemplar.id}`);
  await comando(page, "Aprobar disponibilidad");
  expect((await get(request, `ejemplares/${d.ejemplar.id}`)).estado).toBe("DISPONIBLE");
});

test("interbibliotecario: la estrategia arma el remito, viaja, se entrega y retorna", async ({
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
  await expect(page.getByText("TramitacionInterbibliotecaria")).toBeVisible();
  await comando(page, "Asignar ejemplar", elegirEjemplar(page, d.ejemplar.id));
  await page.getByRole("link", { name: /Ir al remito/ }).click();
  await expect(page.getByText("EnPreparacion")).toBeVisible();
  await recorrerRemito(page);

  await page.goto(`/solicitudes/${s.id}`);
  await comando(page, "Entregar al socio");
  await devolver(page, request, s.id);
  await page.getByRole("button", { name: "Preparar retorno" }).click();
  await recorrerRemito(page);
  await page.goto(`/ejemplares/${d.ejemplar.id}`);
  await comando(page, "Aprobar disponibilidad");
  const e = await get(request, `ejemplares/${d.ejemplar.id}`);
  expect(e.sede_actual_id).toBe(d.origen.id);
  expect(e.estado).toBe("DISPONIBLE");
});

test("una recepción con daño deja el remito con incidencias y la solicitud en cola", async ({
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
  await comando(page, "Asignar ejemplar", elegirEjemplar(page, d.ejemplar.id));
  await page.getByRole("link", { name: /Ir al remito/ }).click();
  await comando(page, "Empaquetar");
  await comando(page, "Despachar");
  await comando(page, "Recibir envío", async () => {
    await page.getByRole("dialog").getByRole("button", { name: "Dañado" }).click();
  });
  await expect(page.getByText("Recibido con incidencias").first()).toBeVisible();
  const solicitud = await get(request, `solicitudes/${s.id}`);
  expect(solicitud.estado).toBe("PENDIENTE");
  expect(solicitud.ejemplar_id).toBeNull();
});

test("reserva: apartar copia y entregarla desde su ficha", async ({ page, request }) => {
  const d = await datos(request);
  const r = await post(request, "reservas", {
    socio_id: d.socio.id,
    libro_id: d.libro.id,
    sede_retiro_id: d.origen.id,
  });
  await page.goto(`/reservas/${r.id}`);
  await comando(page, "Apartar copia", elegirEjemplar(page, d.ejemplar.id));
  await comando(page, "Entregar al socio");
  expect((await get(request, `reservas/${r.id}`)).estado).toBe("CUMPLIDA");
});

test("los siete reportes consultan la API y exportan CSV", async ({ page }) => {
  for (const [tipo, endpoint] of [
    ["activos", "reportes/activos"],
    ["vencidos", "prestamos-vencidos"],
    ["demanda", "demanda-interbibliotecaria"],
    ["disponibilidad", "disponibilidad"],
    ["logistica", "reportes/logistica"],
    ["movimientos", "movimientos"],
    ["operaciones", "operaciones"],
  ]) {
    const response = page.waitForResponse(
      (r) => r.url().includes(endpoint) && r.request().resourceType() === "fetch",
    );
    await page.goto(`/reportes/${tipo}`);
    expect((await response).ok()).toBeTruthy();
    const boton = page.getByRole("button", { name: "Exportar CSV" });
    await expect(boton).toBeEnabled();
    const descarga = page.waitForEvent("download");
    await boton.click();
    expect((await descarga).suggestedFilename()).toContain(`entrelibros-${tipo}`);
  }
});

test("ABMC de ejemplar queda evidenciado en bitácora y disponibilidad", async ({
  page,
  request,
}) => {
  const d = await datos(request);
  const inventario = `ABMC-${Date.now()}`;
  await page.goto("/ejemplares/nuevo");
  await page.getByLabel("Código de inventario", { exact: true }).fill(inventario);
  await page.getByLabel("Libro", { exact: true }).selectOption(String(d.libro.id));
  await page.getByLabel("Sede propietaria", { exact: true }).selectOption(String(d.origen.id));
  await page.getByRole("button", { name: "Guardar ejemplar", exact: true }).click();
  await expect(page).toHaveURL(/\/ejemplares\/\d+$/);
  const id = Number(page.url().split("/").pop());
  await page.getByRole("link", { name: "Editar", exact: true }).click();
  await page.getByLabel("Condición física", { exact: true }).selectOption("NO_APTO");
  await page.getByRole("button", { name: "Guardar ejemplar", exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/ejemplares/${id}$`));
  await comando(page, "Dar de baja");
  const response = page.waitForResponse((r) => r.url().includes("/api/reportes/operaciones/"));
  await page.goto("/reportes/operaciones");
  const reporte = await (await response).json();
  const eventos = reporte.filas.filter(
    (f: { entidad: string; registro_id: number }) =>
      f.entidad === "ejemplares" && f.registro_id === id,
  );
  expect(eventos.map((f: { accion: string }) => f.accion)).toEqual(["ALTA", "MODIFICACION", "BAJA"]);
  await expect(page.getByText(inventario, { exact: false }).first()).toBeVisible();
  const data = await (
    await request.get(`${api}/reportes/disponibilidad/?desde=2000-01-01&hasta=2100-01-01`)
  ).json();
  const fila = data.filas.find(
    (f: { libro_id: number; sede_propietaria_id: number }) =>
      f.libro_id === d.libro.id && f.sede_propietaria_id === d.origen.id,
  );
  expect(fila.total).toBe(2);
  expect(fila.disponibles).toBe(1);
  expect(fila.por_estado.BAJA).toBe(1);
});

test("alta de libro con portada: se ve en el catálogo y en sus ejemplares", async ({ page, request }) => {
  // PNG de 1×1 válido.
  const png = Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    "base64",
  );
  const titulo = `Con portada ${Date.now()}`;
  await page.goto("/catalogo/nuevo");
  await page.getByLabel("Título", { exact: true }).fill(titulo);
  await page.getByLabel("Autor o autores", { exact: true }).fill("Autora");
  await page.getByLabel("Editorial", { exact: true }).fill("Editorial");
  await page.getByLabel("Edición", { exact: true }).fill("1");
  await page.getByLabel("Portada (opcional)").setInputFiles({ name: "tapa.png", mimeType: "image/png", buffer: png });
  await page.getByRole("button", { name: "Guardar libro", exact: true }).click();
  await expect(page).toHaveURL(/\/catalogo\/\d+$/);
  const libroId = Number(page.url().split("/").pop());
  const libro = await get(request, `libros/${libroId}`);
  expect(libro.portada_url).toContain(`/api/libros/${libroId}/portada/`);
  await expect(page.getByRole("img", { name: `Portada de ${titulo}` })).toBeVisible();

  const d = await datos(request);
  await post(request, "ejemplares", {
    codigo_inventario: `CP-${Date.now()}`,
    libro_id: libroId,
    sede_propietaria_id: d.origen.id,
    condicion_fisica: "APTO",
  });
  await page.goto(`/ejemplares?libro_id=${libroId}`);
  await expect(page.getByRole("img", { name: `Portada de ${titulo}` }).first()).toBeVisible();
});

test("eliminar un libro sin historial desde su ficha", async ({ page, request }) => {
  const libro = await post(request, "libros", {
    titulo: `Para borrar ${Date.now()}`,
    autor: "Autor",
    editorial: "Editorial",
    edicion: "1",
  });
  await page.goto(`/catalogo/${libro.id}`);
  await page.getByRole("button", { name: "Eliminar", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByText(libro.titulo, { exact: false })).toBeVisible();
  await dialog.getByRole("button", { name: "Eliminar", exact: true }).click();
  await expect(page).toHaveURL(/\/catalogo$/);
  const res = await request.get(`${api}/libros/${libro.id}/`);
  expect(res.status()).toBe(404);
});
