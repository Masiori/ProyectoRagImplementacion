/**
 * Cliente HTTP del backend.
 *
 * - Inyecta `Authorization: Bearer <jwt>` automáticamente en cada request.
 * - Si una response es 401:
 *     1. Limpia el JWT local
 *     2. Muestra un toast
 *     3. Redirige a /login (fuera del flujo React, vía window.location)
 *
 * El interceptor de 401 NO se dispara durante:
 *   - El intercambio inicial code→token (eso va directo con fetch, no por aquí)
 *   - Llamadas al propio `/login` o `/callback`
 */

import axios, { AxiosError } from "axios";
import { toast } from "sonner";

import { clearToken, getToken } from "@/services/auth";

const BASE_URL = import.meta.env.VITE_API_URL;

export const api = axios.create({
  baseURL: BASE_URL,
  // Sin withCredentials: la auth va por header, no por cookies
});

// ============================================================
// Request interceptor: inyectar JWT
// ============================================================
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ============================================================
// Response interceptor: manejo de 401
// ============================================================

/**
 * Bandera para evitar múltiples redirects simultáneos si varias requests
 * fallan con 401 al mismo tiempo.
 */
let isRedirectingTo401 = false;

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && !isRedirectingTo401) {
      isRedirectingTo401 = true;
      clearToken();
      toast.error("Tu sesión expiró. Por favor inicia sesión de nuevo.");

      // Redirección fuera del router (estamos fuera del árbol React aquí)
      setTimeout(() => {
        window.location.href = "/login";
      }, 800);
    }
    return Promise.reject(error);
  },
);
