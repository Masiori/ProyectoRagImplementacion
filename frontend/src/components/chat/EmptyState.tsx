import { ChefHat } from "lucide-react";

const SUGGESTIONS = [
  "¿Qué es la bandeja paisa?",
  "¿Cómo se prepara el ajiaco santafereño?",
  "¿Qué ingredientes lleva el sancocho?",
  "Cuéntame sobre la gastronomía del Pacífico",
];

interface Props {
  onSuggestionClick: (question: string) => void;
}

export function EmptyState({ onSuggestionClick }: Props) {
  return (
    <div className="flex flex-1 items-center justify-center px-4 py-8">
      <div className="flex max-w-lg flex-col items-center gap-6 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
          <ChefHat className="h-8 w-8 text-primary" />
        </div>

        <div>
          <h2 className="text-2xl font-semibold">
            ¿Sobre qué quieres preguntar?
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Pregúntame sobre recetas tradicionales, ingredientes, regiones
            gastronómicas o historia culinaria de Colombia. Mis respuestas se
            basan únicamente en los documentos que has cargado.
          </p>
        </div>

        <div className="flex w-full flex-col gap-2">
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Sugerencias
          </span>
          <div className="flex flex-wrap justify-center gap-2">
            {SUGGESTIONS.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => onSuggestionClick(suggestion)}
                className="rounded-full border bg-card px-3 py-1.5 text-sm transition-colors hover:bg-accent hover:text-accent-foreground"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
