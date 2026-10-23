import { seed } from "../data/seed";
import type {
  Database,
  Entity,
  NewEntity,
  Resource,
  EstadoRemito,
} from "../domain/models";
import { available, today } from "../domain/selectors";
import {
  ApiError,
  type Command,
  type CommandInput,
  type LibraryApi,
} from "./contracts";

const KEY = "entrelibros:demo:v1";
const copy = <T>(x: T): T => structuredClone(x);
const nextId = (rows: { id: number }[]) =>
  Math.max(0, ...rows.map((r) => r.id)) + 1;
const fail = (message: string, field?: string): never => {
  throw new ApiError(message, field ? { [field]: [message] } : {});
};
const required = (condition: unknown, message: string, field?: string) => {
  if (!condition) fail(message, field);
};
const instant = () => new Date().toISOString();
const num = (input: CommandInput, key: string) => Number(input[key]);
const text = (input: CommandInput, key: string) =>
  String(input[key] ?? "").trim();
function activeSede(db: Database, id: number) {
  required(
    db.sedes.some((s) => s.id === id && s.estado === "ACTIVA"),
    "La sede debe estar activa.",
  );
}
function activeSocio(db: Database, id: number) {
  required(
    db.socios.some((s) => s.id === id && s.estado === "HABILITADO"),
    "El socio debe estar habilitado.",
  );
}
function unique(
  db: Database,
  resource: Resource,
  field: string,
  value: unknown,
  id?: number,
) {
  if (!value) return;
  const rows = db[resource] as unknown as Record<string, unknown>[];
  required(
    !rows.some(
      (r) =>
        r.id !== id &&
        String(r[field]).toLocaleLowerCase() ===
          String(value).toLocaleLowerCase(),
    ),
    "Ya existe un registro con ese valor.",
    field,
  );
}

