import {
  createContext,
  useCallback,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { toast } from "sonner";

import { api } from "@/services/api";
import {
  buildLoginUrl,
  buildLogoutUrl,
  clearToken,
  consumePostLoginRedirect,
  exchangeCodeForToken,
  getToken,
  setToken,
} from "@/services/auth";
import type { UserResponse } from "@/types/api";

// ============================================================
// Tipos del contexto
// ============================================================
interface AuthContextValue {
  user: UserResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (postLoginRedirect?: string) => Promise<void>;
  logout: () => void;
  /** Procesa el ?code=&state= del callback. Devuelve la ruta destino. */
  handleCallback: (code: string, state: string) => Promise<string>;
}

export const AuthContext = createContext<AuthContextValue | undefined>(
  undefined,
);

// ============================================================
// Provider
// ============================================================
interface ProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: ProviderProps) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Al montar: si hay JWT en sessionStorage, validar contra /me.
   * Si responde 200 → autenticado.
   * Si responde 401 → token expirado/inválido → limpiar y seguir sin sesión.
   */
  useEffect(() => {
    const token = getToken();
    if (!token) {
      setIsLoading(false);
      return;
    }

    api
      .get<UserResponse>("/me")
      .then((response) => {
        setUser(response.data);
      })
      .catch(() => {
        // El interceptor de api.ts ya limpia el token y redirige en 401.
        // Aquí solo nos aseguramos de no quedar con el spinner.
        clearToken();
        setUser(null);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  // ----------------------------------------------------------
  // login: redirige al Hosted UI de Cognito
  // ----------------------------------------------------------
  const login = useCallback(async (postLoginRedirect: string = "/chat") => {
    try {
      const url = await buildLoginUrl(postLoginRedirect);
      window.location.href = url;
    } catch (err) {
      toast.error(`No se pudo iniciar el login: ${String(err)}`);
    }
  }, []);

  // ----------------------------------------------------------
  // logout: limpiar local + redirigir al logout de Cognito
  // ----------------------------------------------------------
  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    window.location.href = buildLogoutUrl();
  }, []);

  // ----------------------------------------------------------
  // handleCallback: code → token → user
  // ----------------------------------------------------------
  const handleCallback = useCallback(
    async (code: string, state: string): Promise<string> => {
      const idToken = await exchangeCodeForToken(code, state);
      setToken(idToken);

      // Verificar contra el backend y poblar el user
      const response = await api.get<UserResponse>("/me");
      setUser(response.data);

      return consumePostLoginRedirect();
    },
    [],
  );

  const value: AuthContextValue = {
    user,
    isLoading,
    isAuthenticated: user !== null,
    login,
    logout,
    handleCallback,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
