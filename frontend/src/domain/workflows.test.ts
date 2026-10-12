import { describe, expect, it, vi, afterEach } from "vitest";
import { seed } from "../data/seed";
import { applyCommand, createMockApi, saveEntity } from "../api/mock";
import { buildReport } from "./reports";
import { available } from "./selectors";

afterEach(() => vi.useRealTimers());
describe("Recorridos de demostración basados en el modelo", () => {
  it("completa préstamo local y devolución sin duplicar socio/libro en Prestamo", () => {
    const db = structuredClone(seed);
    const s = saveEntity(db, "solicitudes", {
      socio_id: 1,
      libro_id: 2,
      ejemplar_id: 4,
      sede_origen_id: 1,
      sede_destino_id: 1,
      reserva_id: null,
      tipo: "LOCAL",
      estado: "PENDIENTE",
      fecha_solicitud: "",
    });
    expect(db.ejemplares.find((e) => e.id === 4)?.estado).toBe("ASIGNADO");
    applyCommand(db, "solicitudes", s.id, "preparar-entrega");
    applyCommand(db, "solicitudes", s.id, "entregar", {
      fecha_entrega: "2026-10-12T12:00:00-03:00",
      fecha_vencimiento: "2026-10-26T12:00:00-03:00",
    });
    const p = db.prestamos.find((p) => p.solicitud_id === s.id)!;
    expect(p).not.toHaveProperty("socio_id");
    expect(p).not.toHaveProperty("estado");
    expect(() => applyCommand(db, "solicitudes", s.id, "entregar")).toThrow();
    applyCommand(db, "prestamos", p.id, "devolver", {
      fecha_devolucion: "2026-10-13T12:00:00-03:00",
      condicion_devolucion: "NO_APTO",
    });
    const e = db.ejemplares.find((e) => e.id === 4)!;
    expect(e.estado).toBe("EN_REVISION");
    expect(available(e, db)).toBe(false);
  });
  it("inhabilitar impide nuevos préstamos y no impide devoluciones", () => {
    const db = structuredClone(seed);
    applyCommand(db, "socios", 3, "inhabilitar");
    expect(() =>
      applyCommand(db, "solicitudes", 40, "asignar", { ejemplar_id: 6 }),
    ).toThrow("habilitado");
    expect(() =>
      applyCommand(db, "prestamos", 18, "devolver", {
        fecha_devolucion: "2026-10-12T12:00:00-03:00",
        condicion_devolucion: "APTO",
      }),
    ).not.toThrow();
  });
  it("rechaza documentos y números de socio duplicados", () => {
    const db = structuredClone(seed);
    expect(() =>
      saveEntity(db, "socios", {
        numero_socio: "999",
        documento: "32456789",
        nombre: "Otro socio",
        contacto: "contacto",
        estado: "HABILITADO",
      }),
    ).toThrow("Ya existe");
    expect(() =>
      saveEntity(db, "socios", {
        numero_socio: "1042",
        documento: "9999",
        nombre: "Otro socio",
        contacto: "contacto",
        estado: "HABILITADO",
      }),
    ).toThrow("Ya existe");
  });
  it("impide doble asignación del mismo ejemplar", () => {
    const db = structuredClone(seed);
    const data = {
      socio_id: 1,
      libro_id: 2,
      ejemplar_id: 4,
      sede_origen_id: 1,
      sede_destino_id: 1,
      reserva_id: null,
      tipo: "LOCAL" as const,
      estado: "PENDIENTE" as const,
      fecha_solicitud: "",
    };
    saveEntity(db, "solicitudes", data);
    expect(() => saveEntity(db, "solicitudes", data)).toThrow(
      "no está disponible",
    );
  });
  it("recorre remito, preserva propietario e historial y habilita entrega después de recibir", () => {
    const db = structuredClone(seed);
    const s = saveEntity(db, "solicitudes", {
      socio_id: 1,
      libro_id: 2,
      ejemplar_id: 4,
      sede_origen_id: 1,
      sede_destino_id: 3,
      reserva_id: null,
      tipo: "INTERBIBLIOTECARIO",
      estado: "PENDIENTE",
      fecha_solicitud: "",
    });
    const r = saveEntity(db, "remitos", {
      numero: "REM-TEST",
      sede_origen_id: 1,
      sede_destino_id: 3,
      estado: "EN_PREPARACION",
      fecha_creacion: "",
      fecha_despacho: null,
      fecha_recepcion: null,
    });
    expect(() => applyCommand(db, "remitos", r.id, "empaquetar")).toThrow(
      "al menos",
    );
    applyCommand(db, "remitos", r.id, "asignar", { ejemplar_id: 4 });
    applyCommand(db, "remitos", r.id, "empaquetar");
    applyCommand(db, "remitos", r.id, "despachar");
    const e = db.ejemplares.find((e) => e.id === 4)!;
    expect(e.sede_actual_id).toBeNull();
    expect(e.sede_propietaria_id).toBe(1);
    expect(() => applyCommand(db, "remitos", r.id, "cancelar")).toThrow(
      "no está permitida",
    );
    applyCommand(db, "remitos", r.id, "registrar-salida");
    expect(() =>
      applyCommand(db, "remitos", r.id, "recibir", {
        responsable: "Personal Norte",
        verificados: [],
      }),
    ).toThrow("Verificá");
    applyCommand(db, "remitos", r.id, "recibir", {
      responsable: "Personal Sur",
      verificados: [4],
    });
    expect(e.sede_actual_id).toBe(3);
    expect(e.sede_propietaria_id).toBe(1);
    expect(s.estado).toBe("LISTA_PARA_ENTREGA");
    expect(
      db.evento_remitos
        .filter((e) => e.remito_id === r.id)
        .map((e) => e.estado_nuevo),
    ).toEqual([
      "EN_PREPARACION",
      "EMPAQUETADO",
      "DESPACHADO",
      "EN_TRANSITO",
      "RECIBIDO",
    ]);
  });
  it("reserva requiere plazo explícito y se cumple con la entrega", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-12T12:00:00-03:00"));
    const db = structuredClone(seed);
    const r = saveEntity(db, "reservas", {
      socio_id: 1,
      libro_id: 2,
      sede_retiro_id: 1,
      ejemplar_asignado_id: null,
      fecha_reserva: "",
      fecha_limite_retiro: null,
      estado: "PENDIENTE",
    });
    expect(() =>
      applyCommand(db, "reservas", r.id, "asignar-reserva", { ejemplar_id: 4 }),
    ).toThrow("explícitamente");
    applyCommand(db, "reservas", r.id, "asignar-reserva", {
      ejemplar_id: 4,
      fecha_limite_retiro: "2026-10-14T12:00:00-03:00",
    });
    expect(r.estado).toBe("LISTA_PARA_RETIRO");
    const s = db.solicitudes.find((s) => s.reserva_id === r.id)!;
    applyCommand(db, "solicitudes", s.id, "entregar", {
      fecha_entrega: "2026-10-12T12:00:00-03:00",
      fecha_vencimiento: "2026-10-26T12:00:00-03:00",
    });
    expect(r.estado).toBe("CUMPLIDA");
  });
  it("no permite iniciar operaciones con sedes dadas de baja", () => {
    const db = structuredClone(seed);
    expect(() =>
      saveEntity(db, "reservas", {
        socio_id: 1,
        libro_id: 2,
        sede_retiro_id: 4,
        ejemplar_asignado_id: null,
        fecha_reserva: "",
        fecha_limite_retiro: null,
        estado: "PENDIENTE",
      }),
    ).toThrow("activa");
  });
  it("una operación inválida no se persiste", async () => {
    const map = new Map<string, string>();
    const api = createMockApi({
      getItem: (k) => map.get(k) ?? null,
      setItem: (k, v) => {
        map.set(k, v);
      },
      removeItem: (k) => {
        map.delete(k);
      },
    });
    const before = await api.snapshot();
    await expect(
      api.command("remitos", 18, "recibir", { verificados: [] }),
    ).rejects.toThrow();
    expect(await api.snapshot()).toEqual(before);
  });
});
describe("Cuatro reportes", () => {
  const filter = { desde: "2026-10-01", hasta: "2026-10-09", sede: null };
  it("calcula tres días de atraso en el corte de ejemplo", () => {
    const r = buildReport("vencidos", structuredClone(seed), filter);
    expect(r.rows).toHaveLength(1);
    expect(r.rows[0][3]).toBe(3);
  });
  it("conserva el vencido histórico aunque se devuelva después del corte", () => {
    const db = structuredClone(seed);
    db.prestamos[0].fecha_devolucion = "2026-10-10T12:00:00-03:00";
    expect(buildReport("vencidos", db, filter).rows[0][3]).toBe(3);
  });
  it("excluye canceladas de la demanda y usa destino como solicitante", () => {
    const db = structuredClone(seed);
    db.solicitudes[2].estado = "CANCELADA";
    const r = buildReport("demanda", db, filter);
    expect(r.rows).toEqual([["Rayuela", 1, "Sede Norte"]]);
  });
  it("no calcula promedio de remitos aún no recibidos", () => {
    expect(
      buildReport("movimientos", structuredClone(seed), filter).rows[0],
    ).toEqual(["Biblioteca Central → Sede Norte", 1, 0, "Sin recepciones"]);
  });
  it("calcula disponibilidad sobre todos los ejemplares y admite filtros vacíos", () => {
    const r = buildReport("disponibilidad", structuredClone(seed), filter);
    expect(r.summary).toBe("6 de 12 ejemplares disponibles");
    expect(
      buildReport("demanda", structuredClone(seed), { ...filter, sede: 4 })
        .rows,
    ).toEqual([]);
  });
});
