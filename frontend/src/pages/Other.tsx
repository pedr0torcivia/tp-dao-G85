import { useState, type CSSProperties, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { SunMoon } from "lucide-react";
import { useLibrary } from "../app/context";
import {
  bookName,
  code,
  dateLabel,
  isOverdue,
  pesos,
  socioName,
} from "../domain/selectors";
import {
  Alert,
  Badge,
  Button,
  Empty,
  Field,
  Heading,
  inputClass,
  panelClass,
  primaryClass,
  SearchBox,
  Table,
} from "../components/ui";
import { CommandDialog } from "./Commands";
import { Logo } from "../components/Logo";

export function Appearance() {
  const { theme, setTheme } = useLibrary();
  return (
    <>
      <Heading title="Apariencia" description="Elegí el tema con el que querés trabajar." />
      <div className="card card-pad max-w-[640px]">
        <div role="group" aria-label="Tema de la aplicación" className="flex flex-wrap gap-2">
          {(["light", "dark", "system"] as const).map((t, i) => (
            <Button
              key={t}
              variant={t === theme ? "primary" : "outline"}
              aria-pressed={t === theme}
              onClick={() => setTheme(t)}
            >
              {["Claro", "Oscuro", "Sistema"][i]}
            </Button>
          ))}
        </div>
        <p className="mt-4 text-sm text-[var(--muted-foreground)]">
          La elección se conserva para tus próximas visitas.
        </p>
      </div>
    </>
  );
}
export function Returns() {
  const { db, sedeId } = useLibrary();
  const [query, setQuery] = useState("");
  const [todas, setTodas] = useState(false);
  const [selected, setSelected] = useState<number | null>(null);
  const loans = db!.prestamos
    .filter((p) => !p.fecha_devolucion)
    .map((p) => ({ p, s: db!.solicitudes.find((s) => s.id === p.solicitud_id)! }))
    .filter(({ s }) => todas || s.sede_destino_id === sedeId)
    .filter(({ p, s }) =>
      `${code("PRE", p.id)} ${socioName(s.socio_id, db!)} ${bookName(s.libro_id, db!)} ${db!.ejemplares.find((e) => e.id === s.ejemplar_id)?.codigo_inventario ?? ""}`
        .toLowerCase()
        .includes(query.toLowerCase()),
    )
    .sort((a, b) => a.p.fecha_vencimiento.localeCompare(b.p.fecha_vencimiento));
  return (
    <>
      <Heading
        kicker="Circulación"
        title="Registrar devolución"
        description="Buscá por socio, libro o código del ejemplar. Al devolver, el material queda en revisión hasta que lo habilites (o vuelva a su sede)."
      />
      <div className="toolbar">
        <SearchBox value={query} onChange={setQuery} placeholder="Socio, libro o código de ejemplar" />
        <label className="flex items-center gap-2 text-sm" style={{ flex: "0 0 auto" }}>
          <input type="checkbox" checked={todas} onChange={(e) => setTodas(e.target.checked)} />
          Incluir préstamos de otras sedes
        </label>
      </div>
      <Table
        headers={["Libro y socio", "Ejemplar", "Vence", "Situación", ""]}
        rows={loans.map(({ p, s }) => [
          <div>
            <div className="cell-main">{bookName(s.libro_id, db!)}</div>
            <div className="cell-sub">{socioName(s.socio_id, db!)} · {code("PRE", p.id)}</div>
          </div>,
          <span className="mono">{db!.ejemplares.find((e) => e.id === s.ejemplar_id)?.codigo_inventario}</span>,
          dateLabel(p.fecha_vencimiento),
          isOverdue(p) ? (
            <div>
              <Badge value="VENCIDO" />
              <div className="cell-sub text-[var(--bad)]">{p.dias_atraso} días · {pesos(p.multa)}</div>
            </div>
          ) : (
            <Badge value="ACTIVO" label="Al día" />
          ),
          <Button size="sm" onClick={() => setSelected(p.id)}>
            Devolver
          </Button>,
        ])}
        empty={<Empty title="No hay préstamos abiertos" detail={todas ? "Toda la red está al día." : "Ninguno se entregó en tu sede. Probá incluir otras sedes."} />}
      />
      {selected !== null && (
        <CommandDialog resource="prestamos" id={selected} action="devolver" onClose={() => setSelected(null)} />
      )}
    </>
  );
}
const loginLetters = [
  ["L", -6, -5, 380, 16, 84, 58, -4],
  ["e", 15, 4, 120, 18, -60, 70, -11],
  ["b", 37, -7, 260, 21, 78, -48, -5],
  ["r", 61, 7, 90, 15, -54, 64, -9],
  ["o", 80, -4, 330, 19, -72, 56, -15],
  ["s", 2, 31, 100, 17, 58, -42, -7],
  ["L", 22, 22, 230, 20, -80, 62, -17],
  ["e", 46, 28, 160, 14, 64, 76, -3],
  ["b", 72, 28, 110, 22, -68, -56, -13],
  ["r", 90, 33, 270, 18, -86, 58, -6],
  ["o", -6, 59, 250, 23, 72, -64, -18],
  ["s", 14, 57, 145, 16, -60, 78, -12],
  ["L", 35, 52, 100, 19, 80, -50, -4],
  ["e", 53, 54, 350, 21, -76, 68, -14],
  ["b", 78, 62, 165, 15, -52, -74, -8],
  ["r", 4, 86, 150, 20, 64, -80, -16],
  ["o", 26, 84, 310, 17, -86, -56, -10],
  ["s", 47, 84, 95, 24, 60, -68, -6],
  ["L", 66, 85, 210, 18, -72, -62, -13],
  ["e", 87, 89, 135, 16, -66, -78, -5],
] as const;

export function Access() {
  const {
    theme,
    setTheme,
    usuario,
    authLoading,
    authError,
    iniciarSesion,
    comprobarSesion,
  } = useLibrary();
  const location = useLocation();
  const navigate = useNavigate();
  const [user, setUser] = useState(""),
    [password, setPassword] = useState(""),
    [error, setError] = useState(""),
    [submitting, setSubmitting] = useState(false),
    [motion, setMotion] = useState(true);
  const from = location.state?.from;
  const destination =
    typeof from === "string" &&
    from.startsWith("/") &&
    !from.startsWith("//") &&
    !from.startsWith("/acceso")
      ? from
      : "/inicio";
  async function submit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await iniciarSesion(user.trim(), password);
      navigate(destination, { replace: true });
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "No pudimos iniciar la sesión.",
      );
    } finally {
      setSubmitting(false);
    }
  }
  if (authLoading)
    return (
      <p role="status" className="p-10">
        Verificando sesión…
      </p>
    );
  if (usuario) return <Navigate to={destination} replace />;
  return (
    <div className="relative min-h-svh overflow-hidden bg-[var(--access-background)]">
      <div
        aria-hidden="true"
        className="login-letters"
        style={{ animationPlayState: motion ? "running" : "paused" }}
      >
        {loginLetters.map(
          ([letter, left, top, size, duration, dx, dy, delay], i) => (
            <img
              key={i}
              src={`/assets/motion/letra-${letter}.png`}
              alt=""
              style={
                {
                  left: `${left}%`,
                  top: `${top}%`,
                  "--size": `${size}px`,
                  "--duration": `${duration}s`,
                  "--dx": `${dx}px`,
                  "--dy": `${dy}px`,
                  "--delay": `${delay}s`,
                } as CSSProperties
              }
            />
          ),
        )}
      </div>
      <div className="relative mx-auto max-w-[1440px] p-6 pt-12 md:px-16 lg:px-28">
        <div className="mb-14 flex justify-end">
          <Button
            variant="outline"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            <SunMoon size={18} />
            {theme === "dark" ? "Tema oscuro" : "Tema claro"}
          </Button>
        </div>
        <div className="grid items-center gap-12 lg:grid-cols-[1fr_448px] lg:gap-24">
          <section>
            <Logo symbol className="mb-12 h-28 w-28 lg:mb-20" />
            <p className="mb-6 text-xs tracking-[2px] text-[var(--muted-foreground)]">
              ENTRELIBROS · RED DE BIBLIOTECAS
            </p>
            <h1 className="font-heading text-[42px] leading-[1.18] font-medium tracking-tight text-[var(--access-title)] lg:text-[64px]">
              Una red.
              <br />
              Muchas historias.
            </h1>
            <p className="mt-8 max-w-lg text-lg leading-relaxed text-[var(--muted-foreground)]">
              Libros, personas y sedes conectadas
              <br className="hidden md:block" /> en un mismo lugar.
            </p>
          </section>
          <form
            onSubmit={submit}
            className="rounded-2xl border border-[var(--access-border)] bg-[var(--access-card)] p-7 sm:p-10"
          >
            <h2 className="text-[26px] font-semibold text-[var(--access-title)]">
              Ingresá a tu biblioteca
            </h2>
            <p className="mt-3 mb-8 text-sm text-[var(--muted-foreground)]">
              Acceso para el personal de EntreLibros.
            </p>
            {(error || authError) && <Alert error>{error || authError}</Alert>}
            {authError && (
              <Button
                variant="outline"
                type="button"
                onClick={() => void comprobarSesion()}
              >
                Reintentar conexión
              </Button>
            )}
            <div className="space-y-6">
              <Field label="Usuario">
                <input
                  className={inputClass}
                  required
                  autoComplete="username"
                  value={user}
                  onChange={(e) => setUser(e.target.value)}
                />
              </Field>
              <Field label="Contraseña">
                <input
                  className={inputClass}
                  required
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </Field>
            </div>
            <Button className="mt-8 w-full" type="submit" disabled={submitting}>
              {submitting ? "Ingresando…" : "Ingresar"}
            </Button>
            <p className="mt-7 text-xs leading-relaxed text-[var(--muted-foreground)]">
              ¿Necesitás acceso?
              <br />
              Contactá a la administración de tu sede.
            </p>
          </form>
        </div>
        <footer className="mt-14 flex flex-wrap justify-between gap-4 text-xs text-[var(--muted-foreground)]">
          <p>EntreLibros · Un espacio para cada historia.</p>
          <button
            type="button"
            aria-pressed={!motion}
            className="underline underline-offset-4"
            onClick={() => setMotion((v) => !v)}
          >
            {motion ? "Pausar movimiento" : "Activar movimiento"}
          </button>
        </footer>
      </div>
    </div>
  );
}
export function NotFound({ forbidden = false }: { forbidden?: boolean }) {
  return (
    <div className={`${panelClass} mx-auto max-w-xl py-16 text-center`}>
      <Heading
        title={
          forbidden
            ? "No tenés acceso a esta sección"
            : "No pudimos abrir esta página"
        }
        description={
          forbidden
            ? "Contactá a la administración de tu sede."
            : "La dirección no existe o el registro ya no está disponible."
        }
      />
      <Link className={primaryClass} to="/inicio">
        Ir a la mesa de trabajo
      </Link>
    </div>
  );
}
