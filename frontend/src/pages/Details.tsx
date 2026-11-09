import { useState, type ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Pencil, Undo2 } from "lucide-react";
import type {
  Database,
  EstadoRemito,
  OperacionRemito,
  Resource,
} from "../domain/models";
import type { Command } from "../api/contracts";
import { api } from "../api";
import { useLibrary } from "../app/context";
import {
  available,
  bookName,
  code,
  dateLabel,
  dateTimeLabel,
  inOpenRemito,
  loanState,
  pesos,
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
  PatternNote,
  primaryClass,
  Stepper,
  Table,
} from "../components/ui";
import { config, pathOf } from "./resources";
import { Cover } from "./Lists";
import { actionLabels, CommandDialog } from "./Commands";

const remitoOps: Record<OperacionRemito, Command> = {
  agregar: "asignar",
  quitar: "quitar",
  empaquetar: "empaquetar",
  reabrir: "reabrir",
  despachar: "despachar",
  recibir: "recibir",
  cancelar: "cancelar",
};
const remitoOpLabels: Record<OperacionRemito, string> = {
  agregar: "Agregar ejemplar",
  quitar: "Quitar ejemplar",
  empaquetar: "Empaquetar",
  reabrir: "Reabrir",
  despachar: "Despachar",
  recibir: "Recibir envío",
  cancelar: "Cancelar envío",
};
const nextHint: Partial<Record<EstadoRemito, string>> = {
  EN_PREPARACION:
    "Agregá los ejemplares que viajan y empaquetá cuando el paquete esté completo.",
  EMPAQUETADO:
    "El paquete está cerrado. Despachalo cuando lo retire el transporte (o reabrilo para corregirlo).",
  EN_TRANSITO:
    "El material está viajando. La sede destino debe recibirlo y verificar cada ejemplar.",
  RECIBIDO: "El envío llegó completo y en condiciones. No requiere más acciones.",
  RECIBIDO_CON_INCIDENCIAS:
    "El envío llegó con daños o faltantes. Las solicitudes afectadas volvieron a la cola.",
  CANCELADO: "El envío se anuló antes de salir.",
};
const solicitudHint: Record<string, string> = {
  PENDIENTE:
    "Hay que asignarle una copia disponible de la sede de origen.",
  ASIGNADA: "La copia está reservada. Falta prepararla para la entrega.",
  EN_TRASLADO:
    "La copia viaja en un remito. La entrega se habilita cuando la sede de retiro la recibe.",
  LISTA_PARA_ENTREGA: "El socio puede retirar el libro: registrá la entrega.",
  CUMPLIDA: "Se entregó al socio y se generó el préstamo.",
  RECHAZADA: "La solicitud se rechazó.",
  CANCELADA: "La solicitud se canceló.",
};

function Facts({ items }: { items: [string, ReactNode][] }) {
  return (
    <dl className="facts">
      {items.map(([k, v]) => (
        <div key={k}>
          <dt>{k}</dt>
          <dd>{v ?? "—"}</dd>
        </div>
      ))}
    </dl>
  );
}
const linkTo = (to: string, label: ReactNode) => <Link to={to}>{label}</Link>;

function NextStep({
  title,
  text,
  children,
}: {
  title: string;
  text: ReactNode;
  children?: ReactNode;
}) {
  return (
    <section className="card card-pad next-step">
      <h3>{title}</h3>
      <p>{text}</p>
      {children && <div className="action-stack">{children}</div>}
    </section>
  );
}

