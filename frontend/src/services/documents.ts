/**
 * Cliente para los endpoints de documentos del backend.
 *
 * Endpoints del backend:
 *   POST   /api/documents          → subir archivo (multipart/form-data)
 *   GET    /api/documents          → listar documentos del usuario
 *   GET    /api/documents/{id}     → detalle de un documento
 *   DELETE /api/documents/{id}     → borrar (chunks + S3)
 *
 * Todos requieren JWT (lo inyecta el interceptor de api.ts).
 */

import { AxiosError } from "axios";

import { api } from "@/services/api";
import type {
  DocumentDetailResponse,
  DocumentResponse,
} from "@/types/api";

/**
 * Sube un archivo al backend.
 * El procesamiento (extracción + chunking + embeddings) ocurre en background;
 * el endpoint devuelve inmediatamente con status="pending".
 */
export async function uploadDocument(file: File): Promise<DocumentResponse> {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await api.post<DocumentResponse>(
      "/api/documents",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      },
    );
    return response.data;
  } catch (err) {
    throw normalizeApiError(err, "Error al subir el documento");
  }
}

/** Lista los documentos del usuario autenticado, más recientes primero. */
export async function listDocuments(): Promise<DocumentResponse[]> {
  const response = await api.get<DocumentResponse[]>("/api/documents");
  return response.data;
}

/** Obtiene el detalle de un documento (incluye s3_key, user_id). */
export async function getDocument(id: string): Promise<DocumentDetailResponse> {
  const response = await api.get<DocumentDetailResponse>(`/api/documents/${id}`);
  return response.data;
}

/** Borra un documento (sus chunks por CASCADE, su archivo en S3). */
export async function deleteDocument(id: string): Promise<void> {
  try {
    await api.delete(`/api/documents/${id}`);
  } catch (err) {
    throw normalizeApiError(err, "Error al eliminar el documento");
  }
}

// ============================================================
// Helpers
// ============================================================

/**
 * Convierte un error de axios en un Error con mensaje legible para mostrar.
 * Prefiere el `detail` de FastAPI si está disponible.
 */
function normalizeApiError(err: unknown, fallback: string): Error {
  if (err instanceof AxiosError) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") {
      return new Error(detail);
    }
    if (err.response?.status) {
      return new Error(`${fallback} (HTTP ${err.response.status})`);
    }
  }
  return new Error(fallback);
}
