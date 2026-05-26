import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { ChatInput } from "@/components/chat/ChatInput";
import { ChatMessages } from "@/components/chat/ChatMessages";
import { ConversationSidebar } from "@/components/chat/ConversationSidebar";
import { EmptyState } from "@/components/chat/EmptyState";
import { FullScreenLoader } from "@/components/FullScreenLoader";
import { useChat } from "@/hooks/useChat";
import { useConversations } from "@/hooks/useConversations";

/**
 * Página principal del chat.
 *
 * Layout:
 *   - Sidebar (izquierda, fijo) con conversaciones
 *   - Main (derecha) con mensajes + input
 *
 * Rutas:
 *   /chat                       → conversación nueva (vacía)
 *   /chat/:conversationId       → conversación específica
 */
export function ChatPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const navigate = useNavigate();

  const [inputValue, setInputValue] = useState("");

  // Lista de conversaciones (sidebar)
  const {
    conversations,
    isLoading: convsLoading,
    refresh: refreshConversations,
    remove: removeConversation,
  } = useConversations();

  // Mensajes de la conversación activa
  const { messages, isLoading: msgsLoading, isWaitingAgent, sendMessage } =
    useChat({
      conversationId: conversationId ?? null,
      onConversationCreated: (newId) => {
        // Tras el primer mensaje, navegar a la URL con id y refrescar el sidebar
        refreshConversations();
        navigate(`/chat/${newId}`, { replace: true });
      },
    });

  const handleNewConversation = () => {
    setInputValue("");
    navigate("/chat");
  };

  const handleDeleteConversation = async (id: string) => {
    await removeConversation(id);
    // Si la activa fue borrada, ir a una nueva
    if (id === conversationId) {
      navigate("/chat");
    }
  };

  const handleSubmit = async (question: string) => {
    setInputValue("");
    await sendMessage(question);
  };

  return (
    <div className="flex flex-1 h-[calc(100vh-3.5rem)]">
      <ConversationSidebar
        conversations={conversations}
        isLoading={convsLoading}
        activeId={conversationId}
        onNew={handleNewConversation}
        onDelete={handleDeleteConversation}
      />

      <main className="flex min-w-0 flex-1 flex-col">
        {msgsLoading ? (
          <div className="flex flex-1 items-center justify-center">
            <FullScreenLoader message="Cargando conversación..." />
          </div>
        ) : messages.length === 0 ? (
          <EmptyState onSuggestionClick={setInputValue} />
        ) : (
          <ChatMessages messages={messages} />
        )}

        <ChatInput
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleSubmit}
          disabled={isWaitingAgent || msgsLoading}
        />
      </main>
    </div>
  );
}
