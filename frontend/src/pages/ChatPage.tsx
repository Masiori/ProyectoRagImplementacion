import { MessageSquare } from "lucide-react";

/**
 * Página de chat.
 * En M6.4 implementaremos:
 *   - Sidebar con la lista de conversaciones
 *   - Lista de mensajes (user / assistant) con sources
 *   - Input para enviar nuevas preguntas
 */
export function ChatPage() {
  return (
    <div className="container flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
      <MessageSquare className="h-12 w-12 text-muted-foreground" />
      <h1 className="text-2xl font-semibold">Chat</h1>
      <p className="max-w-md text-sm text-muted-foreground">
        Aquí vivirá la interfaz tipo chatbot. Se implementa en la fase M6.4
        una vez tengamos la autenticación lista (M6.2) y la página de documentos
        (M6.3).
      </p>
    </div>
  );
}
