'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  Filter,
  Search,
  RefreshCw,
  AlertCircle,
  Lock
} from 'lucide-react'
import { fetchApi, getStoredUser, isManagerPlus } from '@/lib/api-client'

interface AuditLog {
  timestamp: string
  user_id: string
  user_name?: string
  user_role?: string
  user_department?: string
  tool_name: string
  tool_args?: any
  allowed: boolean
  decision_reason?: string
}

export default function AuditLogsPage() {
  const router = useRouter()
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [user, setUser] = useState<any>(null)
  const [isAuthorized, setIsAuthorized] = useState<boolean | null>(null)

  // Filters
  const [statusFilter, setStatusFilter] = useState<'all' | 'allowed' | 'denied'>('all')
  const [searchQuery, setSearchQuery] = useState('')

  const loadLogs = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await fetchApi<AuditLog[]>('/api/v1/admin/audit-logs')
      setLogs(data)
    } catch (err: any) {
      console.error('Failed to load audit logs:', err)
      setError(err.message || 'Failed to load audit logs.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const currentUser = getStoredUser()
    setUser(currentUser)
    if (!currentUser || !isManagerPlus(currentUser)) {
      setIsAuthorized(false)
      setLoading(false)
    } else {
      setIsAuthorized(true)
      loadLogs()
    }
  }, [])

  if (isAuthorized === false) {
    return (
      <div className="p-8 max-w-xl mx-auto my-12 text-center">
        <div className="bg-red-50 border border-red-200 rounded-2xl p-8 shadow-sm space-y-4">
          <div className="w-12 h-12 rounded-full bg-red-100 text-red-600 flex items-center justify-center mx-auto">
            <Lock className="w-6 h-6" />
          </div>
          <h1 className="font-serif text-2xl font-normal text-red-950">
            Access Denied (403 Forbidden)
          </h1>
          <p className="text-xs text-red-700 leading-relaxed">
            The Security Audit Trail is strictly reserved for Manager, Director, and C-Level personnel. Your account ({user?.full_name || 'Current User'} - {user?.role_level || 'Employee'}) does not possess sufficient administrative clearance.
          </p>
          <button
            onClick={() => router.push('/dashboard')}
            className="mt-2 px-5 py-2 bg-red-900 hover:bg-red-950 text-white text-xs font-medium rounded-lg transition-colors"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    )
  }

  const filteredLogs = logs.filter((log) => {
    if (statusFilter === 'allowed' && !log.allowed) return false
    if (statusFilter === 'denied' && log.allowed) return false

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      const matchUser = (log.user_name || '').toLowerCase().includes(q) || (log.user_id || '').toLowerCase().includes(q)
      const matchTool = (log.tool_name || '').toLowerCase().includes(q)
      const matchReason = (log.decision_reason || '').toLowerCase().includes(q)
      return matchUser || matchTool || matchReason
    }

    return true
  })

  const totalLogs = logs.length
  const allowedCount = logs.filter(l => l.allowed).length
  const deniedCount = logs.filter(l => !l.allowed).length

  return (
    <div className="p-6 sm:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-serif text-2xl sm:text-3xl font-normal text-gray-900 tracking-tight">
              Security Audit Trail
            </h1>
            <span className="text-[10px] uppercase font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
              Manager+ Privileged
            </span>
          </div>
          <p className="mt-1 text-xs sm:text-sm text-gray-600">
            Immutable log of all agentic tool execution attempts and RBAC permission gate decisions.
          </p>
        </div>

        <button
          onClick={loadLogs}
          className="self-start sm:self-auto p-2.5 bg-white border border-gray-200 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-50 transition-colors shadow-xs flex items-center gap-2 text-xs font-medium"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-white to-gray-50 hover:to-white border border-gray-200/90 p-5 rounded-xl shadow-sm hover:shadow-md transition-shadow">
          <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">Total Audit Invocations</div>
          <div className="text-3xl font-serif font-semibold text-gray-900 mt-1.5">{totalLogs}</div>
        </div>
        <div className="bg-gradient-to-br from-white to-emerald-50/30 hover:to-white border border-emerald-100 p-5 rounded-xl shadow-sm hover:shadow-md transition-shadow">
          <div className="text-[10px] font-semibold text-emerald-600 uppercase tracking-wider">Authorized Executions</div>
          <div className="text-3xl font-serif font-semibold text-emerald-700 mt-1.5">{allowedCount}</div>
        </div>
        <div className="bg-gradient-to-br from-white to-red-50/30 hover:to-white border border-red-100 p-5 rounded-xl shadow-sm hover:shadow-md transition-shadow">
          <div className="text-[10px] font-semibold text-red-600 uppercase tracking-wider">Blocked / Denied Invocations</div>
          <div className="text-3xl font-serif font-semibold text-red-700 mt-1.5">{deniedCount}</div>
        </div>
      </div>

      {/* Filter & Search Toolbar */}
      <div className="bg-white border border-gray-200/90 p-4 rounded-xl shadow-xs flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by user, tool name, or reason..."
            className="w-full pl-9 pr-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-200"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-3.5 h-3.5 text-gray-400 shrink-0" />
          <select
            value={statusFilter}
            onChange={(e: any) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-800 font-medium focus:outline-none"
          >
            <option value="all">All Invocations</option>
            <option value="allowed">Allowed Only</option>
            <option value="denied">Denied Only</option>
          </select>
        </div>
      </div>

      {/* ERROR STATE */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* AUDIT LOGS TABLE */}
      <div className="bg-white border border-gray-200/90 rounded-2xl shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-gray-500 flex items-center justify-center gap-2">
            <div className="w-4 h-4 border-2 border-gray-900 border-t-transparent rounded-full animate-spin" />
            Loading security audit log entries...
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-12 text-center text-xs text-gray-500">
            No audit log entries match your selected filter criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50/80 border-b border-gray-200/80 text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                  <th className="py-3.5 px-6">Timestamp</th>
                  <th className="py-3.5 px-6">User Context</th>
                  <th className="py-3.5 px-6">Tool Requested</th>
                  <th className="py-3.5 px-6">Permission Gate</th>
                  <th className="py-3.5 px-6">Decision Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-xs text-gray-700">
                {filteredLogs.map((l, idx) => (
                  <tr key={idx} className="hover:bg-gray-50/60 transition-colors">
                    <td className="py-3.5 px-6 font-mono text-[11px] text-gray-500 whitespace-nowrap">
                      {l.timestamp ? new Date(l.timestamp).toLocaleString() : '—'}
                    </td>
                    <td className="py-3.5 px-6">
                      <div className="font-semibold text-gray-900">{l.user_name || l.user_id}</div>
                      <div className="text-[10px] text-gray-500 font-mono">
                        {l.user_id} {l.user_role ? `• ${l.user_role}` : ''}
                      </div>
                    </td>
                    <td className="py-3.5 px-6 font-mono font-medium text-gray-800">
                      {l.tool_name}
                    </td>
                    <td className="py-3.5 px-6">
                      {l.allowed ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <ShieldCheck className="w-3 h-3 text-emerald-600" />
                          Allowed
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-red-50 text-red-700 border border-red-200">
                          <ShieldX className="w-3 h-3 text-red-600" />
                          Denied
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-6 max-w-sm text-gray-600 text-xs leading-normal">
                      {l.decision_reason || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
