// Fuente: FigJam Modelos (clases + DER). Snake case coincide con Django.
// Las portadas son recursos de presentación; no se agregan al modelo Libro.
export interface Sede {
  id: number;
  nombre: string;
  direccion: string;
  contacto: string;
  horarios: string;
  estado: "ACTIVA" | "BAJA";
}
export interface Socio {
  id: number;
  numero_socio: string;
  documento: string;
  nombre: string;
  contacto: string;
  estado: "HABILITADO" | "INHABILITADO";
}
export interface Autor {
  id: number;
  nombre: string;
}
export interface Libro {
  id: number;
  isbn: string | null;
  titulo: string;
  editorial: string;
  edicion: string;
}
export interface LibroAutor {
  libro_id: number;
  autor_id: number;
}
export type EstadoEjemplar =
  | "DISPONIBLE"
  | "ASIGNADO"
  | "EN_TRANSITO"
  | "LISTO_PARA_ENTREGA"
  | "PRESTADO"
  | "EN_REVISION"
  | "BAJA";
export interface Ejemplar {
  id: number;
  codigo_inventario: string;
  libro_id: number;
  sede_propietaria_id: number;
  sede_actual_id: number | null;
  estado: EstadoEjemplar;
  condicion_fisica: string;
}
export type EstadoSolicitud =
  | "PENDIENTE"
  | "RECHAZADA"
  | "ASIGNADA"
  | "EN_TRASLADO"
  | "LISTA_PARA_ENTREGA"
  | "CUMPLIDA"
  | "CANCELADA";
export interface SolicitudPrestamo {
  id: number;
  socio_id: number;
  libro_id: number;
  ejemplar_id: number | null;
  sede_origen_id: number;
  sede_destino_id: number;
  reserva_id: number | null;
  fecha_solicitud: string;
  tipo: "LOCAL" | "INTERBIBLIOTECARIO";
  estado: EstadoSolicitud;
}
export interface Prestamo {
  id: number;
  solicitud_id: number;
  fecha_entrega: string;
  fecha_vencimiento: string;
  fecha_devolucion: string | null;
  condicion_devolucion: string | null;
}
export type EstadoReserva =
  "PENDIENTE" | "LISTA_PARA_RETIRO" | "CUMPLIDA" | "CANCELADA" | "EXPIRADA";
export interface Reserva {
  id: number;
  socio_id: number;
  libro_id: number;
  sede_retiro_id: number;
  ejemplar_asignado_id: number | null;
  fecha_reserva: string;
  fecha_limite_retiro: string | null;
  estado: EstadoReserva;
}
export type EstadoRemito =
  | "EN_PREPARACION"
  | "EMPAQUETADO"
  | "DESPACHADO"
  | "EN_TRANSITO"
  | "RECIBIDO"
  | "CANCELADO";
export interface Remito {
  id: number;
  numero: string;
  sede_origen_id: number;
  sede_destino_id: number;
  estado: EstadoRemito;
  fecha_creacion: string;
  fecha_despacho: string | null;
  fecha_recepcion: string | null;
}
export interface DetalleRemito {
  id: number;
  remito_id: number;
  ejemplar_id: number;
  solicitud_id: number | null;
  condicion_salida: string;
  condicion_recepcion: string | null;
}
export interface EventoRemito {
  id: number;
  remito_id: number;
  fecha_hora: string;
  estado_anterior: EstadoRemito | null;
  estado_nuevo: EstadoRemito;
  responsable: string;
  observacion: string;
}
export interface Database {
  sedes: Sede[];
  socios: Socio[];
  autores: Autor[];
  libros: Libro[];
  libro_autores: LibroAutor[];
  ejemplares: Ejemplar[];
  solicitudes: SolicitudPrestamo[];
  prestamos: Prestamo[];
  reservas: Reserva[];
  remitos: Remito[];
  detalle_remitos: DetalleRemito[];
  evento_remitos: EventoRemito[];
}
export type Resource = Exclude<keyof Database, "libro_autores">;
export type Entity<K extends Resource> = Database[K][number];
export type NewEntity<K extends Resource> = Omit<Entity<K>, "id">;
