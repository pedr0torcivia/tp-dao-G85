export type ReportType =
  | "activos"
  | "vencidos"
  | "demanda"
  | "disponibilidad"
  | "logistica"
  | "movimientos"
  | "operaciones";
export interface ReportFilter {
  desde: string;
  hasta: string;
  sede: number | null;
}
export interface ReportKpi {
  label: string;
  value: string;
  tone?: "ok" | "warn" | "bad" | "info";
}
export interface ReportResult {
  headers: string[];
  rows: (string | number)[][];
  summary: string;
  rule: string;
  kpis?: ReportKpi[];
}
