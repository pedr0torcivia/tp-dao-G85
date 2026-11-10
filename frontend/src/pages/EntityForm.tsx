import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import type { NewEntity, Resource } from "../domain/models";
import { api } from "../api";
import { ApiError } from "../api/contracts";
import { useLibrary } from "../app/context";
import { available, sedeName } from "../domain/selectors";
import {
  Alert,
  Back,
  Badge,
  Button,
  Field,
  Heading,
  outlineClass,
  PatternNote,
} from "../components/ui";
import { config, fieldsFor, pathOf, tipoSolicitud } from "./resources";

const help: Partial<Record<Resource, { title: string; steps: string[] }>> = {
  libros: {
    title: "Una ficha, muchas copias",
    steps: [
      "Cargá los datos bibliográficos. El ISBN evita duplicados; sin ISBN se controla título + autor + editorial + edición.",
      "Después agregá las copias físicas (ejemplares) desde la ficha del libro.",
    ],
  },
  ejemplares: {
    title: "Cada copia tiene su recorrido",
    steps: [
      "El código de inventario identifica la copia y no puede repetirse.",
      "La sede propietaria es dónde vuelve siempre la copia después de un préstamo interbibliotecario.",
    ],
  },
  socios: {
    title: "La ficha del lector",
    steps: [
      "El número de socio y el documento no pueden repetirse.",
      "Los socios nuevos empiezan habilitados.",
    ],
  },
  sedes: {
    title: "Una biblioteca en la red",
    steps: ["El nombre de la sede no puede repetirse.", "Las sedes nuevas empiezan activas."],
  },
  reservas: {
    title: "Un lugar en la espera",
    steps: [
      "Reservá cuando no hay copias libres en la sede donde el socio quiere retirar.",
      "Cuando aparezca una copia, apartala desde la reserva: queda lista para retirar hasta la fecha límite.",
    ],
  },
  remitos: {
    title: "Libros que viajan",
    steps: [
      "Normalmente no hace falta crearlo a mano: preparar una solicitud interbibliotecaria o un retorno arma el remito solo.",
      "Si lo creás acá, agregá los ejemplares desde su ficha y seguí: empaquetar → despachar → recibir.",
    ],
  },
};

/** Columna de imagen con vista previa: portada del libro o foto de la copia. */
function ImagePicker({
  label,
  hint,
  actual,
  archivo,
  onChange,
}: {
  label: string;
  hint: string;
  actual: string | null;
  archivo: File | null;
  onChange: (f: File | null) => void;
}) {
  const [preview, setPreview] = useState<string | null>(null);
  useEffect(() => {
    if (!archivo) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(archivo);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [archivo]);
  const src = preview ?? actual;
  return (
    <div className="media-picker">
      <label htmlFor="portada-libro" className="field-label">
        {label}
      </label>
      <div className={`media-frame ${src ? "" : "empty"}`}>
        {src ? <img src={src} alt="Vista previa" /> : <span>Sin imagen</span>}
      </div>
      <div className="mt-2 flex flex-wrap gap-2">
        <span className="btn btn-outline btn-sm media-button">
          {src ? "Cambiar imagen" : "Elegir imagen"}
          <input
            id="portada-libro"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => onChange(e.target.files?.[0] ?? null)}
          />
        </span>
        {archivo && (
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => onChange(null)}>
            Quitar
          </button>
        )}
      </div>
      <span className="field-hint">{archivo ? `${archivo.name} · se guarda al confirmar` : hint}</span>
    </div>
  );
}

export function EntityForm({ resource }: { resource: Resource }) {
  if (resource === "solicitudes") return <NuevaSolicitud />;
  return <GenericForm resource={resource} />;
}

