import { request } from "./http";
import { isDemo } from ".";

export interface Usuario {
  id: number;
  username: string;
  nombre: string;
}
interface Sesion {
  usuario: Usuario | null;
  csrfToken: string;
}
const demo: Usuario = {
  id: 0,
  username: "biblioteca",
  nombre: "Personal de biblioteca",
};

export async function consultarSesion(): Promise<Usuario | null> {
  if (isDemo) return sessionStorage.getItem("entrelibros:sesion") ? demo : null;
  return (await request<Sesion>("auth/sesion/")).usuario;
}

export async function ingresar(
  username: string,
  password: string,
): Promise<Usuario> {
  if (isDemo) {
    if (username !== "biblioteca" || password !== "demo")
      throw new Error("Usuario o contraseña incorrectos.");
    sessionStorage.setItem("entrelibros:sesion", "1");
    return demo;
  }
  // Obtener también un token nuevo si el formulario estuvo abierto mucho tiempo.
  await consultarSesion();
  const sesion = await request<Sesion>("auth/ingresar/", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  if (!sesion.usuario) throw new Error("No pudimos iniciar la sesión.");
  return sesion.usuario;
}

export async function salir(): Promise<void> {
  if (isDemo) sessionStorage.removeItem("entrelibros:sesion");
  else await request<Sesion>("auth/salir/", { method: "POST" });
}
