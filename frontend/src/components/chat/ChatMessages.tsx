import { useEffect, useRef } from "react";

import { ChatMessage } from "@/components/chat/ChatMessage";
import type { DisplayMessage } from "@/hooks/useChat";

interface Props {
  messages: DisplayMessage[];
}

export function ChatMessages({ messages }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  // Auto-scroll al final cuando llega un mensaje nuevo
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto flex max-w-3xl flex-col gap-4 px-4 py-6">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
