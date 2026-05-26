import { Plus } from "lucide-react";

import { ConversationItem } from "@/components/chat/ConversationItem";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { ConversationResponse } from "@/types/api";

interface Props {
  conversations: ConversationResponse[];
  isLoading: boolean;
  activeId?: string;
  onNew: () => void;
  onDelete: (id: string) => Promise<void>;
}

export function ConversationSidebar({
  conversations,
  isLoading,
  activeId,
  onNew,
  onDelete,
}: Props) {
  return (
    <aside className="flex w-72 shrink-0 flex-col border-r bg-muted/20">
      {/* Botón Nueva conversación */}
      <div className="border-b p-3">
        <Button
          onClick={onNew}
          className="w-full justify-start"
          variant="outline"
        >
          <Plus className="h-4 w-4" />
          Nueva conversación
        </Button>
      </div>

      {/* Lista */}
      <div className="flex-1 overflow-y-auto p-2">
        {isLoading ? (
          <div className="flex flex-col gap-2">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-9 w-full" />
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <p className="px-3 py-6 text-center text-sm text-muted-foreground">
            Aún no tienes conversaciones.
          </p>
        ) : (
          <div className="flex flex-col gap-1">
            {conversations.map((conv) => (
              <ConversationItem
                key={conv.id}
                conversation={conv}
                isActive={conv.id === activeId}
                onDelete={onDelete}
              />
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
