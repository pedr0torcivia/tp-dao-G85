import type { Database, Entity, NewEntity, Resource } from "../domain/models";

export class ApiError extends Error {
  constructor(
    message: string,
    public fields: Record<string, string[]> = {},
    public status = 400,
  ) {
    super(message);
  }
}
export type Command =
  | "habilitar"
  | "inhabilitar"
  | "dar-de-baja"
  | "reactivar"
  | "asignar"
  | "preparar-entrega"
  | "entregar"
  | "cancelar"
  | "devolver"
  | "empaquetar"
  | "despachar"
  | "registrar-salida"
  | "recibir"
  | "asignar-reserva"
  | "expirar"
  | "aprobar-disponibilidad";
export type CommandInput = Record<string, string | number | number[] | null>;

export interface LibraryApi {
  snapshot(): Promise<Database>;
  save<K extends Resource>(
    resource: K,
    data: NewEntity<K>,
    id?: number,
  ): Promise<Entity<K>>;
  command(
    resource: Resource,
    id: number,
    action: Command,
    input?: CommandInput,
  ): Promise<void>;
  saveBookAuthors(bookId: number, authorNames: string[]): Promise<void>;
  reset(): Promise<void>;
}

// Sólo /sedes está implementado en Django. Las demás rutas son propuestas
// de integración: se confirmarán al implementar cada módulo del backend.
export const resourcePaths: Record<Resource, string> = {
  sedes: "sedes",
  socios: "socios",
  libros: "libros",
  autores: "autores",
  ejemplares: "ejemplares",
  solicitudes: "solicitudes",
  prestamos: "prestamos",
  reservas: "reservas",
  remitos: "remitos",
  detalle_remitos: "detalles-remito",
  evento_remitos: "eventos-remito",
};
