import { FileText } from "lucide-react";

/**
 * Página de documentos.
 * En M6.3 implementaremos:
 *   - Upload por drag&drop o file input
 *   - Lista de documentos con estado (pending/processing/ready/failed)
 *   - Polling de estado cada 2s
 *   - Botón de borrar
 */
export function DocumentsPage() {
  return (
    <div className="container flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
      <FileText className="h-12 w-12 text-muted-foreground" />
      <h1 className="text-2xl font-semibold">Documentos</h1>
      <p className="max-w-md text-sm text-muted-foreground">
        Aquí podrás subir y gestionar los documentos que alimentan la base de
        conocimiento del agente. Se implementa en la fase M6.3.
      </p>
    </div>
  );
}
