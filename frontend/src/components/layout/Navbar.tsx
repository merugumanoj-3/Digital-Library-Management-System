// FILE: src/components/layout/Navbar.tsx
import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BookOpen, Sun, Moon, Bell, User, Settings, LogOut,
  Shield, Menu, X, Sparkles, Library,
} from 'lucide-react'
import { useAuthStore, useThemeStore } from '@/store'
import { usersApi } from '@/api'
import { useQuery } from '@tanstack/react-query'
import { getInitials } from '@/utils'
import type { Notification } from '@/types'

export default function Navbar() {
  const { isAuthenticated, user, clearAuth } = useAuthStore()
  const { theme, toggleTheme } = useThemeStore()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [notifOpen, setNotifOpen] = useState(false)
  const dropRef = useRef<HTMLDivElement>(null)
  const notifRef = useRef<HTMLDivElement>(null)

  const { data: notifData } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => usersApi.getNotifications().then((r) => r.data),
    enabled: isAuthenticated,
    refetchInterval: 60_000,
  })

  const notifications: Notification[] = notifData || []
  const unreadCount = notifications.filter((n) => !n.is_read).length

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropRef.current && !dropRef.current.contains(e.target as Node)) setDropdownOpen(false)
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) setNotifOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const handleLogout = () => {
    clearAuth()
    navigate('/')
  }

  return (
    <header className="fixed top-0 inset-x-0 z-40 glass border-b border-white/5">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 shrink-0">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-purple-600 to-blue-500 flex items-center justify-center shadow-lg shadow-purple-500/30">
            <BookOpen size={16} className="text-white" />
          </div>
          <span className="text-lg font-bold gradient-text hidden sm:block">LIBRIX AI</span>
        </Link>

        {/* Desktop nav links */}
        <div className="hidden md:flex items-center gap-1">
          <Link
            to="/library"
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-slate-300 hover:text-white hover:bg-white/5 transition-colors"
          >
            <Library size={15} />
            Library
          </Link>
          {isAuthenticated && (
            <Link
              to="/ai"
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-slate-300 hover:text-white hover:bg-white/5 transition-colors"
            >
              <Sparkles size={15} />
              AI Assistant
            </Link>
          )}
        </div>

        {/* Right side */}
        <div className="flex items-center gap-2">
          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-all"
            title="Toggle theme"
          >
            {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
          </button>

          {!isAuthenticated ? (
            <>
              <Link
                to="/login"
                className="hidden sm:inline-flex px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors rounded-xl hover:bg-white/5"
              >
                Login
              </Link>
              <Link
                to="/register"
                className="inline-flex px-4 py-2 text-sm font-semibold rounded-xl bg-gradient-to-r from-purple-600 to-blue-500 text-white hover:opacity-90 transition-opacity shadow-lg shadow-purple-500/20"
              >
                Register
              </Link>
            </>
          ) : (
            <>
              {/* Notifications */}
              <div className="relative" ref={notifRef}>
                <button
                  onClick={() => setNotifOpen((v) => !v)}
                  className="relative p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-all"
                >
                  <Bell size={17} />
                  {unreadCount > 0 && (
                    <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-red-500 text-[10px] font-bold text-white flex items-center justify-center">
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  )}
                </button>
                <AnimatePresence>
                  {notifOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: 8, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 8, scale: 0.95 }}
                      className="absolute right-0 top-full mt-2 w-80 rounded-2xl border border-[#1e2d4a] bg-[#0f1629] shadow-2xl shadow-purple-500/10 overflow-hidden"
                    >
                      <div className="p-4 border-b border-[#1e2d4a]">
                        <p className="text-sm font-semibold text-slate-100">Notifications</p>
                      </div>
                      <div className="max-h-80 overflow-y-auto">
                        {notifications.length === 0 ? (
                          <p className="text-sm text-slate-500 p-4 text-center">No notifications</p>
                        ) : (
                          notifications.slice(0, 8).map((n) => (
                            <div
                              key={n.id}
                              className={`px-4 py-3 border-b border-[#1e2d4a] last:border-0 ${!n.is_read ? 'bg-purple-500/5' : ''}`}
                            >
                              <p className="text-xs font-medium text-slate-200">{n.title}</p>
                              <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{n.message}</p>
                            </div>
                          ))
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Avatar dropdown */}
              <div className="relative" ref={dropRef}>
                <button
                  onClick={() => setDropdownOpen((v) => !v)}
                  className="flex items-center gap-2 p-1 pr-2 rounded-xl border border-[#1e2d4a] hover:border-purple-500/40 transition-all bg-[#0f1629]"
                >
                  {user?.avatar_url ? (
                    <img
                      src={user.avatar_url}
                      alt={user.full_name}
                      className="w-7 h-7 rounded-lg object-cover"
                    />
                  ) : (
                    <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-purple-600 to-blue-500 flex items-center justify-center text-xs font-bold text-white">
                      {getInitials(user?.full_name || 'U')}
                    </div>
                  )}
                  <span className="text-xs font-medium text-slate-300 hidden sm:block max-w-24 truncate">
                    {user?.full_name}
                  </span>
                </button>

                <AnimatePresence>
                  {dropdownOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: 8, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 8, scale: 0.95 }}
                      className="absolute right-0 top-full mt-2 w-52 rounded-2xl border border-[#1e2d4a] bg-[#0f1629] shadow-2xl shadow-purple-500/10 overflow-hidden"
                    >
                      <div className="p-3 border-b border-[#1e2d4a]">
                        <p className="text-sm font-semibold text-slate-100 truncate">{user?.full_name}</p>
                        <p className="text-xs text-slate-500 truncate">{user?.email}</p>
                      </div>
                      <div className="p-1">
                        <DropItem icon={<User size={14} />} label="Dashboard" to="/dashboard" close={() => setDropdownOpen(false)} />
                        <DropItem icon={<Settings size={14} />} label="Profile" to="/profile" close={() => setDropdownOpen(false)} />
                        {user?.role === 'admin' && (
                          <DropItem icon={<Shield size={14} />} label="Admin Panel" to="/admin" close={() => setDropdownOpen(false)} />
                        )}
                        <button
                          onClick={handleLogout}
                          className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                        >
                          <LogOut size={14} />
                          Logout
                        </button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </>
          )}

          {/* Mobile hamburger */}
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-all"
          >
            {menuOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </nav>

      {/* Mobile menu */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden border-t border-[#1e2d4a] bg-[#0a0e1a]/95 backdrop-blur-xl"
          >
            <div className="p-4 flex flex-col gap-1">
              <MobileLink to="/library" label="Library" onClick={() => setMenuOpen(false)} />
              {isAuthenticated && (
                <MobileLink to="/ai" label="AI Assistant" onClick={() => setMenuOpen(false)} />
              )}
              {!isAuthenticated && (
                <>
                  <MobileLink to="/login" label="Login" onClick={() => setMenuOpen(false)} />
                  <MobileLink to="/register" label="Register" onClick={() => setMenuOpen(false)} />
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}

function DropItem({ icon, label, to, close }: { icon: React.ReactNode; label: string; to: string; close: () => void }) {
  return (
    <Link
      to={to}
      onClick={close}
      className="flex items-center gap-2.5 px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
    >
      {icon}
      {label}
    </Link>
  )
}

function MobileLink({ to, label, onClick }: { to: string; label: string; onClick: () => void }) {
  return (
    <Link
      to={to}
      onClick={onClick}
      className="px-3 py-2.5 text-sm font-medium text-slate-300 hover:text-white hover:bg-white/5 rounded-xl transition-colors"
    >
      {label}
    </Link>
  )
}

