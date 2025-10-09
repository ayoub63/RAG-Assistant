import {
  ChatInput,
  ChatMessage,
  ChatMessages,
  ChatSection,
  useChatUI,
  useFile,
} from '@llamaindex/chat-ui'
import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export function CustomChat() {
  const [messages, setMessages] = useState<Message[]>([])

  const sendMessage = async (msg: Message) => {
    setMessages(prev => [...prev, msg])

    const res = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: msg.content }),
    })
    const data = await res.json()

    const aiMsg: Message = { role: 'assistant', content: data.answer }
    setMessages(prev => [...prev, aiMsg])
  }

  const handler = {
    messages,
    sendMessage,
  }

  const { image, uploadFile, reset, getAttachments } = useFile({
    uploadAPI: 'http://localhost:8000/upload',
  })

  const attachments = getAttachments()

  return (
    <ChatSection handler={handler} className="h-screen overflow-hidden p-0 md:p-5">
      <CustomChatMessages messages={messages} />
      <ChatInput attachments={attachments} resetUploadedFiles={reset}>
        {image ? (
          <img className="max-h-[100px] object-contain" src={image.url} alt="uploaded" />
        ) : null}
        <ChatInput.Form
          onSubmit={async (value: string) => {
            await sendMessage({ role: 'user', content: value })
          }}
        >
          <ChatInput.Field />
          <ChatInput.Upload
            allowedExtensions={['jpg', 'png', 'jpeg']}
            onUpload={async (file) => {
              await uploadFile(file) // ✅ must return void
            }}
          />
          <ChatInput.Submit />
        </ChatInput.Form>
      </ChatInput>
    </ChatSection>
  )
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
                    alt={msg.role === 'user' ? 'User' : 'AI'}
                    src={msg.role === 'user' ? '/user.png' : '/llama.png'}
                  />
                </ChatMessage.Avatar>
                <ChatMessage.Content>
                  <ChatMessage.Part.Markdown>{msg.content}</ChatMessage.Part.Markdown>
                </ChatMessage.Content>
              </ChatMessage>
            </motion.div>
          ))}
        </AnimatePresence>
      </ChatMessages.List>
    </ChatMessages>
  )
}