export function EntityDetail({ resource }: { resource: Resource }) {
  const { id } = useParams();
  const { db, refresh, notify } = useLibrary();
  const navigate = useNavigate();
  const n = Number(id);
  const [action, setAction] = useState<{ resource: Resource; id: number; command: Command } | null>(null);
  const [busy, setBusy] = useState(false);
  const record = db![resource].find((r) => r.id === n);
  if (!record)
    return (
      <>
        <Back to={`/${pathOf(resource)}`} />
        <Alert error>No encontramos ese registro.</Alert>
      </>
    );
  const run = (command: Command, target: Resource = resource, targetId = n) =>
    setAction({ resource: target, id: targetId, command });

  async function retorno(ejemplarId: number) {
    setBusy(true);
    try {
      const remito = await api.prepararRetorno(ejemplarId);
      await refresh();
      notify("Ejemplar agregado al remito de retorno.");
      navigate(`/remitos/${remito.id}`);
    } catch (e) {
      notify(e instanceof Error ? e.message : "No pudimos preparar el retorno.");
    } finally {
      setBusy(false);
    }
  }

  let body: ReactNode = null;
  let title: ReactNode = "";
  let kicker: ReactNode = config[resource]?.singular;
  let headerActions: ReactNode = null;
  const editable = ["socios", "sedes", "libros", "ejemplares"].includes(resource);
  if (editable)
    headerActions = (
      <Link className={outlineClass} to={`/${pathOf(resource)}/${n}/editar`}>
        <Pencil size={15} /> Editar
      </Link>
    );

  if (resource === "solicitudes") {
    const s = db!.solicitudes.find((x) => x.id === n)!;
    const prestamo = db!.prestamos.find((p) => p.solicitud_id === n);
    const remito = s.remito_id ? db!.remitos.find((r) => r.id === s.remito_id) : undefined;
    const cerrada = ["RECHAZADA", "CANCELADA"].includes(s.estado);
    title = `Solicitud ${code("SOL", n)}`;
    kicker = (
      <>
        Solicitud {statusLabels[s.tipo].toLowerCase()} <Badge value={s.estado} />
      </>
    );
    body = (
      <>
        <section className="card card-pad mb-4">
          {cerrada ? (
            <Alert tone="neutral">{solicitudHint[s.estado]}</Alert>
          ) : (
            <Stepper
              current={s.estado}
              steps={s.recorrido.map((e) => ({ key: e, label: statusLabels[e] }))}
            />
          )}
        </section>
        <div className="detail-grid">
          <div className="grid gap-4">
            <section className="card card-pad">
              <Facts
                items={[
                  ["Socio", linkTo(`/socios/${s.socio_id}`, socioName(s.socio_id, db!))],
                  ["Libro", linkTo(`/catalogo/${s.libro_id}`, bookName(s.libro_id, db!))],
                  ["Sale de", sedeName(s.sede_origen_id, db!)],
                  ["Se retira en", sedeName(s.sede_destino_id, db!)],
                  [
                    "Ejemplar",
                    s.ejemplar_id
                      ? linkTo(
                          `/ejemplares/${s.ejemplar_id}`,
                          db!.ejemplares.find((e) => e.id === s.ejemplar_id)?.codigo_inventario,
                        )
                      : "Sin asignar",
                  ],
                  ["Registrada", dateTimeLabel(s.fecha_solicitud)],
                  ...(remito
                    ? ([["Remito", linkTo(`/remitos/${remito.id}`, `${remito.numero} · ${statusLabels[remito.estado]}`)]] as [string, ReactNode][])
                    : []),
                  ...(s.reserva_id
                    ? ([["Reserva", linkTo(`/reservas/${s.reserva_id}`, code("RES", s.reserva_id))]] as [string, ReactNode][])
                    : []),
                  ...(prestamo
                    ? ([["Préstamo", linkTo(`/prestamos/${prestamo.id}`, code("PRE", prestamo.id))]] as [string, ReactNode][])
                    : []),
                ]}
              />
            </section>
          </div>
          <div className="grid gap-4">
            <NextStep
              title="Qué sigue"
              text={
                s.estado === "ASIGNADA" && remito && !s.acciones.includes("preparar-entrega")
                  ? `La copia ya viaja en el remito ${remito.numero} (${statusLabels[remito.estado].toLowerCase()}). ${sedeName(s.sede_origen_id, db!)} lo empaqueta y despacha; cuando ${sedeName(s.sede_destino_id, db!)} lo reciba, se habilita la entrega.`
                  : solicitudHint[s.estado]
              }
            >
              {s.acciones.map((a) => (
                <Button
                  key={a}
                  size="sm"
                  variant={["cancelar", "rechazar"].includes(a) ? "danger" : "primary"}
                  onClick={() => run(a as Command)}
                >
                  {actionLabels[a as Command]}
                </Button>
              ))}
              {s.estado === "ASIGNADA" && remito && (
                <Link className="btn btn-outline btn-sm" to={`/remitos/${remito.id}`}>
                  Ir al remito {remito.numero}
                </Link>
              )}
              {s.estado === "EN_TRASLADO" && remito && (
                <Link className="btn btn-outline btn-sm" to={`/remitos/${remito.id}`}>
                  Seguir el envío
                </Link>
              )}
            </NextStep>
            <PatternNote pattern="Strategy">
              El tipo de la solicitud elige la estrategia{" "}
              <code>{s.estrategia}</code>. Al preparar la entrega:{" "}
              {s.estrategia_descripcion} El resto del circuito (asignar,
              entregar, devolver) es común a ambos tipos.
            </PatternNote>
          </div>
        </div>
      </>
    );
  }

  if (resource === "remitos") {
    const r = db!.remitos.find((x) => x.id === n)!;
    const detalles = db!.detalle_remitos.filter((d) => d.remito_id === n);
    const eventos = db!.evento_remitos
      .filter((e) => e.remito_id === n)
      .sort((a, b) => Date.parse(a.fecha_hora) - Date.parse(b.fecha_hora) || a.id - b.id);
    const incid = r.estado === "RECIBIDO_CON_INCIDENCIAS";
    title = `Remito ${r.numero}`;
    kicker = (
      <>
        {sedeName(r.sede_origen_id, db!)} → {sedeName(r.sede_destino_id, db!)}{" "}
        <Badge value={r.estado} />
      </>
    );
    const ops: OperacionRemito[] = ["agregar", "quitar", "empaquetar", "reabrir", "despachar", "recibir", "cancelar"];
    body = (
      <>
        <section className="card card-pad mb-4">
          {r.estado === "CANCELADO" ? (
            <Alert tone="neutral">Este envío fue cancelado antes de salir.</Alert>
          ) : (
            <Stepper
              current={incid ? "RECIBIDO" : r.estado}
              failed={incid}
              steps={[
                { key: "EN_PREPARACION", label: "En preparación", hint: dateLabel(r.fecha_creacion) },
                { key: "EMPAQUETADO", label: "Empaquetado" },
                { key: "EN_TRANSITO", label: "En tránsito", hint: r.fecha_despacho ? dateLabel(r.fecha_despacho) : undefined },
                {
                  key: "RECIBIDO",
                  label: incid ? "Recibido con incidencias" : "Recibido",
                  hint: r.fecha_recepcion ? dateLabel(r.fecha_recepcion) : undefined,
                },
              ]}
            />
          )}
        </section>
        <div className="detail-grid">
          <div className="grid min-w-0 gap-4">
            <h2 className="section-title !mt-0">Contenido del paquete</h2>
            <Table
              headers={["Ejemplar", "Libro", "Motivo", "Salió", "Llegó"]}
              rows={detalles.map((d) => {
                const e = db!.ejemplares.find((x) => x.id === d.ejemplar_id)!;
                return [
                  <Link className="mono underline" to={`/ejemplares/${e.id}`}>{e.codigo_inventario}</Link>,
                  bookName(e.libro_id, db!),
                  d.solicitud_id ? (
                    <Link className="underline" to={`/solicitudes/${d.solicitud_id}`}>
                      Pedido {code("SOL", d.solicitud_id)}
                    </Link>
                  ) : e.sede_propietaria_id === r.sede_destino_id ? (
                    "Retorno a su sede"
                  ) : (
                    "Traslado"
                  ),
                  <Badge value={d.condicion_salida} />,
                  d.resultado_recepcion ? <Badge value={d.resultado_recepcion} /> : <span className="muted">—</span>,
                ];
              })}
              empty={
                <div className="empty">
                  <strong>El paquete está vacío</strong>
                  <span>Agregá al menos un ejemplar para poder empaquetarlo.</span>
                </div>
              }
            />
            <h2 className="section-title">Trazabilidad</h2>
            <section className="card card-pad">
              <ol className="timeline">
                {eventos.map((e) => (
                  <li key={e.id}>
                    <b>
                      {e.estado_anterior ? `${statusLabels[e.estado_anterior] ?? e.estado_anterior} → ` : ""}
                      {statusLabels[e.estado_nuevo] ?? e.estado_nuevo}
                    </b>
                    <small>
                      {dateTimeLabel(e.fecha_hora)} · {e.responsable}
                      {e.observacion ? ` · ${e.observacion}` : ""}
                    </small>
                  </li>
                ))}
              </ol>
            </section>
          </div>
          <div className="grid gap-4">
            <NextStep title="Qué sigue" text={nextHint[r.estado]}>
              {r.acciones.map((op) => (
                <Button
                  key={op}
                  size="sm"
                  variant={op === "cancelar" ? "danger" : op === "quitar" || op === "reabrir" ? "outline" : "primary"}
                  disabled={(op === "quitar" || op === "empaquetar") && !detalles.length}
                  onClick={() => run(remitoOps[op])}
                >
                  {remitoOpLabels[op]}
                </Button>
              ))}
            </NextStep>
            <PatternNote pattern="State">
              El remito delega cada operación en el objeto de su estado actual,{" "}
              <code>{r.estado_clase}</code>: {r.estado_descripcion}
              <div className="ops" aria-label="Operaciones del estado">
                {ops.map((op) => (
                  <span key={op} className={`op ${r.acciones.includes(op) ? "on" : "off"}`}>
                    {op}()
                  </span>
                ))}
              </div>
              <p className="mt-2 text-xs text-[var(--muted-foreground)]">
                Verde: lo que este estado admite. Tachado: lo rechaza con un
                error de transición.
              </p>
            </PatternNote>
          </div>
        </div>
      </>
    );
  }

  if (resource === "prestamos") {
    const p = db!.prestamos.find((x) => x.id === n)!;
    const s = db!.solicitudes.find((x) => x.id === p.solicitud_id)!;
    const e = db!.ejemplares.find((x) => x.id === s.ejemplar_id);
    const estado = loanState(p);
    const debeVolver =
      e && e.estado === "EN_REVISION" && e.sede_actual_id !== e.sede_propietaria_id && !inOpenRemito(e.id, db!);
    title = `Préstamo ${code("PRE", n)}`;
    kicker = (
      <>
        Préstamo <Badge value={estado} />
      </>
    );
    body = (
      <div className="detail-grid">
        <section className="card card-pad">
          <Facts
            items={[
              ["Socio", linkTo(`/socios/${s.socio_id}`, socioName(s.socio_id, db!))],
              ["Libro", linkTo(`/catalogo/${s.libro_id}`, bookName(s.libro_id, db!))],
              ["Ejemplar", e ? linkTo(`/ejemplares/${e.id}`, e.codigo_inventario) : "—"],
              ["Entregado en", sedeName(s.sede_destino_id, db!)],
              ["Entrega", dateTimeLabel(p.fecha_entrega)],
              ["Vence", dateTimeLabel(p.fecha_vencimiento)],
              ["Devolución", p.fecha_devolucion ? dateTimeLabel(p.fecha_devolucion) : "Pendiente"],
              ["Estado al devolver", p.condicion_devolucion ? <Badge value={p.condicion_devolucion} /> : "—"],
              ["Días de atraso", p.dias_atraso ? <b className="text-[var(--bad)]">{p.dias_atraso}</b> : "0"],
              ["Multa", p.multa ? <b className="text-[var(--bad)]">{pesos(p.multa)}</b> : pesos(0)],
              ["Solicitud", linkTo(`/solicitudes/${s.id}`, code("SOL", s.id))],
            ]}
          />
        </section>
        <NextStep
          title="Qué sigue"
          text={
            !p.fecha_devolucion
              ? estado === "VENCIDO"
                ? `Está vencido: acumula ${pesos(p.multa)} de multa. Al devolverlo, el ejemplar pasa a revisión.`
                : "Cuando el socio devuelva el libro, registrá la devolución y el estado del material."
              : debeVolver
                ? "El ejemplar es de otra sede: armá el remito de retorno."
                : "El préstamo está cerrado."
          }
        >
          {!p.fecha_devolucion && (
            <Button size="sm" onClick={() => run("devolver")}>
              Registrar devolución
            </Button>
          )}
          {debeVolver && e && (
            <Button size="sm" disabled={busy} onClick={() => void retorno(e.id)}>
              <Undo2 size={14} /> Preparar retorno
            </Button>
          )}
        </NextStep>
      </div>
    );
  }

  if (resource === "reservas") {
    const r = db!.reservas.find((x) => x.id === n)!;
    const s = db!.solicitudes.find((x) => x.reserva_id === n);
    const vencida =
      r.estado === "LISTA_PARA_RETIRO" && r.fecha_limite_retiro && Date.parse(r.fecha_limite_retiro) < Date.now();
    title = `Reserva ${code("RES", n)}`;
    kicker = (
      <>
        Reserva <Badge value={r.estado} />
      </>
    );
    body = (
      <>
        <section className="card card-pad mb-4">
          {["CANCELADA", "EXPIRADA"].includes(r.estado) ? (
            <Alert tone="neutral">La reserva está {statusLabels[r.estado].toLowerCase()}.</Alert>
          ) : (
            <Stepper
              current={r.estado}
              steps={[
                { key: "PENDIENTE", label: "En espera", hint: "Sin copia apartada" },
                { key: "LISTA_PARA_RETIRO", label: "Lista para retirar", hint: r.fecha_limite_retiro ? `hasta ${dateLabel(r.fecha_limite_retiro)}` : undefined },
                { key: "CUMPLIDA", label: "Retirada" },
              ]}
            />
          )}
        </section>
        <div className="detail-grid">
          <section className="card card-pad">
            <Facts
              items={[
                ["Socio", linkTo(`/socios/${r.socio_id}`, socioName(r.socio_id, db!))],
                ["Libro", linkTo(`/catalogo/${r.libro_id}`, bookName(r.libro_id, db!))],
                ["Sede de retiro", sedeName(r.sede_retiro_id, db!)],
                ["Reservada", dateTimeLabel(r.fecha_reserva)],
                ["Retirar hasta", dateTimeLabel(r.fecha_limite_retiro)],
                [
                  "Ejemplar apartado",
                  r.ejemplar_asignado_id
                    ? linkTo(`/ejemplares/${r.ejemplar_asignado_id}`, db!.ejemplares.find((e) => e.id === r.ejemplar_asignado_id)?.codigo_inventario)
                    : "—",
                ],
              ]}
            />
          </section>
          <NextStep
            title="Qué sigue"
            text={
              r.estado === "PENDIENTE"
                ? "Cuando haya una copia disponible en la sede de retiro, apartala para el socio."
                : r.estado === "LISTA_PARA_RETIRO"
                  ? vencida
                    ? "Venció el plazo de retiro. Podés marcarla como expirada para liberar la copia."
                    : "La copia está apartada en mostrador. Entregala cuando el socio venga."
                  : "La reserva está cerrada."
            }
          >
            {r.estado === "PENDIENTE" && (
              <Button size="sm" onClick={() => run("asignar-reserva")}>Apartar copia</Button>
            )}
            {r.estado === "LISTA_PARA_RETIRO" && s && !vencida && (
              <Button size="sm" onClick={() => run("entregar", "solicitudes", s.id)}>Entregar al socio</Button>
            )}
            {vencida && (
              <Button size="sm" variant="outline" onClick={() => run("expirar")}>Marcar como expirada</Button>
            )}
            {["PENDIENTE", "LISTA_PARA_RETIRO"].includes(r.estado) && (
              <Button size="sm" variant="danger" onClick={() => run("cancelar")}>Cancelar reserva</Button>
            )}
          </NextStep>
        </div>
      </>
    );
  }

  if (resource === "ejemplares") {
    const e = db!.ejemplares.find((x) => x.id === n)!;
    const lejos = e.sede_actual_id !== null && e.sede_actual_id !== e.sede_propietaria_id;
    const viaja = inOpenRemito(e.id, db!);
    title = e.codigo_inventario;
    kicker = (
      <>
        Ejemplar <Badge value={e.estado} />
      </>
    );
    const historial = db!.detalle_remitos.filter((d) => d.ejemplar_id === n);
    body = (
      <>
        <div className="detail-grid">
          <section className="card card-pad flex flex-col gap-6 sm:flex-row">
            <Cover id={e.libro_id} title={bookName(e.libro_id, db!)} large />
            <Facts
              items={[
                ["Libro", linkTo(`/catalogo/${e.libro_id}`, bookName(e.libro_id, db!))],
                ["Pertenece a", sedeName(e.sede_propietaria_id, db!)],
                ["Está en", e.sede_actual_id === null ? "Viajando" : sedeName(e.sede_actual_id, db!)],
                ["Estado", <Badge value={e.estado} />],
                ["Condición", <Badge value={e.condicion_fisica} />],
                ["Alta", dateLabel(e.fecha_alta ?? null)],
              ]}
            />
          </section>
          <NextStep
            title="Qué sigue"
            text={
              e.estado === "EN_REVISION"
                ? lejos
                  ? viaja
                    ? "Ya está incluido en un remito de retorno."
                    : "Está fuera de su sede: armá el remito de retorno."
                  : e.condicion_fisica === "APTO"
                    ? "Revisalo y aprobá su disponibilidad para que vuelva a circular."
                    : "No está apto. Repará y cambiá su condición (Editar) o dalo de baja."
                : e.estado === "DISPONIBLE"
                  ? "Disponible para préstamo."
                  : `Está ${statusLabels[e.estado].toLowerCase()}.`
            }
          >
            {e.estado === "EN_REVISION" && !lejos && e.condicion_fisica === "APTO" && (
              <Button size="sm" onClick={() => run("aprobar-disponibilidad")}>Aprobar disponibilidad</Button>
            )}
            {e.estado === "EN_REVISION" && lejos && !viaja && (
              <Button size="sm" disabled={busy} onClick={() => void retorno(e.id)}>
                <Undo2 size={14} /> Preparar retorno
              </Button>
            )}
            {["DISPONIBLE", "EN_REVISION"].includes(e.estado) && (
              <Button size="sm" variant="danger" onClick={() => run("dar-de-baja")}>Dar de baja</Button>
            )}
          </NextStep>
        </div>
        <h2 className="section-title">Recorrido entre sedes</h2>
        <Table
          headers={["Remito", "Trayecto", "Estado", "Resultado"]}
          rows={historial.map((d) => {
            const r = db!.remitos.find((x) => x.id === d.remito_id)!;
            return [
              <Link className="underline" to={`/remitos/${r.id}`}>{r.numero}</Link>,
              `${sedeName(r.sede_origen_id, db!)} → ${sedeName(r.sede_destino_id, db!)}`,
              <Badge value={r.estado} />,
              d.resultado_recepcion ? <Badge value={d.resultado_recepcion} /> : "—",
            ];
          })}
          empty={<div className="empty">Este ejemplar nunca viajó entre sedes.</div>}
        />
      </>
    );
  }

  if (resource === "libros") {
    const b = db!.libros.find((x) => x.id === n)!;
    const es = db!.ejemplares.filter((e) => e.libro_id === n);
    title = b.titulo;
    kicker = "Catálogo";
    body = <BookDetail db={db!} id={n} />;
    headerActions = (
      <>
        {headerActions}
        <Link className={primaryClass} to={`/solicitudes/nuevo?libro_id=${n}`}>Pedir este libro</Link>
      </>
    );
    void es;
  }

  if (resource === "socios") {
    const s = db!.socios.find((x) => x.id === n)!;
    title = s.nombre;
    kicker = (
      <>
        Socio N.º {s.numero_socio} <Badge value={s.estado} />
      </>
    );
    const sols = db!.solicitudes.filter((x) => x.socio_id === n);
    const prestamos = db!.prestamos.filter((p) => sols.some((x) => x.id === p.solicitud_id));
    const deuda = prestamos.reduce((acc, p) => acc + (p.multa || 0), 0);
    body = (
      <>
        <div className="detail-grid">
          <section className="card card-pad">
            <Facts
              items={[
                ["Documento", s.documento],
                ["Contacto", s.contacto],
                ["Préstamos activos", prestamos.filter((p) => !p.fecha_devolucion).length],
                ["Multas", deuda ? <b className="text-[var(--bad)]">{pesos(deuda)}</b> : pesos(0)],
              ]}
            />
          </section>
          <NextStep
            title="Habilitación"
            text={
              s.estado === "HABILITADO"
                ? "Puede pedir préstamos y reservas."
                : "No puede iniciar préstamos ni reservas. Sí puede devolver."
            }
          >
            <Button
              size="sm"
              variant={s.estado === "HABILITADO" ? "danger" : "primary"}
              onClick={() => run(s.estado === "HABILITADO" ? "inhabilitar" : "habilitar")}
            >
              {s.estado === "HABILITADO" ? "Inhabilitar" : "Habilitar"}
            </Button>
            {s.estado === "HABILITADO" && (
              <Link className="btn btn-outline btn-sm" to={`/solicitudes/nuevo?socio_id=${n}`}>
                Nueva solicitud
              </Link>
            )}
          </NextStep>
        </div>
        <h2 className="section-title">Historial de lectura</h2>
        <Table
          headers={["Solicitud", "Libro", "Estado", "Préstamo"]}
          onRowClick={(i) => navigate(`/solicitudes/${sols[i].id}`)}
          rows={sols.map((x) => {
            const p = prestamos.find((pp) => pp.solicitud_id === x.id);
            return [
              <span className="mono">{code("SOL", x.id)}</span>,
              bookName(x.libro_id, db!),
              <Badge value={x.estado} />,
              p ? <Badge value={loanState(p)} /> : "—",
            ];
          })}
          empty={<div className="empty">Todavía no pidió libros.</div>}
        />
      </>
    );
  }

  if (resource === "sedes") {
    const s = db!.sedes.find((x) => x.id === n)!;
    title = s.nombre;
    kicker = (
      <>
        Sede <Badge value={s.estado} />
      </>
    );
    const propios = db!.ejemplares.filter((e) => e.sede_propietaria_id === n);
    body = (
      <>
        <div className="detail-grid">
          <section className="card card-pad">
            <Facts
              items={[
                ["Dirección", s.direccion],
                ["Contacto", s.contacto],
                ["Horarios", s.horarios],
                ["Ejemplares propios", propios.length],
                ["Disponibles", propios.filter((e) => available(e, db!)).length],
              ]}
            />
          </section>
          <NextStep
            title="Estado en la red"
            text={
              s.estado === "ACTIVA"
                ? "Opera normalmente. Darla de baja impide iniciar préstamos, reservas y envíos desde o hacia ella."
                : "Está dada de baja: no inicia operaciones nuevas."
            }
          >
            <Button
              size="sm"
              variant={s.estado === "ACTIVA" ? "danger" : "primary"}
              onClick={() => run(s.estado === "ACTIVA" ? "dar-de-baja" : "reactivar")}
            >
              {s.estado === "ACTIVA" ? "Dar de baja" : "Reactivar"}
            </Button>
          </NextStep>
        </div>
        <h2 className="section-title">Fondo de la sede</h2>
        <Table
          headers={["Ejemplar", "Libro", "Ubicación", "Estado"]}
          onRowClick={(i) => navigate(`/ejemplares/${propios[i].id}`)}
          rows={propios.map((e) => [
            <span className="mono">{e.codigo_inventario}</span>,
            bookName(e.libro_id, db!),
            e.sede_actual_id === n ? "En la sede" : sedeName(e.sede_actual_id, db!),
            <Badge value={e.estado} />,
          ])}
        />
      </>
    );
  }

  return (
    <>
      <Back to={`/${pathOf(resource)}`}>Volver a {config[resource]?.title.toLowerCase()}</Back>
      <Heading kicker={kicker} title={title} action={headerActions} />
      {body}
      {action && (
        <CommandDialog
          resource={action.resource}
          id={action.id}
          action={action.command}
          onClose={() => setAction(null)}
        />
      )}
    </>
  );
}

