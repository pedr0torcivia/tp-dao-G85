import { useState, type ReactNode } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { BookOpen, Plus, Undo2 } from "lucide-react";
import { useLibrary } from "../app/context";
import type { Resource } from "../domain/models";
import {
  available,
  bookName,
  code,
  dateLabel,
  loanState,
  pesos,
  sedeName,
  socioName,
  statusLabels,
} from "../domain/selectors";
import { portadaDe } from "../data/portadas";
import {
  Badge,
  Empty,
  Heading,
  outlineClass,
  primaryClass,
  SearchBox,
  Table,
} from "../components/ui";
import { config, pathOf } from "./resources";

export function Cover({
  title,
  large = false,
  compact = false,
}: {
  id?: number;
  title: string;
  large?: boolean;
  compact?: boolean;
}) {
  const [failed, setFailed] = useState(false);
  const src = portadaDe(title);
  const size = large
    ? "h-[260px] w-[176px]"
    : compact
      ? "h-[52px] w-[36px]"
      : "h-[178px] w-[120px]";
  return src && !failed ? (
    <img
      src={src}
      alt={`Portada de ${title}`}
      onError={() => setFailed(true)}
      className={`${size} shrink-0 cover-img object-cover`}
    />
  ) : (
    <div
      aria-label={`Sin portada: ${title}`}
      className={`${size} flex shrink-0 items-center justify-center rounded bg-[var(--muted)] text-[var(--muted-foreground)]`}
    >
      <BookOpen size={compact ? 16 : 28} />
    </div>
  );
}

const PAGE = 25;

interface Row {
  id: number;
  search: string;
  sedes: number[];
  state: string;
  cells: ReactNode[];
}

