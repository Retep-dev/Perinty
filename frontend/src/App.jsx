import React, { useState } from 'react'
import { Bot, RefreshCw, Layers, ShieldCheck, Github, ExternalLink, HelpCircle } from 'lucide-react'
import DocumentUploader from './components/DocumentUploader'
import ChatWindow from './components/ChatWindow'

export default function App() {
  const backendUrl = 'http://localhost:8000'
  const [activeDocument, setActiveDocument] = useState(null)
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
    <div className="flex flex-col min-h-screen bg-[#090d16] text-slate-100">
      
      {/* Background Decorative Blobs */}
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-500/10 rounded-full blur-[120px] pointer-events-none"></div>

      {/* Navigation Header */}
      <header className="border-b border-slate-800/80 px-6 py-4 flex items-center justify-between glass z-10 sticky top-0">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/20">
            <Bot size={22} className="animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold font-outfit tracking-tight flex items-center gap-2">
              Perinty <span className="text-xs bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full font-semibold font-sans">RAG MVP</span>
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-400 hover:text-slate-200 transition-colors hidden sm:flex items-center gap-1.5 text-sm"
          >
            <Github size={16} />
            <span>Repository</span>
            <ExternalLink size={12} />
          </a>
          <div className="h-4 w-px bg-slate-800 hidden sm:block"></div>
          <div className="flex items-center gap-2 text-xs bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-slate-300">
            <ShieldCheck size={14} className="text-emerald-500" />
            <span>Upwork Showcase</span>
          </div>
        </div>
      </header>

      {/* Main Section */}
      <main className="flex-grow max-w-7xl w-full mx-auto px-4 md:px-8 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8 z-10">
        
        {/* Left Column: controls and uploader */}
        <section className="lg:col-span-4 flex flex-col gap-6">
          
          {/* Pitch Panel */}
          <div className="glass p-6 flex flex-col gap-3 relative overflow-hidden bg-gradient-to-br from-indigo-950/20 to-purple-950/20">
            <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-full blur-2xl"></div>
            <h2 className="text-sm font-semibold font-outfit uppercase tracking-wider text-indigo-400">Upwork Portfolio Showcase</h2>
            <h3 className="text-lg font-bold text-slate-100 font-outfit leading-snug">
              Secure Document Q&amp;A System (RAG)
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              This portfolio project demonstrates chunk parsing, local or Supabase pgvector embedding pipelines, similarity searching, and token streaming. 
            </p>
            <div className="flex flex-col gap-2 mt-2">
              <div className="flex items-center gap-2 text-xs text-slate-300">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400"></div>
                <span>Sentence Splitter Ingestion (512 overlap 64)</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-300">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400"></div>
                <span>Embedding Model: Gemini text-embedding-004</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-300">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400"></div>
                <span>LLM Generation: Gemini-1.5-Flash</span>
              </div>
            </div>
          </div>

          {/* Document Ingestion Card */}
          <DocumentUploader
            backendUrl={backendUrl}
            onUploadSuccess={handleUploadSuccess}
            onClearAll={handleClearAll}
          />
          
          {/* Quick Guide / Help */}
          <div className="glass p-6 flex flex-col gap-3">
            <h3 className="text-sm font-semibold font-outfit text-slate-200 flex items-center gap-2">
              <HelpCircle size={16} className="text-indigo-400" />
              Quick-Start Guide
            </h3>
            <ol className="text-xs text-slate-400 list-decimal pl-4 flex flex-col gap-2">
              <li>Upload a documentation file (e.g. <code>.txt</code> or <code>.md</code> FAQ format).</li>
              <li>Wait for the vector store indexing to complete successfully.</li>
              <li>Type queries in the chat window to get streamed answers with citations.</li>
              <li>Click the "Reset Store" button at any time to clear vector archives.</li>
            </ol>
          </div>

        </section>

        {/* Right Column: Chat Screen */}
        <section className="lg:col-span-8">
          <ChatWindow
            backendUrl={backendUrl}
            activeDocument={activeDocument}
          />
        </section>

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 px-6 py-4 mt-auto text-center text-xs text-slate-500">
        <p>&copy; {new Date().getFullYear()} Perinty. Built for Upwork Full-Stack AI Developer Showcase.</p>
      </footer>
    </div>
  )
}
