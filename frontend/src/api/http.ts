import { ApiError, resourcePaths, type LibraryApi } from "./contracts";
import type { Database, Entity, Resource } from "../domain/models";

const base = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const csrf = document.cookie
    .split("; ")
    .find((c) => c.startsWith("csrftoken="))
    ?.split("=")[1];
  let response: Response;
  try {
    response = await fetch(
      path.startsWith(base + "/") ? path : `${base}/${path}`,
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
    const detail = body?.error?.detail ?? body;
    throw new ApiError(
      typeof detail?.detail === "string"
        ? detail.detail
        : "No pudimos completar la operación.",
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
    db.libro_autores = await request("libro-autores/");
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
  saveBookAuthors: (id, autores) =>
    request(`libros/${id}/autores/`, {
      method: "PUT",
      body: JSON.stringify({ autores }),
    }),
  async reset() {
    throw new ApiError(
      "Restablecer ejemplos sólo está disponible en modo demostración.",
    );
  },
};
