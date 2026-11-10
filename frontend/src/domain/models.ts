// Espejo de los serializers de Django (snake_case). Los campos marcados como
// "calculado" los resuelve el backend: el frontend no reimplementa reglas.
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
export interface Libro {
  id: number;
  isbn: string | null;
  titulo: string;
  autor: string;
  editorial: string;
  edicion: string;
  /** calculado · URL de la portada cargada (null si no tiene) */
  portada_url?: string | null;
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
  fecha_alta?: string;
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
  /** calculado · clase Strategy que tramita la solicitud */
  estrategia: string;
  /** calculado · qué hace "preparar entrega" con esta estrategia */
  estrategia_descripcion: string;
  /** calculado · estados que recorre la solicitud en su circuito */
  recorrido: EstadoSolicitud[];
  /** calculado · operaciones disponibles ahora */
  acciones: string[];
  /** calculado · último remito que transportó el ejemplar */
  remito_id: number | null;
}
export interface Prestamo {
  id: number;
  solicitud_id: number;
  fecha_entrega: string;
  fecha_vencimiento: string;
  fecha_devolucion: string | null;
  condicion_devolucion: string | null;
  /** calculado · ACTIVO, VENCIDO o DEVUELTO */
  estado?: "ACTIVO" | "VENCIDO" | "DEVUELTO";
  /** calculado · días de atraso (al día de hoy o a la devolución) */
  dias_atraso: number;
  /** calculado · multa acumulada en pesos */
  multa: number;
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
  | "EN_TRANSITO"
  | "RECIBIDO"
  | "RECIBIDO_CON_INCIDENCIAS"
  | "CANCELADO";
export type OperacionRemito =
  | "agregar"
  | "quitar"
  | "empaquetar"
  | "reabrir"
  | "despachar"
  | "recibir"
  | "cancelar";
export type ResultadoRecepcion = "CONFORME" | "DANADO" | "EXTRAVIADO";
export interface Remito {
  id: number;
  numero: string;
  sede_origen_id: number;
  sede_destino_id: number;
  estado: EstadoRemito;
  /** calculado · clase State activa (patrón State) */
  estado_clase: string;
  estado_descripcion: string;
  /** calculado · operaciones que admite el estado actual */
  acciones: OperacionRemito[];
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
  resultado_recepcion: ResultadoRecepcion | null;
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
  libros: Libro[];
  ejemplares: Ejemplar[];
  solicitudes: SolicitudPrestamo[];
  prestamos: Prestamo[];
  reservas: Reserva[];
  remitos: Remito[];
  detalle_remitos: DetalleRemito[];
  evento_remitos: EventoRemito[];
}
export type Resource = keyof Database;
export type Entity<K extends Resource> = Database[K][number];
export type NewEntity<K extends Resource> = Omit<Entity<K>, "id">;
