import { useState } from "react";
import { Link } from "react-router-dom";
import { Loader2, MessageSquare, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import type { ConversationResponse } from "@/types/api";

interface Props {
  conversation: ConversationResponse;
  isActive: boolean;
  onDelete: (id: string) => Promise<void>;
}

export function ConversationItem({ conversation, isActive, onDelete }: Props) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDeleting(true);
    try {
      await onDelete(conversation.id);
      setDialogOpen(false);
    } catch {
      // toast ya mostrado
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <Link
        to={`/chat/${conversation.id}`}
        className={cn(
          "group flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
          isActive
            ? "bg-accent text-accent-foreground"
            : "text-muted-foreground hover:bg-accent/50 hover:text-foreground",
        )}
      >
        <MessageSquare className="h-4 w-4 shrink-0" />
        <span className="flex-1 truncate" title={conversation.title || "Sin título"}>
          {conversation.title || "Sin título"}
        </span>

        {/* Botón borrar: visible al hover o si está activa */}
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setDialogOpen(true);
          }}
          className={cn(
            "rounded p-1 text-muted-foreground transition-opacity hover:bg-background hover:text-destructive",
            isActive ? "opacity-100" : "opacity-0 group-hover:opacity-100",
          )}
          aria-label="Eliminar conversación"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </Link>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>¿Eliminar conversación?</DialogTitle>
            <DialogDescription>
              Se borrará <strong>{conversation.title || "esta conversación"}</strong>{" "}
              y todos sus mensajes. Esta acción no se puede deshacer.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDialogOpen(false)}
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
