'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import {
  MessageSquare,
  Calendar,
  ShieldAlert,
  BarChart2,
  LogOut,
  User,
  ShieldCheck,
  Building2,
  ChevronRight
} from 'lucide-react'
import { getStoredUser, getStoredToken, logoutUser, isManagerPlus } from '@/lib/api-client'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const [user, setUser] = useState<any>(null)
  const [isAuthChecked, setIsAuthChecked] = useState(false)

  useEffect(() => {
    const token = getStoredToken()
    if (!token) {
      router.push('/login')
      return
    }
    const currentUser = getStoredUser()
    setUser(currentUser)
    setIsAuthChecked(true)
  }, [router])

  if (!isAuthChecked) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center gap-3 text-[#191919]/70 text-sm font-medium">
          <div className="w-5 h-5 border-2 border-[#191919] border-t-transparent rounded-full animate-spin" />
          Checking authentication & permissions...
        </div>
      </div>
    )
  }

  const isManager = isManagerPlus(user)

  const navItems = [
    {
      label: 'Chat',
      href: '/dashboard',
      icon: MessageSquare,
      show: true,
    },
    {
      label: 'My Leave Requests',
      href: '/dashboard/leave-requests',
      icon: Calendar,
      show: true,
    },
    {
      label: 'Audit Logs',
      href: '/dashboard/audit-logs',
      icon: ShieldAlert,
      show: isManager,
      badge: 'Manager+'
    },
    {
      label: 'Evaluation Report',
      href: '/dashboard/evaluation',
      icon: BarChart2,
      show: isManager,
      badge: 'Manager+'
    },
  ]

  const logoSVG = (
    <svg
      viewBox="0 0 256 256"
      fill="currentColor"
      className="w-5 h-5 text-[#191919]"
    >
      <path d="M 144 256 L 27.598 256 L 144 139.598 Z" />
      <path d="M 256 207.5 L 200 256 L 200 56 L 0 56 L 48 0 L 256 0 Z" />
      <path d="M 0 204.402 L 0 112 L 92.402 112 Z" />
    </svg>
  )

  return (
    <div className="min-h-screen bg-[#FAF9F6] flex overflow-hidden">
      {/* LEFT SIDEBAR (~260px) */}
      <aside className="w-64 bg-white border-r border-gray-200/80 flex flex-col justify-between shrink-0 shadow-sm">
        <div className="flex flex-col h-full">
          {/* Top Brand Header */}
          <div className="p-5 border-b border-gray-100">
            <Link href="/dashboard" className="flex items-center gap-2">
              {logoSVG}
              <div className="flex flex-col">
                <span className="font-semibold text-sm tracking-tight text-[#191919]">
                  Stratos Enterprises
                </span>
                <span className="text-[9px] uppercase tracking-wider font-semibold text-[#191919]/60">
                  SentinelRAG Console
                </span>
              </div>
            </Link>
          </div>

          {/* User Profile Card */}
          {user && (
            <div className="p-4 mx-3 my-3 bg-[#F4F3F3] border border-gray-200/70 rounded-xl">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-[#191919] text-white flex items-center justify-center text-xs font-semibold shrink-0">
                  {user.full_name ? user.full_name.split(' ').map((n: string) => n[0]).join('') : 'U'}
                </div>
                <div className="flex flex-col min-w-0 flex-1">
                  <span className="text-xs font-semibold text-[#191919] truncate">
                    {user.full_name || 'Enterprise User'}
                  </span>
                  <div className="flex items-center gap-1 text-[10px] text-gray-500 font-medium truncate">
                    <Building2 className="w-3 h-3 text-gray-400 shrink-0" />
                    <span className="truncate">{user.department || 'Staff'}</span>
                    <span>•</span>
                    <span className="truncate">{user.role_level}</span>
                  </div>
                </div>
              </div>
              <div className="mt-2.5 pt-2 border-t border-gray-200/60 flex items-center justify-between text-[10px] font-mono text-gray-600">
                <span className="bg-white px-1.5 py-0.5 rounded border border-gray-200 font-semibold">{user.employee_id}</span>
                <span className="flex items-center gap-1 text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded font-sans font-medium">
                  <ShieldCheck className="w-3 h-3" /> Level {user.clearance_level}
                </span>
              </div>
            </div>
          )}

          {/* Navigation Links */}
          <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
            <div className="px-3 py-1.5 text-[10px] uppercase font-semibold text-gray-400 tracking-wider">
              Navigation
            </div>

            {navItems.filter(item => item.show).map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href))

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-[#191919] text-white shadow-md'
                      : 'text-[#191919]/75 hover:bg-[#F4F3F3] hover:text-[#191919] hover:translate-x-1'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-gray-500'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && !isActive && (
                    <span className="text-[9px] uppercase font-semibold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                      {item.badge}
                    </span>
                  )}
                </Link>
              )
            })}
          </nav>

          {/* Sign Out Button */}
          <div className="p-3 border-t border-gray-100">
            <button
              onClick={logoutUser}
              className="w-full flex items-center justify-between px-3 py-2.5 text-xs font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <LogOut className="w-4 h-4 text-red-500" />
                <span>Sign Out</span>
              </div>
              <ChevronRight className="w-3.5 h-3.5 text-red-400" />
            </button>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        {/* Top App Header */}
        <header className="h-14 bg-white border-b border-gray-200/80 px-6 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2 text-xs font-medium text-gray-500">
            <span>Stratos Console</span>
            <span>/</span>
            <span className="text-gray-900 font-semibold capitalize">
              {pathname === '/dashboard' ? 'AI Assistant Chat' : pathname.replace('/dashboard/', '').replace('-', ' ')}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-[11px] text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>RBAC Enforced</span>
            </div>
            <div className="text-[11px] text-gray-500 bg-gray-100 px-2.5 py-1 rounded-full border border-gray-200 font-mono">
              Groq Llama 3.3 70B
            </div>
          </div>
        </header>

        {/* Dynamic Page Content */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
