import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { getChunk } from "@/services/chat";
import type { ChunkResponse, Source } from "@/types/api";

interface Props {
  source: Source | null;
  open: boolean;
  onClose: () => void;
}

/**
 * Modal que muestra el contenido completo del chunk usado como fuente.
 * Solo hace el fetch cuando el dialog se abre, no antes.
 */
export function SourceDialog({ source, open, onClose }: Props) {
  const [chunk, setChunk] = useState<ChunkResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !source) return;

    setChunk(null);
    setError(null);
    setIsLoading(true);

    getChunk(source.chunk_id)
      .then((data) => setChunk(data))
      .catch((err) => {
        console.error("[SourceDialog] Error:", err);
        setError("No se pudo cargar el contenido de esta fuente.");
      })
      .finally(() => setIsLoading(false));
  }, [open, source]);

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-baseline gap-2">
            <span className="truncate">{source?.filename}</span>
            {source && (
              <span className="text-sm font-normal text-muted-foreground">
                {(source.similarity * 100).toFixed(0)}% similitud
              </span>
            )}
          </DialogTitle>
          <DialogDescription>
            Fragmento exacto que el agente usó para generar su respuesta.
          </DialogDescription>
        </DialogHeader>

        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}

        {error && (
          <div className="rounded-md border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
            {error}
          </div>
        )}

        {chunk && (
          <div className="max-h-[60vh] overflow-y-auto rounded-md bg-muted/50 p-4 font-mono text-sm leading-relaxed whitespace-pre-wrap">
            {chunk.content}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
