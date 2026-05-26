import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import {
  deleteDocument,
  listDocuments,
  uploadDocument,
} from "@/services/documents";
import type { DocumentResponse } from "@/types/api";

const POLL_INTERVAL_MS = 2000;

/**
 * Hook que gestiona la lista de documentos del usuario.
 *
 * Comportamiento:
 *   - Fetch inicial al montar.
 *   - Polling cada 2s SOLO si hay documentos en estado `pending`/`processing`.
 *   - El polling se detiene automáticamente cuando todos terminan.
 *   - Al desmontar, limpia el interval.
 *
 * Expone:
 *   - documents:  lista actual
 *   - isLoading:  true durante el primer fetch
 *   - upload(file): sube y refresca
 *   - remove(id): borra y refresca
 */
export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // `isMountedRef` evita setear estado tras desmontar (warning de React)
  const isMountedRef = useRef(true);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ----------------------------------------------------------
  // Fetch silencioso (no toca isLoading)
  // ----------------------------------------------------------
  const fetchDocuments = useCallback(async (): Promise<DocumentResponse[] | null> => {
    try {
      const docs = await listDocuments();
      if (isMountedRef.current) {
        setDocuments(docs);
      }
      return docs;
    } catch (err) {
      // Errores de polling se loggean pero no se muestran como toast
      // (evita spam si la red falla momentáneamente)
      console.error("[useDocuments] Error fetching:", err);
      return null;
    }
  }, []);

  // ----------------------------------------------------------
  // Polling: arranca si hay docs en progreso; se detiene si no
  // ----------------------------------------------------------
  useEffect(() => {
    const hasInProgress = documents.some(
      (d) => d.status === "pending" || d.status === "processing",
    );

    if (!hasInProgress) {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      return;
    }

    if (pollIntervalRef.current) return; // ya hay un poll activo

    pollIntervalRef.current = setInterval(() => {
      fetchDocuments();
    }, POLL_INTERVAL_MS);

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [documents, fetchDocuments]);

  // ----------------------------------------------------------
  // Fetch inicial + cleanup
  // ----------------------------------------------------------
  useEffect(() => {
    isMountedRef.current = true;

    fetchDocuments().finally(() => {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    });

    return () => {
      isMountedRef.current = false;
    };
  }, [fetchDocuments]);

  // ----------------------------------------------------------
  // upload
  // ----------------------------------------------------------
  const upload = useCallback(
    async (file: File): Promise<void> => {
      try {
        await uploadDocument(file);
        await fetchDocuments();
        toast.success(`"${file.name}" subido. Procesando...`);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Error desconocido";
        toast.error(message);
        throw err;
      }
    },
    [fetchDocuments],
  );

  // ----------------------------------------------------------
  // remove
  // ----------------------------------------------------------
  const remove = useCallback(async (id: string): Promise<void> => {
    try {
      await deleteDocument(id);
      // Optimistic: quitar de la lista local sin esperar fetch
      setDocuments((prev) => prev.filter((d) => d.id !== id));
      toast.success("Documento eliminado");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Error desconocido";
      toast.error(message);
      throw err;
    }
  }, []);

  return {
    documents,
    isLoading,
    upload,
    remove,
  };
}
