import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  ArrowRight,
  BookOpenCheck,
  ClipboardList,
  HandHelping,
  PackageCheck,
  Plus,
  Search,
  Truck,
  Undo2,
  Wrench,
} from "lucide-react";
import type { Resource } from "../domain/models";
import type { Command } from "../api/contracts";
import { useLibrary } from "../app/context";
import { tasksFor } from "../domain/tasks";
import {
  awaitingReturn,
  bookName,
  code,
  dateLabel,
  pesos,
  sedeName,
  socioName,
  type Tone,
} from "../domain/selectors";
import { api } from "../api";
import { Badge, Button, Kpi } from "../components/ui";
import { CommandDialog } from "./Commands";

const plural = (n: number, uno: string, varios: string) =>
  `${n} ${n === 1 ? uno : varios}`;

interface Task {
  key: string;
  title: ReactNode;
  detail: ReactNode;
  to: string;
  action?: { label: string; resource: Resource; id: number; command: Command };
  custom?: ReactNode;
}

function Lane({
  title,
  subtitle,
  icon,
  tone,
  tasks,
  empty,
  more,
  onRun,
}: {
  title: string;
  subtitle: string;
  icon: ReactNode;
  tone: Tone;
  tasks: Task[];
  empty: string;
  more?: { to: string; label: string };
  onRun: (t: NonNullable<Task["action"]>) => void;
}) {
  const visible = tasks.slice(0, 6);
  return (
    <section
      className="lane card"
      style={
        {
          "--tone": `var(--${tone})`,
          "--tone-bg": `var(--${tone}-bg)`,
        } as React.CSSProperties
      }
    >
      <header className="lane-head">
        <span className="lane-icon">{icon}</span>
        <div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>
        <span className="count">{tasks.length}</span>
      </header>
      {visible.length ? (
        visible.map((t) => (
          <div key={t.key} className="task">
            <Link to={t.to} className="task-body">
              <p>{t.title}</p>
              <small>{t.detail}</small>
            </Link>
            {t.custom ??
              (t.action && (
                <Button size="sm" onClick={() => onRun(t.action!)}>
                  {t.action.label}
                </Button>
              ))}
          </div>
        ))
      ) : (
        <p className="lane-empty">{empty}</p>
      )}
      {more && tasks.length > visible.length && (
        <Link to={more.to} className="lane-more">
          {more.label} ({tasks.length}) →
        </Link>
      )}
    </section>
  );
}

