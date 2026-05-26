import { FileText } from "lucide-react";

import { DocumentCard } from "@/components/documents/DocumentCard";
import { Skeleton } from "@/components/ui/skeleton";
import type { DocumentResponse } from "@/types/api";

interface Props {
  documents: DocumentResponse[];
  isLoading: boolean;
  onDelete: (id: string) => Promise<void>;
}

export function DocumentList({ documents, isLoading, onDelete }: Props) {
  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-20 w-full" />
        ))}
      </div>
    );
  }

  if (documents.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="flex flex-col gap-3">
      {documents.map((doc) => (
        <DocumentCard key={doc.id} document={doc} onDelete={onDelete} />
      ))}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed bg-muted/30 px-6 py-12 text-center">
      <FileText className="h-10 w-10 text-muted-foreground" />
      <h3 className="font-medium">Aún no tienes documentos</h3>
      <p className="max-w-sm text-sm text-muted-foreground">
        Sube tu primer archivo PDF, TXT, MD o DOCX para comenzar a alimentar
        la base de conocimiento del agente.
      </p>
    </div>
  );
}
