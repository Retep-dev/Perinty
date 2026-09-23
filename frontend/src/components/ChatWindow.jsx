import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, CornerDownLeft, Sparkles, FileText, PlusCircle, History } from 'lucide-react'
import { parseStream } from '../stream'

export default function ChatWindow({ backendUrl, activeDocument, userId, setUserId, hasDocuments }) {
  const [sessionId, setSessionId] = useState(() => {
    // Reuse session id across refreshes for the same browser tab session
    const existing = sessionStorage.getItem('perinty_session_id')
    if (existing) return existing
    const fresh = crypto.randomUUID()
    sessionStorage.setItem('perinty_session_id', fresh)
    return fresh
  })

  const [pastSessions, setPastSessions] = useState([])
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I am your Support Assistant. Upload your documentation in the sidebar, and I will answer questions strictly based on the content. Enter your User ID above to start.',
    }
  ])
  const [input, setInput] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [historyLoaded, setHistoryLoaded] = useState(false)

  const messagesEndRef = useRef(null)

  const fetchPastSessions = async (targetUser) => {
    if (!targetUser || !targetUser.trim()) return
    try {
      const res = await fetch(`${backendUrl}/chat/sessions/${encodeURIComponent(targetUser.trim())}`)
      if (res.ok) {
        const data = await res.json()
        setPastSessions(data.sessions || [])
      }
    } catch (e) {
      console.error('Failed to fetch past sessions', e)
    }
  }

  const handleNewChat = () => {
    const fresh = crypto.randomUUID()
    sessionStorage.setItem('perinty_session_id', fresh)
    setSessionId(fresh)
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: 'Started a fresh chat session! Your uploaded documents and user login remain active. Ask me anything.',
      }
    ])
    if (userId.trim()) {
      setTimeout(() => fetchPastSessions(userId), 500)
    }
  }

  const scrollToBottom = () => {
    // Keep chat scrolling inside its panel, including in the landing preview.
    const panel = messagesEndRef.current?.parentElement
    panel?.scrollTo({ top: panel.scrollHeight, behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isGenerating])

  // Load chat history and past session list when userId or sessionId changes
  useEffect(() => {
    if (!userId.trim()) {
      setHistoryLoaded(false)
      setPastSessions([])
      setMessages([])
      return
    }

    fetchPastSessions(userId)

    const loadHistory = async () => {
      try {
        const response = await fetch(
          `${backendUrl}/chat/history/${encodeURIComponent(userId)}?session_id=${encodeURIComponent(sessionId)}`
        )
        if (response.ok) {
          const data = await response.json()
          const history = (data.messages || []).map((msg) => ({
            id: msg.id,
            role: msg.role,
            content: msg.content,
            sources: msg.sources || [],
          }))
          setMessages([
            {
              id: 'welcome',
              role: 'assistant',
              content: `Welcome back, ${userId}. Loaded session ${sessionId.slice(0, 8)}...`,
            },
            ...history,
          ])
        }
      } catch (err) {
        console.error('Failed to load chat history', err)
      } finally {
        setHistoryLoaded(true)
      }
    }

    loadHistory()
  }, [userId, sessionId, backendUrl])

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim() || isGenerating || !hasDocuments) return
    if (!userId.trim()) {
      alert('Please enter a User ID above the chat.')
      return
    }

    const userMessageText = input.trim()
    setInput('')
    setIsGenerating(true)

    // Append user message
    const userMsgId = Date.now().toString()
    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: 'user', content: userMessageText }
    ])

    // Setup placeholder assistant message
    const assistantMsgId = (Date.now() + 1).toString()
    setMessages((prev) => [
      ...prev,
      { id: assistantMsgId, role: 'assistant', content: '', sources: [] }
    ])

    try {
      const response = await fetch(`${backendUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessageText,
          user_id: userId,
          session_id: sessionId,
          active_document: activeDocument,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to generate response')
      }

      // Stream the response reader
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let done = false
      let rawStreamText = ''
      let parsedSources = []

      while (!done) {
        const { value, done: readerDone } = await reader.read()
        done = readerDone
        if (value) {
          const chunk = decoder.decode(value, { stream: !done })
          rawStreamText += chunk

          const parsed = parseStream(rawStreamText)
          const displayContent = parsed.content
          parsedSources = parsed.sources

          // Update assistant message text in real time
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? { ...msg, content: displayContent, sources: parsedSources }
                : msg
            )
          )
        }
      }
      rawStreamText += decoder.decode()
      const final = parseStream(rawStreamText, true)
      setMessages((prev) => prev.map((msg) => msg.id === assistantMsgId ? { ...msg, content: final.content, sources: final.sources } : msg))
    } catch (err) {
      console.error(err)
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                content: 'Failed to complete query. Please ensure the backend server is running and your NVIDIA API key is configured.'
              }
            : msg
        )
      )
    } finally {
      setIsGenerating(false)
      if (userId.trim()) {
        fetchPastSessions(userId)
      }
    }
  }

  // Ensure current active session is always in the dropdown list
  const displaySessions = [...pastSessions]
  if (!displaySessions.some(s => s.session_id === sessionId)) {
    displaySessions.unshift({
      session_id: sessionId,
      last_message: 'Active conversation',
    })
  }

  return (
    <div className="glass flex flex-col h-[600px] sm:h-[650px] lg:h-[700px] w-full min-w-0 overflow-hidden">
      {/* Header */}
      <div className="border-b border-slate-800/80 px-4 sm:px-6 py-3.5 flex flex-wrap items-center justify-between gap-3 bg-slate-950/20">
        <div className="flex items-center gap-3 min-w-0">
          <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400 shrink-0">
            <Bot size={20} />
          </div>
          <div className="min-w-0">
            <h2 className="font-semibold text-slate-100 font-outfit text-sm md:text-base truncate">Support Copilot</h2>
            <div className="flex items-center gap-1.5 mt-0.5 min-w-0">
              <span className={`w-2 h-2 rounded-full shrink-0 ${activeDocument ? 'bg-emerald-500 animate-pulse' : 'bg-slate-600'}`}></span>
              <span className="text-xs text-slate-400 truncate max-w-[180px] sm:max-w-[280px]">
                {activeDocument ? `Indexed: ${activeDocument}` : hasDocuments ? 'All Documents' : 'No document uploaded'}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1 text-slate-400 text-xs bg-slate-900 px-2.5 sm:px-3 py-1.5 rounded-full border border-slate-800 shrink-0">
          <Sparkles size={12} className="text-indigo-400 shrink-0" />
          <span>NVIDIA NIM</span>
        </div>
      </div>

      {/* User ID bar */}
      <div className="px-4 sm:px-6 py-2.5 border-b border-slate-800/80 bg-slate-900/30 flex flex-wrap items-center gap-2 sm:gap-3">
        <label htmlFor="user-id" className="text-xs text-slate-400 font-medium shrink-0">User ID</label>
        <input
          id="user-id"
          type="text"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          placeholder="e.g. alice"
          className="bg-slate-950/60 border border-slate-800 focus:border-indigo-500/50 rounded-lg px-3 py-1 text-xs sm:text-sm text-slate-100 placeholder-slate-600 focus:outline-none w-36 sm:w-48 shrink-0"
        />
        <span className="text-[11px] text-slate-500 truncate hidden md:inline">
          Session: {sessionId.slice(0, 8)}...
        </span>
        {!historyLoaded && userId.trim() && (
          <span className="text-[11px] text-indigo-400 animate-pulse shrink-0">Loading...</span>
        )}

        <div className="ml-auto flex items-center gap-2 shrink-0">
          <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 rounded-lg px-2 py-0.5">
            <History size={13} className="text-indigo-400 shrink-0" />
            <select
              value={sessionId}
              onChange={(e) => {
                const selectedSid = e.target.value
                sessionStorage.setItem('perinty_session_id', selectedSid)
                setSessionId(selectedSid)
              }}
              className="bg-transparent text-slate-300 text-xs font-medium focus:outline-none max-w-[140px] sm:max-w-[190px] truncate cursor-pointer py-0.5"
              title="Switch to a past conversation session"
            >
              {displaySessions.map((s) => (
                <option key={s.session_id} value={s.session_id} className="bg-slate-950 text-slate-200">
                  {s.session_id === sessionId ? '▶ ' : ''}{s.last_message || `Session ${s.session_id.slice(0, 6)}`}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleNewChat}
            className="flex items-center gap-1.5 text-xs text-indigo-300 hover:text-white bg-indigo-600/20 hover:bg-indigo-600/40 border border-indigo-500/30 px-2.5 py-1 rounded-lg transition-all shadow-sm font-medium shrink-0"
            title="Start a new chat session without logging out"
          >
            <PlusCircle size={14} className="text-indigo-400" />
            <span className="hidden sm:inline">New Chat</span>
          </button>
        </div>
      </div>

      {/* Messages Scroll Feed */}
      <div className="flex-grow overflow-y-auto p-4 sm:p-6 flex flex-col gap-4 sm:gap-6 bg-slate-950/5 min-w-0">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-2.5 sm:gap-3 max-w-[92%] sm:max-w-[85%] min-w-0 ${
              msg.role === 'user' ? 'self-end flex-row-reverse' : 'self-start'
            }`}
          >
            {/* Avatar */}
            <div className={`p-2 h-8 w-8 sm:h-9 sm:w-9 rounded-full flex items-center justify-center shrink-0 border ${
              msg.role === 'user'
                ? 'bg-slate-800 border-slate-700 text-slate-100'
                : 'bg-indigo-950/60 border-indigo-900/60 text-indigo-400'
            }`}>
              {msg.role === 'user' ? <User size={15} /> : <Bot size={15} />}
            </div>

            {/* Bubble */}
            <div className="flex flex-col gap-2 min-w-0 max-w-full">
              <div className={`p-3.5 sm:p-4 rounded-2xl text-xs sm:text-sm leading-relaxed break-words overflow-hidden ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white rounded-tr-none'
                  : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none'
              }`}>
                {msg.content || (isGenerating && msg.id === messages[messages.length - 1].id ? (
                  <span className="flex gap-1.5 items-center py-1">
                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </span>
                ) : null)}
              </div>

              {/* Citations / Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="flex flex-col gap-1.5 mt-1 min-w-0 max-w-full">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1 pl-1">
                    <FileText size={10} /> Reference Sources
                  </span>
                  <div className="flex flex-wrap gap-2 max-w-full overflow-hidden">
                    {msg.sources.map((src) => (
                      <div
                        key={src.index}
                        title={src.snippet}
                        className="text-xs bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-lg p-2 max-w-full sm:max-w-[240px] truncate cursor-help transition-all"
                      >
                        <span className="inline-block bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-[10px] px-1.5 py-0.5 rounded mr-1.5 font-bold">
                          {src.index}
                        </span>
                        <span className="text-slate-300 font-medium">{src.file_name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Tray */}
      <form onSubmit={handleSend} className="p-3 sm:p-4 border-t border-slate-800 bg-slate-900/20 flex gap-2 sm:gap-3 items-center w-full min-w-0">
        <div className="relative flex-grow min-w-0">
          <input
            id="chat-input-text"
            type="text"
            placeholder={hasDocuments ? "Ask anything about your documents..." : "Upload a document in the sidebar to start querying..."}
            value={input}
            disabled={!hasDocuments || !userId.trim() || isGenerating}
            onChange={(e) => setInput(e.target.value)}
            className="w-full bg-slate-950/60 border border-slate-800 focus:border-indigo-500/50 rounded-xl py-2.5 sm:py-3 pl-3.5 sm:pl-4 pr-10 sm:pr-12 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500/20 disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-300 min-w-0"
          />
          <span className="absolute right-3.5 top-3.5 text-xs text-slate-500 flex items-center gap-1 hidden sm:flex">
            <CornerDownLeft size={12} />
          </span>
        </div>

        <button
          id="btn-chat-send"
          type="submit"
          disabled={!hasDocuments || !userId.trim() || !input.trim() || isGenerating}
          className="p-2.5 sm:p-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-300 hover:scale-[1.02] shrink-0"
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  )
}