function BookDetail({ db, id }: { db: Database; id: number }) {
  const navigate = useNavigate();
  const b = db.libros.find((x) => x.id === id)!;
  const es = db.ejemplares.filter((e) => e.libro_id === id);
  const porSede = db.sedes
    .map((s) => ({
      sede: s,
      total: es.filter((e) => e.sede_propietaria_id === s.id && e.estado !== "BAJA").length,
      disponibles: es.filter((e) => e.sede_propietaria_id === s.id && available(e, db)).length,
    }))
    .filter((x) => x.total);
  return (
    <>
      <div className="detail-grid">
        <section className="card card-pad flex flex-col gap-6 sm:flex-row">
          <Cover id={id} title={b.titulo} large />
          <Facts
            items={[
              ["Autor", b.autor],
              ["Editorial", b.editorial],
              ["Edición", b.edicion],
              ["ISBN", b.isbn ?? "Sin ISBN"],
              ["Copias en la red", es.filter((e) => e.estado !== "BAJA").length],
              ["Disponibles ahora", es.filter((e) => available(e, db)).length],
            ]}
          />
        </section>
        <section className="card card-pad">
          <h3 className="mb-3 font-bold">Disponibilidad por sede</h3>
          <div className="sede-avail">
            {porSede.map(({ sede, total, disponibles }) => (
              <div key={sede.id} className="row">
                <div className="flex-1">
                  <p className="text-sm font-semibold">{sede.nombre}</p>
                  <div className="avail-bar">
                    <span style={{ width: `${(disponibles / total) * 100}%` }} />
                  </div>
                </div>
                <span className="text-sm">
                  <b>{disponibles}</b>/{total}
                </span>
              </div>
            ))}
            {!porSede.length && <p className="muted text-sm">No hay copias registradas.</p>}
          </div>
          <div className="action-stack mt-4">
            <Link className="btn btn-primary btn-sm" to={`/solicitudes/nuevo?libro_id=${id}`}>
              Pedir prestado
            </Link>
            <Link className="btn btn-outline btn-sm" to={`/reservas/nuevo?libro_id=${id}`}>
              Reservar
            </Link>
            <Link className="btn btn-outline btn-sm" to={`/ejemplares/nuevo?libro_id=${id}`}>
              Agregar copia
            </Link>
          </div>
        </section>
      </div>
      <h2 className="section-title">Copias</h2>
      <Table
        headers={["Ejemplar", "Pertenece a", "Está en", "Estado", "Condición"]}
        onRowClick={(i) => navigate(`/ejemplares/${es[i].id}`)}
        rows={es.map((e) => [
          <span className="mono">{e.codigo_inventario}</span>,
          sedeName(e.sede_propietaria_id, db),
          e.sede_actual_id === null ? "Viajando" : sedeName(e.sede_actual_id, db),
          <Badge value={e.estado} />,
          <Badge value={e.condicion_fisica} />,
        ])}
      />
    </>
  );
}
