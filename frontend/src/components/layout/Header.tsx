import { Link, NavLink } from "react-router-dom";
import { ChefHat, FileText, LogIn, LogOut, MessageSquare } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";

export function Header() {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        {/* Logo */}
        <Link to="/" className="mr-6 flex items-center gap-2 font-semibold">
          <ChefHat className="h-5 w-5 text-primary" />
          <span>Agente Gastronomía</span>
        </Link>

        {/* Navegación — solo si hay sesión */}
        {isAuthenticated && (
          <nav className="flex items-center gap-1 text-sm">
            <NavLinkItem to="/chat" icon={<MessageSquare className="h-4 w-4" />}>
              Chat
            </NavLinkItem>
            <NavLinkItem
              to="/documents"
              icon={<FileText className="h-4 w-4" />}
            >
              Documentos
            </NavLinkItem>
          </nav>
        )}

        {/* User info / login */}
        <div className="ml-auto flex items-center gap-3 text-sm">
          {isAuthenticated && user ? (
            <>
              <span className="hidden text-muted-foreground sm:inline">
                {user.email}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={logout}
                aria-label="Cerrar sesión"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Cerrar sesión</span>
              </Button>
            </>
          ) : (
            <Button variant="ghost" size="sm" asChild>
              <Link to="/login">
                <LogIn className="h-4 w-4" />
                Iniciar sesión
              </Link>
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}

function NavLinkItem({
  to,
  icon,
  children,
}: {
  to: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-2 rounded-md px-3 py-2 transition-colors",
          isActive
            ? "bg-accent text-accent-foreground"
            : "text-muted-foreground hover:text-foreground hover:bg-accent/50",
        )
      }
    >
      {icon}
      {children}
    </NavLink>
  );
}
