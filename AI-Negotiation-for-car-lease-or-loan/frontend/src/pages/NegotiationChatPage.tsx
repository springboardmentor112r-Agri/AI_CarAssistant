import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import {
  Bot,
  Send,
  Loader2,
  Plus,
  FileText,
  Car,
  ChevronLeft,
  Trash2,
  User,
} from "lucide-react";
import { api } from "../services/api";
import { useAuthStore } from "../store/authStore";
import { API_BASE_URL } from "../config/apiBaseUrl";
import SLAViewer from "../components/SLAViewer";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

interface ThreadSummary {
  thread_id: string;
  started: string;
  last_updated: string;
  message_count: number;
  preview: string;
}

const buildWelcomeMessage = (doc: any): Message => {
  const score = doc?.contract_fairness_score ?? null;
  const flags = doc?.sla_json?.red_flags?.length ?? 0;
  const scoreText =
    score !== null ? `**Fairness Score: ${score}/100**\n\n` : "";
  const flagText =
    flags > 0
      ? `I found **${flags} issue${flags > 1 ? "s" : ""}** worth discussing.\n\n`
      : "No major red flags found.\n\n";
  return {
    id: crypto.randomUUID(),
    role: "assistant",
    content: `## Contract Analysis Ready\n\n${scoreText}${flagText}What would you like to negotiate first?`,
    isStreaming: false,
  };
};

const formatRelativeTime = (dateStr: string) => {
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return "";
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
};

