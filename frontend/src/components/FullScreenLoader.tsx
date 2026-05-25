import { Loader2 } from "lucide-react";

interface Props {
  message?: string;
}

/** Loader centrado que ocupa toda la pantalla (o el contenedor padre). */
export function FullScreenLoader({ message }: Props) {
  return (
    <div className="flex min-h-screen flex-1 flex-col items-center justify-center gap-3">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
      {message && (
        <p className="text-sm text-muted-foreground">{message}</p>
      )}
    </div>
  );
}