export function Home() {
  const { db, sedeId, refresh, notify } = useLibrary();
  const [run, setRun] = useState<NonNullable<Task["action"]> | null>(null);
  const [busy, setBusy] = useState<number | null>(null);
  const t = tasksFor(db!, sedeId);
  const sede = sedeName(sedeId, db!);
  const sol = (id: number) => db!.solicitudes.find((s) => s.id === id)!;

  async function retorno(ejemplarId: number) {
    setBusy(ejemplarId);
    try {
      const remito = await api.prepararRetorno(ejemplarId);
      await refresh();
      notify(`Ejemplar agregado al remito de retorno #${remito.id}.`);
    } catch (e) {
      notify(e instanceof Error ? e.message : "No pudimos preparar el retorno.");
    } finally {
      setBusy(null);
    }
  }

  const mostrador: Task[] = t.paraEntregar.map((s) => ({
    key: `e${s.id}`,
    title: `${bookName(s.libro_id, db!)}`,
    detail: `${socioName(s.socio_id, db!)} · ${s.reserva_id ? "reserva" : s.tipo === "LOCAL" ? "local" : `llegó de ${sedeName(s.sede_origen_id, db!)}`}`,
    to: `/solicitudes/${s.id}`,
    action: { label: "Entregar", resource: "solicitudes", id: s.id, command: "entregar" },
  }));

  const pedidos: Task[] = [
    ...t.porAsignar.map((s) => ({
      key: `a${s.id}`,
      title: bookName(s.libro_id, db!),
      detail: `${code("SOL", s.id)} · ${socioName(s.socio_id, db!)} · ${s.tipo === "LOCAL" ? "retira acá" : `retira en ${sedeName(s.sede_destino_id, db!)}`}`,
      to: `/solicitudes/${s.id}`,
      action: { label: "Asignar copia", resource: "solicitudes" as Resource, id: s.id, command: "asignar" as Command },
    })),
    ...t.porPreparar.map((s) => ({
      key: `p${s.id}`,
      title: bookName(s.libro_id, db!),
      detail: `${code("SOL", s.id)} · copia asignada, falta prepararla`,
      to: `/solicitudes/${s.id}`,
      action: { label: "Preparar", resource: "solicitudes" as Resource, id: s.id, command: "preparar-entrega" as Command },
    })),
    ...t.reservasPorAsignar.map((r) => ({
      key: `r${r.id}`,
      title: bookName(r.libro_id, db!),
      detail: `${code("RES", r.id)} · reserva de ${socioName(r.socio_id, db!)}`,
      to: `/reservas/${r.id}`,
      action: { label: "Apartar copia", resource: "reservas" as Resource, id: r.id, command: "asignar-reserva" as Command },
    })),
  ];

  const envios: Task[] = [
    ...t.remitosPorRecibir.map((r) => ({
      key: `in${r.id}`,
      title: `${r.numero} · llega de ${sedeName(r.sede_origen_id, db!)}`,
      detail: `${plural(db!.detalle_remitos.filter((d) => d.remito_id === r.id).length, "ejemplar", "ejemplares")} · despachado ${dateLabel(r.fecha_despacho)}`,
      to: `/remitos/${r.id}`,
      action: { label: "Recibir", resource: "remitos" as Resource, id: r.id, command: "recibir" as Command },
    })),
    ...t.remitosPorArmar.map((r) => {
      const n = db!.detalle_remitos.filter((d) => d.remito_id === r.id).length;
      const next: Command | null =
        r.estado === "EMPAQUETADO" ? "despachar" : n ? "empaquetar" : null;
      return {
        key: `out${r.id}`,
        title: `${r.numero} · hacia ${sedeName(r.sede_destino_id, db!)}`,
        detail: `${plural(n, "ejemplar", "ejemplares")} · ${r.estado === "EMPAQUETADO" ? "listo para despachar" : "en preparación"}`,
        to: `/remitos/${r.id}`,
        action: next
          ? {
              label: next === "despachar" ? "Despachar" : "Empaquetar",
              resource: "remitos" as Resource,
              id: r.id,
              command: next,
            }
          : undefined,
      };
    }),
  ];

  const pendientesRetorno = awaitingReturn(db!).filter(
    (e) => e.sede_actual_id === sedeId,
  );
  const revision: Task[] = [
    ...t.vencidos.map((p) => {
      const s = sol(p.solicitud_id);
      return {
        key: `v${p.id}`,
        title: `${socioName(s.socio_id, db!)} · ${p.dias_atraso} días de atraso`,
        detail: `${bookName(s.libro_id, db!)} · multa ${pesos(p.multa)}`,
        to: `/prestamos/${p.id}`,
        action: { label: "Devolución", resource: "prestamos" as Resource, id: p.id, command: "devolver" as Command },
      };
    }),
    ...t.enRevision.map((e) => {
      const ajeno = e.sede_propietaria_id !== e.sede_actual_id;
      const enCola = pendientesRetorno.some((x) => x.id === e.id);
      return {
        key: `x${e.id}`,
        title: `${bookName(e.libro_id, db!)} · ${e.codigo_inventario}`,
        detail: ajeno
          ? `Es de ${sedeName(e.sede_propietaria_id, db!)}: debe volver a su sede`
          : e.condicion_fisica === "APTO"
            ? "Devuelto en buen estado: revisalo y habilitalo"
            : "No apto: reparar o dar de baja",
        to: `/ejemplares/${e.id}`,
        action:
          !ajeno && e.condicion_fisica === "APTO"
            ? { label: "Habilitar", resource: "ejemplares" as Resource, id: e.id, command: "aprobar-disponibilidad" as Command }
            : undefined,
        custom:
          ajeno && enCola ? (
            <Button size="sm" variant="outline" disabled={busy === e.id} onClick={() => void retorno(e.id)}>
              <Undo2 size={14} /> Retorno
            </Button>
          ) : ajeno ? (
            <Badge value="EN_TRANSITO" label="En remito" />
          ) : undefined,
      };
    }),
  ];

  const fecha = new Intl.DateTimeFormat("es-AR", {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(new Date());

  return (
    <>
      <section className="hero">
        <p className="kicker">{fecha}</p>
        <h1>Mesa de trabajo · {sede}</h1>
        <p>
          Todo lo que tu sede tiene que resolver, ordenado por tarea. Cada fila
          tiene el botón del paso siguiente: no hace falta buscarlo.
        </p>
        <div className="hero-actions">
          <Link className="btn btn-primary" to="/solicitudes/nuevo">
            <Plus size={16} /> Nueva solicitud
          </Link>
          <Link className="btn btn-outline" to="/prestamos/devolucion">
            <Undo2 size={16} /> Registrar devolución
          </Link>
          <Link className="btn btn-outline" to="/catalogo">
            <Search size={16} /> Consultar disponibilidad
          </Link>
        </div>
      </section>

      <div className="kpi-grid">
        <Kpi icon={<ClipboardList size={18} />} value={pedidos.length} label="Pedidos por atender" tone="warn" to="/solicitudes" />
        <Kpi icon={<BookOpenCheck size={18} />} value={t.prestamosSede.length} label="Préstamos activos en la sede" tone="info" to="/prestamos" />
        <Kpi icon={<AlertTriangle size={18} />} value={t.vencidos.length} label="Préstamos vencidos" tone={t.vencidos.length ? "bad" : "ok"} to="/reportes/vencidos" />
        <Kpi icon={<Truck size={18} />} value={t.enCamino.length} label="Libros viajando hacia acá" tone="move" to="/remitos" />
      </div>

      <div className="lanes">
        <Lane
          title="Mostrador: listos para entregar"
          subtitle="El socio puede retirarlos ahora"
          icon={<HandHelping size={19} />}
          tone="info"
          tasks={mostrador}
          empty="No hay material esperando en el mostrador."
          more={{ to: "/solicitudes", label: "Ver todas" }}
          onRun={setRun}
        />
        <Lane
          title="Pedidos por atender"
          subtitle="Solicitudes y reservas que esperan una copia de esta sede"
          icon={<ClipboardList size={19} />}
          tone="warn"
          tasks={pedidos}
          empty="Sin pedidos pendientes. ¡Al día!"
          more={{ to: "/solicitudes", label: "Ver solicitudes" }}
          onRun={setRun}
        />
        <Lane
          title="Envíos entre sedes"
          subtitle="Remitos por armar, despachar o recibir"
          icon={<PackageCheck size={19} />}
          tone="move"
          tasks={envios}
          empty="No hay envíos que requieran acción."
          more={{ to: "/remitos", label: "Ver remitos" }}
          onRun={setRun}
        />
        <Lane
          title="Vencidos y material en revisión"
          subtitle="Atrasos para reclamar y copias para revisar o devolver"
          icon={<Wrench size={19} />}
          tone="bad"
          tasks={revision}
          empty="Nada para revisar."
          more={{ to: "/prestamos", label: "Ver préstamos" }}
          onRun={setRun}
        />
      </div>

      <p className="mt-6 text-sm text-[var(--muted-foreground)]">
        ¿Primera vez? Mirá{" "}
        <Link to="/guia" className="font-semibold text-[var(--primary)] underline underline-offset-4">
          cómo funciona el circuito <ArrowRight size={13} className="inline" />
        </Link>
      </p>

      {run && (
        <CommandDialog
          resource={run.resource}
          id={run.id}
          action={run.command}
          onClose={() => setRun(null)}
        />
      )}
    </>
  );
}
