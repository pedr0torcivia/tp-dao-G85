import type { Database, Resource } from "../domain/models";
import { statusLabels, today } from "../domain/selectors";

export interface FormField {
  key: string;
  label: string;
  type?: "text" | "textarea" | "select" | "datetime-local";
  required?: boolean;
  options?: [string, string][];
  hint?: string;
  placeholder?: string;
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
      "El fondo de toda la red. Abrí un libro para ver en qué sedes hay copias disponibles y pedirlo.",
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
    description:
      "Cada pedido de un socio, desde que se registra hasta que se entrega. Abrí una para ver en qué paso está y qué sigue.",
    create: "Nueva solicitud",
    search: "Buscar por solicitud, socio o libro",
  },
  prestamos: {
    title: "Préstamos",
    singular: "préstamo",
    description: "Libros en manos de socios: vencimientos, atrasos y multas.",
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
    description:
      "Paquetes de ejemplares que viajan entre sedes. Se arman solos al preparar solicitudes interbibliotecarias o retornos.",
    create: "Nuevo remito",
    search: "Buscar remito, sede o ejemplar",
  },
};
export const pathOf = (resource: Resource) =>
  resource === "libros" ? "catalogo" : resource;
export const tipoSolicitud = (
  sedeOrigenId: unknown,
  sedeDestinoId: unknown,
): "LOCAL" | "INTERBIBLIOTECARIO" =>
  sedeOrigenId === sedeDestinoId ? "LOCAL" : "INTERBIBLIOTECARIO";
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
        field("autor", "Autor o autores"),
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
      ];
    case "reservas":
      return [
        select("socio_id", "Socio", socios),
        select("libro_id", "Libro", libros),
        select("sede_retiro_id", "Lo retira en", sedes),
      ];
    case "remitos":
      return [
        select("sede_origen_id", "Sale de", sedes),
        select("sede_destino_id", "Va hacia", sedes),
        {
          ...field("numero", "Número de remito", "text", false),
          hint: "Si lo dejás vacío se genera automáticamente (REM-año-número).",
          placeholder: "Automático",
        },
      ];
    default:
      return [];
  }
}
export const defaultDateTime = () => `${today()}T12:00`;
export const stateOptions = (values: string[]): [string, string][] =>
  values.map((v) => [v, statusLabels[v] ?? v]);
