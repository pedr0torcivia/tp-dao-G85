import { useState, type FormEvent, type ReactNode } from "react";
import type { Resource, ResultadoRecepcion } from "../domain/models";
import { api } from "../api";
import { ApiError, type Command, type CommandInput } from "../api/contracts";
import {
  available,
  bookName,
  inOpenRemito,
  sedeName,
  socioName,
  statusLabels,
} from "../domain/selectors";
import { useLibrary } from "../app/context";
import { Alert, Button, Dialog, Field, PatternNote } from "../components/ui";

export const actionLabels: Record<Command, string> = {
  habilitar: "Habilitar socio",
  inhabilitar: "Inhabilitar socio",
  "dar-de-baja": "Dar de baja",
  reactivar: "Reactivar sede",
  asignar: "Asignar ejemplar",
  "preparar-entrega": "Preparar entrega",
  entregar: "Entregar al socio",
  cancelar: "Cancelar",
  rechazar: "Rechazar",
  devolver: "Registrar devolución",
  empaquetar: "Empaquetar",
  reabrir: "Reabrir paquete",
  quitar: "Quitar ejemplar",
  despachar: "Despachar",
  recibir: "Recibir envío",
  "asignar-reserva": "Asignar ejemplar",
  expirar: "Marcar como expirada",
  "aprobar-disponibilidad": "Aprobar disponibilidad",
};

/** Fecha/hora local en formato de <input type="datetime-local">. */
const localInput = (offsetDays = 0) => {
  const d = new Date(Date.now() + offsetDays * 86400000);
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Argentina/Buenos_Aires",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(d);
  const v = (t: string) => parts.find((p) => p.type === t)?.value ?? "00";
  return `${v("year")}-${v("month")}-${v("day")}T${v("hour")}:${v("minute")}`;
};
const toApiDate = (raw: string) =>
  `${raw}${raw.length === 16 ? ":00" : ""}-03:00`;

const resultadoOpciones: [ResultadoRecepcion, string, string][] = [
  ["CONFORME", "Llegó bien", "ok"],
  ["DANADO", "Dañado", "warn"],
  ["EXTRAVIADO", "No llegó", "bad"],
];

