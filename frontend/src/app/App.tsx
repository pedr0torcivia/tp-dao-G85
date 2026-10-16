import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { LibraryProvider } from "./context";
import { Layout } from "./Layout";
import { EntityList } from "../pages/Lists";
import { EntityDetail } from "../pages/Details";
import { EntityForm } from "../pages/EntityForm";
import { Access, Appearance, Home, NotFound, Returns } from "../pages/Other";
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
export function App() {
  return (
    <LibraryProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/acceso" replace />} />
          <Route path="/acceso" element={<Access />} />
          <Route element={<Layout />}>
            <Route path="inicio" element={<Home />} />
            <Route path="apariencia" element={<Appearance />} />
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
        </Routes>
      </BrowserRouter>
    </LibraryProvider>
  );
}
