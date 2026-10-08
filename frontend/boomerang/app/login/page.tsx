'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Navbar } from '@/components/navbar'
import { BoomerangVideoBg } from '@/components/boomerang-video-bg'
import { fetchApi } from '@/lib/api-client'

interface DemoPersona {
  id: string
  name: string
  title: string
  dept: string
  role: string
  clearance: string
}

const DEMO_PERSONAS: DemoPersona[] = [
  { id: 'STX-E-010', name: 'Meera Nair', title: 'Senior Software Engineer', dept: 'Engineering', role: 'Employee', clearance: 'Level 1' },
  { id: 'STX-F-011', name: 'Manoj Tiwari', title: 'Accountant', dept: 'Finance', role: 'Employee', clearance: 'Level 1' },
  { id: 'STX-F-005', name: 'Kunal Mehta', title: 'Accounts Payable Lead', dept: 'Finance', role: 'Team Lead', clearance: 'Level 2' },
  { id: 'STX-HR-002', name: 'Abhishek Pandey', title: 'HR Manager', dept: 'HR', role: 'Manager (HR-Admin)', clearance: 'Level 3' },
  { id: 'STX-F-007', name: 'Deepak Shetty', title: 'Finance Manager', dept: 'Finance', role: 'Manager (Finance-Admin)', clearance: 'Level 3' },
  { id: 'STX-F-001', name: 'Raghav Bansal', title: 'Finance Director', dept: 'Finance', role: 'Director (Company-Wide)', clearance: 'Level 3' },
  { id: 'STX-HR-001', name: 'Sunita Krishnamurthy', title: 'HR Director', dept: 'HR', role: 'Director (Company-Wide)', clearance: 'Level 3' }
]

export default function LoginPage() {
  const router = useRouter()
  const [employeeId, setEmployeeId] = useState('')
  const [selectedPersonaId, setSelectedPersonaId] = useState('')
  const [loading, setLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  const handleSelectPersona = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value
    setSelectedPersonaId(id)
    setEmployeeId(id)
    if (errorMessage) setErrorMessage('')
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmedId = employeeId.trim()

    if (!trimmedId) {
      setErrorMessage('Please enter or select a valid Employee ID.')
      return
    }

    setLoading(true)
    setErrorMessage('')

    try {
      const data = await fetchApi('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({ employee_id: trimmedId }),
      })

      // Store JWT token and user profile in localStorage for session state
      if (typeof window !== 'undefined') {
        localStorage.setItem('sentinel_token', data.access_token)
        localStorage.setItem('sentinel_user', JSON.stringify(data.user))
      }

      // Redirect to dashboard
      router.push('/dashboard')
    } catch (err: any) {
      console.error('Login error:', err)
      setErrorMessage(err.message || 'Employee ID not found in roster.')
      setLoading(false)
    }
  }

  const activePersona = DEMO_PERSONAS.find(p => p.id === employeeId)

  return (
    <main className="relative min-h-screen bg-white overflow-hidden flex flex-col justify-between">
      {/* Background Video */}
      <BoomerangVideoBg />

      {/* Top Navbar */}
      <Navbar />

      {/* Center Login Form Box */}
      <div className="relative z-10 flex-1 flex items-center justify-center px-4 sm:px-6 pt-24 pb-12">
        <div className="w-full max-w-md bg-white/90 backdrop-blur-md border border-gray-200 rounded-2xl p-6 sm:p-8 shadow-xl">
          {/* Header */}
          <div className="text-center mb-6">
            <h1 className="font-serif text-2xl sm:text-3xl font-normal text-[#191919] tracking-tight">
              Sign in to Stratos Enterprises
            </h1>
            <p className="mt-2 text-xs sm:text-sm text-[#191919]/65">
              Select a demo role or enter an Employee ID to continue
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleLogin} className="space-y-4">
            {/* Quick Demo Persona Dropdown */}
            <div>
              <label htmlFor="personaSelect" className="block text-xs font-semibold text-[#191919]/80 uppercase tracking-wider mb-1.5 flex items-center justify-between">
                <span>Quick Demo Role Selector</span>
                <span className="text-[10px] text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 font-normal">Demo Mode</span>
              </label>
              <select
                id="personaSelect"
                value={selectedPersonaId}
                onChange={handleSelectPersona}
                className="w-full px-3.5 py-2.5 bg-[#F4F3F3] border border-gray-300 rounded-lg text-xs font-medium text-[#191919] focus:outline-none focus:ring-2 focus:ring-[#191919]/20 focus:border-[#191919] transition-all"
                disabled={loading}
              >
                <option value="">-- Choose a Role Persona to Test --</option>
                {DEMO_PERSONAS.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.dept} - {p.role}) [{p.id}]
                  </option>
                ))}
              </select>
            </div>

            {/* Persona Preview Chip */}
            {activePersona && (
              <div className="p-3 bg-emerald-50/80 border border-emerald-200 rounded-lg text-xs space-y-1">
                <div className="font-semibold text-emerald-950 flex items-center justify-between">
                  <span>{activePersona.name}</span>
                  <span className="text-[10px] bg-white px-1.5 py-0.5 rounded border border-emerald-300 font-mono text-emerald-800">{activePersona.id}</span>
                </div>
                <div className="text-[11px] text-emerald-800 flex items-center gap-2">
                  <span>{activePersona.title}</span>
                  <span>•</span>
                  <span>{activePersona.dept}</span>
                  <span>•</span>
                  <span className="font-semibold">{activePersona.clearance}</span>
                </div>
              </div>
            )}

            {/* Manual Employee ID Input */}
            <div>
              <label htmlFor="employeeId" className="block text-xs font-medium text-[#191919]/70 uppercase tracking-wider mb-1.5">
                Or Enter Employee ID
              </label>
              <input
                id="employeeId"
                type="text"
                value={employeeId}
                onChange={(e) => {
                  setEmployeeId(e.target.value)
                  setSelectedPersonaId(e.target.value)
                  if (errorMessage) setErrorMessage('')
                }}
                placeholder="e.g., STX-E-010"
                className="w-full px-4 py-3 bg-[#F4F3F3] border border-gray-200 rounded-lg text-sm text-[#191919] placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#191919]/20 focus:border-[#191919] transition-all duration-150 font-mono"
                disabled={loading}
              />

              {/* Inline Error Message */}
              {errorMessage && (
                <div className="mt-2 text-xs text-red-600 font-medium flex items-center gap-1.5 bg-red-50 p-2.5 rounded-md border border-red-200">
                  <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{errorMessage}</span>
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || !employeeId.trim()}
              className="w-full py-3.5 bg-[#191919] text-white text-sm font-medium rounded-lg hover:bg-[#191919]/90 disabled:opacity-50 transition-all duration-200 shadow-sm flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Authenticating...</span>
                </>
              ) : (
                <span>Sign In as {activePersona ? activePersona.name.split(' ')[0] : 'Employee'}</span>
              )}
            </button>
          </form>

          {/* Helper Subtext */}
          <div className="mt-6 pt-4 border-t border-gray-200/80 text-center">
            <p className="text-[11px] text-[#191919]/50 leading-normal">
              Demo environment — select any role above to test how RBAC clearance levels (Level 1 Employee vs Level 3 HR/Finance Manager vs Director) control data access.
            </p>
          </div>
        </div>
      </div>

      {/* Subtle Footer */}
      <footer className="relative z-10 py-4 text-center text-xs text-[#191919]/40 border-t border-gray-200/50 bg-white/40 backdrop-blur-sm">
        Stratos Enterprises © 2026 | SentinelRAG Security Architecture
      </footer>
    </main>
  )
}
