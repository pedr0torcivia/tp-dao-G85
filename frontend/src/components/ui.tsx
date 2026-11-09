import {
  useEffect,
  useRef,
  useId,
  cloneElement,
  isValidElement,
  type ReactElement,
  type ButtonHTMLAttributes,
  type CSSProperties,
  type ReactNode,
} from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  Check,
  Info,
  Search,
  SearchX,
  X,
} from "lucide-react";
import { statusLabels, toneOf, type Tone } from "../domain/selectors";

export const primaryClass = "btn btn-primary";
export const accentClass = "btn btn-accent";
export const outlineClass = "btn btn-outline";
export const ghostClass = "btn btn-ghost";
export const dangerClass = "btn btn-danger";
export const inputClass = "input";
export const panelClass = "card card-pad";

type Variant = "primary" | "accent" | "outline" | "ghost" | "danger";
const variants: Record<Variant, string> = {
  primary: primaryClass,
  accent: accentClass,
  outline: outlineClass,
  ghost: ghostClass,
  danger: dangerClass,
};

export function Button({
  variant = "primary",
  size,
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: "sm";
}) {
  return (
    <button
      type="button"
      {...props}
      className={`${variants[variant]} ${size === "sm" ? "btn-sm" : ""} ${className}`}
    />
  );
}

/** Píldora de estado: el color sale del significado, no del componente. */
export function Badge({ value, label }: { value: string; label?: string }) {
  return (
    <span className="pill" data-tone={toneOf(value)}>
      {label ?? statusLabels[value] ?? value}
    </span>
  );
}

export function Heading({
  title,
  description,
  action,
  kicker,
}: {
  title: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  kicker?: ReactNode;
}) {
  return (
    <div className="page-head">
      <div className="min-w-0">
        {kicker && <p className="kicker">{kicker}</p>}
        <h1>{title}</h1>
        {description && <p className="desc">{description}</p>}
      </div>
      {action && <div className="flex flex-wrap gap-2">{action}</div>}
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
      className="no-print mb-4 inline-flex items-center gap-2 text-sm font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
    >
      <ArrowLeft size={16} />
      {children}
    </Link>
  );
}

export function Empty({
  title = "No encontramos resultados",
  detail = "Probá con otra búsqueda o modificá los filtros.",
  action,
}: {
  title?: string;
  detail?: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty">
      <SearchX size={26} />
      <strong>{title}</strong>
      <span>{detail}</span>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export function Alert({
  children,
  error = false,
  tone,
}: {
  children: ReactNode;
  error?: boolean;
  tone?: Tone;
}) {
  const t = tone ?? (error ? "bad" : "info");
  const Icon = t === "bad" || t === "warn" ? AlertTriangle : t === "ok" ? Check : Info;
  return (
    <div role={error ? "alert" : "status"} className="alert" data-tone={t}>
      <Icon size={17} />
      <div>{children}</div>
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
    <div className="search relative min-w-0">
      <Search
        size={17}
        className="pointer-events-none absolute top-3 left-3 text-[var(--muted-foreground)]"
      />
      <input
        type="search"
        aria-label={placeholder}
        className="input pl-10"
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
  onRowClick,
  empty,
}: {
  headers: string[];
  rows: ReactNode[][];
  onRowClick?: (index: number) => void;
  empty?: ReactNode;
}) {
  if (!rows.length) return <>{empty ?? <Empty />}</>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {headers.map((h, i) => (
              <th key={i} scope="col">
                {h}
              </th>
            ))}
            {onRowClick && <th aria-hidden="true" />}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr
              key={i}
              className={onRowClick ? "clickable" : undefined}
              onClick={
                onRowClick
                  ? (e) => {
                      if ((e.target as HTMLElement).closest("a,button")) return;
                      onRowClick(i);
                    }
                  : undefined
              }
            >
              {r.map((c, j) => (
                <td key={j}>{c}</td>
              ))}
              {onRowClick && (
                <td className="go" aria-hidden="true">
                  →
                </td>
              )}
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
  hint,
  children,
  className = "",
}: {
  label: string;
  error?: string[];
  hint?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  const id = useId();
  return (
    <div className={className}>
      <label htmlFor={id} className="field-label">
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
      {hint && !error && <span className="field-hint">{hint}</span>}
      {error && (
        <span
          role="alert"
          id={`${id}-error`}
          className="mt-1.5 block text-xs font-medium text-[var(--bad)]"
        >
          {error.join(" ")}
        </span>
      )}
    </div>
  );
}

export function Dialog({
  title,
  onClose,
  busy = false,
  children,
  wide = false,
}: {
  title: ReactNode;
  onClose: () => void;
  busy?: boolean;
  children: ReactNode;
  wide?: boolean;
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
      aria-labelledby="dialog-title"
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) onClose();
      }}
      className="dialog"
      style={wide ? { width: "min(94vw, 760px)" } : undefined}
    >
      <div className="mb-2 flex items-start justify-between gap-3">
        <h2 id="dialog-title">{title}</h2>
        <button
          type="button"
          className="icon-btn"
          disabled={busy}
          onClick={onClose}
          aria-label="Cerrar"
        >
          <X size={19} />
        </button>
      </div>
      {children}
    </dialog>
  );
}

