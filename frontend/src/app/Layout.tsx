import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import {
  BookCopy,
  BookOpenCheck,
  Bookmark,
  Building2,
  ChartNoAxesColumn,
  ClipboardList,
  CornerDownLeft,
  House,
  LibraryBig,
  LogOut,
  Map as MapIcon,
  Menu,
  Moon,
  Plus,
  Sun,
  SunMoon,
  Truck,
  Users,
  X,
} from "lucide-react";
import { useLibrary } from "./context";
import { tasksFor } from "../domain/tasks";
import { Alert, Button } from "../components/ui";

interface NavEntry {
  path: string;
  label: string;
  icon: typeof House;
  count?: number;
  quiet?: boolean;
  end?: boolean;
}

export function Layout() {
  const {
    db,
    error,
    loading,
    refresh,
    theme,
    setTheme,
    sedeId,
    setSedeId,
    toast,
    usuario,
    cerrarSesion,
    notify,
  } = useLibrary();
  const [open, setOpen] = useState(false);
  const [saliendo, setSaliendo] = useState(false);
  const location = useLocation();
  useEffect(() => setOpen(false), [location.pathname]);

  const t = db ? tasksFor(db, sedeId) : null;
  const groups: { title: string; items: NavEntry[] }[] = [
    {
      title: "Hoy",
      items: [
        {
          path: "inicio",
          label: "Mesa de trabajo",
          icon: House,
          count: t ? t.circulacion + t.logistica : 0,
        },
      ],
    },
    {
      title: "Circulación",
      items: [
        {
          path: "solicitudes",
          label: "Solicitudes",
          icon: ClipboardList,
          count: t?.circulacion,
        },
        {
          path: "prestamos",
          label: "Préstamos",
          icon: BookOpenCheck,
          count: t?.vencidos.length,
          end: true,
        },
        {
          path: "prestamos/devolucion",
          label: "Devoluciones",
          icon: CornerDownLeft,
        },
        {
          path: "reservas",
          label: "Reservas",
          icon: Bookmark,
          count: t?.reservasPorAsignar.length,
          quiet: true,
        },
      ],
    },
    {
      title: "Logística",
      items: [
        { path: "remitos", label: "Remitos", icon: Truck, count: t?.logistica },
      ],
    },
    {
      title: "Colección",
      items: [
        { path: "catalogo", label: "Catálogo", icon: LibraryBig },
        { path: "ejemplares", label: "Ejemplares", icon: BookCopy },
      ],
    },
    {
      title: "La red",
      items: [
        { path: "socios", label: "Socios", icon: Users },
        { path: "sedes", label: "Sedes", icon: Building2 },
      ],
    },
    {
      title: "Análisis",
      items: [
        { path: "reportes", label: "Reportes", icon: ChartNoAxesColumn },
        { path: "guia", label: "Cómo funciona", icon: MapIcon },
      ],
    },
  ];
  const all = groups.flatMap((g) => g.items);
  const section =
    [...all]
      .sort((a, b) => b.path.length - a.path.length)
      .find((n) => location.pathname.startsWith(`/${n.path}`))?.label ??
    (location.pathname === "/apariencia" ? "Apariencia" : "Inicio");
  const sedeActual = db?.sedes.find((s) => s.id === sedeId);
  const nextTheme =
    theme === "light" ? "dark" : theme === "dark" ? "system" : "light";
  const ThemeIcon = theme === "light" ? Sun : theme === "dark" ? Moon : SunMoon;

  async function logout() {
    setSaliendo(true);
    try {
      await cerrarSesion();
    } catch (e) {
      notify(e instanceof Error ? e.message : "No pudimos cerrar la sesión.");
    } finally {
      setSaliendo(false);
    }
  }

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
          className="fixed inset-0 z-30 bg-black/45 lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}
      <aside className={`sidebar ${open ? "is-open" : ""}`}>
        <div className="sidebar-brand">
          <img src="/brand/isotipo-dark.svg" alt="" />
          <Link to="/inicio" className="min-w-0">
            <strong>EntreLibros</strong>
            <small>Red de bibliotecas</small>
          </Link>
          <button
            className="icon-btn ml-auto lg:hidden"
            onClick={() => setOpen(false)}
            aria-label="Cerrar menú"
          >
            <X size={19} />
          </button>
        </div>
        <div className="sede-switch">
          <label htmlFor="sede-trabajo">Estás trabajando en</label>
          <select
            id="sede-trabajo"
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
        </div>
        <nav aria-label="Navegación principal">
          {groups.map((g) => (
            <div key={g.title} className="nav-group">
              <p className="nav-group-title">{g.title}</p>
              {g.items.map((n) => (
                <NavLink
                  key={n.path}
                  to={`/${n.path}`}
                  end={n.end}
                  className={({ isActive }) =>
                    `nav-item ${isActive ? "active" : ""}`
                  }
                >
                  <n.icon size={18} />
                  <span>{n.label}</span>
                  {!!n.count && (
                    <span
                      className={`nav-count ${n.quiet ? "quiet" : ""}`}
                      title="Pendientes en tu sede"
                    >
                      {n.count}
                    </span>
                  )}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="avatar" aria-hidden="true">
            {(usuario?.nombre ?? "?").slice(0, 1).toUpperCase()}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-[13px] font-semibold">
              {usuario?.nombre}
            </p>
            <p className="truncate text-[11.5px] text-[var(--nav-muted)]">
              {sedeActual?.nombre ?? "Sin sede"}
            </p>
          </div>
          <button
            type="button"
            className="icon-btn"
            onClick={() => setTheme(nextTheme)}
            aria-label={`Tema: ${theme === "light" ? "claro" : theme === "dark" ? "oscuro" : "del sistema"}. Cambiar`}
            title="Cambiar tema"
          >
            <ThemeIcon size={17} />
          </button>
          <button
            type="button"
            className="icon-btn"
            onClick={() => void logout()}
            disabled={saliendo}
            aria-label="Cerrar sesión"
            title="Cerrar sesión"
          >
            <LogOut size={17} />
          </button>
        </div>
      </aside>
      <div className="main-area">
        <header className="topbar">
          <button
            onClick={() => setOpen(true)}
            aria-label="Abrir menú"
            className="icon-btn lg:hidden"
          >
            <Menu size={21} />
          </button>
          <div className="crumbs">
            <span className="hidden sm:inline">
              {sedeActual?.nombre ?? "EntreLibros"}
            </span>
            <span className="hidden sm:inline">/</span>
            <strong className="truncate">{section}</strong>
          </div>
          <div className="topbar-search">
            <Link
              to="/prestamos/devolucion"
              className="btn btn-outline btn-sm hidden md:inline-flex"
            >
              <CornerDownLeft size={15} /> Devolución
            </Link>
            <Link to="/solicitudes/nuevo" className="btn btn-primary btn-sm">
              <Plus size={15} /> Nueva solicitud
            </Link>
          </div>
        </header>
        <main id="contenido" className="workspace">
          {error ? (
            <>
              <Alert error>{error}</Alert>
              <Button onClick={() => void refresh()}>Reintentar</Button>
            </>
          ) : loading && !db ? (
            <div role="status" className="card card-pad animate-pulse">
              Cargando biblioteca…
            </div>
          ) : (
            db && <Outlet />
          )}
        </main>
      </div>
      {toast && (
        <div role="status" className="toast">
          {toast}
        </div>
      )}
    </div>
  );
}
