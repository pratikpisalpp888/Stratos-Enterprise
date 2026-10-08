'use client'

import { useState, useRef, useEffect } from 'react'
import {
  Send,
  Sparkles,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  FileText,
  User,
  ArrowRight,
  Info,
  Clock,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react'
import { fetchApi, getStoredUser } from '@/lib/api-client'
import { TextShimmer } from '@/components/ui/shimmer-text'

interface SourceInfo {
  chunk_id?: string
  document_type?: string
  department?: string
  owner_name?: string
  final_score?: number
  content?: string
}

interface ChatMessage {
  id: string
  sender: 'user' | 'ai'
  text: string
  sources?: SourceInfo[]
  intent?: string
  flags?: string[]
  responseTimeMs?: number
  isBlocked?: boolean
}

// Simple Lightweight Markdown Formatter
function MarkdownRenderer({ content }: { content: string }) {
  const lines = content.split('\n')
  return (
    <div className="space-y-2 text-xs sm:text-sm text-gray-800 leading-relaxed">
      {lines.map((line, i) => {
        let trimmed = line.trim()
        if (!trimmed) return <div key={i} className="h-1" />

        // Headings ###
        if (trimmed.startsWith('### ')) {
          return (
            <h3 key={i} className="font-serif text-base font-semibold text-gray-900 mt-3 mb-1">
              {trimmed.replace('### ', '')}
            </h3>
          )
        }
        if (trimmed.startsWith('## ')) {
          return (
            <h2 key={i} className="font-serif text-lg font-semibold text-gray-900 mt-4 mb-1">
              {trimmed.replace('## ', '')}
            </h2>
          )
        }

        // Bullet points * or -
        if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
          const bulletText = trimmed.substring(2)
          return (
            <div key={i} className="flex items-start gap-2 pl-2 my-1">
              <span className="text-[#191919]/40 font-bold">•</span>
              <span>{formatBoldText(bulletText)}</span>
            </div>
          )
        }

        // Numbered list items
        if (/^\d+\.\s/.test(trimmed)) {
          const parts = trimmed.split(/^\d+\.\s/)
          const num = trimmed.match(/^\d+/)?.[0]
          return (
            <div key={i} className="flex items-start gap-2 pl-2 my-1">
              <span className="font-semibold text-gray-500 font-mono text-xs">{num}.</span>
              <span>{formatBoldText(parts[1] || '')}</span>
            </div>
          )
        }

        return <p key={i}>{formatBoldText(line)}</p>
      })}
    </div>
  )
}