// Simulación de los casos de uso para probar pantallas. Estas validaciones
// deberán implementarse en servicios/transacciones de Django al integrar.
export function saveEntity<K extends Resource>(
  db: Database,
  resource: K,
  data: NewEntity<K>,
  id?: number,
): Entity<K> {
  const clean = Object.fromEntries(
    Object.entries(data).map(([k, v]) => [
      k,
      typeof v === "string" ? v.trim() : v,
    ]),
  ) as Record<string, unknown>;
  const fields: Partial<Record<Resource, string[]>> = {
    sedes: ["nombre", "direccion", "contacto", "horarios"],
    socios: ["numero_socio", "documento", "nombre", "contacto"],
    libros: ["titulo", "editorial", "edicion"],
    autores: ["nombre"],
    ejemplares: [
      "codigo_inventario",
      "libro_id",
      "sede_propietaria_id",
      "condicion_fisica",
    ],
  };
  for (const f of fields[resource] ?? [])
    required(clean[f], "Este campo es obligatorio.", f);
  for (const f of resource === "sedes"
    ? ["nombre"]
    : resource === "socios"
      ? ["numero_socio", "documento"]
      : resource === "libros"
        ? ["isbn"]
        : resource === "ejemplares"
          ? ["codigo_inventario"]
          : resource === "remitos"
            ? ["numero"]
            : [])
    unique(db, resource, f, clean[f], id);
  const table = db[resource] as unknown as Record<string, unknown>[];
  const old = id === undefined ? undefined : table.find((r) => r.id === id);
  if (id !== undefined) required(old, "No encontramos el registro.");
  if (resource === "sedes") clean.estado = old?.estado ?? "ACTIVA";
  if (resource === "socios") clean.estado = old?.estado ?? "HABILITADO";
  if (resource === "ejemplares") {
    required(
      db.libros.some((b) => b.id === clean.libro_id),
      "Elegí un libro válido.",
      "libro_id",
    );
    activeSede(db, Number(clean.sede_propietaria_id));
    if (old) {
      required(
        ["DISPONIBLE", "EN_REVISION", "BAJA"].includes(String(old.estado)),
        "No se puede editar un ejemplar comprometido con una operación.",
      );
      required(
        old.libro_id === clean.libro_id &&
          old.sede_propietaria_id === clean.sede_propietaria_id,
        "La edición no puede cambiar la identidad del libro ni su sede propietaria.",
      );
    }
    clean.estado =
      old?.estado ??
      (clean.condicion_fisica === "APTO" ? "DISPONIBLE" : "EN_REVISION");
    if (clean.condicion_fisica !== "APTO" && clean.estado === "DISPONIBLE")
      clean.estado = "EN_REVISION";
    clean.sede_actual_id = old?.sede_actual_id ?? clean.sede_propietaria_id;
  }
  if (resource === "solicitudes" || resource === "reservas") {
    activeSocio(db, Number(clean.socio_id));
    required(
      db.libros.some((b) => b.id === clean.libro_id),
      "Elegí un libro válido.",
      "libro_id",
    );
  }
  if (resource === "solicitudes") {
    activeSede(db, Number(clean.sede_origen_id));
    activeSede(db, Number(clean.sede_destino_id));
    clean.tipo =
      clean.sede_origen_id === clean.sede_destino_id
        ? "LOCAL"
        : "INTERBIBLIOTECARIO";
    clean.estado = "PENDIENTE";
    clean.fecha_solicitud = instant();
    clean.reserva_id = null;
    if (clean.ejemplar_id) {
      const e = db.ejemplares.find((e) => e.id === clean.ejemplar_id);
      required(
        e &&
          available(e, db) &&
          e.libro_id === clean.libro_id &&
          e.sede_propietaria_id === clean.sede_origen_id,
        "El ejemplar no está disponible en el origen seleccionado.",
        "ejemplar_id",
      );
      e!.estado = "ASIGNADO";
      clean.estado = "ASIGNADA";
    }
  }
  if (resource === "reservas") {
    activeSede(db, Number(clean.sede_retiro_id));
    required(
      !db.reservas.some(
        (r) =>
          r.socio_id === clean.socio_id &&
          r.libro_id === clean.libro_id &&
          r.sede_retiro_id === clean.sede_retiro_id &&
          ["PENDIENTE", "LISTA_PARA_RETIRO"].includes(r.estado),
      ),
      "Ya existe una reserva vigente para ese socio, libro y sede.",
    );
    clean.estado = "PENDIENTE";
    clean.fecha_reserva = instant();
    clean.ejemplar_asignado_id = null;
    clean.fecha_limite_retiro = null;
  }
  if (resource === "remitos") {
    activeSede(db, Number(clean.sede_origen_id));
    activeSede(db, Number(clean.sede_destino_id));
    required(
      clean.sede_origen_id !== clean.sede_destino_id,
      "El origen y el destino deben ser diferentes.",
      "sede_destino_id",
    );
    clean.estado = "EN_PREPARACION";
    clean.fecha_creacion = instant();
    clean.fecha_despacho = null;
    clean.fecha_recepcion = null;
  }
  const row = { ...clean, id: id ?? nextId(table as { id: number }[]) };
  if (old) Object.assign(old, row);
  else table.push(row);
  if (resource === "remitos" && id === undefined)
    db.evento_remitos.push({
      id: nextId(db.evento_remitos),
      remito_id: row.id,
      fecha_hora: instant(),
      estado_anterior: null,
      estado_nuevo: "EN_PREPARACION",
      responsable: "Personal de biblioteca",
      observacion: "Remito registrado.",
    });
  return row as unknown as Entity<K>;
}

