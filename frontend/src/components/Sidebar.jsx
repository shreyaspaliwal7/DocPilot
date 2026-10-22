import React, { useRef, useState } from "react"
import { FileTextIcon, TrashIcon, UploadIcon, DatabaseIcon } from "./Icons"
import MetricsPanel from "./MetricsPanel"

export default function Sidebar({
  documents,
  metrics,
  metricsLoading,
  onRefreshMetrics,
  onUploadDocument,
  onDeleteDocument,
  uploading,
  uploadError,
}) {
  const fileInputRef = useRef(null)
  const [selectedFile, setSelectedFile] = useState(null)

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      onUploadDocument(file)
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
    }
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return "0 B"
    const kb = bytes / 1024
    if (kb < 1024) return `${kb.toFixed(1)} KB`
    return `${(kb / 1024).toFixed(1)} MB`
  }

  return (
    <aside className="w-80 bg-slate-900 border-r border-slate-800 flex flex-col h-screen select-none">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded bg-indigo-600 flex items-center justify-center text-white font-bold text-sm">
            D
          </div>
          <div>
            <h1 className="text-sm font-semibold text-slate-100 tracking-tight">docpilot</h1>
            <p className="text-[11px] text-slate-400">multi-source knowledge assistant</p>
          </div>
        </div>
      </div>

      <div className="p-4 border-b border-slate-800">
        <div className="text-xs font-medium text-slate-300 mb-2 flex items-center justify-between">
          <span>documents</span>
          <span className="text-[10px] text-slate-500">{documents.length} indexed</span>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt"
          onChange={handleFileChange}
          className="hidden"
          id="file-upload"
        />
        <label
          htmlFor="file-upload"
          className={`flex items-center justify-center gap-2 p-2.5 rounded-lg border border-dashed border-slate-700 hover:border-indigo-500 bg-slate-800/40 hover:bg-slate-800 cursor-pointer text-xs text-slate-300 transition ${
            uploading ? "opacity-50 pointer-events-none" : ""
          }`}
        >
          <UploadIcon className="w-4 h-4 text-indigo-400" />
          <span>{uploading ? "indexing document..." : "upload .pdf or .txt"}</span>
        </label>

        {uploadError && (
          <div className="mt-2 text-[11px] text-rose-400 bg-rose-950/40 p-2 rounded border border-rose-900/50">
            {uploadError}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
        {documents.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-500 px-4">
            no documents uploaded yet. upload a policy handbook or report to search.
          </div>
        ) : (
          documents.map((doc) => (
            <div
              key={doc.id}
              className="group flex items-center justify-between p-2 rounded-md hover:bg-slate-800/80 border border-transparent hover:border-slate-800 transition text-xs"
            >
              <div className="flex items-center gap-2 min-w-0 pr-2">
                <FileTextIcon className="w-4 h-4 text-slate-400 shrink-0" />
                <div className="truncate">
                  <div className="text-slate-200 truncate font-medium text-[12px]">{doc.filename}</div>
                  <div className="text-[10px] text-slate-500">
                    {formatFileSize(doc.file_size)} &bull; {doc.chunk_count} chunks
                  </div>
                </div>
              </div>
              <button
                onClick={() => onDeleteDocument(doc.id)}
                className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-rose-400 rounded transition"
                title="delete document"
              >
                <TrashIcon className="w-3.5 h-3.5" />
              </button>
            </div>
          ))
        )}
      </div>

      <div className="p-3 border-t border-slate-800">
        <MetricsPanel
          metrics={metrics}
          loading={metricsLoading}
          onRefresh={onRefreshMetrics}
        />
      </div>
    </aside>
  )
}
