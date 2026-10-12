import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { Database } from "../domain/models";
import { api } from "../api";

type Theme = "light" | "dark" | "system";
interface Context {
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
  const [db, setDb] = useState<Database | null>(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  const [theme, setThemeState] = useState<Theme>(() => {
    const t = localStorage.getItem("entrelibros:theme");
    return t === "light" || t === "dark" ? t : "system";
  });
  const [sedeId, setSedeId] = useState(1),
    [toast, setToast] = useState("");
  async function refresh() {
    setLoading(true);
    setError("");
    try {
      setDb(await api.snapshot());
    } catch (e) {
      setError(e instanceof Error ? e.message : "No pudimos cargar los datos.");
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void refresh();
  }, []);
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
