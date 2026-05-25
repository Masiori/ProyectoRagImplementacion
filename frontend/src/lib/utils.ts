import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combina clases Tailwind condicionalmente y resuelve conflictos.
 * Requerida por los componentes de shadcn/ui.
 *
 * Ejemplo:
 *   cn("px-2 py-1", isActive && "bg-blue-500", "px-4")
 *   → "py-1 bg-blue-500 px-4"  (px-4 gana sobre px-2)
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
