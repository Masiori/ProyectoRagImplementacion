/**
 * Cliente para los endpoints de chat del backend.
 *
 * Endpoints:
 *   POST   /api/chat                                  → enviar pregunta
 *   GET    /api/chat/conversations                    → listar conversaciones
 *   GET    /api/chat/conversations/{id}               → conversación + mensajes
 *   DELETE /api/chat/conversations/{id}               → borrar conversación
 *   GET    /api/documents/chunks/{id}                 → contenido del chunk (preview de sources)
 *
 * Todos requieren JWT (lo inyecta el interceptor de api.ts).
 */

import { AxiosError } from "axios";

import { api } from "@/services/api";
import type {
  ChatRequest,
  ChatResponse,
  ChunkResponse,
  ConversationDetailResponse,
  ConversationResponse,
} from "@/types/api";

/** Timeout extendido para chat porque Llama en CPU puede tardar hasta ~60-90s. */
const CHAT_TIMEOUT_MS = 90_000;

// ============================================================
// Chat
// ============================================================

/** Envía una pregunta al agente. Si conversation_id es null, crea una nueva. */
export async function sendMessage(
  request: ChatRequest,
): Promise<ChatResponse> {
  try {
    const response = await api.post<ChatResponse>("/api/chat", request, {
      timeout: CHAT_TIMEOUT_MS,
    });
    return response.data;
  } catch (err) {
    throw normalizeChatError(err);
  }
}

// ============================================================
// Conversaciones
// ============================================================

export async function listConversations(): Promise<ConversationResponse[]> {
  const response = await api.get<ConversationResponse[]>(
    "/api/chat/conversations",
  );
  return response.data;
}

export async function getConversation(
  id: string,
): Promise<ConversationDetailResponse> {
  const response = await api.get<ConversationDetailResponse>(
    `/api/chat/conversations/${id}`,
  );
  return response.data;
}

export async function deleteConversation(id: string): Promise<void> {
  try {
    await api.delete(`/api/chat/conversations/${id}`);
  } catch (err) {
    throw normalizeGenericError(err, "Error al eliminar la conversación");
  }
}

// ============================================================
// Chunks (preview de fuentes)
// ============================================================

export async function getChunk(id: string): Promise<ChunkResponse> {
  const response = await api.get<ChunkResponse>(
    `/api/documents/chunks/${id}`,
  );
  return response.data;
}

// ============================================================
// Manejo específico de errores del chat
// ============================================================

function normalizeChatError(err: unknown): Error {
  if (err instanceof AxiosError) {
    // Timeout (Llama colgada o muy lenta)
    if (err.code === "ECONNABORTED") {
      return new Error(
        "El agente tardó demasiado en responder. Intenta de nuevo o reformula la pregunta.",
      );
    }

    // Sin respuesta del backend (caído o red)
    if (!err.response) {
      return new Error("Sin conexión con el servidor. Revisa tu red.");
    }

    const status = err.response.status;
    const detail = err.response.data?.detail;

    // 503: servicios caídos (Ollama, embeddings)
    if (status === 503) {
      return new Error(
        "El servicio de IA no está disponible en este momento. Intenta más tarde.",
      );
    }

    // 422: validación (pregunta muy larga, etc.)
    if (status === 422 && typeof detail !== "undefined") {
      return new Error(
        typeof detail === "string" ? detail : "Pregunta inválida.",
      );
    }

    // 4xx con detail
    if (typeof detail === "string") {
      return new Error(detail);
    }

    return new Error(`Error del servidor (HTTP ${status}).`);
  }

  return new Error("Error inesperado al enviar la pregunta.");
}

function normalizeGenericError(err: unknown, fallback: string): Error {
  if (err instanceof AxiosError) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return new Error(detail);
    if (err.response?.status) {
      return new Error(`${fallback} (HTTP ${err.response.status})`);
    }
  }
  return new Error(fallback);
}
