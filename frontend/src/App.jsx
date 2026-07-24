import React, { useState } from 'react'
import { Bot, ShieldCheck, Github, ExternalLink, HelpCircle } from 'lucide-react'
import DocumentUploader from './components/DocumentUploader'
import ChatWindow from './components/ChatWindow'

export default function App() {
  const backendUrl = '/api'

  const [activeDocument, setActiveDocument] = useState(null)
  const [userId, setUserId] = useState('')
  const [resetting, setResetting] = useState(false)

  const handleUploadSuccess = (fileName) => {
    setActiveDocument(fileName)
  }

  const handleClearAll = async () => {
    setResetting(true)
    try {
      const response = await fetch(`${backendUrl}/clear`, {
        method: 'POST',
      })
      if (response.ok) {
        setActiveDocument(null)
        alert('Knowledge base successfully cleared!')
      } else {
        alert('Failed to clear knowledge base.')
      }
    } catch (err) {
      console.error(err)
      alert('Error connecting to backend server.')
    } finally {
      setResetting(false)
    }
  }

  return (
    <div className="flex flex-col min-h-screen bg-[#090d16] text-slate-100 overflow-x-hidden selection:bg-indigo-500/30">

      {/* Background Decorative Blobs */}
      <div className="fixed top-[-10%] left-[-10%] w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="fixed bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-500/10 rounded-full blur-[120px] pointer-events-none"></div>

      {/* Navigation Header */}
      <header className="border-b border-slate-800/80 px-4 sm:px-8 py-3.5 flex items-center justify-between glass z-20 sticky top-0">
        <div className="flex items-center gap-3 min-w-0">
          <div className="p-2 sm:p-2.5 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/20 shrink-0">
            <Bot size={20} className="animate-pulse sm:w-5.5 sm:h-5.5" />
          </div>
          <div className="min-w-0">
            <h1 className="text-lg sm:text-xl font-bold font-outfit tracking-tight flex items-center gap-2 truncate">
              Perinty <span className="text-xs bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full font-semibold font-sans shrink-0">RAG v2</span>
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3 sm:gap-4 shrink-0">
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-400 hover:text-slate-200 transition-colors hidden sm:flex items-center gap-1.5 text-xs sm:text-sm"
          >
            <Github size={16} />
            <span>Repository</span>
            <ExternalLink size={12} />
          </a>
          <div className="h-4 w-px bg-slate-800 hidden sm:block"></div>
          <div className="flex items-center gap-1.5 sm:gap-2 text-[11px] sm:text-xs bg-slate-900 border border-slate-800 px-2.5 sm:px-3 py-1.5 rounded-lg text-slate-300">
            <ShieldCheck size={14} className="text-emerald-500 shrink-0" />
            <span>Upwork Showcase</span>
          </div>
        </div>
      </header>

      {/* Main Section */}
      <main className="flex-grow max-w-[1440px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 z-10 min-w-0">

        {/* Left Column: controls and uploader */}
        <section className="lg:col-span-4 xl:col-span-3 flex flex-col gap-6 min-w-0">

          {/* Pitch Panel */}
          <div className="glass p-5 sm:p-6 flex flex-col gap-3 relative overflow-hidden bg-gradient-to-br from-indigo-950/20 to-purple-950/20">
            <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-full blur-2xl pointer-events-none"></div>
            <h2 className="text-xs font-semibold font-outfit uppercase tracking-wider text-indigo-400">Upwork Portfolio Showcase</h2>
            <h3 className="text-base sm:text-lg font-bold text-slate-100 font-outfit leading-snug">
              Secure Document Q&amp;A System (RAG)
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Phase 2 adds Supabase pgvector persistence, multi-format document parsing, per-document management, and persistent chat memory.
            </p>
            <div className="flex flex-col gap-2 mt-1">
              <div className="flex items-center gap-2 text-xs text-slate-300 min-w-0">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0"></div>
                <span className="truncate">Supabase pgvector persistence</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-300 min-w-0">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0"></div>
                <span className="truncate">Multi-format: PDF, DOCX, HTML, CSV, TXT, MD, JSON</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-300 min-w-0">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0"></div>
                <span className="truncate">Per-user persistent chat memory</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-300 min-w-0">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0"></div>
                <span className="truncate">LLM: meta/llama-3.1-8b-instruct</span>
              </div>
            </div>
          </div>

          {/* Document Ingestion Card */}
          <DocumentUploader
            backendUrl={backendUrl}
            onUploadSuccess={handleUploadSuccess}
            onClearAll={handleClearAll}
          />

        </section>

        {/* Right Section: Chat Screen & Quick-Start Guide side-by-side */}
        <section className="lg:col-span-8 xl:col-span-9 flex flex-col xl:flex-row gap-6 items-start min-w-0">
          
          {/* Chat Window */}
          <div className="flex-grow w-full min-w-0">
            <ChatWindow
              backendUrl={backendUrl}
              activeDocument={activeDocument}
              userId={userId}
              setUserId={setUserId}
            />
          </div>

          {/* Quick Guide / Help Panel on the right side */}
          <div className="glass p-5 sm:p-6 flex flex-col gap-4 w-full xl:w-72 shrink-0">
            <h3 className="text-sm font-semibold font-outfit text-slate-200 flex items-center gap-2 border-b border-slate-800/80 pb-3">
              <HelpCircle size={18} className="text-indigo-400 shrink-0" />
              Quick-Start Guide
            </h3>
            <ol className="text-xs text-slate-300 list-decimal pl-4 flex flex-col gap-3 leading-relaxed">
              <li>Enter a <strong className="text-indigo-400">User ID</strong> above the chat to enable session memory.</li>
              <li>Upload documentation files (<code className="text-[10px] bg-slate-900 border border-slate-800 px-1 py-0.5 rounded text-indigo-300">PDF, DOCX, CSV...</code>).</li>
              <li>Manage documents in the sidebar — delete individual files anytime.</li>
              <li>Ask questions in the chat; prior turns in the session are remembered.</li>
            </ol>

            <div className="mt-2 pt-3 border-t border-slate-800/80 flex flex-col gap-2">
              <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-500">System Capabilities</span>
              <div className="flex flex-wrap gap-1.5 text-[11px] text-slate-400">
                <span className="bg-slate-900/80 border border-slate-800 px-2 py-0.5 rounded text-indigo-300">GitHub CI/CD</span>
                <span className="bg-slate-900/80 border border-slate-800 px-2 py-0.5 rounded text-purple-300">Langfuse Tracing</span>
                <span className="bg-slate-900/80 border border-slate-800 px-2 py-0.5 rounded">pgvector</span>
                <span className="bg-slate-900/80 border border-slate-800 px-2 py-0.5 rounded">NVIDIA NIM</span>
                <span className="bg-slate-900/80 border border-slate-800 px-2 py-0.5 rounded">Llama 3.1 8B</span>
                <span className="bg-slate-900/80 border border-slate-800 px-2 py-0.5 rounded">Citations</span>
              </div>
            </div>
          </div>

        </section>

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 px-6 py-4 mt-auto text-center text-xs text-slate-500">
        <p>&copy; {new Date().getFullYear()} Perinty. Built for Upwork Full-Stack AI Developer Showcase.</p>
      </footer>
    </div>
  )
}
