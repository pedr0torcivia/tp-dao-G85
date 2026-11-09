import type { Database } from "./models";
import { isOverdue } from "./selectors";

/**
 * Pendientes de la sede de trabajo. Cada lista responde a "¿qué tengo que
 * hacer ahora?" para que el personal no tenga que deducir el siguiente paso
 * recorriendo pantallas.
 */
export function tasksFor(db: Database, sedeId: number) {
  const solicitudes = db.solicitudes;
  const porAsignar = solicitudes.filter(
    (s) => s.estado === "PENDIENTE" && s.sede_origen_id === sedeId,
  );
  const porPreparar = solicitudes.filter(
    (s) =>
      s.estado === "ASIGNADA" &&
      s.sede_origen_id === sedeId &&
      s.acciones.includes("preparar-entrega"),
  );
  const paraEntregar = solicitudes.filter(
    (s) => s.estado === "LISTA_PARA_ENTREGA" && s.sede_destino_id === sedeId,
  );
  const enCamino = solicitudes.filter(
    (s) => s.estado === "EN_TRASLADO" && s.sede_destino_id === sedeId,
  );
  const reservasPorAsignar = db.reservas.filter(
    (r) => r.estado === "PENDIENTE" && r.sede_retiro_id === sedeId,
  );
  const remitosPorArmar = db.remitos.filter(
    (r) =>
      r.sede_origen_id === sedeId &&
      (r.estado === "EN_PREPARACION" || r.estado === "EMPAQUETADO"),
  );
  const remitosPorRecibir = db.remitos.filter(
    (r) => r.sede_destino_id === sedeId && r.estado === "EN_TRANSITO",
  );
  const prestamosSede = db.prestamos.filter((p) => {
    const s = solicitudes.find((x) => x.id === p.solicitud_id);
    return !p.fecha_devolucion && s?.sede_destino_id === sedeId;
  });
  const vencidos = prestamosSede.filter((p) => isOverdue(p));
  const enRevision = db.ejemplares.filter(
    (e) => e.estado === "EN_REVISION" && e.sede_actual_id === sedeId,
  );
  return {
    porAsignar,
    porPreparar,
    paraEntregar,
    enCamino,
    reservasPorAsignar,
    remitosPorArmar,
    remitosPorRecibir,
    prestamosSede,
    vencidos,
    enRevision,
    circulacion: porAsignar.length + porPreparar.length + paraEntregar.length,
    logistica: remitosPorArmar.length + remitosPorRecibir.length,
  };
}
