import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { deleteConversation, listConversations } from "@/services/chat";
import type { ConversationResponse } from "@/types/api";

/**
 * Hook que gestiona la lista de conversaciones del sidebar.
 *
 * Expone:
 *   - conversations:  lista actual
 *   - isLoading:      true durante el primer fetch
 *   - refresh:        re-fetch manual (tras crear una conversación nueva)
 *   - remove:         borra y actualiza la lista
 */
export function useConversations() {
  const [conversations, setConversations] = useState<ConversationResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const isMountedRef = useRef(true);

  const fetchConversations = useCallback(async () => {
    try {
      const data = await listConversations();
      if (isMountedRef.current) {
        setConversations(data);
      }
    } catch (err) {
      console.error("[useConversations] Error fetching:", err);
    }
  }, []);

  useEffect(() => {
    isMountedRef.current = true;
    fetchConversations().finally(() => {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    });
    return () => {
      isMountedRef.current = false;
    };
  }, [fetchConversations]);

  const refresh = useCallback(() => {
    return fetchConversations();
  }, [fetchConversations]);

  const remove = useCallback(async (id: string): Promise<void> => {
    try {
      await deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      toast.success("Conversación eliminada");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Error desconocido";
      toast.error(message);
      throw err;
    }
  }, []);

  return {
    conversations,
    isLoading,
    refresh,
    remove,
  };
}
