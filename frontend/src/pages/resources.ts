import type { Database, Resource } from "../domain/models";
import { available, statusLabels, today } from "../domain/selectors";

export interface FormField {
  key: string;
  label: string;
  type?: "text" | "textarea" | "select" | "datetime-local";
  required?: boolean;
  options?: [string, string][];
}
export interface ResourceConfig {
  title: string;
  singular: string;
  description: string;
  create: string;
  search: string;
}
export const config: Partial<Record<Resource, ResourceConfig>> = {
  socios: {
    title: "Socios",
    singular: "socio",
    description:
      "Administrá los datos y la habilitación de los socios de la red.",
    create: "Nuevo socio",
    search: "Buscar por nombre, documento o número de socio",
  },
  sedes: {
    title: "Sedes",
    singular: "sede",
    description: "Consultá los datos y el estado de las bibliotecas de la red.",
    create: "Nueva sede",
    search: "Buscar por sede, dirección o contacto",
  },
  libros: {
    title: "Catálogo",
    singular: "libro",
    description:
      "Encontrá tu próxima lectura y consultá dónde está disponible.",
    create: "Nuevo libro",
    search: "Buscar por título, autor o ISBN",
  },
  ejemplares: {
    title: "Ejemplares",
    singular: "ejemplar",
    description:
      "Cada copia física conserva su identificación y sede propietaria.",
    create: "Nuevo ejemplar",
    search: "Buscar por identificador o sede",
  },
  solicitudes: {
    title: "Solicitudes",
    singular: "solicitud",
    description: "Seguí cada solicitud desde su registro hasta la entrega.",
    create: "Nueva solicitud",
    search: "Buscar por solicitud, socio o libro",
  },
  prestamos: {
    title: "Préstamos",
    singular: "préstamo",
    description: "Consultá las entregas, los vencimientos y las devoluciones.",
    create: "Registrar devolución",
    search: "Buscar préstamo, socio o ejemplar",
  },
  reservas: {
    title: "Reservas",
    singular: "reserva",
    description:
      "Consultá los libros esperados y las asignaciones para retiro.",
    create: "Nueva reserva",
    search: "Buscar reserva, socio o libro",
  },
  remitos: {
    title: "Remitos",
    singular: "remito",
    description: "Prepará y seguí el traslado de ejemplares entre sedes.",
    create: "Nuevo remito",
    search: "Buscar remito, sede o ejemplar",
  },
};
export const pathOf = (resource: Resource) =>
  resource === "libros" ? "catalogo" : resource;
const field = (
  key: string,
  label: string,
  type: FormField["type"] = "text",
  required = true,
): FormField => ({ key, label, type, required });
export function fieldsFor(resource: Resource, db: Database): FormField[] {
  const sedes: [string, string][] = db.sedes
    .filter((s) => s.estado === "ACTIVA")
    .map((s) => [String(s.id), s.nombre]);
  const libros: [string, string][] = db.libros.map((b) => [
    String(b.id),
    b.titulo,
  ]);
  const socios: [string, string][] = db.socios
    .filter((s) => s.estado === "HABILITADO")
    .map((s) => [String(s.id), `${s.nombre} · ${s.documento}`]);
  const select = (
    key: string,
    label: string,
    options: [string, string][],
    required = true,
  ): FormField => ({ key, label, type: "select", required, options });
  switch (resource) {
    case "socios":
      return [
        field("numero_socio", "Número de socio"),
        field("documento", "Documento"),
        field("nombre", "Nombre completo"),
        field("contacto", "Contacto"),
      ];
    case "sedes":
      return [
        field("nombre", "Nombre"),
        field("direccion", "Dirección"),
        field("contacto", "Contacto"),
        field("horarios", "Horarios", "textarea"),
      ];
    case "libros":
      return [
        field("titulo", "Título"),
        field("autores", "Autores (separados por coma)"),
        field("isbn", "ISBN", "text", false),
        field("editorial", "Editorial"),
        field("edicion", "Edición"),
      ];
    case "ejemplares":
      return [
        field("codigo_inventario", "Código de inventario"),
        select("libro_id", "Libro", libros),
        select("sede_propietaria_id", "Sede propietaria", sedes),
        select("condicion_fisica", "Condición física", [
          ["APTO", "Apto para préstamo"],
          ["NO_APTO", "No apto para préstamo"],
        ]),
      ];
    case "solicitudes":
      return [
        select("socio_id", "Socio", socios),
        select("libro_id", "Libro", libros),
        select("sede_origen_id", "Sede de origen", sedes),
        select("sede_destino_id", "Sede de retiro", sedes),
        select(
          "ejemplar_id",
          "Ejemplar (opcional hasta asignación)",
          db.ejemplares
            .filter((e) => available(e, db))
            .map((e) => [
              String(e.id),
              `${e.codigo_inventario} · ${db.libros.find((b) => b.id === e.libro_id)?.titulo}`,
            ]),
          false,
        ),
      ];
    case "reservas":
      return [
        select("socio_id", "Socio", socios),
        select("libro_id", "Libro", libros),
        select("sede_retiro_id", "Sede de retiro", sedes),
      ];
    case "remitos":
      return [
        field("numero", "Número de remito"),
        select("sede_origen_id", "Sede de origen", sedes),
        select("sede_destino_id", "Sede de destino", sedes),
      ];
    default:
      return [];
  }
}
export const defaultDateTime = () => `${today()}T12:00`;
export const stateOptions = (values: string[]): [string, string][] =>
  values.map((v) => [v, statusLabels[v] ?? v]);
