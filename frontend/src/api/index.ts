import { httpApi } from "./http";

// La interfaz siempre trabaja contra la API de Django: las reglas de negocio
// viven en un solo lugar (el backend) y el frontend sólo las presenta.
export const api = httpApi;
