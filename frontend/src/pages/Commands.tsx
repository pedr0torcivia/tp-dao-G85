import { useEffect, useRef, useState, type FormEvent } from "react";
import type { Resource } from "../domain/models";
import { api } from "../api";
import { ApiError, type Command, type CommandInput } from "../api/contracts";
import {
  available,
  bookName,
  sedeName,
  statusLabels,
} from "../domain/selectors";
import { useLibrary } from "../app/context";
import { Alert, Button, Field, inputClass } from "../components/ui";
import { defaultDateTime, type FormField } from "./resources";

export const actionLabels: Record<Command, string> = {
  habilitar: "Habilitar socio",
  inhabilitar: "Inhabilitar socio",
  "dar-de-baja": "Dar de baja",
  reactivar: "Reactivar sede",
  asignar: "Asignar ejemplar",
  "preparar-entrega": "Preparar entrega local",
  entregar: "Registrar entrega",
  cancelar: "Cancelar operación",
  rechazar: "Rechazar solicitud",
  devolver: "Registrar devolución",
  empaquetar: "Empaquetar",
  despachar: "Despachar",
  "registrar-salida": "Registrar salida",
  recibir: "Registrar recepción",
  "asignar-reserva": "Asignar y preparar ejemplar",
  expirar: "Registrar expiración",
  "aprobar-disponibilidad": "Aprobar disponibilidad",
};
export function CommandDialog({
  resource,
  id,
  action,
  onClose,
}: {
  resource: Resource;
  id: number;
  action: Command;
  onClose: () => void;
}) {
  const { db, refresh, notify } = useLibrary();
  const ref = useRef<HTMLDialogElement>(null);
  const [values, setValues] = useState<Record<string, string>>({
    fecha_entrega: defaultDateTime(),
    fecha_devolucion: defaultDateTime(),
    condicion_devolucion: "APTO",
    responsable: "Personal de biblioteca",
  });
  const [checked, setChecked] = useState<number[]>([]),
    [error, setError] = useState<ApiError | null>(null),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    const dialog = ref.current!;
    dialog.showModal();
    return () => dialog.close();
  }, []);
  let fields: FormField[] = [];
  if (action === "asignar" || action === "asignar-reserva") {
    const solicitud = db!.solicitudes.find((s) => s.id === id),
      reserva = db!.reservas.find((r) => r.id === id),
      remito = db!.remitos.find((r) => r.id === id);
    const options = db!.ejemplares
      .filter((e) => {
        if (resource === "solicitudes")
          return (
            available(e, db!) &&
            e.libro_id === solicitud?.libro_id &&
            e.sede_propietaria_id === solicitud?.sede_origen_id
          );
        if (resource === "reservas")
          return (
            available(e, db!) &&
            e.libro_id === reserva?.libro_id &&
            e.sede_actual_id === reserva?.sede_retiro_id
          );
        return (
          (available(e, db!) || e.estado === "ASIGNADO") &&
          e.sede_propietaria_id === remito?.sede_origen_id &&
          e.sede_actual_id === remito?.sede_origen_id &&
          !db!.detalle_remitos.some(
            (d) =>
              d.ejemplar_id === e.id &&
              !["RECIBIDO", "CANCELADO"].includes(
                db!.remitos.find((r) => r.id === d.remito_id)!.estado,
              ),
          )
        );
      })
      .map(
        (e) =>
          [
            String(e.id),
            `${e.codigo_inventario} · ${bookName(e.libro_id, db!)} · ${sedeName(e.sede_propietaria_id, db!)}`,
          ] as [string, string],
      );
    fields.push({
      key: "ejemplar_id",
      label: "Ejemplar disponible",
      type: "select",
      required: true,
      options,
    });
    if (action === "asignar-reserva")
      fields.push({
        key: "fecha_limite_retiro",
        label: "Fecha límite de retiro",
        type: "datetime-local",
        required: true,
      });
  }
  if (action === "entregar")
    fields = [
      {
        key: "fecha_entrega",
        label: "Fecha de entrega",
        type: "datetime-local",
        required: true,
      },
      {
        key: "fecha_vencimiento",
        label: "Fecha de vencimiento",
        type: "datetime-local",
        required: true,
      },
    ];
  if (action === "devolver")
    fields = [
      {
        key: "fecha_devolucion",
        label: "Fecha de devolución",
        type: "datetime-local",
        required: true,
      },
      {
        key: "condicion_devolucion",
        label: "Condición del material",
        type: "select",
        required: true,
        options: [
          ["APTO", "Apto para préstamo"],
          ["NO_APTO", "No apto para préstamo"],
        ],
      },
    ];
  if (resource === "remitos" && action !== "asignar")
    fields = [
      { key: "responsable", label: "Responsable", required: true },
      { key: "observacion", label: "Observación", type: "textarea" },
    ];
  const details = db!.detalle_remitos.filter((d) => d.remito_id === id);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const input: CommandInput = {};
      const formData = new FormData(e.currentTarget);
      for (const f of fields) {
        const raw = String(formData.get(f.key) ?? "");
        input[f.key] = f.key.endsWith("_id")
          ? Number(raw)
          : f.type === "datetime-local"
            ? `${raw}${raw.length === 16 ? ":00" : ""}-03:00`
            : raw;
      }
      if (action === "recibir") input.verificados = checked;
      await api.command(resource, id, action, input);
      await refresh();
      notify("La operación se registró correctamente.");
      onClose();
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e
          : new ApiError("No pudimos registrar la operación."),
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <dialog
      ref={ref}
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) onClose();
      }}
      aria-labelledby="operation-title"
      className="fixed inset-0 m-auto max-h-[90svh] w-[min(92vw,600px)] overflow-y-auto rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 shadow-xl backdrop:bg-black/40"
    >
      <form onSubmit={submit}>
        <h2
          id="operation-title"
          className="font-heading text-2xl text-[var(--primary)]"
        >
          {actionLabels[action]}
        </h2>
        <p className="my-4 text-sm text-[var(--muted-foreground)]">
          {action === "inhabilitar"
            ? "La inhabilitación impide nuevos préstamos. Las devoluciones siguen permitidas."
            : action === "devolver"
              ? "Revisá el material y registrá su condición física. Queda en revisión hasta aprobar su disponibilidad."
              : action === "entregar"
                ? "El plazo comienza con la entrega del material al socio. Indicá el vencimiento acordado."
                : action === "asignar-reserva"
                  ? "Indicá el plazo de retiro acordado. No se aplica un plazo automático."
                  : "Confirmá los datos antes de registrar esta operación."}
        </p>
        {error && <Alert error>{error.message}</Alert>}
        <div className="space-y-5">
          {fields.map((f) => (
            <Field key={f.key} label={f.label} error={error?.fields[f.key]}>
              {f.type === "select" ? (
                <select
                  name={f.key}
                  className={inputClass}
                  value={values[f.key] ?? ""}
                  required={f.required}
                  onChange={(e) =>
                    setValues((v) => ({ ...v, [f.key]: e.target.value }))
                  }
                >
                  <option value="">Seleccioná una opción</option>
                  {f.options?.map(([id, label]) => (
                    <option key={id} value={id}>
                      {label}
                    </option>
                  ))}
                </select>
              ) : f.type === "textarea" ? (
                <textarea
                  name={f.key}
                  className={inputClass}
                  value={values[f.key] ?? ""}
                  onChange={(e) =>
                    setValues((v) => ({ ...v, [f.key]: e.target.value }))
                  }
                />
              ) : (
                <input
                  name={f.key}
                  className={inputClass}
                  type={f.type === "datetime-local" ? f.type : "text"}
                  required={f.required}
                  value={values[f.key] ?? ""}
                  onChange={(e) =>
                    setValues((v) => ({ ...v, [f.key]: e.target.value }))
                  }
                />
              )}
            </Field>
          ))}
        </div>
        {action === "recibir" && (
          <fieldset className="mt-6">
            <legend className="mb-3 font-medium">Ejemplares recibidos</legend>
            {details.map((d) => {
              const e = db!.ejemplares.find((e) => e.id === d.ejemplar_id)!;
              return (
                <label
                  key={d.id}
                  className="mb-3 flex items-center gap-3 text-sm"
                >
                  <input
                    type="checkbox"
                    checked={checked.includes(e.id)}
                    onChange={(event) =>
                      setChecked((v) =>
                        event.target.checked
                          ? [...v, e.id]
                          : v.filter((id) => id !== e.id),
                      )
                    }
                  />
                  {e.codigo_inventario} · {bookName(e.libro_id, db!)} ·{" "}
                  {statusLabels[d.condicion_salida] ?? d.condicion_salida}
                </label>
              );
            })}
            <p className="mt-4 text-xs text-[var(--muted-foreground)]">
              La recepción parcial y el tratamiento de incidencias requieren
              definir sus reglas.
            </p>
          </fieldset>
        )}
        <div className="mt-8 flex justify-end gap-3">
          <Button
            variant="outline"
            disabled={busy}
            type="button"
            onClick={onClose}
          >
            Volver
          </Button>
          <Button disabled={busy} type="submit">
            {busy ? "Guardando…" : "Confirmar"}
          </Button>
        </div>
      </form>
    </dialog>
  );
}
