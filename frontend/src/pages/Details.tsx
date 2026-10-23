import { useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import type { Resource } from "../domain/models";
import type { Command } from "../api/contracts";
import { useLibrary } from "../app/context";
import {
  available,
  authorNames,
  bookName,
  code,
  dateLabel,
  daysLate,
  isOverdue,
  sedeName,
  socioName,
  statusLabels,
} from "../domain/selectors";
import {
  Alert,
  Back,
  Badge,
  Button,
  Heading,
  outlineClass,
  panelClass,
  primaryClass,
  Table,
} from "../components/ui";
import { config, pathOf } from "./resources";
import { Cover } from "./Lists";
import { actionLabels, CommandDialog } from "./Commands";

const labels: Record<string, string> = {
  numero_socio: "Número de socio",
  documento: "Documento",
  nombre: "Nombre",
  contacto: "Contacto",
  direccion: "Dirección",
  horarios: "Horarios",
  estado: "Estado",
  titulo: "Título",
  isbn: "ISBN",
  editorial: "Editorial",
  edicion: "Edición",
  codigo_inventario: "Código de inventario",
  condicion_fisica: "Condición física",
  libro_id: "Libro",
  socio_id: "Socio",
  sede_propietaria_id: "Sede propietaria",
  sede_actual_id: "Ubicación actual",
  sede_origen_id: "Sede de origen",
  sede_destino_id: "Sede de retiro / destino",
  sede_retiro_id: "Sede de retiro",
  ejemplar_id: "Ejemplar",
  ejemplar_asignado_id: "Ejemplar asignado",
  reserva_id: "Reserva",
  solicitud_id: "Solicitud",
  numero: "Número",
  tipo: "Circuito",
  fecha_solicitud: "Fecha de solicitud",
  fecha_entrega: "Fecha de entrega",
  fecha_vencimiento: "Fecha de vencimiento",
  fecha_devolucion: "Fecha de devolución",
  condicion_devolucion: "Condición de devolución",
  fecha_reserva: "Fecha de reserva",
  fecha_limite_retiro: "Fecha límite de retiro",
  fecha_creacion: "Fecha de creación",
  fecha_despacho: "Fecha de despacho",
  fecha_recepcion: "Fecha de recepción",
};
export function EntityDetail({ resource }: { resource: Resource }) {
  const { id } = useParams();
  const { db } = useLibrary();
  const n = Number(id);
  const [action, setAction] = useState<Command | null>(null);
  const record = db![resource].find((r) => r.id === n);
  if (!record)
    return (
      <>
        <Back to={`/${pathOf(resource)}`} />
        <Alert error>No encontramos ese registro.</Alert>
      </>
    );
  const data = record as unknown as Record<string, string | number | null>;
  const name =
    resource === "libros"
      ? String(data.titulo)
      : resource === "socios" || resource === "sedes"
        ? String(data.nombre)
        : resource === "remitos"
          ? String(data.numero)
          : resource === "ejemplares"
            ? String(data.codigo_inventario)
            : code(
                resource === "solicitudes"
                  ? "SOL"
                  : resource === "prestamos"
                    ? "PRE"
                    : "RES",
                n,
              );
  const actions: Command[] = [];
  if (resource === "socios")
    actions.push(data.estado === "HABILITADO" ? "inhabilitar" : "habilitar");
  if (resource === "sedes")
    actions.push(data.estado === "ACTIVA" ? "dar-de-baja" : "reactivar");
  if (resource === "ejemplares") {
    if (["DISPONIBLE", "EN_REVISION"].includes(String(data.estado)))
      actions.push("dar-de-baja");
    if (data.estado === "EN_REVISION") actions.push("aprobar-disponibilidad");
  }
  if (resource === "solicitudes") {
    if (data.estado === "PENDIENTE") actions.push("asignar", "rechazar");
    if (data.estado === "ASIGNADA" && data.tipo === "LOCAL")
      actions.push("preparar-entrega");
    if (data.estado === "LISTA_PARA_ENTREGA") actions.push("entregar");
    if (["PENDIENTE", "ASIGNADA"].includes(String(data.estado)))
      actions.push("cancelar");
  }
  if (resource === "prestamos" && !data.fecha_devolucion)
    actions.push("devolver");
  if (resource === "reservas") {
    if (data.estado === "PENDIENTE") actions.push("asignar-reserva");
    if (["PENDIENTE", "LISTA_PARA_RETIRO"].includes(String(data.estado)))
      actions.push("cancelar");
    if (
      data.estado === "LISTA_PARA_RETIRO" &&
      data.fecha_limite_retiro &&
      Date.parse(String(data.fecha_limite_retiro)) < Date.now()
    )
      actions.push("expirar");
  }
  if (resource === "remitos") {
    if (data.estado === "EN_PREPARACION")
      actions.push("asignar", "empaquetar", "cancelar");
    if (data.estado === "EMPAQUETADO") actions.push("despachar", "cancelar");
    if (data.estado === "DESPACHADO") actions.push("registrar-salida");
    if (data.estado === "EN_TRANSITO") actions.push("recibir");
  }
  function display(k: string, v: string | number | null): ReactNode {
    if (v === null || v === "") return "—";
    if (
      k === "estado" ||
      k === "condicion_fisica" ||
      k === "condicion_devolucion"
    )
      return <Badge value={String(v)} />;
    if (k.startsWith("fecha_")) return dateLabel(String(v));
    if (k.startsWith("sede_")) return sedeName(Number(v), db!);
    if (k === "libro_id")
      return (
        <Link className="underline underline-offset-4" to={`/catalogo/${v}`}>
          {bookName(Number(v), db!)}
        </Link>
      );
    if (k === "socio_id")
      return (
        <Link className="underline underline-offset-4" to={`/socios/${v}`}>
          {socioName(Number(v), db!)}
        </Link>
      );
    if (k === "solicitud_id")
      return (
        <Link className="underline underline-offset-4" to={`/solicitudes/${v}`}>
          {code("SOL", Number(v))}
        </Link>
      );
    if (k === "reserva_id")
      return (
        <Link className="underline underline-offset-4" to={`/reservas/${v}`}>
          {code("RES", Number(v))}
        </Link>
      );
    if (k === "ejemplar_id" || k === "ejemplar_asignado_id")
      return (
        <Link className="underline underline-offset-4" to={`/ejemplares/${v}`}>
          {db!.ejemplares.find((e) => e.id === v)?.codigo_inventario}
        </Link>
      );
    return statusLabels[String(v)] ?? v;
  }
  const editable = ["socios", "sedes", "libros", "ejemplares"].includes(
    resource,
  );
  const es =
    resource === "libros" ? db!.ejemplares.filter((e) => e.libro_id === n) : [];
  const s =
    resource === "prestamos"
      ? db!.solicitudes.find((s) => s.id === data.solicitud_id)
      : undefined;
  return (
    <>
      <Back to={`/${pathOf(resource)}`} />
      <Heading
        title={
          resource === "solicitudes"
            ? `Solicitud ${name}`
            : resource === "prestamos"
              ? `Préstamo ${name}`
              : name
        }
        description={
          resource === "libros"
            ? authorNames(
                db!.libros.find((b) => b.id === n)!,
                db!,
              )
            : config[resource]!.description
        }
        action={
          editable && (
            <Link
              className={outlineClass}
              to={`/${pathOf(resource)}/${n}/editar`}
            >
              Editar {config[resource]!.singular}
            </Link>
          )
        }
      />
      <div className="mb-8 flex flex-wrap gap-3">
        {actions.map((a) => (
          <Button
            key={a}
            variant={
              ["cancelar", "inhabilitar", "dar-de-baja"].includes(a)
                ? "outline"
                : "primary"
            }
            onClick={() => setAction(a)}
          >
            {resource === "remitos" && a === "asignar"
              ? "Agregar ejemplar"
              : actionLabels[a]}
          </Button>
        ))}
        {resource === "solicitudes" &&
          data.tipo === "INTERBIBLIOTECARIO" &&
          data.estado === "ASIGNADA" && (
            <Link className={primaryClass} to="/remitos/nuevo">
              Preparar remito
            </Link>
          )}
        {resource === "reservas" && data.estado === "LISTA_PARA_RETIRO" && (
          <Link
            className={primaryClass}
            to={`/solicitudes/${db!.solicitudes.find((s) => s.reserva_id === n)?.id}`}
          >
            Registrar entrega
          </Link>
        )}
      </div>
      <section
        className={`${panelClass} record-sheet mb-8 flex flex-col gap-8 sm:flex-row`}
      >
        {resource === "libros" && <Cover id={n} title={name} large />}
        <dl className="grid flex-1 gap-x-8 gap-y-6 sm:grid-cols-2">
          {Object.entries(data)
            .filter(([k]) => k !== "id")
            .map(([k, v]) => (
              <div key={k}>
                <dt className="mb-2 text-xs text-[var(--muted-foreground)]">
                  {labels[k] ?? k}
                </dt>
                <dd className="break-words text-sm">{display(k, v)}</dd>
              </div>
            ))}
          {s && (
            <>
              <div>
                <dt className="mb-2 text-xs text-[var(--muted-foreground)]">
                  Socio y libro (desde solicitud)
                </dt>
                <dd className="text-sm">
                  {socioName(s.socio_id, db!)} · {bookName(s.libro_id, db!)}
                </dd>
              </div>
              <div>
                <dt className="mb-2 text-xs text-[var(--muted-foreground)]">
                  Situación
                </dt>
                <dd>
                  <Badge
                    value={
                      data.fecha_devolucion
                        ? "DEVUELTO"
                        : isOverdue(db!.prestamos.find((p) => p.id === n)!)
                          ? "VENCIDO"
                          : "ACTIVO"
                    }
                  />
                </dd>
              </div>
            </>
          )}
        </dl>
      </section>
      {resource === "libros" && (
        <>
          <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
            <h2 className="font-heading text-xl">Ejemplares en la red</h2>
            <Link
              to={`/ejemplares/nuevo?libro_id=${n}`}
              className={outlineClass}
            >
              Nuevo ejemplar
            </Link>
          </div>
          <Table
            headers={[
              "Ejemplar",
              "Sede propietaria",
              "Ubicación actual",
              "Estado",
              "",
            ]}
            rows={es.map((e) => [
              e.codigo_inventario,
              sedeName(e.sede_propietaria_id, db!),
              sedeName(e.sede_actual_id, db!),
              <Badge value={e.estado} />,
              available(e, db!) ? (
                <Link
                  className={outlineClass}
                  to={`/solicitudes/nuevo?libro_id=${n}&ejemplar_id=${e.id}`}
                >
                  Seleccionar
                </Link>
              ) : (
                <Link className={outlineClass} to={`/ejemplares/${e.id}`}>
                  Ver detalle
                </Link>
              ),
            ])}
          />
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              className={primaryClass}
              to={`/solicitudes/nuevo?libro_id=${n}`}
            >
              Nueva solicitud
            </Link>
            <Link className={outlineClass} to={`/reservas/nuevo?libro_id=${n}`}>
              Registrar reserva
            </Link>
            <Link className={outlineClass} to={`/ejemplares?libro_id=${n}`}>
              Gestionar ejemplares
            </Link>
          </div>
        </>
      )}
      {resource === "socios" && (
        <>
          <h2 className="font-heading mb-5 text-xl">Solicitudes del socio</h2>
          <Table
            headers={["Solicitud", "Libro", "Estado", ""]}
            rows={db!.solicitudes
              .filter((s) => s.socio_id === n)
              .map((s) => [
                code("SOL", s.id),
                bookName(s.libro_id, db!),
                <Badge value={s.estado} />,
                <Link to={`/solicitudes/${s.id}`} className={outlineClass}>
                  Ver detalle
                </Link>,
              ])}
          />
        </>
      )}
      {resource === "sedes" && (
        <>
          <h2 className="font-heading mb-5 text-xl">Ejemplares de la sede</h2>
          <Table
            headers={["Ejemplar", "Libro", "Estado", ""]}
            rows={db!.ejemplares
              .filter((e) => e.sede_propietaria_id === n)
              .map((e) => [
                e.codigo_inventario,
                bookName(e.libro_id, db!),
                <Badge value={e.estado} />,
                <Link className={outlineClass} to={`/ejemplares/${e.id}`}>
                  Ver detalle
                </Link>,
              ])}
          />
        </>
      )}
      {resource === "solicitudes" && (
        <>
          <h2 className="font-heading mb-5 text-xl">Seguimiento</h2>
          <section className={panelClass}>
            <p className="text-sm">
              Solicitud registrada · {dateLabel(String(data.fecha_solicitud))}
            </p>
            <p className="my-4 text-sm">
              Estado actual: {statusLabels[String(data.estado)]}
            </p>
            {db!.detalle_remitos
              .filter((d) => d.solicitud_id === n)
              .map((d) => (
                <Link
                  key={d.id}
                  className={`${outlineClass} mr-3`}
                  to={`/remitos/${d.remito_id}`}
                >
                  Ver remito{" "}
                  {db!.remitos.find((r) => r.id === d.remito_id)?.numero}
                </Link>
              ))}
            {db!.prestamos
              .filter((p) => p.solicitud_id === n)
              .map((p) => (
                <Link
                  key={p.id}
                  className={outlineClass}
                  to={`/prestamos/${p.id}`}
                >
                  Ver préstamo
                </Link>
              ))}
            {data.estado === "EN_TRASLADO" && (
              <Alert>
                La entrega al socio se habilita cuando el ejemplar llega a la
                sede de retiro.
              </Alert>
            )}
          </section>
        </>
      )}
      {resource === "remitos" && (
        <>
          <h2 className="font-heading mb-5 text-xl">Ejemplares del remito</h2>
          <Table
            headers={[
              "Ejemplar",
              "Libro",
              "Solicitud",
              "Condición de salida",
              "Recepción",
            ]}
            rows={db!.detalle_remitos
              .filter((d) => d.remito_id === n)
              .map((d) => {
                const e = db!.ejemplares.find((e) => e.id === d.ejemplar_id)!;
                return [
                  <Link className="underline" to={`/ejemplares/${e.id}`}>
                    {e.codigo_inventario}
                  </Link>,
                  bookName(e.libro_id, db!),
                  d.solicitud_id ? (
                    <Link
                      className="underline"
                      to={`/solicitudes/${d.solicitud_id}`}
                    >
                      {code("SOL", d.solicitud_id)}
                    </Link>
                  ) : (
                    "Traslado"
                  ),
                  statusLabels[d.condicion_salida] ?? d.condicion_salida,
                  d.condicion_recepcion
                    ? (statusLabels[d.condicion_recepcion] ??
                      d.condicion_recepcion)
                    : "Pendiente",
                ];
              })}
          />
          <h2 className="font-heading mt-8 mb-5 text-xl">
            Historial del remito
          </h2>
          <ol className={panelClass}>
            {db!.evento_remitos
              .filter((e) => e.remito_id === n)
              .sort(
                (a, b) => Date.parse(a.fecha_hora) - Date.parse(b.fecha_hora),
              )
              .map((e) => (
                <li
                  key={e.id}
                  className="border-l-2 border-[var(--border)] pb-6 pl-5 last:pb-0"
                >
                  <p className="text-sm font-medium">
                    {e.estado_anterior
                      ? `${statusLabels[e.estado_anterior]} → `
                      : ""}
                    {statusLabels[e.estado_nuevo]}
                  </p>
                  <p className="mt-2 text-xs text-[var(--muted-foreground)]">
                    {new Date(e.fecha_hora).toLocaleString("es-AR", {
                      timeZone: "America/Argentina/Buenos_Aires",
                    })}{" "}
                    · {e.responsable}
                  </p>
                  {e.observacion && (
                    <p className="mt-2 text-sm">{e.observacion}</p>
                  )}
                </li>
              ))}
          </ol>
        </>
      )}
      {action && (
        <CommandDialog
          resource={resource}
          id={n}
          action={action}
          onClose={() => setAction(null)}
        />
      )}
    </>
  );
}
