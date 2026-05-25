import { Outlet } from "react-router-dom";

import { Header } from "@/components/layout/Header";

/**
 * Layout principal de la aplicación.
 * Renderiza el Header fijo arriba y el contenido de cada página debajo.
 */
export function AppLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex flex-1 flex-col">
        <Outlet />
      </main>
    </div>
  );
}
