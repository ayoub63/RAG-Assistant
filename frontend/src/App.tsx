import { CustomChat } from './components/chat'

export default function Page() {
  return (
    <main className="p-4">
      <h1 className="text-2xl font-bold mb-4">Mock Chat Demo</h1>
      <CustomChat />
    </main>
  )
}