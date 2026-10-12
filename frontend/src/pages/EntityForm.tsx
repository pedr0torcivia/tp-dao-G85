import { useState, type FormEvent } from "react";
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import type { NewEntity, Resource } from "../domain/models";
import { authorNames } from "../domain/selectors";
import { api } from "../api";
import { ApiError } from "../api/contracts";
import { useLibrary } from "../app/context";
import {
  Alert,
  Back,
  Button,
  Field,
  Heading,
  inputClass,
  outlineClass,
  panelClass,
} from "../components/ui";
import { config, fieldsFor, pathOf } from "./resources";

export function EntityForm({ resource }: { resource: Resource }) {
  const { db, sedeId, refresh, notify } = useLibrary();
  const { id } = useParams();
  const [search] = useSearchParams();
  const navigate = useNavigate();
  const record = id
    ? db![resource].find((r) => r.id === Number(id))
    : undefined;
  const conf = config[resource]!;
  const [values, setValues] = useState<Record<string, string>>(() => {
    const result = record
      ? Object.fromEntries(
          Object.entries(record).map(([k, v]) => [k, String(v ?? "")]),
        )
      : {};
    if (resource === "libros" && record)
      result.autores = authorNames(
        db!.libros.find((b) => b.id === Number(id))!,
        db!,
      );
    if (!record) {
      result.sede_origen_id = String(sedeId);
      result.sede_destino_id = String(sedeId);
      result.sede_retiro_id = String(sedeId);
      result.sede_propietaria_id = String(sedeId);
      result.condicion_fisica = "APTO";
    }
    for (const k of ["libro_id", "ejemplar_id"])
      if (search.get(k)) result[k] = search.get(k)!;
    const e = db!.ejemplares.find((e) => e.id === Number(result.ejemplar_id));
    if (e && !record) result.sede_origen_id = String(e.sede_propietaria_id);
    return result;
  });
  const [error, setError] = useState<ApiError | null>(null),
    [busy, setBusy] = useState(false);
  if (id && !record)
    return (
      <>
        <Back to={`/${pathOf(resource)}`} />
        <Alert error>No encontramos ese registro.</Alert>
      </>
    );
  let fields = fieldsFor(resource, db!);
  if (resource === "solicitudes")
    fields = fields.map((f) =>
      f.key === "ejemplar_id"
        ? {
            ...f,
            options: f.options?.filter(([id]) => {
              const e = db!.ejemplares.find((e) => e.id === Number(id))!;
              return (
                e.libro_id === Number(values.libro_id) &&
                e.sede_propietaria_id === Number(values.sede_origen_id)
              );
            }),
          }
        : f,
    );
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const data: Record<string, unknown> = Object.fromEntries(
        fields
          .filter((f) => f.key !== "autores")
          .map((f) => [
            f.key,
            f.key.endsWith("_id")
              ? values[f.key]
                ? Number(values[f.key])
                : null
              : values[f.key]?.trim() || null,
          ]),
      );
      if (record)
        for (const [k, v] of Object.entries(record))
          if (data[k] === undefined) data[k] = v;
      const saved = await api.save(
        resource,
        data as NewEntity<typeof resource>,
        id ? Number(id) : undefined,
      );
      if (resource === "libros")
        await api.saveBookAuthors(saved.id, (values.autores ?? "").split(","));
      await refresh();
      notify("Los datos se guardaron correctamente.");
      navigate(`/${pathOf(resource)}/${saved.id}`);
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e
          : new ApiError("No pudimos guardar los datos."),
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Back to={`/${pathOf(resource)}`} />
      <Heading
        title={id ? `Editar ${conf.singular}` : conf.create}
        description={
          resource === "solicitudes"
            ? "Elegí el socio, el libro y la sede donde se retirará el ejemplar."
            : `Completá los datos de ${conf.singular}.`
        }
      />
      <form onSubmit={submit} className={`${panelClass} max-w-[860px]`}>
        {error && <Alert error>{error.message}</Alert>}
        <div className="grid gap-6 sm:grid-cols-2">
          {fields.map((f) => (
            <Field key={f.key} label={f.label} error={error?.fields[f.key]}>
              {f.type === "select" ? (
                <select
                  className={inputClass}
                  required={f.required}
                  value={values[f.key] ?? ""}
                  disabled={
                    !!id &&
                    resource === "ejemplares" &&
                    ["libro_id", "sede_propietaria_id"].includes(f.key)
                  }
                  onChange={(e) =>
                    setValues((v) => ({
                      ...v,
                      [f.key]: e.target.value,
                      ...(["libro_id", "sede_origen_id"].includes(f.key) &&
                      resource === "solicitudes"
                        ? { ejemplar_id: "" }
                        : {}),
                    }))
                  }
                >
                  <option value="">
                    {f.required ? "Seleccioná una opción" : "Sin asignar"}
                  </option>
                  {f.options?.map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              ) : f.type === "textarea" ? (
                <textarea
                  className={inputClass}
                  rows={3}
                  required={f.required}
                  value={values[f.key] ?? ""}
                  onChange={(e) =>
                    setValues((v) => ({ ...v, [f.key]: e.target.value }))
                  }
                />
              ) : (
                <input
                  className={inputClass}
                  required={f.required}
                  maxLength={
                    ["contacto", "direccion"].includes(f.key)
                      ? 255
                      : ["numero_socio", "documento"].includes(f.key)
                        ? 30
                        : 150
                  }
                  value={values[f.key] ?? ""}
                  onChange={(e) =>
                    setValues((v) => ({ ...v, [f.key]: e.target.value }))
                  }
                />
              )}
            </Field>
          ))}
        </div>
        {resource === "socios" && (
          <p className="mt-6 text-sm text-[var(--muted-foreground)]">
            Los nuevos socios comienzan habilitados. La habilitación se
            administra desde su ficha.
          </p>
        )}
        {resource === "solicitudes" && (
          <Alert>
            {values.sede_origen_id === values.sede_destino_id
              ? "Préstamo local"
              : "Préstamo interbibliotecario"}{" "}
            · La entrega al socio inicia el préstamo.
          </Alert>
        )}
        {resource === "reservas" && (
          <Alert>
            La reserva puede registrarse antes de asignar un ejemplar. El plazo
            de retiro se indica al preparar la asignación.
          </Alert>
        )}
        {resource === "remitos" && (
          <Alert>
            Podés guardar un remito vacío en preparación. Después agregá los
            ejemplares desde su detalle.
          </Alert>
        )}
        <div className="mt-8 flex justify-end gap-3">
          <Link className={outlineClass} to={`/${pathOf(resource)}`}>
            Cancelar
          </Link>
          <Button disabled={busy} type="submit">
            {busy
              ? "Guardando…"
              : resource === "solicitudes"
                ? "Crear solicitud"
                : resource === "reservas"
                  ? "Crear reserva"
                  : resource === "remitos"
                    ? "Guardar preparación"
                    : `Guardar ${conf.singular}`}
          </Button>
        </div>
      </form>
    </>
  );
}
