import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  Outlet,
  useLocation,
} from "react-router-dom";
import { LibraryProvider, useLibrary } from "./context";
import { Alert, Button } from "../components/ui";
import { Layout } from "./Layout";
import { EntityList } from "../pages/Lists";
import { EntityDetail } from "../pages/Details";
import { EntityForm } from "../pages/EntityForm";
import { Access, Appearance, NotFound, Returns } from "../pages/Other";
import { Home } from "../pages/Home";
import { Guide } from "../pages/Guide";
import { ReportCenter, ReportPage } from "../pages/Reports";
import type { Resource } from "../domain/models";
import { pathOf } from "../pages/resources";

const resources: Resource[] = [
  "libros",
  "socios",
  "sedes",
  "ejemplares",
  "solicitudes",
  "prestamos",
  "reservas",
  "remitos",
];
function RequireSession() {
  const { usuario, authLoading, authError, comprobarSesion } = useLibrary();
  const location = useLocation();
  if (authLoading)
    return (
      <p role="status" className="p-10">
        Verificando sesión…
      </p>
    );
  if (authError)
    return (
      <div className="p-10">
        <Alert error>{authError}</Alert>
        <Button onClick={() => void comprobarSesion()}>
          Reintentar conexión
        </Button>
      </div>
    );
  return usuario ? (
    <Outlet />
  ) : (
    <Navigate
      to="/acceso"
      replace
      state={{ from: location.pathname + location.search }}
    />
  );
}
export function App() {
  return (
    <LibraryProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/acceso" replace />} />
          <Route path="/acceso" element={<Access />} />
          <Route element={<RequireSession />}>
            <Route element={<Layout />}>
              <Route path="inicio" element={<Home />} />
              <Route path="apariencia" element={<Appearance />} />
              <Route path="guia" element={<Guide />} />
              <Route path="prestamos/devolucion" element={<Returns />} />
              {resources.map((r) => (
                <Route key={r} path={pathOf(r)}>
                  <Route index element={<EntityList key={r} resource={r} />} />
                  {r !== "prestamos" && (
                    <Route
                      path="nuevo"
                      element={<EntityForm key={`${r}-new`} resource={r} />}
                    />
                  )}
                  <Route
                    path=":id"
                    element={<EntityDetail key={`${r}-detail`} resource={r} />}
                  />
                  {["libros", "socios", "sedes", "ejemplares"].includes(r) && (
                    <Route
                      path=":id/editar"
                      element={<EntityForm key={`${r}-edit`} resource={r} />}
                    />
                  )}
                </Route>
              ))}
              <Route path="reportes" element={<ReportCenter />} />
              <Route path="reportes/:type" element={<ReportPage />} />
              <Route path="sin-acceso" element={<NotFound forbidden />} />
              <Route path="*" element={<NotFound />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </LibraryProvider>
  );
}
