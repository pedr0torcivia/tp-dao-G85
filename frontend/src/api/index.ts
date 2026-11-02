import { createMockApi } from "./mock";
import { httpApi } from "./http";

export const isDemo = import.meta.env.VITE_DATA_SOURCE === "mock";
export const api = isDemo ? createMockApi() : httpApi;