export function CommandDialog({
  resource,
  id,
  action,
  onClose,
  onDone,
}: {
  resource: Resource;
  id: number;
  action: Command;
  onClose: () => void;
  onDone?: () => void;
}) {
  const { db, refresh, notify, usuario } = useLibrary();
  const responsableBase = usuario?.nombre || "Personal de biblioteca";
  const [values, setValues] = useState<Record<string, string>>({
    fecha_entrega: localInput(),
    fecha_vencimiento: localInput(14),
    fecha_devolucion: localInput(),
    fecha_limite_retiro: localInput(3),
    condicion_devolucion: "APTO",
    responsable: responsableBase,
    observacion: "",
    ejemplar_id: "",
  });
  const [preparar, setPreparar] = useState(true);
  const [resultados, setResultados] = useState<
    Record<number, ResultadoRecepcion>
  >({});
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const set = (k: string, v: string) => setValues((x) => ({ ...x, [k]: v }));

  const solicitud =
    resource === "solicitudes"
      ? db!.solicitudes.find((s) => s.id === id)
      : undefined;
  const reserva =
    resource === "reservas" ? db!.reservas.find((r) => r.id === id) : undefined;
  const remito =
    resource === "remitos" ? db!.remitos.find((r) => r.id === id) : undefined;
  const detalles = db!.detalle_remitos.filter((d) => d.remito_id === id);

  // --- Opciones de ejemplar según el contexto -----------------------------
  let copias = db!.ejemplares.filter(() => false);
  if (action === "asignar" && solicitud)
    copias = db!.ejemplares.filter(
      (e) =>
        available(e, db!) &&
        e.libro_id === solicitud.libro_id &&
        e.sede_propietaria_id === solicitud.sede_origen_id,
    );
  if (action === "asignar-reserva" && reserva)
    copias = db!.ejemplares.filter(
      (e) =>
        available(e, db!) &&
        e.libro_id === reserva.libro_id &&
        e.sede_propietaria_id === reserva.sede_retiro_id,
    );
  if (action === "asignar" && remito)
    copias = db!.ejemplares.filter((e) => {
      if (e.sede_actual_id !== remito.sede_origen_id || inOpenRemito(e.id, db!))
        return false;
      const retorno =
        e.estado === "EN_REVISION" &&
        e.sede_propietaria_id === remito.sede_destino_id;
      const pedido = db!.solicitudes.some(
        (s) =>
          s.ejemplar_id === e.id &&
          s.estado === "ASIGNADA" &&
          s.tipo === "INTERBIBLIOTECARIO" &&
          s.sede_destino_id === remito.sede_destino_id,
      );
      return retorno || pedido || available(e, db!);
    });
  if (action === "quitar")
    copias = db!.ejemplares.filter((e) =>
      detalles.some((d) => d.ejemplar_id === e.id),
    );
  const copyLabel = (eid: number) => {
    const e = db!.ejemplares.find((x) => x.id === eid)!;
    const pedido = db!.solicitudes.find(
      (s) => s.ejemplar_id === e.id && s.estado === "ASIGNADA",
    );
    const motivo =
      e.estado === "EN_REVISION"
        ? "retorno a su sede"
        : pedido
          ? `para ${socioName(pedido.socio_id, db!)}`
          : "traslado";
    return `${e.codigo_inventario} · ${bookName(e.libro_id, db!)}${resource === "remitos" ? ` · ${motivo}` : ""}`;
  };

  // --- Texto que explica la consecuencia ---------------------------------
  const explain: Partial<Record<Command, ReactNode>> = {
    inhabilitar:
      "El socio no podrá iniciar préstamos, reservas ni recibir envíos. Las devoluciones siguen permitidas.",
    habilitar: "El socio vuelve a poder pedir material.",
    "dar-de-baja":
      resource === "sedes"
        ? "La sede deja de iniciar préstamos, reservas y envíos. Lo que ya está en viaje puede terminar de recibirse."
        : "El ejemplar sale de circulación. Se conserva en el historial.",
    reactivar: "La sede vuelve a operar en la red.",
    "aprobar-disponibilidad":
      "Confirmás que el material está apto y en su sede: vuelve a estar disponible para préstamo.",
    rechazar: "La solicitud queda cerrada sin préstamo.",
    cancelar:
      resource === "remitos"
        ? "El envío se anula. Los ejemplares vuelven a su estado anterior (disponibles o reservados para su solicitud)."
        : resource === "reservas"
          ? "La reserva se cierra y el ejemplar apartado vuelve a estar disponible."
          : "La solicitud se cierra y el ejemplar asignado vuelve a estar disponible. Si ya estaba en un remito en preparación, se lo quita del paquete.",
    entregar:
      "El préstamo comienza ahora. Se verifica que el socio no tenga préstamos vencidos y que el plazo no supere 60 días.",
    devolver:
      "El ejemplar queda en revisión. Si es de otra sede, vas a poder armar su remito de retorno.",
    "asignar-reserva":
      "El ejemplar queda apartado en mostrador hasta la fecha límite de retiro.",
    expirar:
      "Venció el plazo de retiro: la reserva se cierra y el ejemplar se libera.",
    empaquetar:
      "Se cierra el paquete. Ya no se pueden agregar ejemplares salvo que lo reabras.",
    reabrir: "El remito vuelve a preparación para agregar o quitar ejemplares.",
    despachar:
      "El material sale de la sede y queda en tránsito. A partir de acá el envío no puede cancelarse.",
    recibir:
      "Indicá cómo llegó cada ejemplar. Si alguno llegó dañado o no llegó, el remito queda con incidencias y la solicitud vuelve a la cola para asignar otra copia.",
  };

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const input: CommandInput = {};
      if (["asignar", "asignar-reserva", "quitar"].includes(action))
        input.ejemplar_id = Number(values.ejemplar_id);
      if (action === "asignar-reserva")
        input.fecha_limite_retiro = toApiDate(values.fecha_limite_retiro);
      if (action === "entregar") {
        input.fecha_entrega = toApiDate(values.fecha_entrega);
        input.fecha_vencimiento = toApiDate(values.fecha_vencimiento);
      }
      if (action === "devolver") {
        input.fecha_devolucion = toApiDate(values.fecha_devolucion);
        input.condicion_devolucion = values.condicion_devolucion;
      }
      if (
        resource === "remitos" &&
        ["empaquetar", "reabrir", "despachar", "recibir", "cancelar"].includes(
          action,
        )
      ) {
        input.responsable = values.responsable;
        input.observacion = values.observacion;
      }
      if (action === "recibir") {
        const faltan = detalles.filter((d) => !resultados[d.ejemplar_id]);
        if (faltan.length)
          throw new ApiError(
            "Marcá el resultado de cada ejemplar antes de confirmar.",
          );
        input.resultados = Object.fromEntries(
          Object.entries(resultados).map(([k, v]) => [k, v]),
        );
      }
      await api.command(resource, id, action, input);
      let message = "Listo. La operación quedó registrada.";
      if (action === "asignar" && solicitud && preparar) {
        await api.command(resource, id, "preparar-entrega");
        message =
          solicitud.tipo === "LOCAL"
            ? "Ejemplar asignado y apartado en mostrador."
            : "Ejemplar asignado e incorporado a un remito hacia la sede de retiro.";
      }
      await refresh();
      notify(message);
      onDone?.();
      onClose();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err
          : new ApiError("No pudimos registrar la operación."),
      );
      await refresh().catch(() => undefined);
    } finally {
      setBusy(false);
    }
  }

  const needsCopy = ["asignar", "asignar-reserva", "quitar"].includes(action);
  const title =
    resource === "remitos" && action === "asignar"
      ? "Agregar ejemplar al remito"
      : resource === "remitos" && action === "cancelar"
        ? "Cancelar envío"
        : actionLabels[action];

  return (
    <Dialog title={title} onClose={onClose} busy={busy} wide={action === "recibir"}>
      <form onSubmit={submit} className="mt-2">
        {solicitud && (
          <p className="mb-3 text-sm text-[var(--muted-foreground)]">
            {socioName(solicitud.socio_id, db!)} ·{" "}
            <b className="text-[var(--foreground)]">
              {bookName(solicitud.libro_id, db!)}
            </b>{" "}
            · {sedeName(solicitud.sede_origen_id, db!)} →{" "}
            {sedeName(solicitud.sede_destino_id, db!)}
          </p>
        )}
        {remito && (
          <p className="mb-3 text-sm text-[var(--muted-foreground)]">
            Remito <b className="text-[var(--foreground)]">{remito.numero}</b> ·{" "}
            {sedeName(remito.sede_origen_id, db!)} →{" "}
            {sedeName(remito.sede_destino_id, db!)}
          </p>
        )}
        {action === "preparar-entrega" && solicitud ? (
          <PatternNote pattern="Strategy">
            Esta solicitud es <b>{statusLabels[solicitud.tipo].toLowerCase()}</b>
            , así que la tramita <code>{solicitud.estrategia}</code>:{" "}
            {solicitud.estrategia_descripcion}
          </PatternNote>
        ) : (
          explain[action] && (
            <p className="mb-4 text-sm leading-relaxed text-[var(--muted-foreground)]">
              {explain[action]}
            </p>
          )
        )}
        {error && <Alert error>{error.message}</Alert>}

        <div className="mt-4 grid gap-4">
          {needsCopy && (
            <Field
              label={action === "quitar" ? "Ejemplar a quitar" : "Ejemplar"}
              error={error?.fields.ejemplar_id}
              hint={
                copias.length
                  ? `${copias.length} ${copias.length === 1 ? "copia apta" : "copias aptas"}.`
                  : undefined
              }
            >
              <select
                className="input"
                required
                value={values.ejemplar_id}
                onChange={(e) => set("ejemplar_id", e.target.value)}
              >
                <option value="">Elegí un ejemplar</option>
                {copias.map((e) => (
                  <option key={e.id} value={e.id}>
                    {copyLabel(e.id)}
                  </option>
                ))}
              </select>
            </Field>
          )}
          {needsCopy && !copias.length && (
            <Alert tone="warn">
              No hay copias que cumplan las reglas para esta operación
              {solicitud
                ? ` en ${sedeName(solicitud.sede_origen_id, db!)}`
                : reserva
                  ? ` en ${sedeName(reserva.sede_retiro_id, db!)}`
                  : ""}
              . Revisá la disponibilidad en el catálogo.
            </Alert>
          )}
          {action === "asignar" && solicitud && (
            <label className="option-row">
              <input
                type="checkbox"
                className="mt-1"
                checked={preparar}
                onChange={(e) => setPreparar(e.target.checked)}
              />
              <span>
                <b>Preparar la entrega en el mismo paso</b>
                <span className="block text-[var(--muted-foreground)]">
                  {solicitud.estrategia_descripcion}
                </span>
              </span>
            </label>
          )}
          {action === "asignar-reserva" && (
            <Field label="Retirar hasta">
              <input
                type="datetime-local"
                className="input"
                required
                value={values.fecha_limite_retiro}
                onChange={(e) => set("fecha_limite_retiro", e.target.value)}
              />
            </Field>
          )}
          {action === "entregar" && (
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Entrega" error={error?.fields.fecha_entrega}>
                <input
                  type="datetime-local"
                  className="input"
                  required
                  value={values.fecha_entrega}
                  onChange={(e) => set("fecha_entrega", e.target.value)}
                />
              </Field>
              <Field
                label="Vence"
                error={error?.fields.fecha_vencimiento}
                hint="Plazo habitual: 14 días."
              >
                <input
                  type="datetime-local"
                  className="input"
                  required
                  value={values.fecha_vencimiento}
                  onChange={(e) => set("fecha_vencimiento", e.target.value)}
                />
              </Field>
            </div>
          )}
          {action === "devolver" && (
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Fecha de devolución">
                <input
                  type="datetime-local"
                  className="input"
                  required
                  value={values.fecha_devolucion}
                  onChange={(e) => set("fecha_devolucion", e.target.value)}
                />
              </Field>
              <Field label="Estado del material">
                <select
                  className="input"
                  value={values.condicion_devolucion}
                  onChange={(e) => set("condicion_devolucion", e.target.value)}
                >
                  <option value="APTO">Apto: puede volver a prestarse</option>
                  <option value="NO_APTO">No apto: dañado</option>
                </select>
              </Field>
            </div>
          )}
          {action === "recibir" && (
            <fieldset className="grid gap-2">
              <legend className="field-label">Resultado por ejemplar</legend>
              <div className="mb-1 flex justify-end">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() =>
                    setResultados(
                      Object.fromEntries(
                        detalles.map((d) => [d.ejemplar_id, "CONFORME"]),
                      ),
                    )
                  }
                >
                  Marcar todo como recibido
                </Button>
              </div>
              {detalles.map((d) => {
                const e = db!.ejemplares.find((x) => x.id === d.ejemplar_id)!;
                return (
                  <div key={d.id} className="receive-row sm:grid-cols-[1fr_auto]">
                    <div>
                      <p className="text-sm font-semibold">
                        {bookName(e.libro_id, db!)}
                      </p>
                      <p className="mono text-[var(--muted-foreground)]">
                        {e.codigo_inventario}
                        {d.solicitud_id ? " · para un socio" : " · traslado"}
                      </p>
                    </div>
                    <div className="segmented" role="group" aria-label={`Resultado de ${e.codigo_inventario}`}>
                      {resultadoOpciones.map(([value, label, tone]) => (
                        <button
                          key={value}
                          type="button"
                          data-tone={tone}
                          aria-pressed={resultados[e.id] === value}
                          onClick={() =>
                            setResultados((r) => ({ ...r, [e.id]: value }))
                          }
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </fieldset>
          )}
          {resource === "remitos" &&
            ["empaquetar", "reabrir", "despachar", "recibir", "cancelar"].includes(
              action,
            ) && (
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Responsable">
                  <input
                    className="input"
                    required
                    value={values.responsable}
                    onChange={(e) => set("responsable", e.target.value)}
                  />
                </Field>
                <Field label="Observación (opcional)">
                  <input
                    className="input"
                    value={values.observacion}
                    onChange={(e) => set("observacion", e.target.value)}
                  />
                </Field>
              </div>
            )}
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <Button variant="outline" disabled={busy} onClick={onClose}>
            Volver
          </Button>
          <Button
            type="submit"
            variant={
              ["cancelar", "rechazar", "dar-de-baja", "inhabilitar"].includes(
                action,
              )
                ? "danger"
                : "primary"
            }
            disabled={busy || (needsCopy && !copias.length)}
          >
            {busy ? "Guardando…" : title}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