function GenericForm({ resource }: { resource: Resource }) {
  const { db, sedeId, refresh, notify } = useLibrary();
  const { id } = useParams();
  const [search] = useSearchParams();
  const navigate = useNavigate();
  const record = id ? db![resource].find((r) => r.id === Number(id)) : undefined;
  const conf = config[resource]!;
  const [values, setValues] = useState<Record<string, string>>(() => {
    const result = record
      ? Object.fromEntries(Object.entries(record).map(([k, v]) => [k, String(v ?? "")]))
      : {};
    if (!record) {
      result.sede_origen_id = String(sedeId);
      result.sede_retiro_id = String(sedeId);
      result.sede_propietaria_id = String(sedeId);
      result.condicion_fisica = "APTO";
    }
    for (const k of ["libro_id", "socio_id", "sede_origen_id", "sede_destino_id"])
      if (search.get(k)) result[k] = search.get(k)!;
    return result;
  });
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const [foto, setFoto] = useState<File | null>(null);
  if (id && !record)
    return (
      <>
        <Back to={`/${pathOf(resource)}`} />
        <Alert error>No encontramos ese registro.</Alert>
      </>
    );
  const fields = fieldsFor(resource, db!);
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const data: Record<string, unknown> = Object.fromEntries(
        fields.map((f) => [
          f.key,
          f.key.endsWith("_id")
            ? values[f.key]
              ? Number(values[f.key])
              : null
            : values[f.key]?.trim() || (f.required ? null : ""),
        ]),
      );
      if (record)
        for (const [k, v] of Object.entries(record)) if (data[k] === undefined) data[k] = v;
      const saved = await api.save(resource, data as NewEntity<typeof resource>, id ? Number(id) : undefined);
      let aviso = "Los datos se guardaron correctamente.";
      if (foto && resource === "libros") {
        try {
          await api.subirPortada(saved.id, foto);
        } catch (e) {
          aviso = `Se guardaron los datos, pero la imagen no se subió: ${(e as Error).message}`;
        }
      }
      await refresh();
      notify(aviso);
      navigate(`/${pathOf(resource)}/${saved.id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError("No pudimos guardar los datos."));
    } finally {
      setBusy(false);
    }
  }
  const h = help[resource];
  const conImagen = resource === "libros";
  const actualLibro = resource === "libros" && record ? (record as { portada_url?: string | null }).portada_url : null;
  const imagenActual = actualLibro ?? null;
  return (
    <>
      <Back to={`/${pathOf(resource)}`} />
      <Heading
        kicker={id ? "Edición" : "Alta"}
        title={id ? `Editar ${conf.singular}` : conf.create}
      />
      <form onSubmit={submit} className={`form-layout ${conImagen ? "with-media" : ""}`}>
        {conImagen && (
          <ImagePicker
            label="Portada (opcional)"
            hint="Se muestra en el catálogo y en sus ejemplares. JPG, PNG o WEBP, hasta 3 MB."
            actual={imagenActual}
            archivo={foto}
            onChange={setFoto}
          />
        )}
        <div className="min-w-0">
          {error && <Alert error>{error.message}</Alert>}
          <div className="form-grid">
            {fields.map((f) => (
              <Field
                key={f.key}
                label={f.label + (f.required ? "" : " (opcional)")}
                error={error?.fields[f.key]}
                hint={f.hint}
                className={f.type === "textarea" ? "span-2" : ""}
              >
                {f.type === "select" ? (
                  <select
                    className="input"
                    required={f.required}
                    value={values[f.key] ?? ""}
                    disabled={!!id && resource === "ejemplares" && ["libro_id", "sede_propietaria_id"].includes(f.key)}
                    onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                  >
                    <option value="">Seleccioná una opción</option>
                    {f.options?.map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                ) : f.type === "textarea" ? (
                  <textarea
                    className="input"
                    rows={3}
                    required={f.required}
                    value={values[f.key] ?? ""}
                    onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                  />
                ) : (
                  <input
                    className="input"
                    required={f.required}
                    placeholder={f.placeholder}
                    inputMode={f.key === "isbn" ? "numeric" : undefined}
                    maxLength={["contacto", "direccion"].includes(f.key) ? 255 : ["numero_socio", "documento"].includes(f.key) ? 30 : 150}
                    value={values[f.key] ?? ""}
                    onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                  />
                )}
              </Field>
            ))}
          </div>
          <div className="form-actions">
            <Link className={outlineClass} to={`/${pathOf(resource)}`}>
              Cancelar
            </Link>
            <Button disabled={busy} type="submit">
              {busy ? "Guardando…" : `Guardar ${conf.singular}`}
            </Button>
          </div>
        </div>
        {h && (
          <aside className="side-help">
            <p className="kicker">Antes de guardar</p>
            <h2 className="font-heading text-lg font-semibold">{h.title}</h2>
            <ol>
              {h.steps.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ol>
          </aside>
        )}
      </form>
    </>
  );
}

function NuevaSolicitud() {
  const { db, sedeId, refresh, notify } = useLibrary();
  const [search] = useSearchParams();
  const navigate = useNavigate();
  const [socio, setSocio] = useState(search.get("socio_id") ?? "");
  const [libro, setLibro] = useState(search.get("libro_id") ?? "");
  const [retiro, setRetiro] = useState(String(sedeId));
  const [origen, setOrigen] = useState<string>("");
  const [asignarYa, setAsignarYa] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);

  const sedes = db!.sedes.filter((s) => s.estado === "ACTIVA");
  const disponibilidad = useMemo(
    () =>
      sedes.map((s) => ({
        sede: s,
        copias: db!.ejemplares.filter(
          (e) => e.libro_id === Number(libro) && e.sede_propietaria_id === s.id && available(e, db!),
        ),
      })),
    [db, libro, sedes],
  );
  // Origen sugerido: la sede de retiro si tiene copias; si no, la que más tenga.
  const sugerido =
    disponibilidad.find((d) => String(d.sede.id) === retiro && d.copias.length) ??
    [...disponibilidad].sort((a, b) => b.copias.length - a.copias.length).find((d) => d.copias.length);
  const origenEfectivo = origen || (sugerido ? String(sugerido.sede.id) : retiro);
  const tipo = tipoSolicitud(Number(origenEfectivo), Number(retiro));
  const copiasOrigen = disponibilidad.find((d) => String(d.sede.id) === origenEfectivo)?.copias ?? [];
  const sinCopias = !!libro && disponibilidad.every((d) => !d.copias.length);
  const socioSel = db!.socios.find((s) => String(s.id) === socio);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const saved = await api.save("solicitudes", {
        socio_id: Number(socio),
        libro_id: Number(libro),
        sede_origen_id: Number(origenEfectivo),
        sede_destino_id: Number(retiro),
        tipo,
      } as unknown as NewEntity<"solicitudes">);
      let message = "Solicitud registrada. Queda pendiente de asignar una copia.";
      if (asignarYa && copiasOrigen.length) {
        try {
          await api.command("solicitudes", saved.id, "asignar", { ejemplar_id: copiasOrigen[0].id });
          await api.command("solicitudes", saved.id, "preparar-entrega");
          message =
            tipo === "LOCAL"
              ? `Listo: ${copiasOrigen[0].codigo_inventario} está apartado en mostrador para entregar.`
              : `Listo: ${copiasOrigen[0].codigo_inventario} se incorporó a un remito hacia ${sedeName(Number(retiro), db!)}.`;
        } catch (inner) {
          message = `Solicitud creada, pero no se pudo asignar automáticamente: ${(inner as Error).message}`;
        }
      }
      await refresh();
      notify(message);
      navigate(`/solicitudes/${saved.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err : new ApiError("No pudimos crear la solicitud."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Back to="/solicitudes" />
      <Heading
        title="Nueva solicitud de préstamo"
        description="Elegí quién pide, qué libro y dónde lo retira. El sistema muestra dónde hay copias y decide si el préstamo es local o interbibliotecario."
      />
      <form onSubmit={submit} className="form-layout">
        <div className="grid gap-5">
          {error && <Alert error>{error.message}</Alert>}
          <div className="form-grid">
            <Field label="1. Socio" error={error?.fields.socio_id}>
              <select className="input" required value={socio} onChange={(e) => setSocio(e.target.value)}>
                <option value="">Elegí un socio</option>
                {db!.socios.map((s) => (
                  <option key={s.id} value={s.id} disabled={s.estado !== "HABILITADO"}>
                    {s.nombre} · N.º {s.numero_socio}
                    {s.estado !== "HABILITADO" ? " (inhabilitado)" : ""}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="2. Libro" error={error?.fields.libro_id}>
              <select
                className="input"
                required
                value={libro}
                onChange={(e) => {
                  setLibro(e.target.value);
                  setOrigen("");
                }}
              >
                <option value="">Elegí un libro</option>
                {[...db!.libros]
                  .sort((a, b) => a.titulo.localeCompare(b.titulo))
                  .map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.titulo} — {b.autor}
                    </option>
                  ))}
              </select>
            </Field>
            <Field label="3. Lo retira en" hint="Por defecto, tu sede de trabajo.">
              <select
                className="input"
                value={retiro}
                onChange={(e) => {
                  setRetiro(e.target.value);
                  setOrigen("");
                }}
              >
                {sedes.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.nombre}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          {libro && (
            <fieldset>
              <legend className="field-label">4. ¿De qué sede sale la copia?</legend>
              <div className="sede-avail">
                {disponibilidad.map(({ sede, copias }) => {
                  const sel = String(sede.id) === origenEfectivo;
                  return (
                    <button
                      key={sede.id}
                      type="button"
                      aria-pressed={sel}
                      onClick={() => setOrigen(String(sede.id))}
                    >
                      <div className="flex-1">
                        <p className="text-sm font-semibold">
                          {sede.nombre}
                          {String(sede.id) === retiro && <span className="muted font-normal"> · donde retira</span>}
                        </p>
                        <p className="text-xs text-[var(--muted-foreground)]">
                          {copias.length
                            ? `${copias.length} ${copias.length === 1 ? "copia disponible" : "copias disponibles"}`
                            : "Sin copias disponibles"}
                        </p>
                      </div>
                      <Badge
                        value={String(sede.id) === retiro ? "LOCAL" : "INTERBIBLIOTECARIO"}
                        label={String(sede.id) === retiro ? "Local" : "Interbibliotecario"}
                      />
                    </button>
                  );
                })}
              </div>
              {sinCopias && (
                <Alert tone="warn">
                  No hay copias disponibles en ninguna sede. Podés registrar la
                  solicitud igual (queda pendiente) o{" "}
                  <Link className="font-semibold underline" to={`/reservas/nuevo?libro_id=${libro}${socio ? `&socio_id=${socio}` : ""}`}>
                    crear una reserva
                  </Link>
                  .
                </Alert>
              )}
            </fieldset>
          )}

          {libro && copiasOrigen.length > 0 && (
            <label className="option-row">
              <input type="checkbox" className="mt-1" checked={asignarYa} onChange={(e) => setAsignarYa(e.target.checked)} />
              <span>
                <b>Asignar la copia {copiasOrigen[0].codigo_inventario} y prepararla ahora</b>
                <span className="block text-[var(--muted-foreground)]">
                  {tipo === "LOCAL"
                    ? "Queda lista en mostrador para entregar."
                    : `Se agrega a un remito ${sedeName(Number(origenEfectivo), db!)} → ${sedeName(Number(retiro), db!)}.`}
                </span>
              </span>
            </label>
          )}

          <div className="flex justify-end gap-2">
            <Link className={outlineClass} to="/solicitudes">
              Cancelar
            </Link>
            <Button type="submit" disabled={busy || !socio || !libro || socioSel?.estado !== "HABILITADO"}>
              {busy ? "Registrando…" : "Registrar solicitud"}
            </Button>
          </div>
        </div>

        <aside className="grid gap-4">
          <section className="side-help">
            <p className="kicker">Resumen</p>
            <p className="text-sm">
              Tipo:{" "}
              <Badge value={tipo} />
            </p>
            <p className="mt-2 text-sm text-[var(--muted-foreground)]">
              {tipo === "LOCAL"
                ? "La copia ya está en la sede donde se retira: se entrega en el mostrador."
                : "La copia viaja entre sedes en un remito; se entrega cuando llega."}
            </p>
          </section>
          <PatternNote pattern="Strategy">
            El tipo define la estrategia de tramitación:{" "}
            <code>{tipo === "LOCAL" ? "TramitacionLocal" : "TramitacionInterbibliotecaria"}</code>
            . Ambas validan las sedes al crear y saben “preparar la entrega”,
            cada una a su manera.
          </PatternNote>
        </aside>
      </form>
    </>
  );
}
