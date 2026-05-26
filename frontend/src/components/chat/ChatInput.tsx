import { useEffect, useRef } from "react";
import { Send } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

const MAX_LENGTH = 800; // debe coincidir con MAX_QUESTION_LENGTH del backend
const MAX_HEIGHT_PX = 200; // altura máxima antes de scrollear internamente

interface Props {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (question: string) => void | Promise<void>;
  disabled?: boolean;
}

export function ChatInput({ value, onChange, onSubmit, disabled }: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize del textarea según el contenido
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT_PX)}px`;
  }, [value]);

  const isOverLimit = value.length > MAX_LENGTH;
  const canSubmit = value.trim().length > 0 && !isOverLimit && !disabled;

  const handleSubmit = () => {
    if (!canSubmit) return;
    onSubmit(value.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter envía; Shift+Enter inserta salto de línea
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t bg-background p-4">
      <div className="mx-auto flex max-w-3xl flex-col gap-2">
        <div className="flex items-end gap-2">
          <Textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Escribe tu pregunta sobre gastronomía colombiana..."
            disabled={disabled}
            rows={1}
            className="resize-none"
          />
          <Button
            onClick={handleSubmit}
            disabled={!canSubmit}
            size="icon"
            aria-label="Enviar pregunta"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>

        {/* Contador + ayuda */}
        <div className="flex items-center justify-between px-1 text-xs text-muted-foreground">
          <span>
            Pulsa <kbd className="rounded bg-muted px-1 py-0.5">Enter</kbd> para
            enviar · <kbd className="rounded bg-muted px-1 py-0.5">Shift+Enter</kbd> nueva línea
          </span>
          <span className={cn(isOverLimit && "font-semibold text-destructive")}>
            {value.length} / {MAX_LENGTH}
          </span>
        </div>
      </div>
    </div>
  );
}
