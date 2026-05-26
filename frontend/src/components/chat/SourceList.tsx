import { useState } from "react";
import { FileText } from "lucide-react";

import { SourceDialog } from "@/components/chat/SourceDialog";
import type { Source } from "@/types/api";

interface Props {
  sources: Source[];
}

export function SourceList({ sources }: Props) {
  const [activeSource, setActiveSource] = useState<Source | null>(null);

  if (sources.length === 0) return null;

  return (
    <>
      <div className="mt-3 flex flex-wrap items-center gap-1.5">
        <span className="text-xs font-medium text-muted-foreground">Fuentes:</span>
        {sources.map((source) => (
          <button
            key={source.chunk_id}
            onClick={() => setActiveSource(source)}
            className="inline-flex items-center gap-1.5 rounded-md border bg-background px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            title={`Ver fragmento de ${source.filename}`}
          >
            <FileText className="h-3 w-3" />
            <span className="max-w-[160px] truncate">{source.filename}</span>
            <span className="text-muted-foreground/70">
              {(source.similarity * 100).toFixed(0)}%
            </span>
          </button>
        ))}
      </div>

      <SourceDialog
        source={activeSource}
        open={activeSource !== null}
        onClose={() => setActiveSource(null)}
      />
    </>
  );
}
