import React, { useEffect, useRef, useState } from "react"
import { SendIcon, DatabaseIcon, FileTextIcon, DollarIcon, ShieldIcon } from "./Icons"
import MessageItem from "./MessageItem"

export default function ChatArea({
  messages,
  loading,
  onSendMessage,
  backendConnected,
}) {
  const [input, setInput] = useState("")
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  const handleSubmit = (e) => {
    e.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || loading) return
    onSendMessage(trimmed)
    setInput("")
  }

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const exampleQuestions = [
    {
      title: "sales database",
      q: "how many completed orders do we have and what is total revenue?",
      icon: DatabaseIcon,
    },
    {
      title: "document search",
      q: "what is the remote work policy and equipment stipend?",
      icon: FileTextIcon,
    },
    {
      title: "currency conversion",
      q: "convert 750 usd to inr",
      icon: DollarIcon,
    },
    {
      title: "safety guardrail",
      q: "drop table customers",
      icon: ShieldIcon,
    },
  ]

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950">
      <header className="px-6 py-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-900/60 backdrop-blur">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-slate-200">chat assistant</span>
          <span className="text-xs text-slate-500">&bull;</span>
          <span className="text-xs text-slate-400">rag, sql and live exchange rates</span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span
            className={`w-2 h-2 rounded-full ${
              backendConnected ? "bg-emerald-400" : "bg-rose-400"
            }`}
          />
          <span className="text-slate-400">
            {backendConnected ? "api connected" : "api disconnected"}
          </span>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <div className="max-w-2xl mx-auto py-12 text-center space-y-6">
            <div className="space-y-2">
              <h2 className="text-xl font-semibold text-slate-100">
                ask anything across documents, sales data, and rates
              </h2>
              <p className="text-sm text-slate-400 max-w-lg mx-auto">
                docpilot automatically routes questions to semantic document search,
                readonly postgres sql, or real-time currency apis.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-left pt-4">
              {exampleQuestions.map((item, idx) => {
                const Icon = item.icon
                return (
                  <button
                    key={idx}
                    onClick={() => onSendMessage(item.q)}
                    className="p-3 rounded-lg border border-slate-800 bg-slate-900/60 hover:bg-slate-850 hover:border-slate-700 transition text-left group"
                  >
                    <div className="flex items-center gap-1.5 text-[11px] font-medium text-indigo-400 uppercase tracking-wider mb-1">
                      <Icon className="w-3.5 h-3.5" />
                      <span>{item.title}</span>
                    </div>
                    <div className="text-xs text-slate-300 group-hover:text-slate-100">
                      "{item.q}"
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto">
            {messages.map((msg, index) => (
              <MessageItem key={index} message={msg} />
            ))}
            {loading && (
              <div className="flex justify-start mb-6">
                <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl px-4 py-3 text-xs text-slate-400 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
                  <span>routing and generating answer...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <div className="p-4 border-t border-slate-800 bg-slate-900/40">
        <div className="max-w-3xl mx-auto">
          <form onSubmit={handleSubmit} className="relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              placeholder="ask a question about documents, sales data, or currency rates..."
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 pr-12 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="absolute right-2 p-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600 text-white transition"
              title="send message"
            >
              <SendIcon className="w-4 h-4" />
            </button>
          </form>
          <div className="text-[11px] text-slate-500 text-center mt-2">
            runs entirely on free tiers &bull; prompt injection and sql guardrails active
          </div>
        </div>
      </div>
    </div>
  )
}
