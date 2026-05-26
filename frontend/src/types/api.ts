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
