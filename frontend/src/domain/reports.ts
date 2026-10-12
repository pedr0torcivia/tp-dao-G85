import type { Database } from "./models";
import {
  available,
  bookName,
  code,
  daysLate,
  sedeName,
  socioName,
} from "./selectors";

export type ReportType =
  "vencidos" | "demanda" | "movimientos" | "disponibilidad";
export interface ReportFilter {
  desde: string;
  hasta: string;
  sede: number | null;
}
export interface ReportResult {
  headers: string[];
  rows: (string | number)[][];
  summary: string;
  rule: string;
}
export function buildReport(
  type: ReportType,
  db: Database,
  filter: ReportFilter,
): ReportResult {
  const inRange = (date: string | null) =>
    !!date &&
    Date.parse(date) >= Date.parse(`${filter.desde}T00:00:00-03:00`) &&
    Date.parse(date) <= Date.parse(`${filter.hasta}T23:59:59.999-03:00`);
  if (type === "vencidos") {
    const end = Date.parse(`${filter.hasta}T23:59:59.999-03:00`);
    const loans = db.prestamos
      .filter(
        (p) =>
          Date.parse(p.fecha_entrega) <= end &&
          (!p.fecha_devolucion || Date.parse(p.fecha_devolucion) > end),
      )
      .map((p) => {
        const s = db.solicitudes.find((s) => s.id === p.solicitud_id)!;
        return {
          p,
          s,
          days: daysLate({ ...p, fecha_devolucion: null }, filter.hasta),
        };
      })
      .filter(
        ({ s, p }) =>
          Date.parse(p.fecha_vencimiento) < end &&
          (!filter.sede || s.sede_destino_id === filter.sede),
      );
    return {
      headers: [
        "Préstamo",
        "Socio y libro",
        "Sede de entrega",
        "Días de atraso",
      ],
      rows: loans
        .sort((a, b) => a.s.sede_destino_id - b.s.sede_destino_id)
        .map(({ p, s, days }) => [
          code("PRE", p.id),
          `${socioName(s.socio_id, db)} · ${bookName(s.libro_id, db)}`,
          sedeName(s.sede_destino_id, db),
          days,
        ]),
      summary: `${loans.length} préstamos vencidos`,
      rule: "Agrupación por sede de entrega. Atraso entre vencimiento y fecha de corte; incluye préstamos abiertos en ese corte.",
    };
  }
  if (type === "demanda") {
    const groups = new Map<
      string,
      { libro: number; sede: number; count: number }
    >();
    for (const s of db.solicitudes.filter(
      (s) =>
        s.tipo === "INTERBIBLIOTECARIO" &&
        !["RECHAZADA", "CANCELADA"].includes(s.estado) &&
        inRange(s.fecha_solicitud) &&
        (!filter.sede || s.sede_destino_id === filter.sede),
    )) {
      const key = `${s.libro_id}:${s.sede_destino_id}`;
      const g = groups.get(key) ?? {
        libro: s.libro_id,
        sede: s.sede_destino_id,
        count: 0,
      };
      g.count++;
      groups.set(key, g);
    }
    const groupsList = [...groups.values()].sort((a, b) => b.count - a.count);
    return {
      headers: ["Libro", "Solicitudes", "Sede solicitante"],
      rows: groupsList.map((g) => [
        bookName(g.libro, db),
        g.count,
        sedeName(g.sede, db),
      ]),
      summary: `${groupsList.reduce((t, g) => t + g.count, 0)} solicitudes válidas`,
      rule: "Por fecha de solicitud y sede solicitante (destino). Se excluyen rechazadas y canceladas.",
    };
  }
  if (type === "movimientos") {
    const groups = new Map<
      string,
      {
        origen: number;
        destino: number;
        dispatched: number;
        received: number;
        totalDays: number;
      }
    >();
    for (const r of db.remitos.filter(
      (r) =>
        inRange(r.fecha_despacho) &&
        (!filter.sede ||
          r.sede_origen_id === filter.sede ||
          r.sede_destino_id === filter.sede),
    )) {
      const key = `${r.sede_origen_id}:${r.sede_destino_id}`;
      const g = groups.get(key) ?? {
        origen: r.sede_origen_id,
        destino: r.sede_destino_id,
        dispatched: 0,
        received: 0,
        totalDays: 0,
      };
      g.dispatched++;
      if (r.fecha_recepcion) {
        g.received++;
        g.totalDays +=
          (Date.parse(r.fecha_recepcion) - Date.parse(r.fecha_despacho!)) /
          86400000;
      }
      groups.set(key, g);
    }
    const rows = [...groups.values()];
    return {
      headers: ["Trayecto", "Despachados", "Recibidos", "Tránsito medio"],
      rows: rows.map((g) => [
        `${sedeName(g.origen, db)} → ${sedeName(g.destino, db)}`,
        g.dispatched,
        g.received,
        g.received
          ? `${(g.totalDays / g.received).toLocaleString("es-AR", { maximumFractionDigits: 2 })} días`
          : "Sin recepciones",
      ]),
      summary: `${rows.reduce((t, g) => t + g.dispatched, 0)} envíos despachados`,
      rule: "Por fecha de despacho. Tránsito medio entre despacho y recepción; excluye remitos sin recibir del promedio.",
    };
  }
  const groups = new Map<
    string,
    {
      libro: number;
      sede: number;
      total: number;
      disponibles: number;
      states: Record<string, number>;
    }
  >();
  for (const e of db.ejemplares.filter(
    (e) => !filter.sede || e.sede_propietaria_id === filter.sede,
  )) {
    const key = `${e.libro_id}:${e.sede_propietaria_id}`;
    const g = groups.get(key) ?? {
      libro: e.libro_id,
      sede: e.sede_propietaria_id,
      total: 0,
      disponibles: 0,
      states: {},
    };
    g.total++;
    if (available(e, db)) g.disponibles++;
    g.states[e.estado] = (g.states[e.estado] ?? 0) + 1;
    groups.set(key, g);
  }
  const rows = [...groups.values()];
  return {
    headers: [
      "Libro y sede propietaria",
      "Total",
      "Disponibles",
      "Proporción",
      "Por estado",
    ],
    rows: rows.map((g) => [
      `${bookName(g.libro, db)} · ${sedeName(g.sede, db)}`,
      g.total,
      g.disponibles,
      `${Math.round((g.disponibles / g.total) * 100)} %`,
      Object.entries(g.states)
        .map(([state, n]) => `${state}: ${n}`)
        .join(" · "),
    ]),
    summary: `${rows.reduce((t, g) => t + g.disponibles, 0)} de ${rows.reduce((t, g) => t + g.total, 0)} ejemplares disponibles`,
    rule: "Corte actual por sede propietaria y estado. Prestados, asignados, en revisión o tránsito no cuentan como disponibles.",
  };
}
