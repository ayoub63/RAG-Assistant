import Chat from "./components/ui/chat"
export default function Page() {
  return (
    <main className="p-4">
      <h1 className="text-2xl font-bold mb-4">Prompt Kit Chat</h1>
      <div className="h-[80vh]">
        <Chat />
      </div>
    </main>
  )
}