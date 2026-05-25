import { useContext } from "react";

import { AuthContext } from "@/context/AuthContext";

/**
 * Hook para acceder al contexto de autenticación.
 *
 * Lanza error si se usa fuera del <AuthProvider>; esto ayuda a detectar
 * errores en tiempo de desarrollo (mejor que un null silencioso).
 */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (ctx === undefined) {
    throw new Error("useAuth debe usarse dentro de un <AuthProvider>");
  }
  return ctx;
}
