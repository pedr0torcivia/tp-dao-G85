import { useState, type FormEvent } from "react";
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
import { SunMoon } from "lucide-react";
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
  return (
    <>
      <Heading
        title="Buen día"
        description={`Un vistazo al trabajo de ${sedeName(sedeId, db!)}.`}
      />
      <div className="mb-10 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map(([label, value, path]) => (
          <Link key={label} to={String(path)} className={panelClass}>
            <p className="text-sm text-[var(--muted-foreground)]">{label}</p>
            <p className="font-heading mt-5 text-4xl text-[var(--primary)]">
              {value}
            </p>
          </Link>
        ))}
      </div>
      <h2 className="font-heading mb-5 text-xl">Para atender hoy</h2>
      <Table
        headers={["Solicitud", "Socio", "Libro", "Estado", ""]}
        rows={requests.map((s) => [
          code("SOL", s.id),
          socioName(s.socio_id, db!),
          bookName(s.libro_id, db!),
          <Badge value={s.estado} />,
          <Link className={outlineClass} to={`/solicitudes/${s.id}`}>
            Ver detalle
          </Link>,
        ])}
      />
      <div className="mt-8 flex flex-wrap gap-3">
        <Link className={primaryClass} to="/solicitudes/nuevo">
          Nueva solicitud
        </Link>
        <Link className={outlineClass} to="/prestamos/devolucion">
          Registrar devolución
        </Link>
        <Link className={outlineClass} to="/remitos/nuevo">
          Preparar remito
        </Link>
      </div>
    </>
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
        className="pointer-events-none absolute inset-0 grid grid-cols-3 gap-12 opacity-[0.06] dark:opacity-[0.07]"
      >
        {["L", "e", "b", "r", "o", "s", "L", "b", "e"].map((letter, i) => (
          <img
            key={i}
            src={`/assets/motion/letra-${letter}.png`}
            alt=""
            className={`w-[240px] object-contain ${motion ? "drift" : ""}`}
          />
        ))}
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
