import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, CornerDownLeft, Sparkles, HelpCircle, FileText } from 'lucide-react'

export default function ChatWindow({ backendUrl, activeDocument }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I am your Support Assistant. Upload your documentation in the sidebar, and I will answer questions strictly based on the content.',
    }
  ])
  const [input, setInput] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isGenerating])

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim() || isGenerating) return

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
        body: JSON.stringify({ message: userMessageText }),
      })

      if (!response.ok) {
        throw new Error('Failed to generate response')
      }

      // Stream the response reader
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let done = false
      let accumulatedText = ''
      let sources = []

      while (!done) {
        const { value, done: readerDone } = await reader.read()
        done = readerDone
        if (value) {
          const chunk = decoder.decode(value, { stream: !done })
          accumulatedText += chunk

          // Check if we hit the sources delimiter
          if (accumulatedText.includes('|||SOURCES|||')) {
            const parts = accumulatedText.split('|||SOURCES|||')
            const textResponse = parts[0]
            const sourcesJson = parts[1]

            accumulatedText = textResponse // Only show LLM text before delimiter

            if (sourcesJson) {
              try {
                sources = JSON.parse(sourcesJson)
              } catch (e) {
                console.error("Error parsing sources JSON", e)
              }
            }
          }

          // Update assistant message text in real time
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? { ...msg, content: accumulatedText, sources: sources }
                : msg
            )
          )
        }
      }
    } catch (err) {
      console.error(err)
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? { 
                ...msg, 
                content: 'Failed to complete query. Please ensure the backend server is running and your Gemini API key is configured.' 
              }
            : msg
        )
      )
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="glass flex flex-col h-[650px] overflow-hidden">
      {/* Header */}
      <div className="border-b border-slate-800/80 px-6 py-4 flex items-center justify-between bg-slate-950/20">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400">
            <Bot size={20} />
          </div>
          <div>
            <h2 className="font-semibold text-slate-100 font-outfit text-sm md:text-base">Support Copilot</h2>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={`w-2 h-2 rounded-full ${activeDocument ? 'bg-emerald-500 animate-pulse' : 'bg-slate-600'}`}></span>
              <span className="text-xs text-slate-400 truncate max-w-[200px]">
                {activeDocument ? `Indexed: ${activeDocument}` : 'No document uploaded'}
              </span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-1 text-slate-400 text-xs bg-slate-900 px-3 py-1.5 rounded-full border border-slate-800">
          <Sparkles size={12} className="text-indigo-400" />
          <span>Gemini-1.5-Flash</span>
        </div>
      </div>

      {/* Messages Scroll Feed */}
      <div className="flex-grow overflow-y-auto p-6 flex flex-col gap-6 bg-slate-950/5">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 max-w-[85%] ${
              msg.role === 'user' ? 'self-end flex-row-reverse' : 'self-start'
            }`}
          >
            {/* Avatar */}
            <div className={`p-2 h-9 w-9 rounded-full flex items-center justify-center shrink-0 border ${
              msg.role === 'user' 
                ? 'bg-slate-800 border-slate-700 text-slate-100' 
                : 'bg-indigo-950/60 border-indigo-900/60 text-indigo-400'
            }`}>
              {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
            </div>

            {/* Bubble */}
            <div className="flex flex-col gap-2">
              <div className={`p-4 rounded-2xl text-sm leading-relaxed ${
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
                <div className="flex flex-col gap-1.5 mt-1">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1 pl-1">
                    <FileText size={10} /> Reference Sources
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {msg.sources.map((src) => (
                      <div 
                        key={src.index}
                        title={src.snippet}
                        className="text-xs bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-lg p-2 max-w-[240px] truncate cursor-help transition-all"
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
      <form onSubmit={handleSend} className="p-4 border-t border-slate-800 bg-slate-900/20 flex gap-3 items-center">
        <div className="relative flex-grow">
          <input
            id="chat-input-text"
            type="text"
            placeholder={activeDocument ? "Ask anything about the document..." : "Upload a document in the sidebar to start querying..."}
            value={input}
            disabled={!activeDocument || isGenerating}
            onChange={(e) => setInput(e.target.value)}
            className="w-full bg-slate-950/60 border border-slate-800 focus:border-indigo-500/50 rounded-xl py-3 pl-4 pr-12 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500/20 disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-300"
          />
          <span className="absolute right-3.5 top-3.5 text-xs text-slate-500 flex items-center gap-1 hidden md:flex">
            <CornerDownLeft size={12} />
          </span>
        </div>

        <button
          id="btn-chat-send"
          type="submit"
          disabled={!input.trim() || isGenerating}
          className="p-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-300 hover:scale-[1.02]"
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  )
}
