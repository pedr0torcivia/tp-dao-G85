import { ApiError, resourcePaths, type LibraryApi } from "./contracts";
import type { ReportFilter, ReportResult, ReportType } from "../domain/reports";
import type { Database, Entity, Resource } from "../domain/models";
import { statusLabels } from "../domain/selectors";

const base = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");
export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const csrf = document.cookie
    .split("; ")
    .find((c) => c.startsWith("csrftoken="))
    ?.split("=")[1];
  let response: Response;
  try {
    response = await fetch(
      path.startsWith("/")
        ? new URL(path, new URL(base, location.origin).origin).href
        : `${base}/${path}`,
      {
        ...options,
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(csrf ? { "X-CSRFToken": decodeURIComponent(csrf) } : {}),
          ...options.headers,
        },
      },
    );
  } catch {
    throw new ApiError(
      "No pudimos conectar con la API. Comprobá que el backend esté disponible.",
      {},
      0,
    );
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    if (
      body?.error?.code === "not_authenticated" &&
      typeof window !== "undefined"
    ) {
      window.dispatchEvent(new Event("entrelibros:sesion-vencida"));
    }
    const detail = body?.error?.detail ?? body;
    throw new ApiError(
      typeof detail === "string"
        ? detail
        : Object.values(detail ?? {})
            .flat()
            .filter((v) => typeof v === "string")
            .join(" ") || "No pudimos completar la operación.",
      typeof detail === "object" && detail ? detail : {},
      response.status,
    );
  }
  return body as T;
}
async function list<K extends Resource>(resource: K): Promise<Entity<K>[]> {
  let next: string | null = `${resourcePaths[resource]}/`;
  const all: Entity<K>[] = [];
  while (next) {
    const page: Entity<K>[] | { results: Entity<K>[]; next: string | null } =
      await request(next);
    if (Array.isArray(page)) return page;
    all.push(...page.results);
    // DRF entrega next absoluta; conservamos ruta/query y mismo origen.
    next = page.next
      ? new URL(page.next, location.origin).pathname +
        new URL(page.next, location.origin).search
      : null;
  }
  return all;
}
export const httpApi: LibraryApi = {
  async snapshot() {
    const resources = Object.keys(resourcePaths) as Resource[];
    const values = await Promise.all(resources.map((r) => list(r)));
    const db = Object.fromEntries(
      resources.map((r, i) => [r, values[i]]),
    ) as unknown as Database;
    return db;
  },
  save: (resource, data, id) =>
    request(`${resourcePaths[resource]}/${id === undefined ? "" : `${id}/`}`, {
      method: id === undefined ? "POST" : "PATCH",
      body: JSON.stringify(data),
    }),
  command: (resource, id, action, input = {}) =>
    request(`${resourcePaths[resource]}/${id}/${action}/`, {
      method: "POST",
      body: JSON.stringify(input),
    }),
  report: (type, filter) => report(type, filter),
  prepararRetorno: (ejemplarId) =>
    request("remitos/preparar-retorno/", {
      method: "POST",
      body: JSON.stringify({ ejemplar_id: ejemplarId }),
    }),
};

const pesos = (n: number) =>
  new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 0,
  }).format(n);
const fecha = (iso: string) =>
  new Intl.DateTimeFormat("es-AR", {
    dateStyle: "medium",
    timeZone: "America/Argentina/Buenos_Aires",
  }).format(new Date(iso));
interface Base {
  resumen: string;
  criterio: string;
}

