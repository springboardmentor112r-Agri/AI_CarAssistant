import { useState, useRef, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Send, Copy, MessageSquare, Bot, User } from 'lucide-react'
import { negotiationApi } from '../api'
import { NegotiationMessage } from '../types'
import toast from 'react-hot-toast'
import Spinner from '../components/ui/Spinner'

const STARTER_PROMPTS = [
  'Is this a fair monthly payment?',
  'How do I negotiate a lower money factor?',
  'What are the biggest red flags in my contract?',
  'Write me a message to ask for better terms',
  'What should I ask before signing?',
]

// Simple markdown renderer
const SimpleMarkdown = ({ text, className = '' }: { text: string; className?: string }) => {
  const lines = text.split('\n')
  return (
    <div className={className}>
      {lines.map((line, i) => {
        const boldLine = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        if (line.startsWith('### ')) {
          return <p key={i} className="font-bold text-base mt-2 mb-1" dangerouslySetInnerHTML={{ __html: line.replace('### ', '') }} />
        }
        if (line.startsWith('## ')) {
          return <p key={i} className="font-bold text-base mt-2 mb-1" dangerouslySetInnerHTML={{ __html: line.replace('## ', '') }} />
        }
        if (line.startsWith('# ')) {
          return <p key={i} className="font-bold text-lg mt-2 mb-1" dangerouslySetInnerHTML={{ __html: line.replace('# ', '') }} />
        }
        if (line.startsWith('- ') || line.startsWith('• ') || line.startsWith('* ')) {
          return (
            <div key={i} className="flex items-start gap-2 my-0.5">
              <span className="mt-1 shrink-0">•</span>
              <span dangerouslySetInnerHTML={{ __html: boldLine.replace(/^[-•*] /, '') }} />
            </div>
          )
        }
        if (line.trim() === '') return <div key={i} className="h-2" />
        return <p key={i} className="my-0.5" dangerouslySetInnerHTML={{ __html: boldLine }} />
      })}
    </div>
  )
}

export default function NegotiatePage() {
  const [searchParams] = useSearchParams()
  const contractId = searchParams.get('contractId') ? Number(searchParams.get('contractId')) : undefined
  const [messages, setMessages] = useState<NegotiationMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [threadId, setThreadId] = useState<number | undefined>()
  const [_suggestedMsg, setSuggestedMsg] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async (text: string) => {
    if (!text.trim()) return
    const userMsg: NegotiationMessage = { id: Date.now(), sender_role: 'user', body: text, sent_at: new Date().toISOString() }
    setMessages((m) => [...m, userMsg])
    setInput('')
    setLoading(true)
    setSuggestedMsg(null)

    try {
      const result = await negotiationApi.chat(text, contractId, threadId)
      setThreadId(result.thread_id)
      const aiMsg: NegotiationMessage = {
        id: Date.now() + 1,
        sender_role: 'assistant',
        body: result.response,
        suggested_text: result.suggested_message,
        sent_at: new Date().toISOString(),
      }
      setMessages((m) => [...m, aiMsg])
      if (result.suggested_message) setSuggestedMsg(result.suggested_message)
    } catch {
      toast.error('Failed to get response')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <MessageSquare size={22} className="text-primary-600" />
          Negotiation Assistant
        </h1>
        <p className="text-slate-500 text-sm mt-0.5">
          {contractId ? `Analyzing Contract #${contractId}` : 'Ask anything about car leases and negotiation'}
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-1">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <Bot size={48} className="mx-auto mb-3 text-slate-200" />
            <h3 className="font-semibold text-slate-600 mb-4">How can I help you negotiate?</h3>
            <div className="flex flex-wrap gap-2 justify-center">
              {STARTER_PROMPTS.map((p) => (
                <button
                  key={p}
                  onClick={() => send(p)}
                  className="px-3 py-1.5 bg-white border border-slate-200 rounded-full text-sm text-slate-600 hover:border-primary-400 hover:text-primary-700 transition-colors"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-3 ${msg.sender_role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.sender_role !== 'user' && (
              <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center shrink-0 mt-1">
                <Bot size={16} className="text-primary-600" />
              </div>
            )}
            <div className={`max-w-[75%] ${msg.sender_role === 'user' ? 'order-first' : ''}`}>
              <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.sender_role === 'user'
                  ? 'bg-primary-600 text-white rounded-tr-sm'
                  : 'bg-white border border-slate-200 text-slate-800 rounded-tl-sm'
              }`}>
                {msg.sender_role === 'user' ? (
                  <p>{msg.body}</p>
                ) : (
                  <SimpleMarkdown text={msg.body} className="text-sm" />
                )}
              </div>
              {msg.suggested_text && (
                <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-xl">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-green-700">📨 Ready-to-send dealer message</span>
                    <button
                      onClick={() => { navigator.clipboard.writeText(msg.suggested_text!); toast.success('Copied!') }}
                      className="text-xs text-green-600 hover:underline flex items-center gap-1"
                    >
                      <Copy size={12} /> Copy
                    </button>
                  </div>
                  <SimpleMarkdown text={msg.suggested_text} className="text-sm text-green-800 italic" />
                </div>
              )}
            </div>
            {msg.sender_role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center shrink-0 mt-1">
                <User size={16} className="text-slate-600" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
              <Bot size={16} className="text-primary-600" />
            </div>
            <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3">
              <Spinner className="text-primary-600" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          className="input flex-1"
          placeholder="Ask about your contract or negotiation strategy..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input) } }}
          disabled={loading}
        />
        <button
          onClick={() => send(input)}
          disabled={!input.trim() || loading}
          className="btn-primary px-4"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  )
}