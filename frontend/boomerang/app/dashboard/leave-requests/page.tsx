'use client'

import { useState, useEffect } from 'react'
import {
  Calendar as CalendarIcon,
  Plus,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  X,
  Send,
  Sparkles
} from 'lucide-react'
import { fetchApi, getStoredUser } from '@/lib/api-client'

interface LeaveRequest {
  request_id?: string
  employee_id?: string
  start_date: string
  end_date: string
  reason: string
  status: string
  approved_by?: string
  created_at?: string
}

export default function LeaveRequestsPage() {
  const [requests, setRequests] = useState<LeaveRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [user, setUser] = useState<any>(null)

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [reason, setReason] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [agentResponse, setAgentResponse] = useState('')

  const loadData = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await fetchApi<LeaveRequest[]>('/api/v1/user/leave-requests')
      setRequests(data)
    } catch (err: any) {
      console.error('Failed to load leave requests:', err)
      setError(err.message || 'Failed to load leave requests.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    setUser(getStoredUser())
    loadData()
  }, [])

  const handleApplyLeave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!startDate || !endDate || !reason.trim()) return

    setSubmitting(true)
    setAgentResponse('')

    // Conceptual UX: Routes through the Agentic Tool Pipeline via chat query
    const constructedQuery = `Apply for leave from ${startDate} to ${endDate} because ${reason.trim()}`

    try {
      const res = await fetchApi('/api/v1/chat/query', {
        method: 'POST',
        body: JSON.stringify({ query: constructedQuery }),
      })

      setAgentResponse(res.answer || 'Leave application request processed.')
      setStartDate('')
      setEndDate('')
      setReason('')
      
      // Reload leave requests from backend
      await loadData()
    } catch (err: any) {
      console.error('Leave application failed:', err)
      setAgentResponse(`Error: ${err.message || 'Failed to submit leave request.'}`)
    } finally {
      setSubmitting(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const s = status.toLowerCase()
    if (s.includes('approve')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          Approved
        </span>
      )
    }
    if (s.includes('reject')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-red-50 text-red-700 border border-red-200">
          <XCircle className="w-3.5 h-3.5 text-red-600" />
          Rejected
        </span>
      )
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
        <Clock className="w-3.5 h-3.5 text-amber-600" />
        Pending
      </span>
    )
  }

  return (
    <div className="p-6 sm:p-8 max-w-6xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-2xl sm:text-3xl font-normal text-gray-900 tracking-tight">
            My Leave Requests
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-gray-600">
            View and manage your leave requests. Submissions execute through the SentinelRAG Agentic Tool pipeline.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            className="p-2.5 bg-white border border-gray-200 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-50 transition-colors shadow-xs"
            title="Refresh Data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={() => {
              setIsModalOpen(true)
              setAgentResponse('')
            }}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#191919] text-white text-xs font-medium rounded-lg hover:bg-[#191919]/90 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Apply for Leave</span>
          </button>
        </div>
      </div>

      {/* ERROR STATE */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* TABLE LIST / CARD LIST */}
      <div className="bg-white border border-gray-200/90 rounded-2xl shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-gray-500 flex items-center justify-center gap-2">
            <div className="w-4 h-4 border-2 border-gray-900 border-t-transparent rounded-full animate-spin" />
            Loading leave requests from data store...
          </div>
        ) : requests.length === 0 ? (
          <div className="p-12 text-center flex flex-col items-center justify-center space-y-3">
            <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-400">
              <CalendarIcon className="w-5 h-5" />
            </div>
            <div className="text-sm font-semibold text-gray-900">No Leave Requests Found</div>
            <p className="text-xs text-gray-500 max-w-sm">
              You haven&apos;t submitted any leave requests yet. Click &quot;Apply for Leave&quot; above to file a request via AI agent.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50/80 border-b border-gray-200/80 text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                  <th className="py-3.5 px-6">Request ID</th>
                  <th className="py-3.5 px-6">Dates</th>
                  <th className="py-3.5 px-6">Reason</th>
                  <th className="py-3.5 px-6">Status</th>
                  <th className="py-3.5 px-6">Approved By</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-xs text-gray-700">
                {requests.map((r, idx) => (
                  <tr key={r.request_id || idx} className="hover:bg-gray-50/60 transition-colors">
                    <td className="py-4 px-6 font-mono font-medium text-gray-900">
                      {r.request_id || `LR-${1000 + idx}`}
                    </td>
                    <td className="py-4 px-6 font-medium text-gray-900">
                      <div>{r.start_date} <span className="text-gray-400 font-normal">to</span> {r.end_date}</div>
                    </td>
                    <td className="py-4 px-6 max-w-xs text-gray-600 truncate">
                      {r.reason}
                    </td>
                    <td className="py-4 px-6">
                      {getStatusBadge(r.status)}
                    </td>
                    <td className="py-4 px-6 font-mono text-gray-500 text-[11px]">
                      {r.approved_by || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* APPLY LEAVE MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-gray-200 shadow-2xl max-w-md w-full p-6 space-y-5 animate-in fade-in zoom-in duration-150">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[#191919]" />
                <h2 className="font-serif text-lg font-semibold text-gray-900">
                  Apply for Leave
                </h2>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleApplyLeave} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-gray-600 uppercase mb-1">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    required
                    className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs font-mono text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#191919]/20"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-gray-600 uppercase mb-1">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    required
                    className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs font-mono text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#191919]/20"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-gray-600 uppercase mb-1">
                  Reason for Leave
                </label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  required
                  rows={3}
                  placeholder="e.g., Personal family obligation and travel"
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#191919]/20"
                />
              </div>

              {agentResponse && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-900 space-y-1">
                  <div className="font-semibold text-blue-950 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-blue-600" /> Agent Response:
                  </div>
                  <p>{agentResponse}</p>
                </div>
              )}

              <div className="flex gap-2 pt-2 justify-end">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-medium rounded-lg transition-colors"
                >
                  Close
                </button>

                <button
                  type="submit"
                  disabled={submitting || !startDate || !endDate || !reason.trim()}
                  className="px-5 py-2.5 bg-[#191919] hover:bg-[#191919]/90 disabled:opacity-50 text-white text-xs font-medium rounded-lg transition-colors flex items-center gap-2 shadow-xs"
                >
                  {submitting ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Executing Tool...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5" />
                      <span>Submit Request</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
