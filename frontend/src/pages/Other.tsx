import { useState, type CSSProperties, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useLibrary } from "../app/context";
import { api, isDemo } from "../api";
import {
  bookName,
  code,
  daysLate,
  isOverdue,
  sedeName,
  socioName,
  today,
} from "../domain/selectors";
import {
  Alert,
  Badge,
  Button,
  ConfirmDialog,
  Field,
  Heading,
  inputClass,
  outlineClass,
  panelClass,
  primaryClass,
  Table,
} from "../components/ui";
import { CommandDialog } from "./Commands";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpenCheck,
  CornerDownLeft,
  Plus,
  SunMoon,
  Truck,
} from "lucide-react";
import { Logo } from "../components/Logo";

export function Home() {
  const { db, sedeId } = useLibrary();
  const loans = db!.prestamos.filter(
    (p) =>
      !p.fecha_devolucion &&
      db!.solicitudes.find((s) => s.id === p.solicitud_id)?.sede_destino_id ===
        sedeId,
  );
  const requests = db!.solicitudes.filter(
    (s) =>
      s.sede_destino_id === sedeId &&
      ["PENDIENTE", "ASIGNADA", "LISTA_PARA_ENTREGA"].includes(s.estado),
  );
  const metrics = [
    ["Solicitudes pendientes", requests.length, "/solicitudes"],
    ["Préstamos activos", loans.length, "/prestamos"],
    [
      "Vencidos",
      loans.filter((p) => isOverdue(p)).length,
      "/reportes/vencidos",
    ],
    [
      "Remitos en tránsito",
      db!.remitos.filter(
        (r) =>
          r.estado === "EN_TRANSITO" &&
          (r.sede_origen_id === sedeId || r.sede_destino_id === sedeId),
      ).length,
      "/remitos",
    ],
  ];
  const dueLoans = [...loans]
    .sort((a, b) => a.fecha_vencimiento.localeCompare(b.fecha_vencimiento))
    .slice(0, 4);
  const inbound = db!.remitos.filter(
    (r) => r.sede_destino_id === sedeId && r.estado === "EN_TRANSITO",
  );
  const date = new Intl.DateTimeFormat("es-AR", {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(new Date());
  return (
    <div className="desk-page">
      <p className="section-kicker">MOSTRADOR · {date}</p>
      <Heading
        title="Cada libro, en buenas manos."
        description={`La jornada de ${sedeName(sedeId, db!)}: entregas, devoluciones y libros que viajan entre sedes.`}
        action={
          <Link className={primaryClass} to="/solicitudes/nuevo">
            <Plus size={16} />
            Nueva solicitud
          </Link>
        }
      />
      <div className="desk-numbers">
        {metrics.map(([label, value, path]) => (
          <Link key={label} to={String(path)}>
            <span className="font-heading">
              {String(value).padStart(2, "0")}
            </span>
            <div>
              <p>{label}</p>
              <small>
                Consultar <ArrowUpRight size={12} />
              </small>
            </div>
          </Link>
        ))}
      </div>
      <div className="desk-columns">
        <section>
          <div className="section-heading">
            <div>
              <p className="section-kicker">CIRCULACIÓN</p>
              <h2 className="font-heading">En el mostrador</h2>
            </div>
            <Link to="/solicitudes" className="record-link">
              Ver todas <ArrowRight size={16} />
            </Link>
          </div>
          <div className="desk-queue">
            {requests.length ? (
              requests.map((s) => (
                <Link
                  key={s.id}
                  to={`/solicitudes/${s.id}`}
                  className="queue-entry"
                >
                  <span className="queue-mark">
                    <BookOpenCheck size={20} />
                  </span>
                  <div>
                    <small>
                      {code("SOL", s.id)} · {socioName(s.socio_id, db!)}
                    </small>
                    <h3>{bookName(s.libro_id, db!)}</h3>
                    <Badge value={s.estado} />
                  </div>
                  <ArrowUpRight size={16} />
                </Link>
              ))
            ) : (
              <p className="quiet-message">
                El mostrador está al día. No hay solicitudes pendientes en esta
                sede.
              </p>
            )}
          </div>
          <div className="desk-action-row">
            <CornerDownLeft size={19} />
            <div>
              <h3>Recibir un libro</h3>
              <p>Buscá el préstamo y registrá su devolución.</p>
            </div>
            <Link className={outlineClass} to="/prestamos/devolucion">
              Registrar devolución
            </Link>
          </div>
        </section>
        <aside className="desk-notebook">
          <p className="section-kicker">AGENDA DE LA SEDE</p>
          <h2 className="font-heading">Próximas devoluciones</h2>
          {dueLoans.length ? (
            dueLoans.map((p) => {
              const s = db!.solicitudes.find((s) => s.id === p.solicitud_id)!;
              return (
                <Link
                  key={p.id}
                  className="due-entry"
                  to={`/prestamos/${p.id}`}
                >
                  <span
                    className={isOverdue(p) ? "due-date overdue" : "due-date"}
                  >
                    {new Intl.DateTimeFormat("es-AR", {
                      day: "2-digit",
                      month: "short",
                    }).format(new Date(p.fecha_vencimiento))}
                  </span>
                  <div>
                    <h3>{bookName(s.libro_id, db!)}</h3>
                    <p>{socioName(s.socio_id, db!)}</p>
                    {isOverdue(p) && (
                      <small className="text-[var(--destructive)]">
                        {daysLate(p)} días de atraso
                      </small>
                    )}
                  </div>
                </Link>
              );
            })
          ) : (
            <p className="quiet-message">
              No hay préstamos activos en esta sede.
            </p>
          )}
          <div className="inbound-note">
            <Truck size={20} />
            <div>
              <h3>
                {inbound.length}{" "}
                {inbound.length === 1 ? "envío en camino" : "envíos en camino"}
              </h3>
              <p>Ejemplares que llegan desde otras bibliotecas.</p>
              <Link className="record-link" to="/remitos">
                Consultar remitos <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
export function Appearance() {
  const { theme, setTheme, refresh, notify } = useLibrary();
  const [confirm, setConfirm] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function reset() {
    setBusy(true);
    try {
      await api.reset();
      await refresh();
      notify("Se restablecieron los datos de ejemplo.");
      setConfirm(false);
    } catch (e) {
      setError((e as Error).message);
      setConfirm(false);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Heading
        title="Apariencia"
        description="Elegí el tema con el que querés trabajar."
      />
      <div className={`${panelClass} max-w-[860px]`}>
        <div
          role="group"
          aria-label="Tema de la aplicación"
          className="flex flex-wrap gap-3"
        >
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
        <p className="mt-6 text-sm text-[var(--muted-foreground)]">
          La elección se conserva para tus próximas visitas.
        </p>
      </div>
      {isDemo && (
        <div className={`${panelClass} mt-8 max-w-[860px]`}>
          <h2 className="font-heading text-xl">Datos de demostración</h2>
          <p className="my-4 text-sm text-[var(--muted-foreground)]">
            Podés volver al conjunto inicial para probar nuevamente los
            recorridos.
          </p>
          <Button variant="outline" onClick={() => setConfirm(true)}>
            Restablecer ejemplos
          </Button>
        </div>
      )}
      {error && <Alert error>{error}</Alert>}
      {confirm && (
        <ConfirmDialog
          title="Restablecer ejemplos"
          description="Se eliminarán los cambios de demostración guardados en este navegador."
          onConfirm={() => void reset()}
          onCancel={() => setConfirm(false)}
          busy={busy}
        />
      )}
    </>
  );
}
export function Returns() {
  const { db } = useLibrary();
  const [query, setQuery] = useState(""),
    [selected, setSelected] = useState<number | null>(null);
  const loans = db!.prestamos
    .filter((p) => !p.fecha_devolucion)
    .filter((p) => {
      const s = db!.solicitudes.find((s) => s.id === p.solicitud_id)!;
      return `${code("PRE", p.id)} ${socioName(s.socio_id, db!)} ${db!.ejemplares.find((e) => e.id === s.ejemplar_id)?.codigo_inventario}`
        .toLowerCase()
        .includes(query.toLowerCase());
    });
  return (
    <>
      <Heading
        title="Registrar devolución"
        description="Buscá el préstamo o ejemplar y revisá la condición del material."
      />
      <Field label="Buscar préstamo, socio o ejemplar">
        <input
          className={`${inputClass} mb-6 max-w-xl`}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </Field>
      <Table
        headers={["Préstamo", "Socio y libro", "Vencimiento", ""]}
        rows={loans.map((p) => {
          const s = db!.solicitudes.find((s) => s.id === p.solicitud_id)!;
          return [
            code("PRE", p.id),
            `${socioName(s.socio_id, db!)} · ${bookName(s.libro_id, db!)}`,
            p.fecha_vencimiento.slice(0, 10),
            <Button onClick={() => setSelected(p.id)}>
              Registrar devolución
            </Button>,
          ];
        })}
      />
      {selected !== null && (
        <CommandDialog
          resource="prestamos"
          id={selected}
          action="devolver"
          onClose={() => setSelected(null)}
        />
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
  const { theme, setTheme } = useLibrary();
  const navigate = useNavigate();
  const [user, setUser] = useState("biblioteca"),
    [password, setPassword] = useState("demo"),
    [error, setError] = useState(""),
    [motion, setMotion] = useState(true);
  function submit(e: FormEvent) {
    e.preventDefault();
    if (!isDemo) {
      setError(
        "El acceso real requiere implementar y conectar la autenticación del backend.",
      );
      return;
    }
    if (user !== "biblioteca" || password !== "demo") {
      setError("Para la demostración usá biblioteca / demo.");
      return;
    }
    navigate("/inicio");
  }
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
              {isDemo
                ? "Acceso de demostración: biblioteca / demo."
                : "Acceso para el personal de EntreLibros."}
            </p>
            {error && <Alert error>{error}</Alert>}
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
            <Button className="mt-8 w-full" type="submit">
              Ingresar
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
      <Link className={primaryClass} to="/catalogo">
        Volver al catálogo
      </Link>
    </div>
  );
}
