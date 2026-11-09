import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
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
  Empty,
  Field,
  Heading,
  inputClass,
  Figures,
  Kpi,
  Table,
} from "../components/ui";

const reports: [ReportType, string, string][] = [
  ["activos", "Préstamos activos y material en tránsito", "Qué está en manos de socios y qué está viajando entre sedes."],
  ["vencidos", "Préstamos vencidos y multas", "Atrasos por sede, días de demora y multas acumuladas."],
  ["demanda", "Libros más pedidos entre sedes", "Ranking de solicitudes interbibliotecarias por libro y sede."],
  ["disponibilidad", "Disponibilidad por sede", "Copias por libro y sede propietaria, y cuántas están disponibles."],
  ["logistica", "Envíos exitosos e incidencias", "Tasa de éxito de los remitos y ejemplares dañados o extraviados."],
  ["movimientos", "Movimiento entre sedes", "Envíos por trayecto y tiempo promedio de tránsito."],
  ["operaciones", "Bitácora de operaciones", "Altas, modificaciones y bajas con usuario y cambios."],
];
const firstOfPreviousMonth = () => {
  const [y, m] = today().split("-").map(Number);
  const date = new Date(Date.UTC(y, m - 2, 1));
  return date.toISOString().slice(0, 10);
};
export function ReportCenter() {
  return (
    <>
      <Heading
        title="Reportes"
        description="Indicadores de circulación, logística y disponibilidad. Todos se filtran por período y sede, y se pueden imprimir o exportar a CSV."
      />
      <div className="report-list">
        {reports.map(([id, name, description], i) => (
          <Link key={id} to={`/reportes/${id}`} className="report-card">
            <span className="num">RP{String(i + 1).padStart(2, "0")}</span>
            <div>
              <h2>{name}</h2>
              <p>{description}</p>
            </div>
            <span className="go hidden sm:inline">Consultar →</span>
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
    desde: firstOfPreviousMonth(),
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
          <div className="no-print flex gap-2">
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
        className="no-print mb-5 flex flex-wrap items-end gap-3 border-b border-[var(--rule)] pb-4"
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
      {loading && <p className="muted">Cargando reporte…</p>}
      {result && (
        <>
          {result.kpis && (
            <div className="mb-4">
              <Figures>
                {result.kpis.map((k) => (
                  <Kpi key={k.label} value={k.value} label={k.label} tone={k.tone ?? "info"} />
                ))}
              </Figures>
            </div>
          )}
          <h2 className="section-title !mt-2">{result.summary}</h2>
          <p className="mb-5 max-w-[90ch] text-sm text-[var(--muted-foreground)]">
            <b>Criterio:</b> {result.rule}
          </p>
          <Table
            headers={result.headers}
            rows={result.rows}
            empty={<Empty title="Sin datos para este período" detail="Ampliá el rango de fechas o quitá el filtro de sede." />}
          />
        </>
      )}
      <p className="mt-5 text-xs text-[var(--muted-foreground)]">
        EntreLibros · Grupo 85 · Generado: {new Date().toLocaleString("es-AR")}.
        Los indicadores corresponden a los filtros aplicados.
      </p>
    </>
  );
}
