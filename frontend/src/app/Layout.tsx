import { useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import {
  LibraryBig,
  ClipboardList,
  BookOpenCheck,
  Bookmark,
  Truck,
  Users,
  Building2,
  ChartNoAxesColumn,
  SunMoon,
  Menu,
  X,
  LogOut,
} from "lucide-react";
import { useLibrary } from "./context";
import { api, isDemo } from "../api";
import { Alert, Button, ConfirmDialog, inputClass } from "../components/ui";
import { Logo } from "../components/Logo";

const nav = [
  { path: "catalogo", label: "Catálogo", icon: LibraryBig },
  { path: "solicitudes", label: "Solicitudes", icon: ClipboardList },
  { path: "prestamos", label: "Préstamos", icon: BookOpenCheck },
  { path: "reservas", label: "Reservas", icon: Bookmark },
  { path: "remitos", label: "Remitos", icon: Truck },
  { path: "socios", label: "Socios", icon: Users },
  { path: "sedes", label: "Sedes", icon: Building2 },
  { path: "reportes", label: "Reportes", icon: ChartNoAxesColumn },
];
export function Layout() {
  const { db, error, loading, refresh, theme, sedeId, setSedeId, toast } =
    useLibrary();
  const [open, setOpen] = useState(false),
    [resetOpen, setResetOpen] = useState(false);
  const location = useLocation();
  const section =
    location.pathname === "/apariencia"
      ? "Apariencia"
      : (nav.find((n) => location.pathname.startsWith(`/${n.path}`))?.label ??
        "Inicio");
  return (
    <div className="min-h-screen">
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:fixed focus:z-50 focus:bg-[var(--card)] focus:p-4"
      >
        Saltar al contenido
      </a>
      {open && (
        <button
          aria-label="Cerrar navegación"
          className="fixed inset-0 z-30 bg-black/40 lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-[248px] flex-col border-r border-[var(--nav-border)] bg-[var(--nav-background)] p-4 text-[var(--nav-foreground)] ${open ? "flex" : "hidden"} lg:flex`}
      >
        <div className="flex items-center justify-between">
          <Link
            to="/inicio"
            aria-label="EntreLibros · Inicio"
            onClick={() => setOpen(false)}
            className="block px-1 pt-2"
          >
            <Logo className="h-[55px] w-[208px]" />
          </Link>
          <button
            className="lg:hidden"
            onClick={() => setOpen(false)}
            aria-label="Cerrar menú"
          >
            <X size={20} />
          </button>
        </div>
        <p className="mt-4 px-2 text-[11px] tracking-wider text-[var(--nav-muted)]">
          RED DE BIBLIOTECAS
        </p>
        <nav
          aria-label="Navegación principal"
          className="mt-10 flex-1 overflow-y-auto"
        >
          {nav.map((n, i) => (
            <div key={n.path}>
              {(i === 0 || i === 5) && (
                <p
                  className={`${i === 5 ? "mt-8" : ""} mb-4 px-2 text-[11px] tracking-wider text-[var(--nav-muted)]`}
                >
                  {i === 0 ? "CIRCULACIÓN" : "ADMINISTRACIÓN"}
                </p>
              )}
              <NavLink
                to={`/${n.path}`}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  `mb-1 flex min-h-[42px] items-center gap-3 rounded-lg px-3 text-sm ${isActive ? "bg-[var(--nav-active-bg)] font-semibold text-[var(--nav-active-fg)]" : "hover:bg-[var(--nav-active-bg)]"}`
                }
              >
                <n.icon size={18} />
                {n.label}
              </NavLink>
            </div>
          ))}
        </nav>
        <Link
          to="/apariencia"
          onClick={() => setOpen(false)}
          className="mb-6 flex items-center gap-3 rounded-lg border border-[var(--nav-border)] px-3 py-3 text-[13px]"
        >
          <SunMoon size={18} />
          {theme === "system"
            ? "Tema del sistema"
            : theme === "light"
              ? "Tema claro"
              : "Tema oscuro"}
        </Link>
        <div className="flex items-center gap-3 border-t border-[var(--nav-border)] pt-5">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--nav-active-bg)] text-xs font-semibold">
            PB
          </span>
          <div className="min-w-0">
            <p className="text-xs font-medium">Personal de biblioteca</p>
            <p className="mt-1 text-[11px] text-[var(--nav-muted)]">
              {isDemo ? "Sesión de demostración" : "Sesión de trabajo"}
            </p>
          </div>
          <Link to="/acceso" aria-label="Ir al acceso" className="ml-auto">
            <LogOut size={16} />
          </Link>
        </div>
      </aside>
      <div className="lg:ml-[248px]">
        <header className="flex min-h-[76px] items-center justify-between gap-4 border-b border-[var(--border)] bg-[var(--card)] px-5 lg:px-10">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setOpen(true)}
              aria-label="Abrir menú"
              className="lg:hidden"
            >
              <Menu size={22} />
            </button>
            <p className="text-[13px] text-[var(--muted-foreground)]">
              {section} / {section}
            </p>
          </div>
          <select
            aria-label="Sede de trabajo"
            className={`${inputClass} max-w-[220px]`}
            value={sedeId}
            onChange={(e) => setSedeId(Number(e.target.value))}
          >
            {db?.sedes
              .filter((s) => s.estado === "ACTIVA")
              .map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
          </select>
        </header>
        <main
          id="contenido"
          className="mx-auto max-w-[1600px] p-5 pt-9 lg:p-10"
        >
          {isDemo && (
            <p className="mb-6 text-xs text-[var(--muted-foreground)]">
              Demostración · Los cambios se guardan sólo en este navegador.
            </p>
          )}
          {error ? (
            <>
              <Alert error>{error}</Alert>
              <Button onClick={() => void refresh()}>Reintentar</Button>
              {isDemo && (
                <Button
                  variant="outline"
                  className="ml-4"
                  onClick={() => setResetOpen(true)}
                >
                  Restablecer ejemplos
                </Button>
              )}
            </>
          ) : loading && !db ? (
            <div
              role="status"
              className="animate-pulse rounded-xl bg-[var(--muted)] p-10"
            >
              Cargando biblioteca…
            </div>
          ) : (
            db && <Outlet />
          )}
        </main>
      </div>
      {toast && (
        <div
          role="status"
          className="fixed right-5 bottom-5 z-50 max-w-[90vw] rounded-lg border border-[var(--border)] bg-[var(--card)] px-5 py-4 shadow-lg"
        >
          {toast}
        </div>
      )}
      {resetOpen && (
        <ConfirmDialog
          title="Restablecer ejemplos"
          description="Se eliminarán los cambios de demostración guardados en este navegador."
          onConfirm={() =>
            void api
              .reset()
              .then(refresh)
              .then(() => setResetOpen(false))
          }
          onCancel={() => setResetOpen(false)}
        />
      )}
    </div>
  );
}