export default function NegotiationChatPage() {
  const { doc_id: docId } = useParams<{ doc_id: string }>();
  const navigate = useNavigate();

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [document, setDocument] = useState<any>(null);

  const messageEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const streamingContentRef = useRef("");
  const rafIdRef = useRef<number | null>(null);
  const streamingMsgIdRef = useRef<string | null>(null);
  const scrollRafRef = useRef<number | null>(null);

  // Scroll only when messages are added (not on every token update)
  const lastMessageCountRef = useRef(0);
  useEffect(() => {
    if (messages.length !== lastMessageCountRef.current) {
      lastMessageCountRef.current = messages.length;
      messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.length]);

  // Separate scroll for streaming — throttled via rAF
  const scrollDuringStream = () => {
    if (scrollRafRef.current) return;
    scrollRafRef.current = requestAnimationFrame(() => {
      messageEndRef.current?.scrollIntoView({ behavior: "auto" });
      scrollRafRef.current = null;
    });
  };

  useEffect(() => {
    if (!docId) return;
    let mounted = true;

    const initialize = async () => {
      try {
        const doc = await api.documents.getById(docId, true);
        if (!mounted) return;
        setDocument(doc);

        const existingThreads = await api.chat.listThreads(docId);
        if (!mounted) return;
        setThreads(existingThreads);

        if (existingThreads.length > 0) {
          const recent = existingThreads[0];
          setThreadId(recent.thread_id);

          const history = await api.chat.getHistory(recent.thread_id);
          if (!mounted) return;

          if (history.length > 0) {
            setMessages(
              history.map((m: any) => ({
                id: m.message_id,
                role: m.role,
                content: m.content,
                isStreaming: false,
              })),
            );
          } else {
            setMessages([buildWelcomeMessage(doc)]);
          }
        } else {
          const result = await api.chat.newThread(docId);
          if (!mounted) return;
          setThreadId(result.thread_id);
          setThreads([
            {
              thread_id: result.thread_id,
              started: new Date().toISOString(),
              last_updated: new Date().toISOString(),
              message_count: 0,
              preview: "New conversation",
            },
          ]);
          setMessages([buildWelcomeMessage(doc)]);
        }
      } catch (err) {
        console.error("Chat init failed:", err);
      }
    };

    initialize();
    return () => {
      mounted = false;
    };
  }, [docId]);

  const sendMessage = async () => {
    const text = inputText.trim();
    if (!text || isStreaming || !threadId) return;

    // Clear any stuck streaming flags from previous message
    setMessages((prev) =>
      prev.map((m) => (m.isStreaming ? { ...m, isStreaming: false } : m)),
    );

    setInputText("");
    setIsStreaming(true);

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      isStreaming: false,
    };

    const assistantMsgId = crypto.randomUUID();
    const assistantMsg: Message = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      isStreaming: true,
    };
    streamingContentRef.current = "";
    streamingMsgIdRef.current = assistantMsgId;
    setMessages((prev) => [...prev, userMsg, assistantMsg]);

    setTimeout(() => {
      messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 50);

    try {
      const accessToken = useAuthStore.getState().accessToken;

      const response = await fetch(`${API_BASE_URL}/chat/message`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
        body: JSON.stringify({
          doc_id: docId,
          thread_id: threadId,
          message: text,
        }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // Append raw bytes to buffer
        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE messages
        // SSE messages are separated by \n\n
        const parts = buffer.split("\n\n");

        // Last part may be incomplete — keep in buffer
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          // Each part may have multiple lines
          // Find the data: line
          const lines = part.split("\n");
          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;

            const data = line.slice(6);
            // Skip empty data and keepalive comments
            if (!data || data === "") continue;

            if (data === "[DONE]") {
              // Cancel any pending rAF and flush final content
              if (rafIdRef.current) {
                cancelAnimationFrame(rafIdRef.current);
                rafIdRef.current = null;
              }
              const finalContent = streamingContentRef.current;
              streamingMsgIdRef.current = null;
              // Mark message as complete with final content
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, content: finalContent, isStreaming: false }
                    : m,
                ),
              );
              setIsStreaming(false);
              setTimeout(() => {
                messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
              }, 50);
              setThreads((prev) =>
                prev.map((t) =>
                  t.thread_id === threadId
                    ? {
                        ...t,
                        preview: text.slice(0, 60),
                        last_updated: new Date().toISOString(),
                        message_count: (t.message_count || 0) + 2,
                      }
                    : t,
                ),
              );
              return;
            }

            if (data.startsWith("[ERROR]")) {
              throw new Error(data.slice(7));
            }

            // Unescape newlines that were escaped for SSE
            const chunk = data.replace(/\\n/g, "\n");
            streamingContentRef.current += chunk;

            // Batch UI updates at screen refresh rate (~60fps)
            // Instead of re-rendering on every token
            if (!rafIdRef.current) {
              rafIdRef.current = requestAnimationFrame(() => {
                rafIdRef.current = null;
                const snapshot = streamingContentRef.current;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? { ...m, content: snapshot, isStreaming: true }
                      : m,
                  ),
                );
                scrollDuringStream();
              });
            }
          }
        }
      }

      // Stream ended without explicit [DONE]
      // Cancel pending rAF and flush
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
      const finalContent = streamingContentRef.current;
      streamingMsgIdRef.current = null;
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId
            ? { ...m, content: finalContent, isStreaming: false }
            : m,
        ),
      );
      setIsStreaming(false);
    } catch (error: any) {
      console.error("Stream error:", error);
      setIsStreaming(false);
      // Clean up rAF on error
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
      streamingMsgIdRef.current = null;

      const errorText =
        error.message?.includes("rate limit") || error.message?.includes("429")
          ? "## Rate Limit\n\nGroq rate limit reached. Please wait **10 seconds** and try again."
          : error.message?.includes("401")
            ? "## Session Expired\n\nPlease refresh the page and log in again."
            : "## Connection Error\n\nSomething went wrong. Please try again.";

      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId
            ? { ...m, content: errorText, isStreaming: false }
            : m,
        ),
      );
    }
  };

  const switchThread = async (thread: ThreadSummary) => {
    if (thread.thread_id === threadId) return;
    setThreadId(thread.thread_id);
    setMessages([]);
    try {
      const history = await api.chat.getHistory(thread.thread_id);
      if (history.length > 0) {
        setMessages(
          history.map((m: any) => ({
            id: m.message_id,
            role: m.role,
            content: m.content,
            isStreaming: false,
          })),
        );
      } else {
        setMessages([buildWelcomeMessage(document)]);
      }
    } catch (err) {
      console.error("Failed to load thread:", err);
    }
  };

  const handleNewChat = async () => {
    try {
      const result = await api.chat.newThread(docId!);
      const newThread: ThreadSummary = {
        thread_id: result.thread_id,
        started: new Date().toISOString(),
        last_updated: new Date().toISOString(),
        message_count: 0,
        preview: "New conversation",
      };
      setThreads((prev) => [newThread, ...prev]);
      setThreadId(result.thread_id);
      setMessages([
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            "## New Conversation\n\nWhat would you like to discuss about your contract?",
          isStreaming: false,
        },
      ]);
    } catch (err) {
      console.error("Failed to create thread:", err);
    }
  };

  const handleDeleteThread = async (thread_id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm("Delete this conversation?")) return;
    try {
      await api.chat.deleteThread(thread_id);
      const remaining = threads.filter((t) => t.thread_id !== thread_id);
      setThreads(remaining);
      if (thread_id === threadId) {
        if (remaining.length > 0) {
          await switchThread(remaining[0]);
        } else {
          await handleNewChat();
        }
      }
    } catch (err) {
      console.error("Failed to delete thread:", err);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
  };

  const vin = document?.sla_json?.vin || document?.vin;

  return (
    <div
      className="flex h-screen overflow-hidden
                    bg-gray-50 dark:bg-gray-950
                    text-gray-900 dark:text-white"
    >
      {/* ── LEFT SIDEBAR ── */}
      <div
        className="w-56 flex-shrink-0 flex flex-col
                      border-r border-gray-200 dark:border-gray-800
                      bg-white dark:bg-gray-900"
      >
        <div className="p-3 border-b border-gray-200 dark:border-gray-800">
          <button
            onClick={() => navigate("/dashboard")}
            className="flex items-center gap-1.5 text-xs
                       text-gray-500 dark:text-gray-400
                       hover:text-gray-900 dark:hover:text-white
                       transition-colors mb-3"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            Dashboard
          </button>
          <p
            className="text-xs font-semibold text-gray-500
                        dark:text-gray-400 uppercase tracking-wider"
          >
            Conversations
          </p>
        </div>

        <div className="p-3 border-b border-gray-200 dark:border-gray-800">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2
                       py-2 px-3 text-sm font-medium rounded-lg
                       bg-blue-600 hover:bg-blue-700 text-white
                       transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {threads.length === 0 ? (
            <div className="p-4 text-xs text-gray-400 text-center">
              No conversations yet
            </div>
          ) : (
            threads.map((thread) => (
              <div
                key={thread.thread_id}
                onClick={() => switchThread(thread)}
                className={`group relative p-3 cursor-pointer
                  transition-colors border-l-2
                  hover:bg-gray-50 dark:hover:bg-gray-800
                  ${
                    thread.thread_id === threadId
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                      : "border-transparent"
                  }`}
              >
                <p
                  className="text-xs font-medium truncate
                               text-gray-900 dark:text-white
                               leading-relaxed pr-5"
                >
                  {thread.preview || "New conversation"}
                </p>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-gray-400">
                    {formatRelativeTime(thread.last_updated)}
                  </span>
                  <span className="text-xs text-gray-400">
                    {thread.message_count} msgs
                  </span>
                </div>
                <button
                  onClick={(e) => handleDeleteThread(thread.thread_id, e)}
                  className="absolute right-2 top-2 p-1 rounded
                             opacity-0 group-hover:opacity-100
                             transition-opacity text-gray-400
                             hover:text-red-500
                             hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ── CENTER CHAT ── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Bar */}
        <div
          className="h-14 border-b border-gray-200 dark:border-gray-800
                        bg-white dark:bg-gray-900
                        flex items-center px-4 gap-3 flex-shrink-0"
        >
          <div className="flex-1 min-w-0">
            <p
              className="text-sm font-semibold truncate
                          text-gray-900 dark:text-white"
            >
              {document?.filename || "Contract"}
            </p>
            <div className="flex items-center gap-2 mt-0.5">
              {document?.processing_status === "ready" && (
                <span
                  className="text-xs text-green-600
                                 dark:text-green-400 font-medium"
                >
                  Ready
                </span>
              )}
              {document?.contract_fairness_score != null && (
                <span
                  className={`text-xs font-medium ${
                    document.contract_fairness_score >= 80
                      ? "text-green-600 dark:text-green-400"
                      : document.contract_fairness_score >= 50
                        ? "text-yellow-600 dark:text-yellow-400"
                        : "text-red-600 dark:text-red-400"
                  }`}
                >
                  Score {Math.round(document.contract_fairness_score)}/100
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            {vin && (
              <button
                onClick={() => navigate(`/vin/${vin}`)}
                className="flex items-center gap-1.5 px-3 py-1.5
                           text-xs font-medium rounded-lg transition-colors
                           bg-gray-100 dark:bg-gray-800
                           hover:bg-gray-200 dark:hover:bg-gray-700
                           text-gray-700 dark:text-gray-300"
              >
                <Car className="w-3.5 h-3.5" />
                VIN Report
              </button>
            )}
            <button
              onClick={() => navigate(`/documents/${docId}/review`)}
              className="flex items-center gap-1.5 px-3 py-1.5
                         text-xs font-medium rounded-lg transition-colors
                         bg-blue-600 hover:bg-blue-700 text-white"
            >
              <FileText className="w-3.5 h-3.5" />
              View Contract
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {message.role === "assistant" && (
                <div
                  className="w-7 h-7 rounded-full bg-blue-600
                                flex items-center justify-center
                                flex-shrink-0 mt-1"
                >
                  <Bot className="w-4 h-4 text-white" />
                </div>
              )}

              {message.role === "assistant" ? (
                // ── STREAMING: plain text, no markdown parse ──
                // Avoids flicker from parsing incomplete markdown
                message.isStreaming ? (
                  message.content === "" ? (
                    // Typing dots — before first token
                    <div className="flex gap-1.5 items-center h-5 px-1">
                      <div
                        className="w-2 h-2 bg-gray-400 rounded-full
                                      animate-bounce"
                        style={{ animationDelay: "0ms" }}
                      />
                      <div
                        className="w-2 h-2 bg-gray-400 rounded-full
                                      animate-bounce"
                        style={{ animationDelay: "150ms" }}
                      />
                      <div
                        className="w-2 h-2 bg-gray-400 rounded-full
                                      animate-bounce"
                        style={{ animationDelay: "300ms" }}
                      />
                    </div>
                  ) : (
                    // Plain text while tokens arriving — smooth, no flicker
                    <p
                      className="text-sm leading-relaxed
                                  whitespace-pre-wrap font-normal
                                  text-gray-200"
                    >
                      {message.content}
                      <span
                        className="inline-block w-0.5 h-4 bg-blue-400
                                       animate-pulse ml-0.5 align-middle"
                      />
                    </p>
                  )
                ) : (
                  // ── COMPLETE: full markdown render ──
                  // Only after [DONE] received — content is complete
                  <ReactMarkdown
                    className="prose prose-sm dark:prose-invert
                               max-w-none
                               prose-headings:font-bold
                               prose-headings:text-gray-900
                               dark:prose-headings:text-white
                               prose-headings:mb-2
                               prose-headings:mt-3
                               prose-h2:text-base
                               prose-h3:text-sm
                               prose-p:text-gray-700
                               dark:prose-p:text-gray-200
                               prose-p:leading-relaxed
                               prose-p:my-1.5
                               prose-p:font-normal
                               prose-ul:my-2
                               prose-ul:space-y-1
                               prose-li:text-gray-700
                               dark:prose-li:text-gray-200
                               prose-li:font-normal
                               prose-strong:text-gray-900
                               dark:prose-strong:text-white
                               prose-strong:font-semibold
                               prose-blockquote:border-l-4
                               prose-blockquote:border-blue-500
                               prose-blockquote:bg-blue-50
                               dark:prose-blockquote:bg-blue-900/20
                               prose-blockquote:px-4
                               prose-blockquote:py-2
                               prose-blockquote:rounded-r-lg
                               prose-blockquote:not-italic
                               prose-blockquote:my-3
                               prose-blockquote:text-gray-700
                               dark:prose-blockquote:text-gray-200
                               prose-blockquote:font-normal
                               prose-code:bg-gray-100
                               dark:prose-code:bg-gray-700
                               prose-code:px-1.5
                               prose-code:py-0.5
                               prose-code:rounded
                               prose-code:text-xs
                               prose-ol:my-2
                               prose-ol:space-y-1"
                  >
                    {message.content}
                  </ReactMarkdown>
                )
              ) : (
                // ── USER MESSAGE: always plain text ──
                <div className="flex gap-3 justify-end items-end">
                  <div className="max-w-[75%] bg-blue-600 text-white rounded-2xl rounded-br-sm px-4 py-3">
                    <p
                      className="text-sm leading-relaxed
                                  whitespace-pre-wrap font-normal"
                    >
                      {message.content}
                    </p>
                  </div>
                  {/* User avatar — right side of user messages */}
                  <div
                    className="w-7 h-7 rounded-full bg-gray-600
                                  flex items-center justify-center
                                  flex-shrink-0 mb-1"
                  >
                    <User className="w-4 h-4 text-white" />
                  </div>
                </div>
              )}
            </div>
          ))}

          {/* Scroll anchor */}
          <div ref={messageEndRef} />
        </div>

        {/* Input Area */}
        <div
          className="border-t border-gray-200 dark:border-gray-800
                        bg-white dark:bg-gray-900 p-4 flex-shrink-0"
        >
          <div
            className="flex gap-3 items-end
                          max-w-4xl mx-auto"
          >
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={inputText}
                onChange={handleTextareaInput}
                onKeyDown={handleKeyDown}
                disabled={isStreaming}
                placeholder="Ask about your contract... (Enter to send, Shift+Enter for new line)"
                rows={1}
                className="w-full resize-none rounded-2xl px-4 py-3
                           text-sm leading-relaxed
                           bg-gray-50 dark:bg-gray-800
                           border border-gray-200 dark:border-gray-700
                           text-gray-900 dark:text-white
                           placeholder-gray-400 dark:placeholder-gray-500
                           focus:outline-none focus:ring-2
                           focus:ring-blue-500 focus:border-transparent
                           disabled:opacity-50 disabled:cursor-not-allowed
                           transition-colors"
                style={{ maxHeight: "120px" }}
              />
            </div>
            <button
              onClick={sendMessage}
              disabled={isStreaming || !inputText.trim()}
              className={`p-3 rounded-2xl transition-all flex-shrink-0
                ${
                  isStreaming || !inputText.trim()
                    ? "bg-gray-200 dark:bg-gray-700 cursor-not-allowed"
                    : "bg-blue-600 hover:bg-blue-700 shadow-sm cursor-pointer"
                } text-white`}
            >
              {isStreaming ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
          <p
            className="text-xs text-gray-400 dark:text-gray-500
                        text-center mt-2"
          >
            AI advice is for guidance only — verify with a licensed dealer or
            attorney
          </p>
        </div>
      </div>

      {/* ── RIGHT SIDEBAR — CONTRACT TERMS ── */}
      <div
        className="w-72 flex-shrink-0 flex flex-col
                      border-l border-gray-200 dark:border-gray-800
                      bg-white dark:bg-gray-900"
      >
        <div
          className="p-4 border-b border-gray-200
                        dark:border-gray-800 flex-shrink-0"
        >
          <h3
            className="font-semibold text-sm
                         text-gray-900 dark:text-white"
          >
            Contract Terms
          </h3>
        </div>

        <div className="flex-1 overflow-y-auto">
          {docId && <SLAViewer doc_id={docId} />}
        </div>

        {vin && (
          <div
            className="p-3 border-t border-gray-200
                          dark:border-gray-800 flex-shrink-0"
          >
            <button
              onClick={() => navigate(`/vin/${vin}`)}
              className="w-full py-2 px-3 text-xs font-medium
                         bg-gray-100 dark:bg-gray-800
                         hover:bg-gray-200 dark:hover:bg-gray-700
                         text-gray-900 dark:text-white
                         rounded-lg transition-colors
                         flex items-center justify-center gap-2"
            >
              <Car className="w-3.5 h-3.5" />
              View VIN Report
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
