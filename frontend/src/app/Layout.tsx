import { useEffect, useRef, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { ChevronDown, LogOut, Menu, Moon, Plus, Sun, SunMoon, UserRound, X } from "lucide-react";
import { useLibrary } from "./context";
import { tasksFor } from "../domain/tasks";
import { Alert, Button } from "../components/ui";

/**
 * Navegación en dos niveles: módulos arriba (siempre visibles, pocos) y
 * secciones del módulo activo debajo. Reemplaza la barra lateral con trece
 * enlaces: la ubicación queda clara y las tablas ganan ancho.
 */
interface Section {
  to: string;
  label: string;
  hint?: string;
  end?: boolean;
}
interface Module {
  key: string;
  label: string;
  to: string;
  match: string[];
  sections: Section[];
}
const MODULES: Module[] = [
  { key: "mesa", label: "Mesa", to: "/inicio", match: ["/inicio"], sections: [] },
  {
    key: "circulacion",
    label: "Circulación",
    to: "/solicitudes",
    match: ["/solicitudes", "/prestamos", "/reservas"],
    sections: [
      { to: "/solicitudes", label: "Solicitudes", hint: "Pedidos de socios, de la asignación a la entrega" },
      { to: "/prestamos", label: "Préstamos", hint: "Libros en manos de socios, vencimientos y multas", end: true },
      { to: "/prestamos/devolucion", label: "Devoluciones", hint: "Recibir un libro y registrar su estado" },
      { to: "/reservas", label: "Reservas", hint: "Socios esperando una copia libre" },
    ],
  },
  {
    key: "logistica",
    label: "Logística",
    to: "/remitos",
    match: ["/remitos"],
    sections: [{ to: "/remitos", label: "Remitos", hint: "Envíos entre sedes y su trazabilidad" }],
  },
  {
    key: "coleccion",
    label: "Colección",
    to: "/catalogo",
    match: ["/catalogo", "/ejemplares"],
    sections: [
      { to: "/catalogo", label: "Catálogo", hint: "Los títulos de la red y su disponibilidad" },
      { to: "/ejemplares", label: "Ejemplares", hint: "Cada copia física, dónde está y cómo está" },
    ],
  },
  {
    key: "red",
    label: "Red",
    to: "/socios",
    match: ["/socios", "/sedes"],
    sections: [
      { to: "/socios", label: "Socios", hint: "Lectores, habilitación e historial" },
      { to: "/sedes", label: "Sedes", hint: "Bibliotecas de la red, horarios y estado" },
    ],
  },
  {
    key: "informes",
    label: "Informes",
    to: "/reportes",
    match: ["/reportes", "/guia"],
    sections: [
      { to: "/reportes", label: "Reportes", hint: "Siete informes con filtros, PDF y CSV" },
      { to: "/guia", label: "Cómo funciona", hint: "Circuitos y patrones State / Strategy" },
    ],
  },
];

export function Layout() {
  const { db, error, loading, refresh, theme, setTheme, sedeId, setSedeId, toast, usuario, cerrarSesion, notify } =
    useLibrary();
  const [mobile, setMobile] = useState(false);
  const [userMenu, setUserMenu] = useState(false);
  const [openMod, setOpenMod] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  useEffect(() => {
    setMobile(false);
    setUserMenu(false);
    setOpenMod(null);
  }, [location.pathname]);
  useEffect(() => {
    if (!userMenu) return;
    const close = (e: MouseEvent) => {
      if (!menuRef.current?.contains(e.target as Node)) setUserMenu(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [userMenu]);

  const t = db ? tasksFor(db, sedeId) : null;
  const pending: Record<string, number> = {
    mesa: t ? t.circulacion + t.logistica + t.vencidos.length : 0,
  };
  const current =
    MODULES.find((m) => m.match.some((p) => location.pathname.startsWith(p))) ??
    (location.pathname === "/apariencia" ? undefined : MODULES[0]);

  async function logout() {
    try {
      await cerrarSesion();
    } catch (e) {
      notify(e instanceof Error ? e.message : "No pudimos cerrar la sesión.");
    }
  }
  const themeLabel = theme === "light" ? "claro" : theme === "dark" ? "oscuro" : "del sistema";
  const ThemeIcon = theme === "light" ? Sun : theme === "dark" ? Moon : SunMoon;

  return (
    <div className="min-h-screen">
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:fixed focus:z-50 focus:bg-[var(--surface)] focus:p-4"
      >
        Saltar al contenido
      </a>
      <header className="appbar">
        <div className="appbar-row">
          <button
            className="icon-btn lg:hidden"
            aria-label={mobile ? "Cerrar menú" : "Abrir menú"}
            aria-expanded={mobile}
            onClick={() => setMobile((v) => !v)}
          >
            {mobile ? <X size={19} /> : <Menu size={19} />}
          </button>
          <Link to="/inicio" className="brand" aria-label="EntreLibros · Mesa de trabajo">
            <img src="/brand/isotipo-dark.svg" alt="" />
            EntreLibros
          </Link>
          <nav className="modules hidden lg:flex" aria-label="Módulos" onMouseLeave={() => setOpenMod(null)}>
            {MODULES.map((m) => {
              const active = current?.key === m.key;
              const isOpen = openMod === m.key && m.sections.length > 1;
              return (
                <div
                  key={m.key}
                  className={`module-wrap ${isOpen ? "open" : ""}`}
                  onMouseEnter={() => setOpenMod(m.key)}
                  onKeyDown={(e) => e.key === "Escape" && setOpenMod(null)}
                >
                  <Link
                    to={m.to}
                    className={`module ${active ? "active" : ""}`}
                    aria-current={active ? "page" : undefined}
                    aria-haspopup={m.sections.length > 1 ? "true" : undefined}
                    aria-expanded={m.sections.length > 1 ? isOpen : undefined}
                    onFocus={() => setOpenMod(m.key)}
                  >
                    {m.label}
                    {!!pending[m.key] && (
                      <span className="count" title="Tareas pendientes en tu sede">
                        {pending[m.key]}
                      </span>
                    )}
                    {m.sections.length > 1 && <ChevronDown size={13} />}
                  </Link>
                  {isOpen && (
                    <div className="dropdown" role="menu" aria-label={m.label}>
                      {m.sections.map((sec) => (
                        <NavLink
                          key={sec.to}
                          to={sec.to}
                          end={sec.end}
                          role="menuitem"
                          className={({ isActive }) => (isActive ? "active" : "")}
                          onClick={() => setOpenMod(null)}
                        >
                          <b>{sec.label}</b>
                          {sec.hint && <small>{sec.hint}</small>}
                        </NavLink>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </nav>
          <div className="appbar-tools">
            <label className="sede-picker">
              <span className="hidden sm:inline">Sede</span>
              <select aria-label="Sede de trabajo" value={sedeId} onChange={(e) => setSedeId(Number(e.target.value))}>
                {db?.sedes
                  .filter((s) => s.estado === "ACTIVA")
                  .map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.nombre.replace(/^Biblioteca /, "")}
                    </option>
                  ))}
              </select>
            </label>
            <Link
              to="/solicitudes/nuevo"
              className={`btn btn-primary btn-sm ${current?.key === "mesa" ? "hidden" : "hidden sm:inline-flex"}`}
            >
              <Plus size={14} /> Solicitud
            </Link>
            <div className="relative" ref={menuRef}>
              <button
                className="icon-btn"
                aria-label="Menú de usuario"
                aria-expanded={userMenu}
                onClick={() => setUserMenu((v) => !v)}
              >
                <UserRound size={18} />
              </button>
              {userMenu && (
                <div className="menu-pop" role="menu">
                  <p>{usuario?.nombre}</p>
                  <button
                    role="menuitem"
                    onClick={() => setTheme(theme === "light" ? "dark" : theme === "dark" ? "system" : "light")}
                  >
                    <ThemeIcon size={15} /> Tema {themeLabel}
                  </button>
                  <Link role="menuitem" to="/guia">
                    Cómo funciona
                  </Link>
                  <button role="menuitem" onClick={() => void logout()} aria-label="Cerrar sesión">
                    <LogOut size={15} /> Cerrar sesión
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
        {current && current.sections.length > 0 && (
          <nav className="subnav hidden lg:block" aria-label={`Secciones de ${current.label}`}>
            <div className="subnav-row">
              <span className="where">{current.label}</span>
              {current.sections.map((s) => (
                <NavLink
                  key={s.to}
                  to={s.to}
                  end={s.end}
                  className={({ isActive }) => `sublink ${isActive ? "active" : ""}`}
                >
                  {s.label}
                </NavLink>
              ))}
            </div>
          </nav>
        )}
        {mobile && (
          <nav className="mobile-nav lg:hidden" aria-label="Navegación">
            {MODULES.map((m) => (
              <div key={m.key}>
                <h3>{m.label}</h3>
                {(m.sections.length ? m.sections : [{ to: m.to, label: "Mesa de trabajo" }]).map((s) => (
                  <NavLink key={s.to} to={s.to} end={"end" in s ? s.end : undefined} className={({ isActive }) => (isActive ? "active" : "")}>
                    {s.label}
                    {m.key === "mesa" && !!pending.mesa && <span className="count">{pending.mesa}</span>}
                  </NavLink>
                ))}
              </div>
            ))}
          </nav>
        )}
      </header>
      <main id="contenido" className="workspace">
        {error ? (
          <>
            <Alert error>{error}</Alert>
            <Button onClick={() => void refresh()}>Reintentar</Button>
          </>
        ) : loading && !db ? (
          <p role="status" className="muted">
            Cargando biblioteca…
          </p>
        ) : (
          db && <Outlet />
        )}
      </main>
      {toast && (
        <div role="status" className="toast">
          {toast}
        </div>
      )}
    </div>
  );
}
