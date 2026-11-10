import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { Plus, Undo2 } from "lucide-react";
import type { Resource } from "../domain/models";
import type { Command } from "../api/contracts";
import { useLibrary } from "../app/context";
import { tasksFor } from "../domain/tasks";
import {
  available,
  awaitingReturn,
  bookName,
  code,
  pesos,
  sedeName,
  socioName,
} from "../domain/selectors";
import { api } from "../api";
import { Button } from "../components/ui";
import { Cover } from "./Lists";
import { CommandDialog } from "./Commands";

type Run = { resource: Resource; id: number; command: Command };
interface Row {
  key: string;
  libroId?: number;
  sig: string;
  title: string;
  detail: string;
  to: string;
  urgent?: boolean;
  action?: Run & { label: string };
  custom?: ReactNode;
}
interface Group {
  key: string;
  title: string;
  hint: string;
  rows: Row[];
  urgent?: boolean;
}

const plural = (n: number, uno: string, varios: string) => `${n} ${n === 1 ? uno : varios}`;
const shortDate = (iso: string) =>
  new Intl.DateTimeFormat("es-AR", {
    day: "2-digit",
    month: "short",
    timeZone: "America/Argentina/Buenos_Aires",
  }).format(new Date(iso));
const LIMIT = 5;
const toneOfGroup: Record<string, string> = {
  urgente: "bad",
  mostrador: "ok",
  pedidos: "warn",
  envios: "move",
  revision: "neutral",
};

function Lane({ group, onRun }: { group: Group; onRun: (r: Run) => void }) {
  const { db } = useLibrary();
  const [all, setAll] = useState(false);
  const rows = all ? group.rows : group.rows.slice(0, LIMIT);
  const tone = toneOfGroup[group.key];
  return (
    <section
      className={`panel spine lane ${group.urgent ? "urgent" : ""}`}
      style={{ "--tone": `var(--${tone})` } as React.CSSProperties}
      aria-label={group.title}
    >
      <header className="lane-head">
        <span className="n">{group.rows.length}</span>
        <div className="min-w-0">
          <h2>{group.title}</h2>
          <p>{group.hint}</p>
        </div>
      </header>
      {rows.length ? (
        rows.map((r) => (
          <div key={r.key} className={`lane-row ${r.libroId ? "with-cover" : ""}`}>
            {r.libroId && <Cover id={r.libroId} title={bookName(r.libroId, db!)} compact />}
            <div className="min-w-0">
              <span className="sig">
                {r.urgent && <span className="tag">{r.sig}</span>}
                {!r.urgent && r.sig}
              </span>
              <Link className="t" to={r.to}>
                {r.title}
              </Link>
              <small>{r.detail}</small>
            </div>
            {r.custom ??
              (r.action ? (
                <Button
                  size="sm"
                  variant={group.urgent || group.key === "mostrador" ? "primary" : "outline"}
                  onClick={() => onRun(r.action!)}
                >
                  {r.action.label}
                </Button>
              ) : (
                <span />
              ))}
          </div>
        ))
      ) : (
        <p className="lane-empty">Nada pendiente.</p>
      )}
      {group.rows.length > LIMIT && (
        <button type="button" className="lane-foot" onClick={() => setAll((v) => !v)}>
          {all ? "Mostrar menos" : `Ver las ${group.rows.length} →`}
        </button>
      )}
    </section>
  );
}

