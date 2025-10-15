"use client"

import { useEffect, useRef, useState } from "react"
import { cn } from "@/lib/utils"
import { ChatContainerRoot, ChatContainerContent, ChatContainerScrollAnchor } from "@/components/ui/chat-container"
import { Message, MessageActions, MessageAvatar, MessageContent } from "@/components/ui/message"
import { PromptInput, PromptInputAction, PromptInputActions, PromptInputTextarea } from "@/components/ui/prompt-input"
import { Button } from "@/components/ui/button"
import { Paperclip, Send, ChevronDown } from "lucide-react"
import { apiChat, apiDelete, apiList, apiUpload, type BackendDoc } from "@/lib/api"

export type ChatMessage = {
  id: string
  role: "user" | "assistant"
  content: string
}

export type FileAttachment = {
  id: string
  file: File
}

export type ChatProps = {
  className?: string
}

export function Chat({ className }: ChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [attachments, setAttachments] = useState<FileAttachment[]>([])
  const [docs, setDocs] = useState<BackendDoc[]>([])
  const [summary, setSummary] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Load existing PDFs on mount
  useEffect(() => {
    refreshDocs()
  }, [])

  const refreshDocs = async () => {
    try {
      const list = await apiList()
      setDocs(list)
    } catch (err) {
      // swallow for now; optionally display toast
      console.error(err)
    }
  }

  const handleSend = async (value: string) => {
    if (!value.trim() && attachments.length === 0) return
    const newMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: value,
    }
    setMessages((prev) => [...prev, newMessage])
    setIsLoading(true)

    try {
      // Upload any pending attachments first
      if (attachments.length > 0) {
        await Promise.all(
          attachments.map(async (att) => {
            await apiUpload(att.file)
          })
        )
        setAttachments([])
        await refreshDocs()
      }

      // Build chat history for backend
      // Rolling window: include up to last 8 messages
      const windowed = [...messages, newMessage].slice(-8)
      const history = windowed.map((m) => ({
        role: m.role,
        content: m.content,
      }))
      const resp = await apiChat(history, 6, summary || undefined)

      const sourcesSection =
        resp.sources && resp.sources.length
          ? `\n\n---\nSources:\n${resp.sources
              .map((s) => `- ${s.doc} (p. ${s.page})`)
              .join("\n")}`
          : ""

      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `${resp.answer}${sourcesSection}`,
      }
      setMessages((prev) => [...prev, assistantMsg])

      // Update lightweight summary (very simple heuristic)
      const latestUser = newMessage.content
      const latestAnswer = resp.answer
      const newSummary = `User asked: ${latestUser}\nAssistant answered: ${latestAnswer.slice(0, 500)}`
      setSummary((prev) => (prev ? `${prev}\n\n${newSummary}` : newSummary).slice(-2000))
    } catch (err) {
      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `Error: ${(err as Error).message}`,
      }
      setMessages((prev) => [...prev, assistantMsg])
    } finally {
      setIsLoading(false)
    }
  }

  const triggerFilePicker = () => fileInputRef.current?.click()

  const onFilesSelected = (files: FileList | null) => {
    if (!files || files.length === 0) return
    const next: FileAttachment[] = Array.from(files).map((file) => ({
      id: crypto.randomUUID(),
      file,
    }))
    setAttachments((prev) => [...prev, ...next])
  }

  const removeAttachment = (id: string) => {
    setAttachments((prev) => prev.filter((a) => a.id !== id))
  }

  const deleteDoc = async (docId: string) => {
    try {
      await apiDelete(docId)
      await refreshDocs()
    } catch (err) {
      console.error(err)
    }
  }

  // Simple scroll-to-bottom button using StickToBottom API: clicking anchor into view
  const scrollToBottom = () => {
    const el = document.querySelector(
      "[data-chat-scroll-anchor]"
    ) as HTMLDivElement | null
    el?.scrollIntoView({ behavior: "smooth", block: "end" })
  }

  return (
    <div className={cn("flex h-full w-full flex-col", className)}>
      {/* Document list */}
      <div className="border-b border-border px-4 py-2">
        <div className="text-sm text-muted-foreground mb-2">Uploaded PDFs</div>
        {docs.length === 0 ? (
          <div className="text-xs text-muted-foreground">No documents uploaded yet.</div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {docs.map((d) => (
              <div key={d.doc_id} className="border-border bg-muted/50 text-foreground flex items-center gap-2 rounded-md border px-2 py-1 text-xs">
                <span className="max-w-[220px] truncate" title={`${d.filename} (${d.pages}p)`}>{d.filename} ({d.pages})</span>
                <Button size="sm" variant="ghost" onClick={() => deleteDoc(d.doc_id)}>Delete</Button>
              </div>
            ))}
          </div>
        )}
      </div>
      <ChatContainerRoot className="grow">
        <ChatContainerContent className="px-4 py-4 gap-4">
          {messages.map((m) => (
            <Message key={m.id} className={cn(m.role === "user" ? "justify-end" : "justify-start")}
            >
              {m.role === "assistant" && (
                <MessageAvatar src="" alt="Assistant" fallback="AI" />
              )}
              <MessageContent markdown>
                {m.content}
              </MessageContent>
              {m.role === "user" && (
                <MessageAvatar src="" alt="You" fallback="You" />
              )}
            </Message>
          ))}
          <ChatContainerScrollAnchor className="mt-2" data-chat-scroll-anchor />
        </ChatContainerContent>
      </ChatContainerRoot>

      {/* Scroll Button */}
      <div className="pointer-events-none sticky bottom-24 z-10 flex w-full justify-center">
        <Button
          type="button"
          size="icon"
          variant="secondary"
          className="pointer-events-auto shadow"
          onClick={scrollToBottom}
          aria-label="Scroll to bottom"
        >
          <ChevronDown className="h-4 w-4" />
        </Button>
      </div>

      {/* Prompt input with actions and file upload */}
      <div className="border-t border-border px-2 py-3">
        <PromptInput
          isLoading={isLoading}
          onSubmit={() => {
            const ta = document.querySelector(
              "textarea[data-chat-textarea]"
            ) as HTMLTextAreaElement | null
            handleSend(ta?.value ?? "")
            if (ta) ta.value = ""
          }}
          className="mx-auto max-w-3xl"
        >
          <div className="flex items-end gap-2 px-2">
            <PromptInputActions className="order-1">
              <PromptInputAction tooltip="Attach files">
                <Button type="button" size="icon" variant="ghost" onClick={triggerFilePicker}>
                  <Paperclip className="h-4 w-4" />
                </Button>
              </PromptInputAction>
            </PromptInputActions>

            <div className="grow">
              <PromptInputTextarea
                placeholder="Ask anything…"
                className="px-3"
                data-chat-textarea
              />
            </div>

            <PromptInputActions className="order-2">
              <PromptInputAction tooltip="Send">
                <Button type="button" size="icon" onClick={() => {
                  const ta = document.querySelector(
                    "textarea[data-chat-textarea]"
                  ) as HTMLTextAreaElement | null
                  handleSend(ta?.value ?? "")
                  if (ta) ta.value = ""
                }}>
                  <Send className="h-4 w-4" />
                </Button>
              </PromptInputAction>
            </PromptInputActions>
          </div>

          {attachments.length > 0 && (
            <div className="mt-2 flex flex-wrap items-center gap-2 px-2 pb-2">
              {attachments.map((a) => (
                <div key={a.id} className="border-border bg-muted text-muted-foreground flex items-center gap-2 rounded-md border px-2 py-1 text-xs">
                  <span className="max-w-[200px] truncate">{a.file.name}</span>
                  <Button size="sm" variant="ghost" onClick={() => removeAttachment(a.id)}>Remove</Button>
                </div>
              ))}
            </div>
          )}

          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={(e) => onFilesSelected(e.target.files)}
          />
        </PromptInput>
      </div>
    </div>
  )
}

export default Chat


