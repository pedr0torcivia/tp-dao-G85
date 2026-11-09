import { request } from "./http";

export interface Usuario {
  id: number;
  username: string;
  nombre: string;
}
interface Sesion {
  usuario: Usuario | null;
  csrfToken: string;
}
export async function consultarSesion(): Promise<Usuario | null> {
  return (await request<Sesion>("auth/sesion/")).usuario;
}

export async function ingresar(
  username: string,
  password: string,
): Promise<Usuario> {
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
  await request<Sesion>("auth/salir/", { method: "POST" });
}
