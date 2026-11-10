import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { httpApi } from "./http";

beforeEach(() => {
  vi.stubGlobal("document", { cookie: "" });
  vi.stubGlobal("location", { origin: "http://localhost:5173" });
});
afterEach(() => vi.unstubAllGlobals());
const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status });

describe("Contrato HTTP con Django", () => {
  it("carga todas las páginas sin solicitar tablas de autores inexistentes", async () => {
    const fetch = vi.fn(async (url: string) => {
      if (url.endsWith("sedes/"))
        return json({
          results: [{ id: 1, nombre: "Central" }],
          next: "http://backend:8000/api/sedes/?page=2",
        });
      if (url.includes("page=2"))
        return json({ results: [{ id: 2, nombre: "Norte" }], next: null });
      if (url.endsWith("libros/"))
        return json([{ id: 1, titulo: "Rayuela", autor: "Cortázar" }]);
      return json([]);
    });
    vi.stubGlobal("fetch", fetch);
    const db = await httpApi.snapshot();
    expect(db.sedes.map((s) => s.nombre)).toEqual(["Central", "Norte"]);
    expect(db.libros[0].autor).toBe("Cortázar");
    expect(fetch.mock.calls.some(([url]) => url.includes("autores"))).toBe(
      false,
    );
    expect(fetch.mock.calls.some(([url]) => url.includes("backend:8000"))).toBe(
      false,
    );
  });

  it("conserva mensajes de dominio y errores de formulario del backend", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        json(
          {
            error: {
              detail: { documento: ["Ya existe un socio con ese documento."] },
            },
          },
          400,
        ),
      ),
    );
    await expect(
      httpApi.command("socios", 1, "habilitar"),
    ).rejects.toMatchObject({
      status: 400,
      message: "Ya existe un socio con ese documento.",
      fields: { documento: ["Ya existe un socio con ese documento."] },
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        json({ error: { detail: "El ejemplar no está disponible." } }, 400),
      ),
    );
    await expect(httpApi.command("solicitudes", 1, "asignar")).rejects.toThrow(
      "El ejemplar no está disponible.",
    );
  });

  it("presenta los resultados del reporte sin recalcular la demanda", async () => {
    const fetch = vi.fn(async () =>
      json({
        resumen: "2 solicitudes válidas",
        criterio: "Excluye canceladas",
        filas: [
          {
            libro: "Rayuela",
            cantidad: 3,
            sedes: [
              { sede: "Biblioteca Norte", cantidad: 2 },
              { sede: "Biblioteca Central", cantidad: 1 },
            ],
          },
        ],
      }),
    );
    vi.stubGlobal("fetch", fetch);
    const result = await httpApi.report("demanda", {
      desde: "2026-10-01",
      hasta: "2026-10-20",
      sede: 2,
    });
    expect(result.rows).toEqual([[1, "Rayuela", 3, "Norte (2) · Central (1)"]]);
    expect(fetch.mock.calls[0]).toBeDefined();
  });
});
