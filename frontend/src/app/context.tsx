import {
  createContext,
  useContext,
  useEffect,
  useState,
  useRef,
  type ReactNode,
} from "react";
import type { Database } from "../domain/models";
import { api } from "../api";
import { consultarSesion, ingresar, salir, type Usuario } from "../api/auth";

type Theme = "light" | "dark" | "system";
interface Context {
  usuario: Usuario | null;
  authLoading: boolean;
  authError: string;
  comprobarSesion: () => Promise<void>;
  iniciarSesion: (username: string, password: string) => Promise<void>;
  cerrarSesion: () => Promise<void>;
  db: Database | null;
  loading: boolean;
  error: string;
  refresh: () => Promise<void>;
  theme: Theme;
  setTheme: (t: Theme) => void;
  sedeId: number;
  setSedeId: (id: number) => void;
  toast: string;
  notify: (message: string) => void;
}
const Ctx = createContext<Context | null>(null);
export const useLibrary = () => useContext(Ctx)!;
export function LibraryProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authError, setAuthError] = useState("");
  const generation = useRef(0);
  const [db, setDb] = useState<Database | null>(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  const [theme, setThemeState] = useState<Theme>(() => {
    const t = localStorage.getItem("entrelibros:theme");
    return t === "light" || t === "dark" || t === "system" ? t : "light";
  });
  const [sedeId, setSedeIdState] = useState(() => {
    try {
      return Number(localStorage.getItem("entrelibros:sede")) || 1;
    } catch {
      return 1;
    }
  });
  const [toast, setToast] = useState("");
  const setSedeId = (id: number | ((actual: number) => number)) =>
    setSedeIdState((actual) => {
      const next = typeof id === "function" ? id(actual) : id;
      try {
        localStorage.setItem("entrelibros:sede", String(next));
      } catch {
        /* almacenamiento no disponible */
      }
      return next;
    });
  async function refresh() {
    if (!usuario) return;
    const version = generation.current;
    setLoading(true);
    setError("");
    try {
      const snapshot = await api.snapshot();
      if (version !== generation.current) return;
      setDb(snapshot);
      setSedeId((actual) =>
        snapshot.sedes.some((s) => s.id === actual && s.estado === "ACTIVA")
          ? actual
          : (snapshot.sedes.find((s) => s.estado === "ACTIVA")?.id ?? 0),
      );
    } catch (e) {
      if (version !== generation.current) return;
      setError(e instanceof Error ? e.message : "No pudimos cargar los datos.");
    } finally {
      if (version === generation.current) setLoading(false);
    }
  }
  function limpiarSesion() {
    generation.current += 1;
    setUsuario(null);
    setDb(null);
    setError("");
    setToast("");
  }
  async function comprobarSesion() {
    setAuthLoading(true);
    setAuthError("");
    try {
      setUsuario(await consultarSesion());
    } catch (e) {
      setAuthError(
        e instanceof Error ? e.message : "No pudimos verificar la sesión.",
      );
    } finally {
      setAuthLoading(false);
    }
  }
  async function iniciarSesion(username: string, password: string) {
    const user = await ingresar(username, password);
    generation.current += 1;
    setAuthError("");
    setUsuario(user);
  }
  async function cerrarSesion() {
    await salir();
    limpiarSesion();
  }
  useEffect(() => {
    void comprobarSesion();
    const expired = () => limpiarSesion();
    window.addEventListener("entrelibros:sesion-vencida", expired);
    return () =>
      window.removeEventListener("entrelibros:sesion-vencida", expired);
  }, []);
  useEffect(() => {
    if (usuario) void refresh();
  }, [usuario]);
  useEffect(() => {
    const media = matchMedia("(prefers-color-scheme: dark)");
    const update = () => {
      document.documentElement.dataset.theme =
        theme === "system" ? (media.matches ? "dark" : "light") : theme;
    };
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, [theme]);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 4500);
    return () => clearTimeout(timer);
  }, [toast]);
  const setTheme = (t: Theme) => {
    localStorage.setItem("entrelibros:theme", t);
    setThemeState(t);
  };
  return (
    <Ctx.Provider
      value={{
        usuario,
        authLoading,
        authError,
        comprobarSesion,
        iniciarSesion,
        cerrarSesion,
        db,
        loading,
        error,
        refresh,
        theme,
        setTheme,
        sedeId,
        setSedeId,
        toast,
        notify: setToast,
      }}
    >
      {children}
    </Ctx.Provider>
  );
}