export function ConfirmDialog({
  title,
  description,
  onConfirm,
  onCancel,
  busy = false,
  confirmLabel = "Confirmar",
  danger = false,
}: {
  title: string;
  description: ReactNode;
  onConfirm: () => void;
  onCancel: () => void;
  busy?: boolean;
  confirmLabel?: string;
  danger?: boolean;
}) {
  return (
    <Dialog title={title} onClose={onCancel} busy={busy}>
      <p className="my-4 text-sm leading-relaxed text-[var(--muted-foreground)]">
        {description}
      </p>
      <div className="flex justify-end gap-2">
        <Button variant="outline" disabled={busy} onClick={onCancel}>
          Volver
        </Button>
        <Button
          variant={danger ? "danger" : "primary"}
          disabled={busy}
          onClick={onConfirm}
        >
          {busy ? "Guardando…" : confirmLabel}
        </Button>
      </div>
    </Dialog>
  );
}

export interface Step {
  key: string;
  label: string;
  hint?: string;
}
/** Línea de vida: pasos hechos, el actual resaltado y los que faltan. */
export function Stepper({
  steps,
  current,
  failed = false,
}: {
  steps: Step[];
  current: string;
  failed?: boolean;
}) {
  const index = steps.findIndex((s) => s.key === current);
  return (
    <ol className="stepper" aria-label="Avance">
      {steps.map((s, i) => {
        const state =
          index === -1
            ? "upcoming"
            : i < index
              ? "done"
              : i === index
                ? failed
                  ? "failed"
                  : "current"
                : "upcoming";
        return (
          <li
            key={s.key}
            className={`step ${state}`}
            aria-current={state === "current" ? "step" : undefined}
          >
            <span className="dot">
              {state === "done" ? <Check size={15} strokeWidth={3} /> : i + 1}
            </span>
            <b>{s.label}</b>
            {s.hint && <small>{s.hint}</small>}
          </li>
        );
      })}
    </ol>
  );
}

/** Explica, en la propia pantalla, qué patrón de diseño está actuando. */
export function PatternNote({
  pattern,
  children,
}: {
  pattern: string;
  children: ReactNode;
}) {
  return (
    <aside className="pattern-note">
      <span className="tag">Patrón {pattern}</span>
      <div>{children}</div>
    </aside>
  );
}

/** Cifra integrada a una franja de datos. Sólo lo urgente toma color. */
export function Kpi({
  value,
  label,
  tone,
  to,
}: {
  icon?: ReactNode;
  value: ReactNode;
  label: string;
  tone?: Tone;
  to?: string;
}) {
  const style =
    tone === "bad" ? ({ "--tone": "var(--stamp)" } as CSSProperties) : undefined;
  const body = (
    <>
      <strong>{value}</strong>
      <span>{label}</span>
    </>
  );
  return to ? (
    <Link to={to} className="figure" style={style}>
      {body}
    </Link>
  ) : (
    <div className="figure" style={style}>
      {body}
    </div>
  );
}

export function Figures({ children }: { children: ReactNode }) {
  return <div className="figures">{children}</div>;
}
