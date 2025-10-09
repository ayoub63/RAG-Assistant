import {
  ChatInput,
  ChatMessage,
  ChatMessages,
  ChatSection,
  useFile,
} from "@llamaindex/chat-ui";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import type { Message, ChatHandler } from "@llamaindex/chat-ui";

export function CustomChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<
    "streaming" | "ready" | "error" | "submitted"
  >("ready");

  const sendMessage = async (msg: Message) => {
    setMessages((prev) => [...prev, msg]);
    setStatus("submitted");

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: msg.parts?.[0]?.text || "" }),
      });

      const data = await res.json();

      const aiMsg: Message = {
        id: Math.random().toString(),
        role: "assistant",
        parts: [{ type: "text", text: data.answer }],
      };

      setMessages((prev) => [...prev, aiMsg]);
      setStatus("ready");
    } catch (err) {
      console.error(err);
      setStatus("error");
    }
  };

  //handler must include `messages`, `sendMessage`, and `status`
  const handler: ChatHandler = {
    messages,
    sendMessage,
    status,
  };

  const { image, uploadFile, reset, getAttachments } = useFile({
    uploadAPI: "http://localhost:8000/upload",
  });
  const attachments = getAttachments();

  return (
    <ChatSection handler={handler} className="h-screen overflow-hidden p-0 md:p-5">
      <CustomChatMessages messages={messages} />

      {/*No `onSubmit` here */}
      <ChatInput attachments={attachments} resetUploadedFiles={reset}>
        {image ? (
          <img
            className="max-h-[100px] object-contain"
            src={image.url}
            alt="uploaded"
          />
        ) : null}

        {/* Handles submission automatically using handler.sendMessage */}
        <ChatInput.Form>
          <ChatInput.Field />
          <ChatInput.Upload
            allowedExtensions={["jpg", "png", "jpeg"]}
            onUpload={async (file) => {
              await uploadFile(file);
            }}
          />
          <ChatInput.Submit />
        </ChatInput.Form>
      </ChatInput>
    </ChatSection>
  );
}

function CustomChatMessages({ messages }: { messages: Message[] }) {
  return (
    <ChatMessages>
      <ChatMessages.List className="px-0 md:px-16">
        <AnimatePresence>
          {messages.map((msg, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
            >
              <ChatMessage
                message={msg}
                isLast={index === messages.length - 1}
                className="items-start"
              >
                <ChatMessage.Avatar>
                  <img
                    className="border-1 rounded-full border-[#e711dd]"
                    alt={msg.role === "user" ? "User" : "AI"}
                    src={msg.role === "user" ? "/user.png" : "/llama.png"}
                  />
                </ChatMessage.Avatar>
                <ChatMessage.Content>
                  <ChatMessage.Part.Markdown />
                </ChatMessage.Content>
              </ChatMessage>
            </motion.div>
          ))}
        </AnimatePresence>
      </ChatMessages.List>
    </ChatMessages>
  );
}
