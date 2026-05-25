import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { FullScreenLoader } from "@/components/FullScreenLoader";
import { useAuth } from "@/hooks/useAuth";

/**
 * Página de callback de OAuth.
 *
 * Cognito redirige aquí con uno de estos formatos:
 *   - Éxito:  /callback?code=...&state=...
 *   - Error:  /callback?error=...&error_description=...
 *
 * El flujo:
 *   1. Parsear los query params.
 *   2. Si hay error → toast + /login.
 *   3. Si hay code + state → llamar handleCallback() del AuthContext.
 *   4. Redirigir a la URL original (o a /chat).
 *
 * `processedRef` evita doble ejecución en StrictMode (que monta-desmonta-monta).
 */
export function CallbackPage() {
  const { handleCallback } = useAuth();
  const navigate = useNavigate();
  const processedRef = useRef(false);

  useEffect(() => {
    if (processedRef.current) return;
    processedRef.current = true;

    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const state = params.get("state");
    const error = params.get("error");
    const errorDescription = params.get("error_description");

    // --- Error explícito de Cognito ---
    if (error) {
      const msg = errorDescription || error;
      toast.error(`Error en el login: ${msg}`);
      navigate("/login", { replace: true });
      return;
    }

    // --- Faltan params: callback inválido ---
    if (!code || !state) {
      toast.error("Callback inválido (faltan parámetros).");
      navigate("/login", { replace: true });
      return;
    }

    // --- Intercambio code → token ---
    handleCallback(code, state)
      .then((redirectTo) => {
        navigate(redirectTo, { replace: true });
      })
      .catch((err: Error) => {
        toast.error(`Error en autenticación: ${err.message}`);
        navigate("/login", { replace: true });
      });
  }, [handleCallback, navigate]);

  return <FullScreenLoader message="Procesando inicio de sesión..." />;
}
