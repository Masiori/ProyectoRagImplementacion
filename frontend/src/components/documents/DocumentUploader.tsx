import { useRef, useState } from "react";
import { Loader2, Upload } from "lucide-react";
import { toast } from "sonner";

import { cn } from "@/lib/utils";

const ALLOWED_MIME_TYPES = [
  "application/pdf",
  "text/plain",
  "text/markdown",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];

const ALLOWED_EXTENSIONS = ".pdf,.txt,.md,.docx";
const MAX_SIZE_BYTES = 20 * 1024 * 1024; // 20 MB — debe coincidir con backend
const MAX_SIZE_LABEL = "20 MB";

interface Props {
  onUpload: (file: File) => Promise<void>;
  disabled?: boolean;
}

export function DocumentUploader({ onUpload, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const handleFile = async (file: File) => {
    // --- Validación cliente ---
    if (!ALLOWED_MIME_TYPES.includes(file.type)) {
      toast.error(
        `Tipo de archivo no permitido. Acepta: PDF, TXT, MD, DOCX.`,
      );
      return;
    }
    if (file.size > MAX_SIZE_BYTES) {
      toast.error(`El archivo supera el tamaño máximo (${MAX_SIZE_LABEL}).`);
      return;
    }

    // --- Subir ---
    setIsUploading(true);
    try {
      await onUpload(file);
    } catch {
      // toast ya mostrado por el hook
    } finally {
      setIsUploading(false);
      // Limpiar input para permitir re-subir el mismo archivo
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  };

  const handleClick = () => {
    if (!disabled && !isUploading) {
      inputRef.current?.click();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled && !isUploading) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled || isUploading) return;

    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div
      onClick={handleClick}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") handleClick();
      }}
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed bg-muted/30 px-6 py-12 text-center transition-colors",
        isDragging && "border-primary bg-primary/5",
        (disabled || isUploading) && "cursor-not-allowed opacity-50",
        !disabled && !isUploading && "cursor-pointer hover:bg-muted/50",
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ALLOWED_EXTENSIONS}
        className="hidden"
        onChange={handleInputChange}
        disabled={disabled || isUploading}
      />

      {isUploading ? (
        <>
          <Loader2 className="h-10 w-10 animate-spin text-primary" />
          <p className="font-medium">Subiendo archivo...</p>
        </>
      ) : (
        <>
          <Upload className="h-10 w-10 text-muted-foreground" />
          <div>
            <p className="font-medium">
              Arrastra un archivo o haz clic para seleccionar
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              PDF, TXT, MD o DOCX · máx {MAX_SIZE_LABEL}
            </p>
          </div>
        </>
      )}
    </div>
  );
}
