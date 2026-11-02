import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { api } from "../api";
import { useLibrary } from "../app/context";
import { today } from "../domain/selectors";
import {
  type ReportResult,
  type ReportFilter,
  type ReportType,
} from "../domain/reports";
import {
  Alert,
  Back,
  Button,
  Field,
  Heading,
  inputClass,
  panelClass,
  Table,
} from "../components/ui";

const reports: [ReportType, string, string][] = [
  [
    "vencidos",
    "Préstamos vencidos",
    "Cantidad, días de atraso y sede de entrega.",
  ],
  [
    "demanda",
    "Demanda interbibliotecaria",
    "Libros solicitados entre sedes y ranking de demanda.",
  ],
  [
    "movimientos",
    "Movimientos entre sedes",
    "Envíos despachados y tiempo de tránsito de los recibidos.",
  ],
  [
    "disponibilidad",
    "Disponibilidad por sede",
    "Ejemplares por libro, sede propietaria y estado.",
  ],
  [
    "operaciones",
    "Comprobación de operaciones ABMC",
    "Altas, modificaciones, bajas y operaciones, con usuario y cambios.",
  ],
];
export function ReportCenter() {
  return (
    <>
      <Heading
        title="Reportes"
        description="Consultá indicadores de circulación, logística y disponibilidad."
      />
      <div className="report-index">
        {reports.map(([id, name, description], i) => (
          <Link key={id} to={`/reportes/${id}`} className="report-entry group">
            <span className="report-number font-heading">0{i + 1}</span>
            <div>
              <h2 className="font-heading text-2xl">{name}</h2>
              <p className="mt-2 text-sm text-[var(--muted-foreground)]">
                {description}
              </p>
            </div>
            <ArrowUpRight size={21} />
          </Link>
        ))}
      </div>
    </>
  );
}
export function ReportPage() {
  const { type } = useParams();
  const { db } = useLibrary();
  const def = reports.find((r) => r[0] === type);
  const [draft, setDraft] = useState<ReportFilter>({
    desde: "2026-10-01",
    hasta: today(),
    sede: null,
  });
  const [filter, setFilter] = useState(draft),
    [error, setError] = useState("");
  const [result, setResult] = useState<ReportResult | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setResult(null);
    setError("");
    if (def)
      void api
        .report(def[0], filter)
        .then((data) => {
          if (active) setResult(data);
        })
        .catch((e) => {
          if (active)
            setError(
              e instanceof Error ? e.message : "No pudimos cargar el reporte.",
            );
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    return () => {
      active = false;
    };
  }, [type, filter, db]);
  if (!def)
    return (
      <>
        <Back to="/reportes" />
        <Alert error>No encontramos ese reporte.</Alert>
      </>
    );
  function csv() {
    if (!result) return;
    const quote = (x: string | number) => `"${String(x).replace(/"/g, '""')}"`;
    const content =
      "\uFEFF" +
      [result.headers, ...result.rows]
        .map((row) => row.map(quote).join(";"))
        .join("\r\n");
    const url = URL.createObjectURL(
      new Blob([content], { type: "text/csv;charset=utf-8" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = `entrelibros-${type}-${filter.desde}-${filter.hasta}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }
  return (
    <>
      <Back to="/reportes" />
      <Heading
        title={def[1]}
        description={`Período: ${filter.desde}–${filter.hasta} · ${filter.sede ? db!.sedes.find((s) => s.id === filter.sede)?.nombre : "Todas las sedes"}`}
        action={
          <div className="flex gap-3 report-actions">
            <Button
              variant="outline"
              disabled={!result || loading}
              onClick={() => window.print()}
            >
              Imprimir / Guardar PDF
            </Button>
            <Button
              variant="outline"
              disabled={!result || loading}
              onClick={csv}
            >
              Exportar CSV
            </Button>
          </div>
        }
      />
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (draft.desde > draft.hasta) {
            setError("La fecha inicial no puede ser posterior a la final.");
            return;
          }
          setError("");
          setFilter(draft);
        }}
        className={`${panelClass} mb-7 flex flex-wrap items-end gap-5`}
      >
        {
          <Field label="Desde">
            <input
              type="date"
              required
              className={inputClass}
              value={draft.desde}
              onChange={(e) =>
                setDraft((d) => ({ ...d, desde: e.target.value }))
              }
            />
          </Field>
        }
        {
          <Field label="Hasta">
            <input
              required
              type="date"
              className={inputClass}
              value={draft.hasta}
              onChange={(e) =>
                setDraft((d) => ({ ...d, hasta: e.target.value }))
              }
            />
          </Field>
        }
        <Field label="Sede">
          <select
            className={inputClass}
            value={draft.sede ?? ""}
            onChange={(e) =>
              setDraft((d) => ({
                ...d,
                sede: e.target.value ? Number(e.target.value) : null,
              }))
            }
          >
            <option value="">Todas las sedes</option>
            {db!.sedes.map((s) => (
              <option key={s.id} value={s.id}>
                {s.nombre}
              </option>
            ))}
          </select>
        </Field>
        <Button type="submit">Aplicar</Button>
      </form>
      {error && <Alert error>{error}</Alert>}
      {loading && <p>Cargando reporte…</p>}
      {result && (
        <>
          <h2 className="font-heading mb-3 text-2xl">{result.summary}</h2>
          <p className="mb-6 text-sm text-[var(--muted-foreground)]">
            {result.rule}
          </p>
          <div className={`report-result report-${type}`}>
            <Table headers={result.headers} rows={result.rows} />
          </div>
        </>
      )}
      <p className="mt-5 text-xs text-[var(--muted-foreground)]">
        EntreLibros · Grupo 85 · Generado: {new Date().toLocaleString("es-AR")}.
        Los indicadores corresponden a los filtros aplicados.
      </p>
    </>
  );
}
