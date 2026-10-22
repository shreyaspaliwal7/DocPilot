import React from "react"
import { ActivityIcon, RefreshIcon } from "./Icons"

export default function MetricsPanel({ metrics, loading, onRefresh }) {
  if (!metrics) {
    return (
      <div className="p-3 bg-slate-800/80 rounded-lg border border-slate-700/60 text-xs text-slate-400">
        loading system metrics...
      </div>
    )
  }

  const costStr = Number(metrics.total_estimated_cost || 0).toFixed(4)
  const failurePercent = ((metrics.failure_rate || 0) * 100).toFixed(1)

  return (
    <div className="p-3 bg-slate-800/90 rounded-lg border border-slate-700/70 text-xs text-slate-300">
      <div className="flex items-center justify-between mb-2">
        <span className="flex items-center gap-1.5 font-medium text-slate-200">
          <ActivityIcon className="w-3.5 h-3.5 text-emerald-400" />
          system metrics
        </span>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="text-slate-400 hover:text-slate-200 p-1 rounded transition"
          title="refresh metrics"
        >
          <RefreshIcon className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-2 text-[11px]">
        <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
          <div className="text-slate-400">requests</div>
          <div className="text-sm font-semibold text-slate-100">{metrics.total_requests || 0}</div>
        </div>
        <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
          <div className="text-slate-400">avg latency</div>
          <div className="text-sm font-semibold text-slate-100">
            {metrics.average_latency ? `${metrics.average_latency}s` : "0.0s"}
          </div>
        </div>
        <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
          <div className="text-slate-400">est. cost</div>
          <div className="text-sm font-semibold text-slate-100">${costStr}</div>
        </div>
        <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
          <div className="text-slate-400">failure rate</div>
          <div className="text-sm font-semibold text-slate-100">{failurePercent}%</div>
        </div>
      </div>

      {metrics.rate_limit_hit_count > 0 && (
        <div className="mt-2 text-[10px] text-amber-400 bg-amber-950/40 px-2 py-1 rounded border border-amber-800/50">
          rate limit hits: {metrics.rate_limit_hit_count}
        </div>
      )}

      {metrics.most_common_failed_questions && metrics.most_common_failed_questions.length > 0 && (
        <div className="mt-2 pt-2 border-t border-slate-700/60">
          <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">common unhandled</div>
          <ul className="space-y-1">
            {metrics.most_common_failed_questions.slice(0, 2).map((item, i) => (
              <li key={i} className="text-[10px] text-slate-400 truncate flex justify-between">
                <span className="truncate pr-1">{item.question}</span>
                <span className="text-slate-500 font-mono">x{item.count}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
