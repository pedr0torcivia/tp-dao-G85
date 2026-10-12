import {
  useEffect,
  useRef,
  useId,
  cloneElement,
  isValidElement,
  type ReactElement,
  type ButtonHTMLAttributes,
  type ReactNode,
} from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, BookOpen, Search, X } from "lucide-react";
import { statusLabels } from "../domain/selectors";

export const buttonClass =
  "inline-flex min-h-10 items-center justify-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition hover:opacity-85 disabled:cursor-not-allowed disabled:opacity-50";
export const primaryClass = `${buttonClass} border-transparent bg-[var(--action)] text-[var(--primary-foreground)]`;
export const outlineClass = `${buttonClass} border-[var(--border)] bg-[var(--card)] text-[var(--foreground)]`;
export const inputClass =
  "w-full min-h-11 rounded-lg border border-[var(--input)] bg-[var(--card)] px-3 py-2 text-sm text-[var(--foreground)] placeholder:text-[var(--muted-foreground)]";
export const panelClass =
  "rounded-xl border border-[var(--border)] bg-[var(--card)] p-6";

export function Button({
  variant = "primary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "outline";
}) {
  return (
    <button
      {...props}
      className={`${variant === "primary" ? primaryClass : outlineClass} ${className}`}
    />
  );
}
export function Badge({ value }: { value: string }) {
  const theme = [
    "HABILITADO",
    "ACTIVA",
    "DISPONIBLE",
    "CUMPLIDA",
    "RECIBIDO",
    "DEVUELTO",
  ].includes(value)
    ? "bg-[var(--success-bg)] text-[var(--success)]"
    : ["Sin disponibilidad", "PENDIENTE", "EN_PREPARACION"].includes(value)
      ? "bg-[var(--warning-bg)] text-[var(--warning)]"
      : [
            "INHABILITADO",
            "BAJA",
            "CANCELADA",
            "CANCELADO",
            "RECHAZADA",
            "VENCIDO",
            "NO_APTO",
          ].includes(value)
        ? "bg-[var(--warning-bg)] text-[var(--destructive)]"
        : "bg-[var(--info-bg)] text-[var(--info)]";
  return (
    <span
      className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${theme}`}
    >
      {statusLabels[value] ?? value}
    </span>
  );
}
export function Heading({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-10 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 className="font-heading text-[32px] leading-tight font-semibold text-[var(--primary)]">
          {title}
        </h1>
        {description && (
          <p className="mt-4 text-sm text-[var(--muted-foreground)]">
            {description}
          </p>
        )}
      </div>
      {action}
    </div>
  );
}
export function Back({
  to,
  children = "Volver",
}: {
  to: string;
  children?: ReactNode;
}) {
  return (
    <Link
      to={to}
      className="mb-6 inline-flex items-center gap-2 text-sm text-[var(--muted-foreground)]"
    >
      <ArrowLeft size={16} />
      {children}
    </Link>
  );
}
export function Empty({
  title = "No encontramos resultados",
  detail = "Probá con otra búsqueda o modificá los filtros.",
}: {
  title?: string;
  detail?: string;
}) {
  return (
    <div
      className={`${panelClass} flex min-h-52 flex-col items-center justify-center text-center`}
    >
      <BookOpen size={32} className="mb-4 text-[var(--muted-foreground)]" />
      <h2 className="font-heading text-xl">{title}</h2>
      <p className="mt-2 text-sm text-[var(--muted-foreground)]">{detail}</p>
    </div>
  );
}
export function Alert({
  children,
  error = false,
}: {
  children: ReactNode;
  error?: boolean;
}) {
  return (
    <div
      role={error ? "alert" : "status"}
      className={`my-4 rounded-lg border border-[var(--border)] p-4 text-sm ${error ? "bg-[var(--warning-bg)] text-[var(--destructive)]" : "bg-[var(--info-bg)] text-[var(--info)]"}`}
    >
      {children}
    </div>
  );
}
export function SearchBox({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (s: string) => void;
  placeholder: string;
}) {
  return (
    <div className="relative min-w-0 flex-1">
      <Search
        size={17}
        className="absolute top-3.5 left-3 text-[var(--muted-foreground)]"
      />
      <input
        aria-label={placeholder}
        className={`${inputClass} pl-10`}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
export function Table({
  headers,
  rows,
}: {
  headers: string[];
  rows: ReactNode[][];
}) {
  if (!rows.length) return <Empty />;
  return (
    <div className="overflow-x-auto rounded-xl border border-[var(--border)] bg-[var(--card)]">
      <table className="w-full text-left text-sm">
        <thead className="bg-[var(--muted)] text-[var(--muted-foreground)]">
          <tr>
            {headers.map((h, i) => (
              <th
                key={i}
                scope="col"
                className="px-5 py-4 text-[11px] font-medium tracking-wider uppercase"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-[var(--border)]">
              {r.map((c, j) => (
                <td key={j} className="px-5 py-5 align-middle">
                  {c}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string[];
  children: ReactNode;
}) {
  const id = useId();
  return (
    <div className="block text-sm font-medium">
      <label htmlFor={id} className="mb-2 block">
        {label}
      </label>
      {isValidElement(children)
        ? cloneElement(
            children as ReactElement<{
              id: string;
              "aria-describedby"?: string;
              "aria-invalid"?: boolean;
            }>,
            {
              id,
              "aria-describedby": error ? `${id}-error` : undefined,
              "aria-invalid": !!error,
            },
          )
        : children}
      {error && (
        <span
          role="alert"
          id={`${id}-error`}
          className="mt-2 block text-xs text-[var(--destructive)]"
        >
          {error.join(" ")}
        </span>
      )}
    </div>
  );
}
export function ConfirmDialog({
  title,
  description,
  onConfirm,
  onCancel,
  busy = false,
}: {
  title: string;
  description: string;
  onConfirm: () => void;
  onCancel: () => void;
  busy?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current!;
    dialog.showModal();
    return () => dialog.close();
  }, []);
  return (
    <dialog
      ref={ref}
      aria-labelledby="confirm-title"
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) onCancel();
      }}
      className="fixed inset-0 m-auto w-[min(92vw,480px)] rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 shadow-xl backdrop:bg-black/40"
    >
      <div className="flex items-start justify-between gap-3">
        <h2 id="confirm-title" className="font-heading text-xl">
          {title}
        </h2>
        <button disabled={busy} onClick={onCancel} aria-label="Cerrar">
          <X size={20} />
        </button>
      </div>
      <p className="my-5 text-sm leading-relaxed text-[var(--muted-foreground)]">
        {description}
      </p>
      <div className="flex justify-end gap-3">
        <Button variant="outline" disabled={busy} onClick={onCancel}>
          Cancelar
        </Button>
        <Button disabled={busy} onClick={onConfirm}>
          {busy ? "Guardando…" : "Confirmar"}
        </Button>
      </div>
    </dialog>
  );
}