export function Home() {
  const { db, sedeId, refresh, notify } = useLibrary();
  const [run, setRun] = useState<Run | null>(null);
  const [busy, setBusy] = useState<number | null>(null);
  const t = tasksFor(db!, sedeId);
  const sol = (id: number) => db!.solicitudes.find((s) => s.id === id)!;
  const nDetalles = (remitoId: number) => db!.detalle_remitos.filter((d) => d.remito_id === remitoId).length;

  async function retorno(ejemplarId: number) {
    setBusy(ejemplarId);
    try {
      await api.prepararRetorno(ejemplarId);
      await refresh();
      notify("El ejemplar se agregó al remito de retorno.");
    } catch (e) {
      notify(e instanceof Error ? e.message : "No pudimos preparar el retorno.");
    } finally {
      setBusy(null);
    }
  }

  const sinRemito = new Set(awaitingReturn(db!).map((e) => e.id));
  const groups: Group[] = [
    {
      key: "urgente",
      title: "Atender primero",
      hint: "Atrasos y envíos que ya llegaron a la puerta",
      urgent: true,
      rows: [
        ...t.vencidos.map((p) => {
          const s = sol(p.solicitud_id);
          return {
            key: `v${p.id}`,
            libroId: s.libro_id,
            sig: `+${p.dias_atraso} días`,
            urgent: true,
            title: `${bookName(s.libro_id, db!)} · ${socioName(s.socio_id, db!)}`,
            detail: `${code("PRE", p.id)} · venció el ${shortDate(p.fecha_vencimiento)} · multa ${pesos(p.multa)}`,
            to: `/prestamos/${p.id}`,
            action: { label: "Devolución", resource: "prestamos" as Resource, id: p.id, command: "devolver" as Command },
          };
        }),
        ...t.remitosPorRecibir.map((r) => ({
          key: `in${r.id}`,
          sig: r.numero,
          urgent: true,
          title: `Llega de ${sedeName(r.sede_origen_id, db!)}`,
          detail: `${plural(nDetalles(r.id), "ejemplar", "ejemplares")} en tránsito desde el ${r.fecha_despacho ? shortDate(r.fecha_despacho) : "—"}`,
          to: `/remitos/${r.id}`,
          action: { label: "Recibir", resource: "remitos" as Resource, id: r.id, command: "recibir" as Command },
        })),
      ],
    },
    {
      key: "mostrador",
      title: "Mostrador",
      hint: "Listos para entregar al socio",
      rows: t.paraEntregar.map((s) => ({
        key: `e${s.id}`,
        libroId: s.libro_id,
        sig: code("SOL", s.id),
        title: `${bookName(s.libro_id, db!)}`,
        detail: `${socioName(s.socio_id, db!)} · ${s.reserva_id ? "reserva" : s.tipo === "LOCAL" ? "préstamo local" : `llegó de ${sedeName(s.sede_origen_id, db!)}`}`,
        to: `/solicitudes/${s.id}`,
        action: { label: "Entregar", resource: "solicitudes" as Resource, id: s.id, command: "entregar" as Command },
      })),
    },
    {
      key: "pedidos",
      title: "Pedidos que esperan una copia",
      hint: "Solicitudes y reservas que debe atender esta sede",
      rows: [
        ...t.porAsignar.map((s) => ({
          key: `a${s.id}`,
          libroId: s.libro_id,
          sig: code("SOL", s.id),
          title: bookName(s.libro_id, db!),
          detail: `${socioName(s.socio_id, db!)} · ${s.tipo === "LOCAL" ? "retira acá" : `retira en ${sedeName(s.sede_destino_id, db!)}`}`,
          to: `/solicitudes/${s.id}`,
          action: { label: "Asignar copia", resource: "solicitudes" as Resource, id: s.id, command: "asignar" as Command },
        })),
        ...t.porPreparar.map((s) => ({
          key: `p${s.id}`,
          libroId: s.libro_id,
          sig: code("SOL", s.id),
          title: bookName(s.libro_id, db!),
          detail: `${socioName(s.socio_id, db!)} · copia asignada, falta prepararla`,
          to: `/solicitudes/${s.id}`,
          action: { label: "Preparar", resource: "solicitudes" as Resource, id: s.id, command: "preparar-entrega" as Command },
        })),
        ...t.reservasPorAsignar.map((r) => ({
          key: `r${r.id}`,
          libroId: r.libro_id,
          sig: code("RES", r.id),
          title: bookName(r.libro_id, db!),
          detail: `Reserva de ${socioName(r.socio_id, db!)}`,
          to: `/reservas/${r.id}`,
          action: { label: "Apartar copia", resource: "reservas" as Resource, id: r.id, command: "asignar-reserva" as Command },
        })),
      ],
    },
    {
      key: "envios",
      title: "Envíos por armar",
      hint: "Remitos que salen de esta sede",
      rows: t.remitosPorArmar.map((r) => {
        const n = nDetalles(r.id);
        const next: Command | null = r.estado === "EMPAQUETADO" ? "despachar" : n ? "empaquetar" : null;
        return {
          key: `out${r.id}`,
          sig: r.numero,
          title: `Hacia ${sedeName(r.sede_destino_id, db!)}`,
          detail: `${plural(n, "ejemplar", "ejemplares")} · ${r.estado === "EMPAQUETADO" ? "empaquetado, falta despachar" : "en preparación"}`,
          to: `/remitos/${r.id}`,
          action: next
            ? { label: next === "despachar" ? "Despachar" : "Empaquetar", resource: "remitos" as Resource, id: r.id, command: next }
            : undefined,
        };
      }),
    },
    {
      key: "revision",
      title: "Material en revisión",
      hint: "Devoluciones para habilitar o devolver a su sede",
      rows: t.enRevision.map((e) => {
        const ajeno = e.sede_propietaria_id !== e.sede_actual_id;
        return {
          key: `x${e.id}`,
          libroId: e.libro_id,
          sig: e.codigo_inventario,
          title: bookName(e.libro_id, db!),
          detail: ajeno
            ? `Pertenece a ${sedeName(e.sede_propietaria_id, db!)}: debe volver`
            : e.condicion_fisica === "APTO"
              ? "Volvió en buen estado"
              : "No apto: reparar o dar de baja",
          to: `/ejemplares/${e.id}`,
          action:
            !ajeno && e.condicion_fisica === "APTO"
              ? { label: "Habilitar", resource: "ejemplares" as Resource, id: e.id, command: "aprobar-disponibilidad" as Command }
              : undefined,
          custom:
            ajeno && sinRemito.has(e.id) ? (
              <Button size="sm" variant="outline" disabled={busy === e.id} onClick={() => void retorno(e.id)}>
                <Undo2 size={13} /> Retorno
              </Button>
            ) : ajeno ? (
              <span className="mono muted">en remito</span>
            ) : undefined,
        };
      }),
    },
  ];
  const total = groups.reduce((n, g) => n + g.rows.length, 0);

  const hoy = new Intl.DateTimeFormat("es-AR", { weekday: "long", day: "numeric", month: "long" }).format(new Date());
  const proximos = [...t.prestamosSede]
    .filter((p) => !p.dias_atraso)
    .sort((a, b) => a.fecha_vencimiento.localeCompare(b.fecha_vencimiento))
    .slice(0, 5);
  const disponibles = db!.ejemplares.filter((e) => e.sede_propietaria_id === sedeId && available(e, db!)).length;

  return (
    <>
      <div className="desk-head">
        <div>
          <p className="kicker">
            {sedeName(sedeId, db!)} · {hoy}
          </p>
          <h1>Mesa de trabajo</h1>
          <p className="mt-1 text-[13.5px] text-[var(--ink-soft)]">
            {total
              ? `${plural(total, "tarea pendiente", "tareas pendientes")}, ordenadas por prioridad.`
              : "La sede está al día: no hay tareas pendientes."}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link className="btn btn-primary" to="/solicitudes/nuevo">
            <Plus size={15} /> Nueva solicitud
          </Link>
          <Link className="btn btn-outline" to="/prestamos/devolucion">
            Registrar devolución
          </Link>
          <Link className="btn btn-outline hidden md:inline-flex" to="/catalogo">
            Buscar en el catálogo
          </Link>
        </div>
      </div>

      <div className="desk">
        <div className="desk-main">
          {groups[0].rows.length > 0 && <Lane group={groups[0]} onRun={setRun} />}
          <div className="lanes-grid">
            {groups.slice(1).map((g) => (
              <Lane key={g.key} group={g} onRun={setRun} />
            ))}
          </div>
        </div>

        <aside className="side-col">
          <section className="panel ledger" aria-label="Estado de la sede">
            <h3 className="label">La sede hoy</h3>
            <Link to="/prestamos">
              Préstamos activos <b>{t.prestamosSede.length}</b>
            </Link>
            <Link to="/reportes/vencidos" className={t.vencidos.length ? "bad" : ""}>
              Vencidos <b>{t.vencidos.length}</b>
            </Link>
            <Link to="/remitos">
              Libros viajando hacia acá <b>{t.enCamino.length}</b>
            </Link>
            <Link to="/ejemplares">
              Copias disponibles <b>{disponibles}</b>
            </Link>
          </section>
          <section className="panel ledger" aria-label="Próximos vencimientos">
            <h3 className="label">Próximos vencimientos</h3>
            {proximos.length ? (
              proximos.map((p) => {
                const s = sol(p.solicitud_id);
                return (
                  <Link key={p.id} to={`/prestamos/${p.id}`}>
                    <span className="min-w-0 truncate">
                      {bookName(s.libro_id, db!)}
                      <span className="block text-[12px] text-[var(--ink-faint)]">{socioName(s.socio_id, db!)}</span>
                    </span>
                    <span className="mono">{shortDate(p.fecha_vencimiento)}</span>
                  </Link>
                );
              })
            ) : (
              <div className="row muted">Sin préstamos por vencer.</div>
            )}
          </section>
          <p className="px-1 text-[12.5px] text-[var(--ink-faint)]">
            ¿Dudas con el circuito?{" "}
            <Link to="/guia" className="text-[var(--green)] underline underline-offset-2">
              Cómo funciona
            </Link>
          </p>
        </aside>
      </div>

      {run && <CommandDialog resource={run.resource} id={run.id} action={run.command} onClose={() => setRun(null)} />}
    </>
  );
}
