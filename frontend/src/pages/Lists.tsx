import { useState, type ReactNode } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useLibrary } from "../app/context";
import type { Resource } from "../domain/models";
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
import { coverByBook } from "../data/seed";
import {
  Badge,
  Empty,
  Heading,
  inputClass,
  outlineClass,
  primaryClass,
  SearchBox,
  Table,
} from "../components/ui";
import { config, pathOf } from "./resources";
import { ArrowUpRight, BookOpen, Plus } from "lucide-react";

export function Cover({
  id,
  title,
  large = false,
}: {
  id: number;
  title: string;
  large?: boolean;
}) {
  const [failed, setFailed] = useState(false);
  const name = coverByBook[id];
  return name && !failed ? (
    <img
      src={`/assets/portadas/${name}.jpg`}
      alt={`Portada de ${title}`}
      onError={() => setFailed(true)}
      className={`${large ? "h-[280px] w-[190px]" : "h-[138px] w-[92px]"} shrink-0 rounded object-contain`}
    />
  ) : (
    <div
      aria-label={`Sin portada: ${title}`}
      className={`${large ? "h-[280px] w-[190px]" : "h-[138px] w-[92px]"} flex shrink-0 items-center justify-center rounded bg-[var(--muted)] text-[var(--muted-foreground)]`}
    >
      <BookOpen size={28} />
    </div>
  );
}
export function EntityList({ resource }: { resource: Resource }) {
  const { db } = useLibrary();
  const conf = config[resource]!;
  const [searchParams] = useSearchParams();
  const [query, setQuery] = useState(""),
    [sede, setSede] = useState(""),
    [state, setState] = useState(""),
    [page, setPage] = useState(1);
  const detail = (id: number) => (
    <Link
      className="record-link"
      aria-label={`Ver detalle ${id}`}
      to={`/${pathOf(resource)}/${id}`}
    >
      Abrir <ArrowUpRight size={14} />
    </Link>
  );
  const records: {
    id: number;
    search: string;
    sedes: number[];
    state: string;
    cells: ReactNode[];
  }[] = [];
  let headers: string[] = [];
  if (resource === "socios") {
    headers = ["Socio", "Documento", "Contacto", "Habilitación", ""];
    for (const s of db!.socios)
      records.push({
        id: s.id,
        search: `${s.nombre} ${s.documento} ${s.numero_socio} ${s.contacto}`,
        sedes: [],
        state: s.estado,
        cells: [
          <div>
            {s.nombre}
            <p className="mt-1 text-xs text-[var(--muted-foreground)]">
              Socio N.º {s.numero_socio}
            </p>
          </div>,
          s.documento,
          s.contacto,
          <Badge value={s.estado} />,
          detail(s.id),
        ],
      });
  }
  if (resource === "sedes") {
    headers = ["Sede", "Dirección", "Contacto", "Estado", ""];
    for (const s of db!.sedes)
      records.push({
        id: s.id,
        search: `${s.nombre} ${s.direccion} ${s.contacto}`,
        sedes: [s.id],
        state: s.estado,
        cells: [
          s.nombre,
          s.direccion,
          s.contacto,
          <Badge value={s.estado} />,
          detail(s.id),
        ],
      });
  }
  if (resource === "ejemplares") {
    headers = [
      "Ejemplar",
      "Sede propietaria",
      "Ubicación actual",
      "Estado",
      "",
    ];
    for (const e of db!.ejemplares.filter(
      (e) =>
        !searchParams.get("libro_id") ||
        e.libro_id === Number(searchParams.get("libro_id")),
    ))
      records.push({
        id: e.id,
        search: `${e.codigo_inventario} ${bookName(e.libro_id, db!)} ${sedeName(e.sede_propietaria_id, db!)}`,
        sedes: [e.sede_propietaria_id],
        state: e.estado,
        cells: [
          <div>
            {e.codigo_inventario}
            <p className="mt-1 text-xs text-[var(--muted-foreground)]">
              {bookName(e.libro_id, db!)}
            </p>
          </div>,
          sedeName(e.sede_propietaria_id, db!),
          sedeName(e.sede_actual_id, db!),
          <Badge value={e.estado} />,
          detail(e.id),
        ],
      });
  }
  if (resource === "solicitudes") {
    headers = ["Solicitud", "Socio y libro", "Circuito", "Estado", ""];
    for (const s of db!.solicitudes)
      records.push({
        id: s.id,
        search: `${code("SOL", s.id)} ${socioName(s.socio_id, db!)} ${bookName(s.libro_id, db!)}`,
        sedes: [s.sede_origen_id, s.sede_destino_id],
        state: s.estado,
        cells: [
          code("SOL", s.id),
          `${socioName(s.socio_id, db!)} · ${bookName(s.libro_id, db!)}`,
          statusLabels[s.tipo],
          <Badge value={s.estado} />,
          detail(s.id),
        ],
      });
  }
  if (resource === "prestamos") {
    headers = ["Préstamo", "Socio y libro", "Vencimiento", "Situación", ""];
    for (const p of db!.prestamos) {
      const s = db!.solicitudes.find((s) => s.id === p.solicitud_id)!;
      const estado = p.fecha_devolucion
        ? "DEVUELTO"
        : isOverdue(p)
          ? "VENCIDO"
          : "ACTIVO";
      records.push({
        id: p.id,
        search: `${code("PRE", p.id)} ${socioName(s.socio_id, db!)} ${bookName(s.libro_id, db!)} ${db!.ejemplares.find((e) => e.id === s.ejemplar_id)?.codigo_inventario}`,
        sedes: [s.sede_destino_id],
        state: estado,
        cells: [
          code("PRE", p.id),
          `${socioName(s.socio_id, db!)} · ${bookName(s.libro_id, db!)}`,
          dateLabel(p.fecha_vencimiento),
          <div>
            <Badge value={estado} />
            {estado === "VENCIDO" && (
              <p className="mt-1 text-xs text-[var(--destructive)]">
                {daysLate(p)} días de atraso
              </p>
            )}
          </div>,
          detail(p.id),
        ],
      });
    }
  }
  if (resource === "reservas") {
    headers = ["Reserva", "Socio y libro", "Sede de retiro", "Estado", ""];
    for (const r of db!.reservas)
      records.push({
        id: r.id,
        search: `${code("RES", r.id)} ${socioName(r.socio_id, db!)} ${bookName(r.libro_id, db!)}`,
        sedes: [r.sede_retiro_id],
        state: r.estado,
        cells: [
          code("RES", r.id),
          `${socioName(r.socio_id, db!)} · ${bookName(r.libro_id, db!)}`,
          sedeName(r.sede_retiro_id, db!),
          <Badge value={r.estado} />,
          detail(r.id),
        ],
      });
  }
  if (resource === "remitos") {
    headers = ["Remito", "Origen → destino", "Ejemplares", "Estado", ""];
    for (const r of db!.remitos)
      records.push({
        id: r.id,
        search: `${r.numero} ${sedeName(r.sede_origen_id, db!)} ${sedeName(r.sede_destino_id, db!)} ${db!.detalle_remitos
          .filter((d) => d.remito_id === r.id)
          .map(
            (d) =>
              db!.ejemplares.find((e) => e.id === d.ejemplar_id)
                ?.codigo_inventario,
          )
          .join(" ")}`,
        sedes: [r.sede_origen_id, r.sede_destino_id],
        state: r.estado,
        cells: [
          r.numero,
          `${sedeName(r.sede_origen_id, db!)} → ${sedeName(r.sede_destino_id, db!)}`,
          db!.detalle_remitos.filter((d) => d.remito_id === r.id).length,
          <Badge value={r.estado} />,
          detail(r.id),
        ],
      });
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
      (e) =>
        e.libro_id === b.id &&
        (!sede || e.sede_propietaria_id === Number(sede)),
    );
    const hasAvailable = es.some((e) => available(e, db!));
    return (
      `${b.titulo} ${b.isbn} ${authorNames(b, db!)}`
        .toLocaleLowerCase()
        .includes(query.toLocaleLowerCase()) &&
      (!sede || es.length > 0) &&
      (!state || (state === "DISPONIBLE" ? hasAvailable : !hasAvailable))
    );
  });
  const count = resource === "libros" ? books.length : filtered.length;
  return (
    <div className={`collection-page collection-${resource}`}>
      <Heading
        title={conf.title}
        description={conf.description}
        action={
          resource === "prestamos" ? (
            <Link to="/prestamos/devolucion" className={primaryClass}>
              Registrar devolución
            </Link>
          ) : (
            <Link
              className={primaryClass}
              to={`/${pathOf(resource)}/nuevo${resource === "ejemplares" && searchParams.get("libro_id") ? `?libro_id=${searchParams.get("libro_id")}` : ""}`}
            >
              <Plus size={16} />
              {conf.create}
            </Link>
          )
        }
      />
      {resource === "libros" ? (
        <div className="collection-summary">
          <span>
            <strong>{db!.libros.length}</strong> títulos en el catálogo
          </span>
          <span>
            <strong>{db!.ejemplares.length}</strong> ejemplares en la red
          </span>
          <span>
            <strong>
              {db!.sedes.filter((s) => s.estado === "ACTIVA").length}
            </strong>{" "}
            bibliotecas conectadas
          </span>
        </div>
      ) : (
        <div
          className="state-index"
          role="group"
          aria-label={`Estado de ${conf.title.toLowerCase()}`}
        >
          {["", ...states].map((value) => (
            <button
              type="button"
              key={value}
              aria-pressed={state === value}
              onClick={() => {
                setState(value);
                setPage(1);
              }}
            >
              {value ? (statusLabels[value] ?? value) : "Todos"}
              <span>
                {value
                  ? records.filter((r) => r.state === value).length
                  : records.length}
              </span>
            </button>
          ))}
        </div>
      )}
      <div className="collection-tools mb-6 flex flex-col gap-3 md:flex-row">
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
            className={`${inputClass} md:w-[220px]`}
            value={sede}
            onChange={(e) => {
              setSede(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Todas las sedes</option>
            {db!.sedes.map((s) => (
              <option key={s.id} value={s.id}>
                {s.nombre}
              </option>
            ))}
          </select>
        )}
        <select
          aria-label="Filtrar por estado"
          className={`${inputClass} md:w-[220px]`}
          value={state}
          onChange={(e) => {
            setState(e.target.value);
            setPage(1);
          }}
        >
          <option value="">Todos los estados</option>
          {(resource === "libros"
            ? ["DISPONIBLE", "SIN_DISPONIBILIDAD"]
            : states
          ).map((s) => (
            <option key={s} value={s}>
              {statusLabels[s] ?? "Sin disponibilidad"}
            </option>
          ))}
        </select>
      </div>
      <div className="collection-caption">
        <p>
          {resource === "libros"
            ? "EXPLORAR EL FONDO"
            : "REGISTRO DE MOSTRADOR"}
        </p>
        <span>
          {count} {resource === "libros" ? "títulos" : "registros"}
          {query || sede || state ? " encontrados" : " en total"}
        </span>
      </div>
      {resource === "libros" ? (
        books.length ? (
          <div className="book-shelves">
            {books.map((b) => {
              const es = db!.ejemplares.filter(
                (e) =>
                  e.libro_id === b.id &&
                  (!sede || e.sede_propietaria_id === Number(sede)),
              );
              const av = es.filter((e) => available(e, db!));
              return (
                <article key={b.id} className="book-entry">
                  <Link
                    className="book-display"
                    to={`/catalogo/${b.id}`}
                    aria-label={`Consultar ${b.titulo}`}
                  >
                    <span className="book-shelf-number">
                      {String(db!.libros.indexOf(b) + 1).padStart(2, "0")}
                    </span>
                    <Cover id={b.id} title={b.titulo} />
                    <ArrowUpRight size={17} className="book-open-icon" />
                  </Link>
                  <div className="book-description">
                    <p className="book-author">{authorNames(b, db!)}</p>
                    <h2 className="font-heading">
                      <Link to={`/catalogo/${b.id}`}>{b.titulo}</Link>
                    </h2>
                    <p className="book-edition">
                      {b.editorial}
                      {b.edicion ? ` · ${b.edicion}` : ""}
                    </p>
                    <div className="book-availability">
                      <Badge
                        value={av.length ? "DISPONIBLE" : "Sin disponibilidad"}
                      />
                      <span>
                        {av.length
                          ? `${av.length} de ${es.length} copias`
                          : "Admite reserva"}
                      </span>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <Empty />
        )
      ) : (
        <Table
          headers={headers}
          rows={filtered.slice((page - 1) * 20, page * 20).map((r) => r.cells)}
        />
      )}
      {resource !== "libros" && count > 20 && (
        <div className="mt-5 flex items-center justify-end gap-4">
          <button
            className={outlineClass}
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Anterior
          </button>
          <span className="text-sm">
            Página {page} de {Math.ceil(count / 20)}
          </span>
          <button
            className={outlineClass}
            disabled={page * 20 >= count}
            onClick={() => setPage((p) => p + 1)}
          >
            Siguiente
          </button>
        </div>
      )}
    </div>
  );
}
