import type { Database, Ejemplar, Libro, Prestamo } from "./models";

export const localDay = (date: Date) =>
  new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Argentina/Buenos_Aires",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
export const today = () => localDay(new Date());
export const isOverdue = (p: Prestamo, at = new Date()) =>
  !p.fecha_devolucion && Date.parse(p.fecha_vencimiento) < at.getTime();
export const dateLabel = (value: string | null) =>
  value
    ? new Intl.DateTimeFormat("es-AR", {
        dateStyle: "medium",
        timeZone: "America/Argentina/Buenos_Aires",
      }).format(
        new Date(value.length === 10 ? `${value}T12:00:00-03:00` : value),
      )
    : "—";
export const daysLate = (p: Prestamo, cut = today()) =>
  p.fecha_devolucion
    ? 0
    : Math.max(
        0,
        Math.floor(
          (Date.parse(`${cut}T12:00:00-03:00`) -
            Date.parse(
              `${localDay(new Date(p.fecha_vencimiento))}T12:00:00-03:00`,
            )) /
            86400000,
        ),
      );
export const available = (e: Ejemplar, db: Database) =>
  e.estado === "DISPONIBLE" &&
  e.condicion_fisica === "APTO" &&
  e.sede_actual_id === e.sede_propietaria_id &&
  db.sedes.some((s) => s.id === e.sede_propietaria_id && s.estado === "ACTIVA");
export const authorNames = (book: Libro, db: Database) =>
  db.libro_autores
    .filter((a) => a.libro_id === book.id)
    .map((a) => db.autores.find((x) => x.id === a.autor_id)?.nombre)
    .filter(Boolean)
    .join(", ");
export const sedeName = (id: number | null, db: Database) =>
  id === null
    ? "En tránsito"
    : (db.sedes.find((s) => s.id === id)?.nombre ?? "Sede desconocida");
export const socioName = (id: number, db: Database) =>
  db.socios.find((s) => s.id === id)?.nombre ?? "Socio desconocido";
export const bookName = (id: number, db: Database) =>
  db.libros.find((s) => s.id === id)?.titulo ?? "Libro desconocido";
export const code = (prefix: string, id: number) =>
  `${prefix}-${String(id).padStart(4, "0")}`;
export const statusLabels: Record<string, string> = {
  ACTIVA: "Activa",
  BAJA: "De baja",
  HABILITADO: "Habilitado",
  INHABILITADO: "Inhabilitado",
  DISPONIBLE: "Disponible",
  ASIGNADO: "Asignado",
  EN_TRANSITO: "En tránsito",
  LISTO_PARA_ENTREGA: "Listo para entrega",
  PRESTADO: "Prestado",
  EN_REVISION: "En revisión",
  PENDIENTE: "Pendiente",
  RECHAZADA: "Rechazada",
  ASIGNADA: "Asignada",
  EN_TRASLADO: "En traslado",
  LISTA_PARA_ENTREGA: "Lista para entrega",
  CUMPLIDA: "Cumplida",
  CANCELADA: "Cancelada",
  EXPIRADA: "Expirada",
  EN_PREPARACION: "En preparación",
  EMPAQUETADO: "Empaquetado",
  DESPACHADO: "Despachado",
  RECIBIDO: "Recibido",
  CANCELADO: "Cancelado",
  LOCAL: "Local",
  INTERBIBLIOTECARIO: "Interbibliotecario",
  APTO: "Apto para préstamo",
  NO_APTO: "No apto para préstamo",
  ACTIVO: "Activo",
  DEVUELTO: "Devuelto",
  VENCIDO: "Vencido",
  LISTA_PARA_RETIRO: "Lista para retiro",
};
