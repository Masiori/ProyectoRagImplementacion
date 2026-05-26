import { useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Loader2,
  Trash2,
  XCircle,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { DocumentResponse, DocumentStatus } from "@/types/api";

interface Props {
  document: DocumentResponse;
  onDelete: (id: string) => Promise<void>;
}

export function DocumentCard({ document, onDelete }: Props) {
  const [open, setOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await onDelete(document.id);
      setOpen(false);
    } catch {
      // error ya mostrado por el hook
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <div className="flex items-center gap-4 rounded-lg border bg-card p-4 shadow-sm transition-colors hover:bg-accent/30">
        {/* Icono */}
        <FileText className="h-8 w-8 shrink-0 text-muted-foreground" />

        {/* Info principal */}
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <span className="truncate font-medium" title={document.filename}>
            {document.filename}
          </span>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>{formatBytes(document.size_bytes)}</span>
            <span>·</span>
            <span>{formatRelative(document.created_at)}</span>
            {document.status === "ready" && (
              <>
                <span>·</span>
                <span>{document.chunks_count} fragmentos</span>
              </>
            )}
          </div>

          {/* Mensaje de error si falló */}
          {document.status === "failed" && document.error_message && (
            <span
              className="mt-1 text-xs text-destructive"
              title={document.error_message}
            >
              {document.error_message}
            </span>
          )}
        </div>

        {/* Status */}
        <StatusBadge status={document.status} />

        {/* Borrar */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setOpen(true)}
          aria-label="Eliminar documento"
        >
          <Trash2 className="h-4 w-4 text-destructive" />
        </Button>
      </div>

      {/* Dialog de confirmación */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>¿Eliminar documento?</DialogTitle>
            <DialogDescription>
              Se borrará <strong>{document.filename}</strong> y todos sus
              fragmentos vectoriales. Esta acción no se puede deshacer.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={isDeleting}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={isDeleting}
            >
              {isDeleting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Eliminando...
                </>
              ) : (
                <>
                  <Trash2 className="h-4 w-4" />
                  Eliminar
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// ============================================================
// Helpers visuales
// ============================================================

function StatusBadge({ status }: { status: DocumentStatus }) {
  switch (status) {
    case "ready":
      return (
        <Badge variant="success">
          <CheckCircle2 className="mr-1 h-3 w-3" />
          Listo
        </Badge>
      );
    case "processing":
      return (
        <Badge variant="info">
          <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          Procesando
        </Badge>
      );
    case "pending":
      return (
        <Badge variant="warning">
          <AlertCircle className="mr-1 h-3 w-3" />
          Pendiente
        </Badge>
      );
    case "failed":
      return (
        <Badge variant="destructive">
          <XCircle className="mr-1 h-3 w-3" />
          Falló
        </Badge>
      );
  }
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function formatRelative(isoDate: string): string {
  const now = Date.now();
  const then = new Date(isoDate).getTime();
  const diffSec = Math.floor((now - then) / 1000);

  if (diffSec < 60) return "hace un momento";
  if (diffSec < 3600) return `hace ${Math.floor(diffSec / 60)} min`;
  if (diffSec < 86400) return `hace ${Math.floor(diffSec / 3600)} h`;
  if (diffSec < 86400 * 7) return `hace ${Math.floor(diffSec / 86400)} días`;
  return new Date(isoDate).toLocaleDateString("es-CO");
}