export function EntityList({ resource }: { resource: Resource }) {
  const { db, sedeId } = useLibrary();
  const conf = config[resource]!;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [query, setQuery] = useState("");
  const [sede, setSede] = useState("");
  const [state, setState] = useState("");
  const [page, setPage] = useState(1);
  const main = (title: ReactNode, sub?: ReactNode) => (
    <div>
      <div className="cell-main">{title}</div>
      {sub && <div className="cell-sub">{sub}</div>}
    </div>
  );

  const records: Row[] = [];
  let headers: string[] = [];
  if (resource === "socios") {
    headers = ["Socio", "Documento", "Contacto", "Estado"];
    for (const s of db!.socios)
      records.push({
        id: s.id,
        search: `${s.nombre} ${s.documento} ${s.numero_socio} ${s.contacto}`,
        sedes: [],
        state: s.estado,
        cells: [main(s.nombre, `Socio N.º ${s.numero_socio}`), s.documento, s.contacto, <Badge value={s.estado} />],
      });
  }
  if (resource === "sedes") {
    headers = ["Sede", "Dirección", "Horarios", "Estado"];
    for (const s of db!.sedes)
      records.push({
        id: s.id,
        search: `${s.nombre} ${s.direccion} ${s.contacto}`,
        sedes: [s.id],
        state: s.estado,
        cells: [main(s.nombre, s.contacto), s.direccion, s.horarios, <Badge value={s.estado} />],
      });
  }
  if (resource === "ejemplares") {
    headers = ["Código", "Libro", "Sede", "Estado", "Condición"];
    const libro = Number(searchParams.get("libro_id")) || null;
    const corto = (id: number | null) => sedeName(id, db!).replace(/^Biblioteca /, "");
    for (const e of db!.ejemplares.filter((e) => !libro || e.libro_id === libro)) {
      const b = db!.libros.find((x) => x.id === e.libro_id);
      const fuera = e.sede_actual_id !== e.sede_propietaria_id;
      records.push({
        id: e.id,
        search: `${e.codigo_inventario} ${b?.titulo} ${b?.autor} ${sedeName(e.sede_propietaria_id, db!)}`,
        sedes: [e.sede_propietaria_id, ...(e.sede_actual_id ? [e.sede_actual_id] : [])],
        state: e.estado,
        cells: [
          <span className="mono font-semibold">{e.codigo_inventario}</span>,
          main(b?.titulo ?? "—", b?.autor),
          fuera ? (
            <div>
              <div>{e.sede_actual_id === null ? "Viajando" : `En ${corto(e.sede_actual_id)}`}</div>
              <div className="cell-sub">de {corto(e.sede_propietaria_id)}</div>
            </div>
          ) : (
            corto(e.sede_propietaria_id)
          ),
          <Badge value={e.estado} />,
          e.condicion_fisica === "APTO" ? <span className="muted">Apta</span> : <Badge value="NO_APTO" label="No apta" />,
        ],
      });
    }
  }
  if (resource === "solicitudes") {
    headers = ["Solicitud", "Libro y socio", "Trayecto", "Estado"];
    for (const s of db!.solicitudes)
      records.push({
        id: s.id,
        search: `${code("SOL", s.id)} ${socioName(s.socio_id, db!)} ${bookName(s.libro_id, db!)}`,
        sedes: [s.sede_origen_id, s.sede_destino_id],
        state: s.estado,
        cells: [
          main(<span className="mono">{code("SOL", s.id)}</span>, dateLabel(s.fecha_solicitud)),
          main(bookName(s.libro_id, db!), socioName(s.socio_id, db!)),
          s.tipo === "LOCAL" ? (
            <span className="muted">Local · {sedeName(s.sede_destino_id, db!)}</span>
          ) : (
            <span>
              {sedeName(s.sede_origen_id, db!)} → <b>{sedeName(s.sede_destino_id, db!)}</b>
            </span>
          ),
          <Badge value={s.estado} />,
        ],
      });
  }
  if (resource === "prestamos") {
    headers = ["Préstamo", "Libro y socio", "Vence", "Situación"];
    for (const p of db!.prestamos) {
      const s = db!.solicitudes.find((s) => s.id === p.solicitud_id)!;
      const estado = loanState(p);
      records.push({
        id: p.id,
        search: `${code("PRE", p.id)} ${socioName(s.socio_id, db!)} ${bookName(s.libro_id, db!)} ${db!.ejemplares.find((e) => e.id === s.ejemplar_id)?.codigo_inventario}`,
        sedes: [s.sede_destino_id],
        state: estado,
        cells: [
          <span className="mono">{code("PRE", p.id)}</span>,
          main(bookName(s.libro_id, db!), socioName(s.socio_id, db!)),
          dateLabel(p.fecha_vencimiento),
          <div>
            <Badge value={estado} />
            {estado === "VENCIDO" && (
              <div className="cell-sub text-[var(--bad)]">
                {p.dias_atraso} días · {pesos(p.multa)}
              </div>
            )}
          </div>,
        ],
      });
    }
  }
  if (resource === "reservas") {
    headers = ["Reserva", "Libro y socio", "Retira en", "Estado"];
    for (const r of db!.reservas)
      records.push({
        id: r.id,
        search: `${code("RES", r.id)} ${socioName(r.socio_id, db!)} ${bookName(r.libro_id, db!)}`,
        sedes: [r.sede_retiro_id],
        state: r.estado,
        cells: [
          main(<span className="mono">{code("RES", r.id)}</span>, dateLabel(r.fecha_reserva)),
          main(bookName(r.libro_id, db!), socioName(r.socio_id, db!)),
          sedeName(r.sede_retiro_id, db!),
          <Badge value={r.estado} />,
        ],
      });
  }
  if (resource === "remitos") {
    headers = ["Remito", "Trayecto", "Ejemplares", "Estado"];
    for (const r of db!.remitos) {
      const ds = db!.detalle_remitos.filter((d) => d.remito_id === r.id);
      records.push({
        id: r.id,
        search: `${r.numero} ${sedeName(r.sede_origen_id, db!)} ${sedeName(r.sede_destino_id, db!)} ${ds
          .map((d) => db!.ejemplares.find((e) => e.id === d.ejemplar_id)?.codigo_inventario)
          .join(" ")}`,
        sedes: [r.sede_origen_id, r.sede_destino_id],
        state: r.estado,
        cells: [
          main(<span className="mono">{r.numero}</span>, dateLabel(r.fecha_creacion)),
          <span>
            {sedeName(r.sede_origen_id, db!)} → <b>{sedeName(r.sede_destino_id, db!)}</b>
          </span>,
          ds.length,
          <Badge value={r.estado} />,
        ],
      });
    }
  }

  const states = [...new Set(records.map((r) => r.state))];
  const filtered = records.filter(
    (r) =>
      r.search.toLocaleLowerCase().includes(query.toLocaleLowerCase()) &&
      (!sede || r.sedes.includes(Number(sede))) &&
      (!state || r.state === state),
  );

  const books = db!.libros.filter((b) => {
    const es = db!.ejemplares.filter(
      (e) => e.libro_id === b.id && (!sede || e.sede_propietaria_id === Number(sede)),
    );
    const hasAvailable = es.some((e) => available(e, db!));
    return (
      `${b.titulo} ${b.isbn ?? ""} ${b.autor}`.toLocaleLowerCase().includes(query.toLocaleLowerCase()) &&
      (!sede || es.length > 0) &&
      (!state || (state === "DISPONIBLE" ? hasAvailable : !hasAvailable))
    );
  });
  const count = resource === "libros" ? books.length : filtered.length;

  const createAction =
    resource === "prestamos" ? (
      <Link to="/prestamos/devolucion" className={primaryClass}>
        <Undo2 size={16} /> Registrar devolución
      </Link>
    ) : (
      <Link
        className={primaryClass}
        to={`/${pathOf(resource)}/nuevo${resource === "ejemplares" && searchParams.get("libro_id") ? `?libro_id=${searchParams.get("libro_id")}` : ""}`}
      >
        <Plus size={16} /> {conf.create}
      </Link>
    );

  return (
    <>
      <Heading title={conf.title} description={conf.description} action={createAction} />
      {resource !== "libros" && (
        <div className="chips" role="group" aria-label="Filtrar por estado">
          {["", ...states].map((value) => (
            <button
              type="button"
              key={value}
              className="chip"
              aria-pressed={state === value}
              onClick={() => {
                setState(value);
                setPage(1);
              }}
            >
              {value ? (statusLabels[value] ?? value) : "Todos"}
              <span>{value ? records.filter((r) => r.state === value).length : records.length}</span>
            </button>
          ))}
        </div>
      )}
      <div className="toolbar">
        <SearchBox
          value={query}
          onChange={(v) => {
            setQuery(v);
            setPage(1);
          }}
          placeholder={conf.search}
        />
        {resource !== "socios" && (
          <select
            aria-label="Filtrar por sede"
            className="input"
            value={sede}
            onChange={(e) => {
              setSede(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Todas las sedes</option>
            <option value={sedeId}>Mi sede ({sedeName(sedeId, db!)})</option>
            {db!.sedes
              .filter((s) => s.id !== sedeId)
              .map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
          </select>
        )}
        {resource === "libros" && (
          <select
            aria-label="Filtrar por disponibilidad"
            className="input"
            value={state}
            onChange={(e) => setState(e.target.value)}
          >
            <option value="">Toda la colección</option>
            <option value="DISPONIBLE">Con copias disponibles</option>
            <option value="SIN">Sin copias disponibles</option>
          </select>
        )}
      </div>
      <p className="mb-3 text-sm text-[var(--muted-foreground)]">
        {count} {resource === "libros" ? "títulos" : "registros"}
        {query || sede || state ? " encontrados" : ""}
      </p>
      {resource === "libros" ? (
        books.length ? (
          <div className="shelf">
            {books.map((b) => {
              const es = db!.ejemplares.filter(
                (e) =>
                  e.libro_id === b.id &&
                  e.estado !== "BAJA" &&
                  (!sede || e.sede_propietaria_id === Number(sede)),
              );
              const av = es.filter((e) => available(e, db!));
              return (
                <Link key={b.id} to={`/catalogo/${b.id}`} className="book-card">
                  <div className="cover-box">
                    <Cover title={b.titulo} />
                  </div>
                  <div className="book-info">
                    <h2>{b.titulo}</h2>
                    <p className="author">{b.autor}</p>
                    <div className="avail">
                      {av.length ? `${av.length} de ${es.length} disponibles` : es.length ? "Sin copias libres · reservable" : "Sin copias"}
                      <div className="avail-bar">
                        <span style={{ width: es.length ? `${(av.length / es.length) * 100}%` : 0 }} />
                      </div>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        ) : (
          <Empty />
        )
      ) : (
        <Table
          headers={headers}
          rows={filtered.slice((page - 1) * PAGE, page * PAGE).map((r) => r.cells)}
          onRowClick={(i) => navigate(`/${pathOf(resource)}/${filtered[(page - 1) * PAGE + i].id}`)}
        />
      )}
      {resource !== "libros" && count > PAGE && (
        <div className="mt-4 flex items-center justify-end gap-3">
          <button className={`${outlineClass} btn-sm`} disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
            Anterior
          </button>
          <span className="text-sm">
            Página {page} de {Math.ceil(count / PAGE)}
          </span>
          <button className={`${outlineClass} btn-sm`} disabled={page * PAGE >= count} onClick={() => setPage((p) => p + 1)}>
            Siguiente
          </button>
        </div>
      )}
    </>
  );
}
