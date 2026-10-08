const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function fetchApi<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = endpoint.startsWith('http')
    ? endpoint
    : `${API_BASE_URL}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  }

  // Attach JWT token from localStorage if available
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('sentinel_token')
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })

    // Handle 401 Unauthorized globally
    if (response.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('sentinel_token')
        localStorage.removeItem('sentinel_user')
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login'
        }
      }
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || 'Authentication expired. Please log in again.')
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      const errorMessage = errorData.detail || errorData.error || `HTTP error! status: ${response.status}`
      throw new Error(errorMessage)
    }

    return (await response.json()) as T
  } catch (error: any) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Unable to connect to backend server. Please verify the backend API is running.')
    }
    throw error
  }
}

export function getStoredUser() {
  if (typeof window === 'undefined') return null
  const userStr = localStorage.getItem('sentinel_user')
  if (!userStr) return null
  try {
    return JSON.parse(userStr)
  } catch {
    return null
  }
}

export function getStoredToken() {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('sentinel_token')
}

export function logoutUser() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('sentinel_token')
    localStorage.removeItem('sentinel_user')
    window.location.href = '/login'
  }
}

export function isManagerPlus(user: any): boolean {
  if (!user || !user.role_level) return false
  const role = String(user.role_level).toLowerCase()
  return role.includes('manager') || role.includes('director') || role.includes('c-level') || role.includes('vp')
}

