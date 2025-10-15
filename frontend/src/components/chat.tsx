
import { ChatSection } from '@llamaindex/chat-ui'
import { useChat } from "@ai-sdk/react";

export function SimpleChat() {
  const handler = useChat()
  return <ChatSection handler={handler} />
}
