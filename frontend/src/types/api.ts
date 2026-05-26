/**
 * Tipos TypeScript que reflejan las response schemas del backend (Pydantic).
 *
 * Mantener sincronizado con `backend/schemas/`.
 */

// ============================================================
// Auth / Usuarios
// ============================================================
export interface UserResponse {
  id: string;
  email: string;
  auth_provider: "cognito" | "google" | string;
  created_at: string;
  updated_at: string;
}

// ============================================================
// Cognito OAuth
// ============================================================
export interface CognitoTokenResponse {
  id_token: string;
  access_token: string;
  refresh_token?: string;
  expires_in: number;
  token_type: string;
}

// ============================================================
// Documentos (M6.3)
// ============================================================
export type DocumentStatus = "pending" | "processing" | "ready" | "failed";

export interface DocumentResponse {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  status: DocumentStatus;
  error_message: string | null;
  chunks_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentDetailResponse extends DocumentResponse {
  s3_key: string;
  user_id: string;
}

// ============================================================
// Chunks (para preview de fuentes en el chat — M6.4)
// ============================================================
export interface ChunkResponse {
  id: string;
  document_id: string;
  content: string;
  chunk_index: number;
  chunk_metadata: Record<string, unknown> | null;
}

// ============================================================
// Chat (M6.4)
// ============================================================
export interface Source {
  chunk_id: string;
  document_id: string;
  filename: string;
  similarity: number;
}

export interface ChatRequest {
  question: string;
  conversation_id?: string | null;
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  answer: string;
  sources: Source[];
  rejected: boolean;
  rejection_reason: string | null;
}

export interface ConversationResponse {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface MessageResponse {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  sources: Source[] | null;
  created_at: string;
}

export interface ConversationDetailResponse extends ConversationResponse {
  messages: MessageResponse[];
}