async function report(
  type: ReportType,
  filter: ReportFilter,
): Promise<ReportResult> {
  const query = new URLSearchParams({
    desde: filter.desde,
    hasta: filter.hasta,
  });
  if (filter.sede) query.set("sede", String(filter.sede));

  if (type === "vencidos") {
    const data = await request<{
      cantidad: number;
      multas_total: number;
      multa_diaria: number;
      sedes: {
        sede: string;
        prestamos: {
          prestamo_id: number;
          socio: string;
          libro: string;
          fecha_vencimiento: string;
          dias_atraso: number;
          multa: number;
        }[];
      }[];
    }>(`prestamos-vencidos/?${query}`);
    return {
      headers: ["Préstamo", "Socio · libro", "Sede", "Venció", "Atraso", "Multa"],
      rows: data.sedes.flatMap((s) =>
        s.prestamos.map((p) => [
          `PRE-${String(p.prestamo_id).padStart(4, "0")}`,
          `${p.socio} · ${p.libro}`,
          s.sede,
          fecha(p.fecha_vencimiento),
          `${p.dias_atraso} días`,
          pesos(p.multa),
        ]),
      ),
      summary: `${data.cantidad} préstamos vencidos · ${pesos(data.multas_total)} en multas`,
      rule: `Préstamos entregados en el período que al cierre de Hasta seguían sin devolver y con el vencimiento cumplido. Multa: ${pesos(data.multa_diaria)} por día de atraso.`,
      kpis: [
        {
          label: "Préstamos vencidos",
          value: String(data.cantidad),
          tone: data.cantidad ? "bad" : "ok",
        },
        {
          label: "Multas acumuladas",
          value: pesos(data.multas_total),
          tone: "warn",
        },
        { label: "Multa diaria", value: pesos(data.multa_diaria), tone: "info" },
      ],
    };
  }
  if (type === "activos") {
    const data = await request<
      Base & {
        filas: {
          tipo: "PRESTAMO" | "TRANSITO";
          referencia: string;
          detalle: string;
          ejemplar: string;
          ubicacion: string;
          desde: string;
          situacion: string;
        }[];
      }
    >(`reportes/activos/?${query}`);
    const prestamos = data.filas.filter((f) => f.tipo === "PRESTAMO").length;
    return {
      headers: ["Tipo", "Referencia", "Material", "Ejemplar", "Dónde", "Desde", "Situación"],
      rows: data.filas.map((f) => [
        f.tipo === "PRESTAMO" ? "Préstamo" : "En tránsito",
        f.referencia,
        f.detalle,
        f.ejemplar,
        f.ubicacion,
        fecha(f.desde),
        f.situacion,
      ]),
      summary: data.resumen,
      rule: data.criterio,
      kpis: [
        { label: "Préstamos activos", value: String(prestamos), tone: "info" },
        {
          label: "Ejemplares en tránsito",
          value: String(data.filas.length - prestamos),
          tone: "warn",
        },
      ],
    };
  }
  if (type === "logistica") {
    const data = await request<
      Base & {
        totales: Record<string, number | null>;
        filas: {
          origen: string;
          destino: string;
          despachados: number;
          exitosos: number;
          con_incidencias: number;
          en_transito: number;
          danados: number;
          extraviados: number;
          tasa_exito: number | null;
        }[];
      }
    >(`reportes/logistica/?${query}`);
    const t = data.totales;
    const tasa = t.tasa_exito ?? null;
    return {
      headers: [
        "Trayecto",
        "Despachados",
        "Exitosos",
        "Con incidencias",
        "En tránsito",
        "Dañados",
        "Extraviados",
        "Tasa de éxito",
      ],
      rows: data.filas.map((f) => [
        `${f.origen} → ${f.destino}`,
        f.despachados,
        f.exitosos,
        f.con_incidencias,
        f.en_transito,
        f.danados,
        f.extraviados,
        f.tasa_exito === null ? "Sin recepciones" : `${f.tasa_exito} %`,
      ]),
      summary: data.resumen,
      rule: data.criterio,
      kpis: [
        { label: "Envíos despachados", value: String(t.despachados ?? 0), tone: "info" },
        {
          label: "Tasa de éxito",
          value: tasa === null ? "—" : `${tasa} %`,
          tone: tasa === null || tasa >= 90 ? "ok" : "warn",
        },
        {
          label: "Con incidencias",
          value: String(t.con_incidencias ?? 0),
          tone: t.con_incidencias ? "bad" : "ok",
        },
      ],
    };
  }
  if (type === "demanda") {
    const data = await request<
      Base & {
        filas: { libro: string; cantidad: number; sede_destino: string }[];
      }
    >(`reportes/demanda-interbibliotecaria/?${query}`);
    return {
      headers: ["#", "Libro", "Solicitudes", "Sede solicitante"],
      rows: data.filas.map((f, i) => [i + 1, f.libro, f.cantidad, f.sede_destino]),
      summary: data.resumen,
      rule: data.criterio,
    };
  }
  if (type === "movimientos") {
    const [data, sedes] = await Promise.all([
      request<
        Base & {
          filas: {
            sede_origen_id: number;
            sede_destino_id: number;
            despachados: number;
            recibidos: number;
            dias_transito_promedio: number | null;
          }[];
        }
      >(`reportes/movimientos/?${query}`),
      list("sedes"),
    ]);
    const name = (id: number) =>
      sedes.find((s) => s.id === id)?.nombre ?? String(id);
    return {
      headers: ["Trayecto", "Despachados", "Recibidos", "Tránsito medio"],
      rows: data.filas.map((f) => [
        `${name(f.sede_origen_id)} → ${name(f.sede_destino_id)}`,
        f.despachados,
        f.recibidos,
        f.dias_transito_promedio === null
          ? "Sin recepciones"
          : `${f.dias_transito_promedio} días`,
      ]),
      summary: data.resumen,
      rule: data.criterio,
    };
  }
  if (type === "operaciones") {
    const data = await request<
      Base & {
        filas: {
          fecha: string;
          entidad: string;
          registro_id: number;
          accion: string;
          usuario: string;
          descripcion: string;
        }[];
      }
    >(`reportes/operaciones/?${query}`);
    return {
      headers: ["Fecha", "Entidad", "Registro", "Acción", "Usuario", "Cambios"],
      rows: data.filas.map((f) => [
        new Date(f.fecha).toLocaleString("es-AR"),
        f.entidad,
        f.registro_id,
        f.accion,
        f.usuario,
        f.descripcion,
      ]),
      summary: data.resumen,
      rule: data.criterio,
    };
  }
  const data = await request<
    Base & {
      filas: {
        libro: string;
        sede_propietaria: string;
        total: number;
        disponibles: number;
        proporcion_porcentaje: number;
        por_estado: Record<string, number>;
      }[];
    }
  >(`reportes/disponibilidad/?${query}`);
  return {
    headers: ["Libro", "Sede propietaria", "Total", "Disponibles", "Proporción", "Por estado"],
    rows: data.filas.map((f) => [
      f.libro,
      f.sede_propietaria,
      f.total,
      f.disponibles,
      `${f.proporcion_porcentaje} %`,
      Object.entries(f.por_estado)
        .map(([k, v]) => `${statusLabels[k] ?? k}: ${v}`)
        .join(" · "),
    ]),
    summary: data.resumen,
    rule: data.criterio,
  };
}
