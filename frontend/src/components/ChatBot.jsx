import { useState, useRef, useEffect } from 'react'
import { chatAPI } from '../services/api.js'
import styles from './ChatBot.module.css'

const CHIPS = [
  'What is a fair APR?',
  'How do I negotiate mileage?',
  'Draft a dealer email',
  'Explain residual value',
  'Is my early exit fee high?',
]

const WELCOME = "👋 Hi! I'm your AutoGuard AI assistant. Upload a contract first, then I can help you understand the terms and negotiate better deals with your dealer."

export default function ChatBot({ contractId, sla, score }) {
  const [messages, setMessages] = useState([{ role: 'assistant', content: WELCOME }])
  const [input,    setInput]    = useState('')
  const [loading,  setLoading]  = useState(false)
  const bottomRef = useRef()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send(text) {
    const msg = (text || input).trim()
    if (!msg) return
    setInput('')

    const userMsg = { role: 'user', content: msg }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      let reply
      if (contractId) {
        const data = await chatAPI.send(contractId, msg)
        reply = data.reply
      } else {
        // No contract yet — use fallback
        reply = getFallback(msg)
      }
      setMessages(prev => [...prev, { role: 'assistant', content: reply }])
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' }])
    } finally {
      setLoading(false)
    }
  }

  function getFallback(msg) {
    const m = msg.toLowerCase()
    if (m.includes('apr') || m.includes('interest'))
      return '📊 A fair APR for a car lease with good credit is typically 4–6%. Anything above 7% is worth negotiating. Ask your dealer to match a pre-approved bank rate.'
    if (m.includes('mileage'))
      return '🚗 Standard mileage overage is $0.15–$0.18/mile. If your contract says $0.25+, negotiate it down or prepay miles at a lower rate upfront.'
    if (m.includes('email') || m.includes('dealer'))
      return '📧 Here\'s a template:\n\n"Dear [Dealer], after reviewing the lease terms I\'d like to discuss: (1) APR reduction to market rate, (2) mileage overage at $0.18/mi, (3) early termination cap at $1,000. I\'m ready to sign once aligned. Best regards."'
    if (m.includes('residual'))
      return '💡 Residual value is the car\'s estimated worth at lease end. A higher residual (48–58%) means lower monthly payments. It\'s usually non-negotiable but worth understanding.'
    return '🤖 Please upload your contract first so I can analyze the specific terms and give you personalized negotiation advice!'
  }

  return (
    <div className={styles.panel}>
      <div className={styles.title}>
        🤖 Negotiation Assistant
        <span className={styles.pill}>AI Powered</span>
        {score != null && <span className={styles.score}>Score: {score}/100</span>}
      </div>

      <div className={styles.messages}>
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? styles.user : styles.ai}>
            {m.content.split('\n').map((line, j) => (
              <span key={j}>{line}{j < m.content.split('\n').length - 1 && <br />}</span>
            ))}
          </div>
        ))}
        {loading && (
          <div className={styles.ai}>
            <div className={styles.typing}>
              <span /><span /><span />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className={styles.chips}>
        {CHIPS.map(c => (
          <button key={c} className={styles.chip} onClick={() => send(c)}>{c}</button>
        ))}
      </div>

      <div className={styles.inputRow}>
        <input
          className={styles.input}
          placeholder="Ask about your contract…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          disabled={loading}
        />
        <button className={styles.sendBtn} onClick={() => send()} disabled={loading || !input.trim()}>
          ➤
        </button>
      </div>
    </div>
  )
}
