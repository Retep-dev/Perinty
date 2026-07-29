import React, { useState, useEffect } from 'react'
import { Bot, ShieldCheck, Github, ExternalLink, HelpCircle, User, LogIn, BarChart3, LogOut, Sun, Moon } from 'lucide-react'
import DocumentUploader from './components/DocumentUploader'
import ChatWindow from './components/ChatWindow'
import AuthModal from './components/AuthModal'
import AdminAnalytics from './components/AdminAnalytics'

export default function App() {
  const backendUrl = '/api'

  const [activeDocument, setActiveDocument] = useState(null)
  const [userId, setUserId] = useState('')
  const [authUser, setAuthUser] = useState(null)
  const [authModalOpen, setAuthModalOpen] = useState(false)
  const [analyticsOpen, setAnalyticsOpen] = useState(false)
  const [resetting, setResetting] = useState(false)
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('perinty_theme') || 'dark'
  })

  // Synchronize document theme class
  useEffect(() => {
    if (theme === 'light') {
      document.documentElement.classList.add('light')
    } else {
      document.documentElement.classList.remove('light')
    }
  }, [theme])

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(nextTheme)
    localStorage.setItem('perinty_theme', nextTheme)
  }

  // Initialize stored auth user session
  useEffect(() => {
    const saved = localStorage.getItem('perinty_auth_user')
    if (saved) {
      try {
        const userObj = JSON.parse(saved)
        setAuthUser(userObj)
        setUserId(userObj.id)
      } catch (e) {
        console.error('Failed to parse auth user', e)
      }
    }
  }, [])

  const handleAuthSuccess = (userObj) => {
    setAuthUser(userObj)
    setUserId(userObj.id)
  }

  const handleSignOut = () => {
    localStorage.removeItem('perinty_auth_user')
    setAuthUser(null)
    setUserId('')
  }

  const handleUploadSuccess = (fileName) => {
    setActiveDocument(fileName)
  }

  const handleClearAll = async () => {
    setResetting(true)
    try {
      const url = userId
        ? `${backendUrl}/clear?user_id=${encodeURIComponent(userId)}`
        : `${backendUrl}/clear`

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'X-User-ID': userId || '',
        },
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
    <div className={`flex flex-col min-h-screen ${theme === 'light' ? 'light-mode bg-[#f8fafc] text-slate-800' : 'bg-[#090d16] text-slate-100'} overflow-x-hidden selection:bg-indigo-500/30 transition-colors duration-300`}>

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
              Perinty <span className="text-xs bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full font-semibold font-sans shrink-0">RAG SaaS v3</span>
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-2.5 sm:gap-4 shrink-0">

          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            className="p-1.5 sm:px-3 sm:py-1.5 rounded-lg border border-slate-800 bg-slate-900/50 hover:bg-slate-900 text-slate-300 hover:text-white transition-all flex items-center gap-1.5 text-xs font-medium"
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          >
            {theme === 'dark' ? (
              <>
                <Sun size={15} className="text-amber-400 shrink-0" />
                <span className="hidden sm:inline">Light</span>
              </>
            ) : (
              <>
                <Moon size={15} className="text-indigo-400 shrink-0" />
                <span className="hidden sm:inline">Dark</span>
              </>
            )}
          </button>

          {/* Analytics Dashboard Trigger */}
          <button
            onClick={() => setAnalyticsOpen(true)}
            className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-slate-900 border border-slate-800 hover:border-indigo-500/40 px-3 py-1.5 rounded-lg transition-all"
            title="Open SaaS Analytics Dashboard"
          >
            <BarChart3 size={14} className="text-indigo-400" />
            <span className="hidden sm:inline">Analytics</span>
          </button>

          {/* Auth Button / Account Dropdown */}
          {authUser ? (
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5 text-xs bg-indigo-950/60 border border-indigo-900/60 text-indigo-300 px-3 py-1.5 rounded-lg">
                <User size={13} className="text-indigo-400" />
                <span className="max-w-[100px] truncate font-medium">{authUser.name}</span>
              </div>
              <button
                onClick={handleSignOut}
                className="text-slate-400 hover:text-rose-400 p-1.5 rounded-lg transition-colors border border-slate-800 bg-slate-900/40"
                title="Sign Out"
              >
                <LogOut size={14} />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setAuthModalOpen(true)}
              className="flex items-center gap-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white px-3.5 py-1.5 rounded-lg transition-all shadow-md shadow-indigo-600/20"
            >
              <LogIn size={14} />
              <span>Sign In</span>
            </button>
          )}

          <div className="h-4 w-px bg-slate-800 hidden md:block"></div>

          <a
            href="https://github.com/Retep-dev/Perinty/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-400 hover:text-slate-200 transition-colors hidden md:flex items-center gap-1.5 text-xs sm:text-sm"
          >
            <Github size={16} />
            <span>Repository</span>
            <ExternalLink size={12} />
          </a>
        </div>
      </header>

      {/* Main Section */}
      <main className="flex-grow max-w-[1440px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 z-10 min-w-0">

        {/* Left Column: controls and uploader */}
        <section className="lg:col-span-4 xl:col-span-3 flex flex-col gap-6 min-w-0">

          {/* Pitch Panel */}
          <div className="glass p-5 sm:p-6 flex flex-col gap-3 relative overflow-hidden bg-gradient-to-br from-indigo-950/20 to-purple-950/20">
            <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-full blur-2xl pointer-events-none"></div>
            <h2 className="text-xs font-semibold font-outfit uppercase tracking-wider text-indigo-400">Perinty - Chat with your document</h2>
            <h3 className="text-base sm:text-lg font-bold text-slate-100 font-outfit leading-snug">
              Multi-Tenant SaaS Document Q&amp;A (RAG)
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Perinty adds Supabase Auth &amp; Row-Level Security multi-tenancy, user-scoped RAG vector isolation, and SaaS Admin Analytics.
            </p>
            <div className="flex flex-col gap-2 mt-1">
              <div className="flex items-center gap-2 text-xs text-slate-300 min-w-0">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0"></div>
                <span className="truncate">Supabase RLS Multi-Tenancy</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-300 min-w-0">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0"></div>
                <span className="truncate">User-Scoped pgvector Search</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-300 min-w-0">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0"></div>
                <span className="truncate">SaaS Admin Analytics Dashboard</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-300 min-w-0">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0"></div>
                <span className="truncate">Langfuse LLM Observability</span>
              </div>
            </div>
          </div>

          {/* Document Ingestion Card */}
          <DocumentUploader
            backendUrl={backendUrl}
            userId={userId}
            activeDocument={activeDocument}
            onSelectDocument={setActiveDocument}
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
              SaaS Quick-Guide
            </h3>
            <ol className="text-xs text-slate-300 list-decimal pl-4 flex flex-col gap-3 leading-relaxed">
              <li>Click <strong className="text-indigo-400">Sign In</strong> or set a User ID to authenticate your session.</li>
              <li>Upload private documents — files are isolated to your user ID.</li>
              <li>Open <strong className="text-indigo-400">Analytics</strong> in the header to view vector &amp; query usage statistics.</li>
              <li>Query the chat; context is retrieved strictly from your tenant store.</li>
            </ol>

            <div className="mt-2 pt-3 border-t border-slate-800/80 flex flex-col gap-2">
              <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-500">SaaS Stack Badges</span>
              <div className="flex flex-wrap gap-1.5 text-[11px] text-slate-400">
                <span className="bg-slate-900/80 border border-slate-800 px-2 py-0.5 rounded text-indigo-300">Supabase Auth</span>
                <span className="bg-slate-900/80 border border-slate-800 px-2 py-0.5 rounded text-emerald-300">RLS Multi-Tenant</span>
                <span className="bg-slate-900/80 border border-slate-800 px-2 py-0.5 rounded text-purple-300">Langfuse</span>
                <span className="bg-slate-900/80 border border-slate-800 px-2 py-0.5 rounded">GitHub CI/CD</span>
                <span className="bg-slate-900/80 border border-slate-800 px-2 py-0.5 rounded">pgvector HNSW</span>
              </div>
            </div>
          </div>

        </section>

      </main>

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
      />

      {/* Admin Analytics Dashboard Modal */}
      <AdminAnalytics
        backendUrl={backendUrl}
        userId={userId}
        isOpen={analyticsOpen}
        onClose={() => setAnalyticsOpen(false)}
      />

      {/* Footer */}
      <footer className="border-t border-slate-900 px-6 py-4 mt-auto text-center text-xs text-slate-500">
        <p>&copy; {new Date().getFullYear()} Perinty. Built by Afolabi Peter.</p>
      </footer>
    </div>
  )
}