export function applyCommand(
  db: Database,
  resource: Resource,
  id: number,
  action: Command,
  input: CommandInput = {},
) {
  if (resource === "socios") {
    const s = db.socios.find((x) => x.id === id);
    required(s, "Socio inexistente.");
    required(
      action === "habilitar" || action === "inhabilitar",
      "Operación inválida.",
    );
    const next = action === "habilitar" ? "HABILITADO" : "INHABILITADO";
    required(s!.estado !== next, "El socio ya se encuentra en ese estado.");
    s!.estado = next;
    return;
  }
  if (resource === "sedes") {
    const s = db.sedes.find((x) => x.id === id);
    required(s, "Sede inexistente.");
    required(
      action === "reactivar" || action === "dar-de-baja",
      "Operación inválida.",
    );
    const next = action === "reactivar" ? "ACTIVA" : "BAJA";
    required(s!.estado !== next, "La sede ya se encuentra en ese estado.");
    s!.estado = next;
    return;
  }
  if (resource === "ejemplares") {
    const e = db.ejemplares.find((x) => x.id === id);
    required(e, "Ejemplar inexistente.");
    if (action === "aprobar-disponibilidad") {
      required(
        e!.estado === "EN_REVISION" &&
          e!.condicion_fisica === "APTO" &&
          e!.sede_actual_id === e!.sede_propietaria_id,
        "Requiere condición apta y ubicación en la sede propietaria.",
      );
      activeSede(db, e!.sede_propietaria_id);
      e!.estado = "DISPONIBLE";
      return;
    }
    required(
      action === "dar-de-baja" &&
        ["DISPONIBLE", "EN_REVISION"].includes(e!.estado),
      "No se puede dar de baja un ejemplar comprometido.",
    );
    e!.estado = "BAJA";
    return;
  }
  if (resource === "solicitudes") {
    const s = db.solicitudes.find((x) => x.id === id);
    required(s, "Solicitud inexistente.");
    const e = db.ejemplares.find(
      (x) => x.id === (s!.ejemplar_id ?? num(input, "ejemplar_id")),
    );
    if (action === "rechazar") {
      required(
        s!.estado === "PENDIENTE",
        "Sólo puede rechazarse una solicitud pendiente.",
      );
      s!.estado = "RECHAZADA";
      return;
    }
    if (action === "cancelar") {
      required(
        ["PENDIENTE", "ASIGNADA"].includes(s!.estado),
        "Sólo se cancela antes del despacho. La cancelación después de la recepción requiere definir cómo gestionar el ejemplar.",
      );
      required(
        !db.detalle_remitos.some(
          (d) =>
            d.solicitud_id === id &&
            !["CANCELADO", "RECIBIDO"].includes(
              db.remitos.find((r) => r.id === d.remito_id)!.estado,
            ),
        ),
        "La solicitud está en un remito vigente. Cancelá primero el remito.",
      );
      if (e) e.estado = "DISPONIBLE";
      s!.estado = "CANCELADA";
      return;
    }
    activeSocio(db, s!.socio_id);
    activeSede(db, s!.sede_origen_id);
    activeSede(db, s!.sede_destino_id);
    if (action === "asignar") {
      required(
        s!.estado === "PENDIENTE" &&
          e &&
          available(e, db) &&
          e.libro_id === s!.libro_id &&
          e.sede_propietaria_id === s!.sede_origen_id,
        "Elegí un ejemplar disponible que corresponda al libro y origen.",
      );
      s!.ejemplar_id = e!.id;
      e!.estado = "ASIGNADO";
      s!.estado = "ASIGNADA";
      return;
    }
    if (action === "preparar-entrega") {
      required(
        s!.tipo === "LOCAL" &&
          s!.estado === "ASIGNADA" &&
          e?.estado === "ASIGNADO",
        "La solicitud local debe estar asignada.",
      );
      s!.estado = "LISTA_PARA_ENTREGA";
      e!.estado = "LISTO_PARA_ENTREGA";
      return;
    }
    required(
      action === "entregar" &&
        s!.estado === "LISTA_PARA_ENTREGA" &&
        e?.estado === "LISTO_PARA_ENTREGA" &&
        e.sede_actual_id === s!.sede_destino_id,
      "El material todavía no está listo para entregar.",
    );
    const entrega = text(input, "fecha_entrega"),
      vence = text(input, "fecha_vencimiento");
    required(
      entrega && vence && Date.parse(vence) > Date.parse(entrega),
      "El vencimiento debe ser posterior a la entrega.",
      "fecha_vencimiento",
    );
    required(
      !db.prestamos.some((p) => p.solicitud_id === id),
      "Esta solicitud ya generó un préstamo.",
    );
    const reserva = db.reservas.find((r) => r.id === s!.reserva_id);
    if (reserva?.fecha_limite_retiro)
      required(
        Date.parse(entrega) <= Date.parse(reserva.fecha_limite_retiro),
        "El plazo de retiro venció.",
      );
    db.prestamos.push({
      id: nextId(db.prestamos),
      solicitud_id: id,
      fecha_entrega: entrega,
      fecha_vencimiento: vence,
      fecha_devolucion: null,
      condicion_devolucion: null,
    });
    s!.estado = "CUMPLIDA";
    e!.estado = "PRESTADO";
    if (reserva) reserva.estado = "CUMPLIDA";
    return;
  }
  if (resource === "prestamos") {
    const p = db.prestamos.find((x) => x.id === id);
    required(
      p && !p.fecha_devolucion && action === "devolver",
      "El préstamo debe estar activo.",
    );
    const fecha = text(input, "fecha_devolucion"),
      condition = text(input, "condicion_devolucion");
    required(
      fecha && Date.parse(fecha) >= Date.parse(p!.fecha_entrega),
      "La devolución no puede ser anterior a la entrega.",
      "fecha_devolucion",
    );
    required(
      ["APTO", "NO_APTO"].includes(condition),
      "Registrá la condición física.",
      "condicion_devolucion",
    );
    p!.fecha_devolucion = fecha;
    p!.condicion_devolucion = condition;
    const s = db.solicitudes.find((s) => s.id === p!.solicitud_id)!;
    const e = db.ejemplares.find((e) => e.id === s.ejemplar_id)!;
    e.condicion_fisica = condition;
    e.estado = "EN_REVISION";
    return;
  }
  if (resource === "reservas") {
    const r = db.reservas.find((x) => x.id === id);
    required(r, "Reserva inexistente.");
    if (action === "cancelar" || action === "expirar") {
      required(
        ["PENDIENTE", "LISTA_PARA_RETIRO"].includes(r!.estado),
        "La reserva ya está cerrada.",
      );
      if (action === "expirar")
        required(
          r!.estado === "LISTA_PARA_RETIRO" &&
            r!.fecha_limite_retiro &&
            Date.parse(r!.fecha_limite_retiro) < Date.now(),
          "Todavía no venció el plazo de retiro.",
        );
      const e = db.ejemplares.find((e) => e.id === r!.ejemplar_asignado_id);
      if (e) e.estado = "DISPONIBLE";
      db.solicitudes
        .filter((s) => s.reserva_id === id && s.estado !== "CUMPLIDA")
        .forEach((s) => {
          s.estado = "CANCELADA";
        });
      r!.estado = action === "cancelar" ? "CANCELADA" : "EXPIRADA";
      return;
    }
    required(
      action === "asignar-reserva" && r!.estado === "PENDIENTE",
      "La reserva debe estar pendiente.",
    );
    activeSocio(db, r!.socio_id);
    activeSede(db, r!.sede_retiro_id);
    const e = db.ejemplares.find((e) => e.id === num(input, "ejemplar_id"));
    required(
      e &&
        available(e, db) &&
        e.libro_id === r!.libro_id &&
        e.sede_actual_id === r!.sede_retiro_id,
      "Elegí un ejemplar disponible en la sede de retiro.",
    );
    const limit = text(input, "fecha_limite_retiro");
    required(
      limit && Date.parse(limit) > Date.now(),
      "Ingresá explícitamente una fecha límite futura.",
      "fecha_limite_retiro",
    );
    r!.ejemplar_asignado_id = e!.id;
    r!.fecha_limite_retiro = limit;
    r!.estado = "LISTA_PARA_RETIRO";
    e!.estado = "LISTO_PARA_ENTREGA";
    db.solicitudes.push({
      id: nextId(db.solicitudes),
      socio_id: r!.socio_id,
      libro_id: r!.libro_id,
      ejemplar_id: e!.id,
      sede_origen_id: e!.sede_propietaria_id,
      sede_destino_id: r!.sede_retiro_id,
      reserva_id: id,
      fecha_solicitud: instant(),
      tipo: "LOCAL",
      estado: "LISTA_PARA_ENTREGA",
    });
    return;
  }
  if (resource === "remitos") {
    const r = db.remitos.find((x) => x.id === id);
    required(r, "Remito inexistente.");
    if (action !== "cancelar" && action !== "recibir") {
      activeSede(db, r!.sede_origen_id);
      activeSede(db, r!.sede_destino_id);
    }
    const details = db.detalle_remitos.filter((d) => d.remito_id === id);
    if (action === "asignar") {
      required(
        r!.estado === "EN_PREPARACION",
        "Sólo se agregan ejemplares durante la preparación.",
      );
      const e = db.ejemplares.find((e) => e.id === num(input, "ejemplar_id"));
      required(
        e &&
          e.sede_propietaria_id === r!.sede_origen_id &&
          e.sede_actual_id === r!.sede_origen_id,
        "El ejemplar debe pertenecer al origen y estar allí.",
      );
      required(
        !db.detalle_remitos.some(
          (d) =>
            d.ejemplar_id === e!.id &&
            !["CANCELADO", "RECIBIDO"].includes(
              db.remitos.find((x) => x.id === d.remito_id)!.estado,
            ),
        ),
        "El ejemplar ya está incluido en un remito vigente.",
      );
      const s = db.solicitudes.find(
        (s) => s.ejemplar_id === e!.id && s.estado === "ASIGNADA",
      );
      required(
        available(e!, db) ||
          (s &&
            s.tipo === "INTERBIBLIOTECARIO" &&
            s.sede_destino_id === r!.sede_destino_id),
        "El ejemplar no está disponible para este trayecto.",
      );
      e!.estado = "ASIGNADO";
      db.detalle_remitos.push({
        id: nextId(db.detalle_remitos),
        remito_id: id,
        ejemplar_id: e!.id,
        solicitud_id: s?.id ?? null,
        condicion_salida: e!.condicion_fisica,
        condicion_recepcion: null,
      });
      return;
    }
    const transition: Partial<Record<Command, EstadoRemito>> = {
      empaquetar: "EMPAQUETADO",
      despachar: "DESPACHADO",
      "registrar-salida": "EN_TRANSITO",
      recibir: "RECIBIDO",
      cancelar: "CANCELADO",
    };
    const next = transition[action];
    required(next, "Operación inválida.");
    const allowed: Record<string, string[]> = {
      empaquetar: ["EN_PREPARACION"],
      despachar: ["EMPAQUETADO"],
      "registrar-salida": ["DESPACHADO"],
      recibir: ["EN_TRANSITO"],
      cancelar: ["EN_PREPARACION", "EMPAQUETADO"],
    };
    required(
      allowed[action]?.includes(r!.estado),
      "Esta transición no está permitida.",
    );
    if (action === "empaquetar" || action === "despachar")
      required(details.length, "El remito debe contener al menos un ejemplar.");
    if (action === "despachar") {
      for (const d of details) {
        const s = db.solicitudes.find((s) => s.id === d.solicitud_id);
        if (s) activeSocio(db, s.socio_id);
      }
      r!.fecha_despacho = instant();
      for (const d of details) {
        const e = db.ejemplares.find((e) => e.id === d.ejemplar_id)!;
        e.estado = "EN_TRANSITO";
        e.sede_actual_id = null;
        const s = db.solicitudes.find((s) => s.id === d.solicitud_id);
        if (s) s.estado = "EN_TRASLADO";
      }
    }
    if (action === "recibir") {
      const checked = input.verificados;
      required(
        Array.isArray(checked) &&
          details.every((d) => checked.includes(d.ejemplar_id)),
        "Verificá todos los ejemplares. La recepción parcial está pendiente de definición.",
      );
      required(
        text(input, "responsable"),
        "Indicá quién recibe el material.",
        "responsable",
      );
      r!.fecha_recepcion = instant();
      for (const d of details) {
        const e = db.ejemplares.find((e) => e.id === d.ejemplar_id)!;
        e.sede_actual_id = r!.sede_destino_id;
        d.condicion_recepcion = e.condicion_fisica;
        const s = db.solicitudes.find((s) => s.id === d.solicitud_id);
        if (s) {
          e.estado = "LISTO_PARA_ENTREGA";
          s.estado = "LISTA_PARA_ENTREGA";
        } else e.estado = "EN_REVISION";
      }
    }
    if (action === "cancelar")
      for (const d of details) {
        const e = db.ejemplares.find((e) => e.id === d.ejemplar_id)!;
        if (!d.solicitud_id) e.estado = "DISPONIBLE";
      }
    db.evento_remitos.push({
      id: nextId(db.evento_remitos),
      remito_id: id,
      fecha_hora: instant(),
      estado_anterior: r!.estado,
      estado_nuevo: next!,
      responsable: text(input, "responsable") || "Personal de biblioteca",
      observacion: text(input, "observacion"),
    });
    r!.estado = next!;
    return;
  }
  fail("Operación no disponible.");
}

