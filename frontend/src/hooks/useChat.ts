import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { getConversation, sendMessage as sendMessageApi } from "@/services/chat";
import type { MessageResponse, Source } from "@/types/api";

interface UseChatParams {
  conversationId: string | null | undefined;
  /** Callback cuando el backend crea una conversación nueva (en la primera pregunta). */
  onConversationCreated?: (newId: string) => void;
}

/**
 * Hook que gestiona los mensajes de UNA conversación.
 *
 * Comportamiento:
 *   - Si `conversationId` está definido → carga el histórico desde el backend.
 *   - Si es null/undefined → comienza con lista vacía (conversación nueva).
 *   - `sendMessage`:
 *       1. agrega el mensaje del usuario inmediatamente (optimistic)
 *       2. agrega un mensaje fantasma del agente con `isPending: true`
 *       3. llama al backend (puede tardar 30-60s)
 *       4. reemplaza el fantasma por la respuesta real
 *       5. si era conversación nueva, llama a `onConversationCreated`
 */
export function useChat({ conversationId, onConversationCreated }: UseChatParams) {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isWaitingAgent, setIsWaitingAgent] = useState(false);

  const isMountedRef = useRef(true);

  // ----------------------------------------------------------
  // Cargar histórico cuando cambia el conversationId
  // ----------------------------------------------------------
  useEffect(() => {
    isMountedRef.current = true;

    if (!conversationId) {
      // Conversación nueva: empezar vacía
      setMessages([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    getConversation(conversationId)
      .then((data) => {
        if (isMountedRef.current) {
          setMessages(data.messages.map(fromBackendMessage));
        }
      })
      .catch((err) => {
        console.error("[useChat] Error cargando conversación:", err);
        if (isMountedRef.current) {
          toast.error("No se pudo cargar la conversación.");
          setMessages([]);
        }
      })
      .finally(() => {
        if (isMountedRef.current) {
          setIsLoading(false);
        }
      });

    return () => {
      isMountedRef.current = false;
    };
  }, [conversationId]);

  // ----------------------------------------------------------
  // Enviar pregunta
  // ----------------------------------------------------------
  const sendMessage = useCallback(
    async (question: string): Promise<void> => {
      const trimmed = question.trim();
      if (!trimmed) return;
      if (isWaitingAgent) return;

      // 1. Agregar mensaje del usuario (optimistic) + fantasma del agente
      const userMsg: DisplayMessage = {
        id: `temp-user-${Date.now()}`,
        role: "user",
        content: trimmed,
        sources: null,
        isPending: false,
      };
      const ghostMsg: DisplayMessage = {
        id: `temp-ghost-${Date.now()}`,
        role: "assistant",
        content: "",
        sources: null,
        isPending: true,
      };
      setMessages((prev) => [...prev, userMsg, ghostMsg]);
      setIsWaitingAgent(true);

      try {
        const response = await sendMessageApi({
          question: trimmed,
          conversation_id: conversationId ?? null,
        });

        // 2. Reemplazar el fantasma con la respuesta real
        setMessages((prev) => {
          const newMessages = prev.slice(0, -1); // sin el fantasma
          newMessages.push({
            id: response.message_id,
            role: "assistant",
            content: response.answer,
            sources: response.sources.length > 0 ? response.sources : null,
            isPending: false,
            rejected: response.rejected,
          });
          return newMessages;
        });

        // 3. Si era una conversación nueva, notificar al padre
        if (!conversationId && response.conversation_id) {
          onConversationCreated?.(response.conversation_id);
        }
      } catch (err) {
        // Quitar el fantasma y mantener el mensaje del usuario
        setMessages((prev) => prev.slice(0, -1));

        const message = err instanceof Error ? err.message : "Error desconocido";
        toast.error(message);
      } finally {
        setIsWaitingAgent(false);
      }
    },
    [conversationId, isWaitingAgent, onConversationCreated],
  );

  return {
    messages,
    isLoading,
    isWaitingAgent,
    sendMessage,
  };
}

// ============================================================
// Tipos internos
// ============================================================

/**
 * Mensaje tal como lo necesita la UI.
 * Extiende lo que viene del backend con `isPending` (mensaje fantasma) y
 * `rejected` (si la respuesta fue un rechazo del agente).
 */
export interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: Source[] | null;
  isPending: boolean;
  rejected?: boolean;
}

/**
 * Convierte un MessageResponse del backend a DisplayMessage.
 * Detecta si una respuesta del asistente fue un rechazo comparando con la
 * frase canónica (que el backend devuelve textual).
 */
function fromBackendMessage(m: MessageResponse): DisplayMessage {
  return {
    id: m.id,
    role: m.role,
    content: m.content,
    sources: m.sources ?? null,
    isPending: false,
    rejected: m.role === "assistant" && isRejection(m.content),
  };
}

const CANONICAL_REJECTION =
  "No tengo suficiente información en mi base de conocimiento para responder esa pregunta.";

function isRejection(content: string): boolean {
  return content.trim() === CANONICAL_REJECTION;
}
