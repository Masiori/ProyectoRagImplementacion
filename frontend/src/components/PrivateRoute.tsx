import { Navigate, Outlet, useLocation } from "react-router-dom";

import { FullScreenLoader } from "@/components/FullScreenLoader";
import { useAuth } from "@/hooks/useAuth";

/**
 * Componente padre que protege un grupo de rutas.
 *
 * - Si está cargando el estado de auth → spinner.
 * - Si no hay sesión → redirige a /login (guardando la URL original
 *   en `state.from` para volver allí post-login).
 * - Si hay sesión → renderiza las rutas hijas vía <Outlet />.
 */
export function PrivateRoute() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <FullScreenLoader message="Verificando sesión..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
}
