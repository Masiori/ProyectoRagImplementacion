import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ChefHat, LogIn } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";

/**
 * Tipo del state que pasa <Navigate> desde PrivateRoute para recordar
 * la ruta original que el usuario intentaba visitar antes del login.
 */
interface LocationState {
  from?: { pathname?: string };
}

export function LoginPage() {
  const { login, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // ¿Veníamos redirigidos desde una ruta protegida? Volvamos allí post-login.
  const from = (location.state as LocationState | null)?.from?.pathname || "/chat";

  // Si ya hay sesión, no tiene sentido mostrar la pantalla de login.
  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  const handleLogin = () => {
    login(from);
  };

  return (
    <div className="flex flex-1 items-center justify-center p-8">
      <div className="flex w-full max-w-sm flex-col items-center gap-6 rounded-xl border bg-card p-8 shadow-sm">
        <ChefHat className="h-12 w-12 text-primary" />
        <div className="text-center">
          <h1 className="text-2xl font-semibold">Agente Gastronomía</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Inicia sesión para chatear con tu base de conocimiento.
          </p>
        </div>

        <Button
          onClick={handleLogin}
          disabled={isLoading}
          className="w-full"
          size="lg"
        >
          <LogIn className="h-4 w-4" />
          Iniciar sesión
        </Button>

        <p className="text-xs text-muted-foreground">
          Serás redirigido a la página segura de Cognito.
        </p>
      </div>
    </div>
  );
}
