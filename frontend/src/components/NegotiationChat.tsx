"use client";

import { useState } from "react";
import axios from "axios";
import { Button } from "./ui/button";
import { Send, Bot, Sparkles } from "lucide-react";
import { API_ENDPOINTS } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Message {
  role: "USER" | "ASSISTANT";
  content: string;
}

export function NegotiationChat({ contractId }: { contractId: string }) {
  const [messages, setMessages] = useState<Message[]>([
    { role: "ASSISTANT", content: "Hi! I'm your AI negotiation assistant. I've reviewed your contract and I'm ready to help. You can ask me about specific clauses, get negotiation scripts, or find out what questions to ask your dealer." }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || isTyping) return;
    const userText = input;
    setInput("");
    setMessages(prev => [...prev, { role: "USER", content: userText }]);
    setIsTyping(true);
    try {
      const res = await axios.post(API_ENDPOINTS.CHAT(contractId), { content: userText });
      setMessages(prev => [...prev, { role: "ASSISTANT", content: res.data.content }]);
    } catch {
      setMessages(prev => [...prev, { role: "ASSISTANT", content: "Sorry, I lost connection to the server. Please ensure the backend is running." }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-[520px] border border-white/10 rounded-2xl overflow-hidden bg-white/3">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600/20 to-purple-600/20 border-b border-white/10 p-4 flex items-center gap-3">
        <div className="bg-indigo-500/20 p-2 rounded-xl">
          <Bot className="w-5 h-5 text-indigo-400" />
        </div>
        <div>
          <h3 className="font-semibold text-white text-sm">Negotiation AI Assistant</h3>
          <p className="text-xs text-slate-400 flex items-center gap-1"><Sparkles className="w-3 h-3" /> Powered by GPT</p>
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          <span className="text-xs text-green-400">Online</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={cn("flex", msg.role === "USER" ? "justify-end" : "justify-start")}>
            {msg.role === "ASSISTANT" && (
              <div className="w-7 h-7 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center mr-2 shrink-0 mt-1">
                <Bot className="w-3.5 h-3.5 text-indigo-400" />
              </div>
            )}
            <div className={cn(
              "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
              msg.role === "USER"
                ? "bg-gradient-to-br from-indigo-600 to-purple-600 text-white rounded-tr-none shadow-lg"
                : "bg-white/8 border border-white/10 text-slate-300 rounded-tl-none"
            )}>
              {msg.content}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start items-end gap-2">
            <div className="w-7 h-7 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center shrink-0">
              <Bot className="w-3.5 h-3.5 text-indigo-400" />
            </div>
            <div className="bg-white/8 border border-white/10 rounded-2xl rounded-tl-none px-4 py-3 flex gap-1">
              {[0, 1, 2].map(n => (
                <div key={n} className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: `${n * 100}ms` }} />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-white/10 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask about your contract..."
          className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-slate-600 text-sm outline-none input-glow transition-all"
        />
        <Button
          size="icon"
          onClick={sendMessage}
          disabled={isTyping || !input.trim()}
          className="rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 border-0 shrink-0"
        >
          <Send className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