function formatBoldText(text: string) {
  const parts = text.split(/(\*\*.*?\*\*)/g)
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={index} className="font-semibold text-gray-900">
          {part.slice(2, -2)}
        </strong>
      )
    }
    return part
  })
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputQuery, setInputQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState('Synthesizing secure enterprise insights...')
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({})
  const [user, setUser] = useState<any>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setUser(getStoredUser())
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const exampleQueries = [
    { label: 'Salary Breakdown', query: 'What is my current salary breakdown?' },
    { label: 'Leave Balance', query: 'What is my remaining leave balance?' },
    { label: 'Company Policy', query: 'What is the standard working hours and overtime policy?' },
    { label: 'Apply Leave', query: 'Apply for 2 days casual leave starting tomorrow for personal work' },
  ]

  const handleSend = async (queryToSend?: string) => {
    const query = (queryToSend || inputQuery).trim()
    if (!query || loading) return

    const userMessageId = `user-${Date.now()}`
    const userMsg: ChatMessage = {
      id: userMessageId,
      sender: 'user',
      text: query,
    }

    setMessages((prev) => [...prev, userMsg])
    if (!queryToSend) setInputQuery('')
    
    // Determine dynamic loading message
    const lowerQuery = query.toLowerCase()
    let loadMsg = 'Synthesizing secure enterprise insights...'
    if (lowerQuery.includes('salary') || lowerQuery.includes('pay') || lowerQuery.includes('appraisal')) {
      loadMsg = 'Retrieving secure financial records...'
    } else if (lowerQuery.includes('leave') || lowerQuery.includes('holiday') || lowerQuery.includes('vacation')) {
      loadMsg = 'Accessing HR leave management system...'
    } else if (lowerQuery.includes('policy') || lowerQuery.includes('rules') || lowerQuery.includes('handbook')) {
      loadMsg = 'Scanning corporate policy documents...'
    } else if (lowerQuery.includes('report') || lowerQuery.includes('summary') || lowerQuery.includes('department')) {
      loadMsg = 'Aggregating departmental intelligence...'
    } else if (lowerQuery.length < 20 && (lowerQuery.includes('hi') || lowerQuery.includes('hello') || lowerQuery.includes('how'))) {
      loadMsg = 'Connecting to SentinelRAG...'
    }
    
    setLoadingMessage(loadMsg)
    setLoading(true)

    try {
      const response = await fetchApi('/api/v1/chat/query', {
        method: 'POST',
        body: JSON.stringify({ query }),
      })

      const aiMessageId = `ai-${Date.now()}`
      const isBlocked = response.guardrail_flags && response.guardrail_flags.length > 0

      const aiMsg: ChatMessage = {
        id: aiMessageId,
        sender: 'ai',
        text: response.answer,
        sources: response.sources || [],
        intent: response.intent,
        flags: response.guardrail_flags || [],
        responseTimeMs: response.response_time_ms,
        isBlocked: isBlocked,
      }

      setMessages((prev) => [...prev, aiMsg])
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'ai',
        text: `Error: ${err.message || 'Failed to process request.'}`,
        isBlocked: true,
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  const toggleSourceExpand = (msgId: string) => {
    setExpandedSources((prev) => ({ ...prev, [msgId]: !prev[msgId] }))
  }

  const getIntentBadge = (intent?: string) => {
    switch (intent) {
      case 'personal_record_lookup':
        return <span className="text-[10px] uppercase font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">Personal Record</span>
      case 'policy_or_general_info':
        return <span className="text-[10px] uppercase font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">Policy Info</span>
      case 'aggregate_or_report':
        return <span className="text-[10px] uppercase font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">Department Report</span>
      case 'action_request':
        return <span className="text-[10px] uppercase font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">Action Request</span>
      default:
        return <span className="text-[10px] uppercase font-semibold text-gray-600 bg-gray-100 px-2 py-0.5 rounded border border-gray-200">General</span>
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] bg-[#FAF9F6]">
      {/* MESSAGES SCROLL AREA */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
        {messages.length === 0 ? (
          /* EMPTY STATE */
          <div className="max-w-2xl mx-auto my-auto pt-8 pb-12 flex flex-col items-center text-center space-y-6">
            <div className="w-12 h-12 rounded-2xl bg-[#191919] text-white flex items-center justify-center shadow-md">
              <Sparkles className="w-6 h-6" />
            </div>

            <div>
              <h1 className="font-serif text-2xl sm:text-3xl font-normal text-gray-900 tracking-tight">
                Hi {user?.full_name?.split(' ')[0] || 'there'}, ask me anything.
              </h1>
              <p className="mt-2 text-xs sm:text-sm text-gray-600 max-w-md">
                I am your SentinelRAG AI assistant. I can answer policy questions, retrieve your personal records, or perform actions with 100% RBAC integrity.
              </p>
            </div>

            {/* Example Prompt Chips */}
            <div className="w-full pt-4">
              <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-3">
                Suggested Queries for Your Role ({user?.role_level || 'Employee'})
              </div>
              <div className="grid sm:grid-cols-2 gap-3 text-left">
                {exampleQueries.map((item) => (
                  <button
                    key={item.label}
                    onClick={() => handleSend(item.query)}
                    className="p-3.5 bg-white border border-gray-200/80 rounded-xl hover:border-gray-300 hover:bg-gray-50 hover:-translate-y-0.5 hover:shadow-md transition-all duration-200 flex items-start justify-between group"
                  >
                    <div className="flex flex-col gap-1">
                      <span className="text-xs font-semibold text-gray-900 group-hover:text-black transition-colors">
                        {item.label}
                      </span>
                      <span className="text-[11px] text-gray-500 line-clamp-1">
                        &quot;{item.query}&quot;
                      </span>
                    </div>
                    <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-900 group-hover:translate-x-1 transition-all shrink-0 mt-0.5" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* MESSAGE LIST */
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
            >
              {/* Sender Label */}
              <div className="flex items-center gap-2 mb-1.5 px-1">
                {msg.sender === 'user' ? (
                  <span className="text-[11px] font-medium text-gray-500 flex items-center gap-1">
                    <User className="w-3 h-3 text-gray-400" /> You
                  </span>
                ) : (
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-semibold text-gray-900 flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-[#191919]" /> Stratos AI
                    </span>
                    {getIntentBadge(msg.intent)}
                    {msg.responseTimeMs && (
                      <span className="text-[10px] text-gray-400 flex items-center gap-0.5">
                        <Clock className="w-2.5 h-2.5" /> {msg.responseTimeMs}ms
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Message Bubble */}
              <div
                className={`max-w-2xl rounded-2xl px-5 py-4 shadow-sm ${
                  msg.sender === 'user'
                    ? 'bg-[#191919] text-white rounded-tr-xs'
                    : msg.isBlocked
                    ? 'bg-amber-50/90 border border-amber-200 text-amber-900 rounded-tl-xs'
                    : 'bg-white border border-gray-200/90 text-gray-900 rounded-tl-xs'
                }`}
              >
                {msg.isBlocked && (
                  <div className="flex items-center gap-2 text-amber-800 font-semibold text-xs mb-2 pb-2 border-b border-amber-200">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <span>Security / Guardrail Action</span>
                  </div>
                )}

                {msg.sender === 'user' ? (
                  <p className="text-xs sm:text-sm font-normal leading-relaxed whitespace-pre-wrap">
                    {msg.text}
                  </p>
                ) : (
                  <MarkdownRenderer content={msg.text} />
                )}

                {/* Sources Collapsible Section */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-gray-100">
                    <button
                      onClick={() => toggleSourceExpand(msg.id)}
                      className="flex items-center gap-1.5 text-[11px] font-medium text-gray-500 hover:text-gray-800 transition-colors"
                    >
                      <FileText className="w-3.5 h-3.5 text-gray-400" />
                      <span>Retrieved Sources ({msg.sources.length})</span>
                      {expandedSources[msg.id] ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      )}
                    </button>

                    {expandedSources[msg.id] && (
                      <div className="mt-2.5 space-y-2">
                        {msg.sources.map((s, idx) => (
                          <div
                            key={idx}
                            className="p-2.5 bg-gray-50 border border-gray-200/70 rounded-lg text-xs flex flex-col gap-1 font-mono"
                          >
                            <div className="flex items-center justify-between font-sans">
                              <span className="font-semibold text-gray-800 text-[11px]">
                                {s.document_type || 'Document'}
                              </span>
                              {s.final_score && (
                                <span className="text-[10px] text-gray-400">
                                  Relevance Score: {s.final_score}
                                </span>
                              )}
                            </div>
                            <div className="flex flex-wrap gap-2 text-[10px] text-gray-500 font-sans">
                              {s.department && <span className="bg-white px-1.5 py-0.5 rounded border border-gray-200">Dept: {s.department}</span>}
                              {s.owner_name && <span className="bg-white px-1.5 py-0.5 rounded border border-gray-200">Owner: {s.owner_name}</span>}
                              {s.chunk_id && <span className="text-gray-400">ID: {s.chunk_id}</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {/* Typing Loading State */}
        {loading && (
          <div className="flex flex-col items-start">
            <div className="flex items-center gap-2 mb-1.5 px-1">
              <span className="text-[11px] font-semibold text-gray-900 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-[#191919]" /> Stratos AI
              </span>
            </div>
            <div className="bg-white border border-gray-200/90 rounded-2xl rounded-tl-xs px-5 py-3 shadow-sm flex items-center gap-2">
              <TextShimmer className="font-medium text-xs tracking-tight">
                {loadingMessage}
              </TextShimmer>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* FIXED INPUT FOOTER */}
      <div className="p-4 sm:px-8 pb-6 bg-gradient-to-t from-[#FAF9F6] via-[#FAF9F6] to-transparent">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            handleSend()
          }}
          className="max-w-4xl mx-auto flex items-center gap-3 bg-white border border-gray-200/80 rounded-full pl-6 pr-2 py-2 focus-within:border-gray-400 focus-within:ring-4 focus-within:ring-gray-100 transition-all duration-200 shadow-[0_8px_30px_rgb(0,0,0,0.04)]"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask anything about policies, your records, or request an action..."
            className="flex-1 bg-transparent py-2.5 text-xs sm:text-sm text-gray-900 placeholder-gray-400 focus:outline-none"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !inputQuery.trim()}
            className="p-3 bg-[#191919] text-white rounded-full hover:bg-[#191919]/90 disabled:opacity-40 transition-transform active:scale-95 shadow-md shrink-0 flex items-center justify-center"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <div className="mt-3 text-center text-[10px] text-gray-400">
          SentinelRAG Architecture • Encrypted JWT • 100% RBAC Clearance Validated
        </div>
      </div>
    </div>
  )
}
