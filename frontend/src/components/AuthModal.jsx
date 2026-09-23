import React, { useState } from 'react'
import { X, LogIn, UserPlus, Lock, Mail, ShieldCheck } from 'lucide-react'

export default function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (!isOpen) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email.trim()) {
      setError('Please enter a demo identity.')
      return
    }

    setLoading(true)
    setError('')

    try {
      // Simulate auth account generation / guest authentication fallback
      const userId = email.trim().toLowerCase().split('@')[0]
      const authUser = {
        id: userId,
        email: email.trim(),
        name: userId.charAt(0).toUpperCase() + userId.slice(1),
      }

      localStorage.setItem('perinty_auth_user', JSON.stringify(authUser))
      onAuthSuccess(authUser)
      onClose()
    } catch (err) {
      console.error(err)
      setError('Could not save the demo identity. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleGuestLogin = () => {
    const guestId = `guest_${Math.floor(1000 + Math.random() * 9000)}`
    const guestUser = {
      id: guestId,
      email: `${guestId}@perinty.demo`,
      name: `Guest User (${guestId.slice(-4)})`,
      isGuest: true,
    }
    localStorage.setItem('perinty_auth_user', JSON.stringify(guestUser))
    onAuthSuccess(guestUser)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="glass w-full max-w-md p-6 sm:p-8 flex flex-col gap-6 relative border border-slate-800 shadow-2xl bg-[#0e1424]">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-200 p-1.5 rounded-lg transition-colors"
        >
          <X size={18} />
        </button>

        {/* Title */}
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider">
            <ShieldCheck size={16} />
            <span>Perinty Demo Identity</span>
          </div>
          <h2 className="text-xl font-bold font-outfit text-slate-100">
            Choose a Demo Identity
          </h2>
          <p className="text-xs text-slate-400">
            This is not authentication. Anyone who knows a User ID can access its data. Use only non-sensitive demo documents.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs rounded-lg">
              {error}
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
              <Mail size={12} className="text-indigo-400" />
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. dev@company.com"
              className="bg-slate-950/80 border border-slate-800 focus:border-indigo-500/50 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-3 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20"
          >
            <LogIn size={16} />
            <span>{loading ? 'Saving...' : 'Use Demo Identity'}</span>
          </button>
        </form>

        <div className="relative flex items-center justify-center my-1">
          <div className="border-t border-slate-800 w-full"></div>
          <span className="bg-[#0e1424] px-3 text-[10px] text-slate-500 uppercase font-semibold">Or</span>
        </div>

        {/* Guest Access Button */}
        <button
          onClick={handleGuestLogin}
          className="w-full py-2.5 border border-slate-700 hover:border-slate-600 bg-slate-900/60 hover:bg-slate-900 text-slate-300 text-xs font-medium rounded-xl transition-all flex items-center justify-center gap-2"
        >
          <span>Continue as Guest User</span>
        </button>

      </div>
    </div>
  )
}
