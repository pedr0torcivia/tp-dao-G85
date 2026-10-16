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
  House,
  ChevronRight,
} from "lucide-react";
import { useLibrary } from "./context";
import { api, isDemo } from "../api";
import { Alert, Button, ConfirmDialog, inputClass } from "../components/ui";
import { Logo } from "../components/Logo";

const nav = [
  { path: "inicio", label: "Mesa de trabajo", icon: House },
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
        className={`library-nav fixed inset-y-0 left-0 z-40 w-[232px] flex-col border-r border-[var(--nav-border)] bg-[var(--nav-background)] p-4 text-[var(--nav-foreground)] ${open ? "flex" : "hidden"} lg:flex`}
      >
        <div className="flex items-center justify-between">
          <Link
            to="/inicio"
            aria-label="EntreLibros · Inicio"
            onClick={() => setOpen(false)}
            className="block px-1 pt-2"
          >
            <Logo className="h-[55px] w-[190px]" />
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
          className="mt-8 flex-1 overflow-y-auto"
        >
          {nav.map((n, i) => (
            <div key={n.path}>
              {(i === 0 || i === 6) && (
                <p
                  className={`${i === 6 ? "mt-8" : ""} mb-3 px-3 text-[10px] tracking-[1.8px] text-[var(--nav-muted)]`}
                >
                  {i === 0 ? "MOSTRADOR" : "LA RED"}
                </p>
              )}
              <NavLink
                to={`/${n.path}`}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  `nav-entry mb-1 flex min-h-[42px] items-center gap-3 px-3 text-sm ${isActive ? "is-active font-semibold" : ""}`
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
          <span className="flex h-9 w-9 shrink-0 items-center justify-center bg-[var(--nav-active-bg)] text-[var(--brand-orange)]">
            <BookOpenCheck size={18} />
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
      <div className="lg:ml-[232px]">
        <header className="library-topbar flex min-h-[76px] items-center justify-between gap-4 border-b border-[var(--border)] px-5 lg:px-10">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setOpen(true)}
              aria-label="Abrir menú"
              className="lg:hidden"
            >
              <Menu size={22} />
            </button>
            <Link
              to="/inicio"
              className="hidden text-xs text-[var(--muted-foreground)] sm:block"
            >
              EntreLibros
            </Link>
            <ChevronRight
              size={12}
              className="hidden text-[var(--muted-foreground)] sm:block"
            />
            <p className="text-[13px]">
              {section === "Inicio" ? "Mesa de trabajo" : section}
            </p>
          </div>
          <label className="flex items-center gap-3">
            <span className="hidden text-[10px] tracking-widest text-[var(--muted-foreground)] xl:block">
              SEDE DE TRABAJO
            </span>
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
          </label>
        </header>
        <main
          id="contenido"
          className="workspace mx-auto max-w-[1600px] p-5 pt-9 lg:p-10"
        >
          {isDemo && (
            <p className="demo-note mb-7 text-[11px] text-[var(--muted-foreground)]">
              <span>ESPACIO DE PRUEBA</span> Los cambios se guardan en este
              navegador.
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