export function createMockApi(
  storage: Pick<Storage, "getItem" | "setItem" | "removeItem"> = localStorage,
): LibraryApi {
  function read(): Database {
    const raw = storage.getItem(KEY);
    if (!raw) return copy(seed);
    try {
      const db = JSON.parse(raw) as Database;
      if (!Array.isArray(db.libros) || !Array.isArray(db.libro_autores))
        throw new Error();
      return db;
    } catch {
      throw new ApiError(
        "Los datos de demostración no se pudieron leer. Restablecelos desde Apariencia.",
      );
    }
  }
  function write(db: Database) {
    try {
      storage.setItem(KEY, JSON.stringify(db));
    } catch {
      fail(
        "El navegador no pudo guardar los cambios. Comprobá el espacio disponible.",
      );
    }
  }
  return {
    async snapshot() {
      return read();
    },
    async save(resource, data, id) {
      const db = read();
      const result = saveEntity(db, resource, data, id);
      write(db);
      return result;
    },
    async command(resource, id, action, input) {
      const db = read();
      applyCommand(db, resource, id, action, input);
      write(db);
    },
    async saveBookAuthors(bookId, names) {
      const db = read();
      required(
        db.libros.some((b) => b.id === bookId),
        "Libro inexistente.",
      );
      const ids = [...new Set(names.map((n) => n.trim()).filter(Boolean))].map(
        (nombre) => {
          let a = db.autores.find(
            (a) => a.nombre.toLowerCase() === nombre.toLowerCase(),
          );
          if (!a) {
            a = { id: nextId(db.autores), nombre };
            db.autores.push(a);
          }
          return a.id;
        },
      );
      db.libro_autores = db.libro_autores
        .filter((a) => a.libro_id !== bookId)
        .concat(ids.map((autor_id) => ({ libro_id: bookId, autor_id })));
      write(db);
    },
    async reset() {
      storage.removeItem(KEY);
    },
  };
}
