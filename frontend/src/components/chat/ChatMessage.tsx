import { AlertTriangle, Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";

import { SourceList } from "@/components/chat/SourceList";
import type { DisplayMessage } from "@/hooks/useChat";
import { cn } from "@/lib/utils";

interface Props {
  message: DisplayMessage;
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex w-full gap-3",
        isUser ? "justify-end" : "justify-start",
      )}
    >
      {/* Avatar izquierda (solo asistente) */}
      {!isUser && (
        <Avatar variant={message.rejected ? "rejected" : "assistant"} />
      )}

      {/* Bubble */}
      <div
        className={cn(
          "flex max-w-[80%] flex-col rounded-lg px-4 py-3 shadow-sm",
          isUser && "bg-primary text-primary-foreground",
          !isUser && !message.rejected && "border bg-card",
          message.rejected && "border-amber-500/30 bg-amber-50",
        )}
      >
        {/* Mensaje fantasma */}
        {message.isPending ? (
          <PendingIndicator />
        ) : (
          <>
            <div
              className={cn(
                "prose prose-sm max-w-none break-words",
                isUser && "prose-invert",
              )}
            >
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>

            {message.sources && message.sources.length > 0 && (
              <SourceList sources={message.sources} />
            )}
          </>
        )}
      </div>

      {/* Avatar derecha (solo usuario) */}
      {isUser && <Avatar variant="user" />}
    </div>
  );
}

// ============================================================
// Sub-componentes
// ============================================================

function Avatar({ variant }: { variant: "user" | "assistant" | "rejected" }) {
  const Icon = variant === "user" ? User : variant === "rejected" ? AlertTriangle : Bot;
  return (
    <div
      className={cn(
        "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
        variant === "user" && "bg-primary text-primary-foreground",
        variant === "assistant" && "bg-muted text-foreground",
        variant === "rejected" && "bg-amber-100 text-amber-700",
      )}
    >
      <Icon className="h-4 w-4" />
    </div>
  );
}

function PendingIndicator() {
  return (
    <div className="flex items-center gap-2 py-1 text-muted-foreground">
      <div className="flex gap-1">
        <Dot delay="0ms" />
        <Dot delay="150ms" />
        <Dot delay="300ms" />
      </div>
      <span className="text-sm italic">El agente está pensando...</span>
    </div>
  );
}

function Dot({ delay }: { delay: string }) {
  return (
    <span
      className="h-1.5 w-1.5 animate-bounce rounded-full bg-current"
      style={{ animationDelay: delay }}
    />
  );
}
