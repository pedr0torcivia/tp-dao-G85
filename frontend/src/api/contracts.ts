import type { Database, Entity, NewEntity, Resource } from "../domain/models";
import type { ReportFilter, ReportResult, ReportType } from "../domain/reports";

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
  | "rechazar"
  | "devolver"
  | "empaquetar"
  | "reabrir"
  | "quitar"
  | "despachar"
  | "recibir"
  | "asignar-reserva"
  | "expirar"
  | "aprobar-disponibilidad";
export type CommandInput = Record<
  string,
  string | number | number[] | null | Record<string, string>
>;

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
  report(type: ReportType, filter: ReportFilter): Promise<ReportResult>;
  /** Arma (o completa) el remito que devuelve un ejemplar a su sede propietaria. */
  prepararRetorno(ejemplarId: number): Promise<{ id: number }>;
  /** Elimina un registro. El backend valida si está permitido. */
  eliminar(resource: Resource, id: number): Promise<void>;
  /** Sube (o reemplaza) la portada de un libro. */
  subirPortada(libroId: number, archivo: File): Promise<void>;
}

export const resourcePaths: Record<Resource, string> = {
  sedes: "sedes",
  socios: "socios",
  libros: "libros",
  ejemplares: "ejemplares",
  solicitudes: "solicitudes",
  prestamos: "prestamos",
  reservas: "reservas",
  remitos: "remitos",
  detalle_remitos: "detalles-remito",
  evento_remitos: "eventos-remito",
};
