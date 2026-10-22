import React, { useState } from "react"
import { ChevronDownIcon, ChevronRightIcon, DatabaseIcon, FileTextIcon, TerminalIcon, AlertCircleIcon } from "./Icons"

export default function MessageItem({ message }) {
  const [toolsOpen, setToolsOpen] = useState(false)
  const isUser = message.role === "user"

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-2xl bg-indigo-600 text-white rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm">
          {message.content}
        </div>
      </div>
    )
  }

  const { content, sources = [], tools_used = [], isError, isRateLimit } = message

  return (
    <div className="flex justify-start mb-6">
      <div className="max-w-3xl w-full bg-slate-800/90 border border-slate-700/80 rounded-2xl p-4 shadow-sm space-y-3">
        {isError ? (
          <div className="flex items-start gap-2.5 text-rose-300 bg-rose-950/40 p-3 rounded-lg border border-rose-900/60 text-xs leading-relaxed">
            <AlertCircleIcon className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <div className="font-medium text-rose-200">
                {isRateLimit ? "rate limit reached" : "request failed"}
              </div>
              <div>
                {isRateLimit
                  ? "the free tier rate limit was reached. please wait a few seconds before trying again."
                  : content || "an unexpected error occurred while communicating with the assistant."}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-slate-100 text-sm leading-relaxed whitespace-pre-wrap">
            {content}
          </div>
        )}

        {tools_used && tools_used.length > 0 && (
          <div className="pt-2 border-t border-slate-700/60">
            <button
              onClick={() => setToolsOpen(!toolsOpen)}
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition font-medium"
            >
              {toolsOpen ? (
                <ChevronDownIcon className="w-3.5 h-3.5" />
              ) : (
                <ChevronRightIcon className="w-3.5 h-3.5" />
              )}
              <span>tools used ({tools_used.length})</span>
            </button>

            {toolsOpen && (
              <div className="mt-2 space-y-2">
                {tools_used.map((t, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 bg-slate-900/80 rounded border border-slate-700/60 text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[11px] font-semibold text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-900/50">
                        {t.tool}
                      </span>
                      {t.output_summary && (
                        <span className="text-[11px] text-slate-400">
                          {t.output_summary}
                        </span>
                      )}
                    </div>

                    {t.tool === "sql_query" && t.input && (
                      <div className="mt-1">
                        <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">
                          sql query
                        </div>
                        <pre className="p-2 bg-slate-950 text-emerald-400 font-mono text-[11px] rounded overflow-x-auto border border-slate-800">
                          {t.input}
                        </pre>
                      </div>
                    )}

                    {t.tool !== "sql_query" && t.input && (
                      <div className="text-[11px] text-slate-400 font-mono">
                        input: {t.input}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {sources && sources.length > 0 && (
          <div className="pt-2 border-t border-slate-700/60">
            <div className="text-xs font-medium text-slate-400 mb-2 flex items-center gap-1.5">
              <FileTextIcon className="w-3.5 h-3.5 text-slate-400" />
              <span>sources ({sources.length})</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {sources.map((s, idx) => (
                <div
                  key={idx}
                  className="p-2.5 bg-slate-900/70 rounded border border-slate-700/50 text-xs text-slate-300 space-y-1"
                >
                  <div className="flex items-center justify-between font-medium text-[11px] text-slate-200">
                    <span className="truncate pr-1">{s.document}</span>
                    <span className="text-slate-400 text-[10px] shrink-0">
                      p. {s.page} {s.score ? `(${Math.round(s.score * 100)}%)` : ""}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-3 italic">
                    "{s.snippet}"
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
