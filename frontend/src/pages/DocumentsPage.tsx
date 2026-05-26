import { DocumentList } from "@/components/documents/DocumentList";
import { DocumentUploader } from "@/components/documents/DocumentUploader";
import { useDocuments } from "@/hooks/useDocuments";

/**
 * Página de gestión de documentos.
 *
 * Estructura:
 *   - Header de página
 *   - Uploader (drag & drop)
 *   - Lista de documentos con polling automático
 */
export function DocumentsPage() {
  const { documents, isLoading, upload, remove } = useDocuments();

  return (
    <div className="container max-w-3xl py-8">
      {/* Header */}
      <header className="mb-6">
        <h1 className="text-2xl font-semibold">Documentos</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Sube archivos para alimentar la base de conocimiento del agente. El
          procesamiento (extracción y embeddings) ocurre en segundo plano y
          puede tardar entre 10 y 30 segundos.
        </p>
      </header>

      {/* Uploader */}
      <section className="mb-6">
        <DocumentUploader onUpload={upload} />
      </section>

      {/* Lista */}
      <section>
        <DocumentList
          documents={documents}
          isLoading={isLoading}
          onDelete={remove}
        />
      </section>
    </div>
  );
}
