import React, { useState, useEffect } from 'react'
import { BarChart3, Database, FileText, MessageSquare, Layers, RefreshCw, X } from 'lucide-react'

export default function AdminAnalytics({ backendUrl, userId, isOpen, onClose }) {
  const [stats, setStats] = useState({
    total_documents: 0,
    total_chunks: 0,
    total_messages: 0,
    active_sessions: 0,
  })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isOpen) {
      fetchAnalytics()
    }
  }, [isOpen, userId])

  const fetchAnalytics = async () => {
    setLoading(true)
    try {
      const url = userId
        ? `${backendUrl}/analytics?user_id=${encodeURIComponent(userId)}`
        : `${backendUrl}/analytics`

      const response = await fetch(url, {
        headers: {
          'X-User-ID': userId || '',
        },
      })
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (err) {
      console.error('Failed to load analytics', err)
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="glass w-full max-w-2xl p-6 sm:p-8 flex flex-col gap-6 relative border border-slate-800 shadow-2xl bg-[#0e1424]">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/10 rounded-xl text-indigo-400">
              <BarChart3 size={22} />
            </div>
            <div>
              <h2 className="text-lg font-bold font-outfit text-slate-100">
                SaaS Admin Analytics
              </h2>
              <p className="text-xs text-slate-400">
                Real-time usage telemetry &amp; vector storage metrics for{' '}
                <span className="text-indigo-400 font-semibold">{userId || 'All Tenants'}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchAnalytics}
              className="p-2 text-slate-400 hover:text-slate-200 border border-slate-800 rounded-lg bg-slate-900/50 hover:bg-slate-900 transition-all"
              title="Refresh telemetry"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-200 border border-slate-800 rounded-lg bg-slate-900/50 hover:bg-slate-900 transition-all"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {/* Card 1: Documents */}
          <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex flex-col gap-1.5">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium">Documents</span>
              <FileText size={16} className="text-indigo-400" />
            </div>
            <div className="text-2xl font-bold text-slate-100 font-outfit">
              {stats.total_documents}
            </div>
            <span className="text-[10px] text-slate-500">Source files indexed</span>
          </div>

          {/* Card 2: Chunks */}
          <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex flex-col gap-1.5">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium">Vector Chunks</span>
              <Layers size={16} className="text-purple-400" />
            </div>
            <div className="text-2xl font-bold text-slate-100 font-outfit">
              {stats.total_chunks}
            </div>
            <span className="text-[10px] text-slate-500">1024-dim pgvector rows</span>
          </div>

          {/* Card 3: Chat Messages */}
          <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex flex-col gap-1.5">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium">Chat Turns</span>
              <MessageSquare size={16} className="text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-slate-100 font-outfit">
              {stats.total_messages}
            </div>
            <span className="text-[10px] text-slate-500">LLM Q&amp;A history logs</span>
          </div>

          {/* Card 4: Active Sessions */}
          <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex flex-col gap-1.5">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium">Sessions</span>
              <Database size={16} className="text-cyan-400" />
            </div>
            <div className="text-2xl font-bold text-slate-100 font-outfit">
              {stats.active_sessions}
            </div>
            <span className="text-[10px] text-slate-500">Unique conversation IDs</span>
          </div>
        </div>

        {/* Telemetry Footer */}
        <div className="p-4 bg-indigo-950/20 border border-indigo-900/40 rounded-xl flex flex-col gap-2">
          <h4 className="text-xs font-semibold text-indigo-300 font-outfit uppercase tracking-wider">
            System Telemetry &amp; Monitoring
          </h4>
          <p className="text-xs text-slate-400 leading-relaxed">
            All vector queries are tracked using Supabase PostgreSQL HNSW indexing and Langfuse LLM Observability.
          </p>
        </div>

      </div>
    </div>
  )
}
