import React, { useEffect, useState } from "react"
import Sidebar from "./components/Sidebar"
import ChatArea from "./components/ChatArea"

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000"

export default function App() {
  const [documents, setDocuments] = useState([])
  const [metrics, setMetrics] = useState(null)
  const [metricsLoading, setMetricsLoading] = useState(false)
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [backendConnected, setBackendConnected] = useState(false)

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`)
      setBackendConnected(res.ok)
    } catch {
      setBackendConnected(false)
    }
  }

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE}/documents`)
      if (res.ok) {
        const data = await res.json()
        setDocuments(data)
      }
    } catch {
      // silently ignore initial network error
    }
  }

  const fetchMetrics = async () => {
    setMetricsLoading(true)
    try {
      const res = await fetch(`${API_BASE}/metrics`)
      if (res.ok) {
        const data = await res.json()
        setMetrics(data)
      }
    } catch {
      // silently ignore metrics fetch error
    } finally {
      setMetricsLoading(false)
    }
  }

  useEffect(() => {
    checkHealth()
    fetchDocuments()
    fetchMetrics()
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleUploadDocument = async (file) => {
    setUploading(true)
    setUploadError(null)
    const formData = new FormData()
    formData.append("file", file)

    try {
      const res = await fetch(`${API_BASE}/documents/upload`, {
        method: "POST",
        body: formData,
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        setUploadError(err.detail || "upload failed")
        return
      }

      await fetchDocuments()
      fetchMetrics()
    } catch (err) {
      setUploadError("failed to connect to server for upload")
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteDocument = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/documents/${id}`, {
        method: "DELETE",
      })
      if (res.ok) {
        setDocuments((prev) => prev.filter((d) => d.id !== id))
        fetchMetrics()
      }
    } catch {
      // ignore delete network failure
    }
  }

  const handleSendMessage = async (questionText) => {
    const userMsg = { role: "user", content: questionText }
    setMessages((prev) => [...prev, userMsg])
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: questionText }),
      })

      if (res.status === 429) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "rate limit reached on free tier. please wait a few seconds before trying again.",
            isError: true,
            isRateLimit: true,
          },
        ])
        fetchMetrics()
        return
      }

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: err.detail || "an error occurred while processing your request.",
            isError: true,
            isRateLimit: false,
          },
        ])
        fetchMetrics()
        return
      }

      const data = await res.json()
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources || [],
          tools_used: data.tools_used || [],
          isError: false,
        },
      ])
      fetchMetrics()
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "could not connect to backend server. make sure the api service is running.",
          isError: true,
          isRateLimit: false,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-screen bg-slate-950 font-sans text-slate-100 overflow-hidden">
      <Sidebar
        documents={documents}
        metrics={metrics}
        metricsLoading={metricsLoading}
        onRefreshMetrics={fetchMetrics}
        onUploadDocument={handleUploadDocument}
        onDeleteDocument={handleDeleteDocument}
        uploading={uploading}
        uploadError={uploadError}
      />
      <ChatArea
        messages={messages}
        loading={loading}
        onSendMessage={handleSendMessage}
        backendConnected={backendConnected}
      />
    </div>
  )
}
