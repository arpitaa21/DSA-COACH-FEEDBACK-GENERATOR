/**
 * auth.js
 * Frontend session and authentication helpers for DSA Coach.
 */

const TOKEN_KEY = 'dsa_coach_token'
const USER_KEY = 'dsa_coach_user'
const USERNAME_KEY = 'dsa_coach_username'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function getStoredUser() {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function getStoredUsername() {
  const user = getStoredUser()
  return user?.username || localStorage.getItem(USERNAME_KEY) || null
}

export function saveSession(authData) {
  if (!authData) return
  if (authData.access_token) {
    localStorage.setItem(TOKEN_KEY, authData.access_token)
  }
  const userObj = {
    username: authData.username || '',
    email: authData.email || '',
    display_name: authData.display_name || authData.username || '',
  }
  localStorage.setItem(USER_KEY, JSON.stringify(userObj))
  localStorage.setItem(USERNAME_KEY, userObj.username)
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(USERNAME_KEY)
}

export function logout() {
  clearSession()
}

export function authHeaders() {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function safeFetch(url, options = {}) {
  try {
    return await fetch(url, options)
  } catch (err) {
    const error = new Error(
      'Cannot connect to the DSA Coach backend. Please ensure the FastAPI backend is running on http://127.0.0.1:8000.'
    )
    error.status = 503
    throw error
  }
}

async function parseOrThrow(res, endpoint = '') {
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    let message = data.detail
    if (!message) {
      if (res.status === 404) {
        message = `Backend server not reachable at ${endpoint || 'the API'} (HTTP 404). Please ensure the FastAPI backend is running on http://127.0.0.1:8000.`
      } else if (res.status === 502 || res.status === 503 || res.status === 504) {
        message = `Backend server is currently unavailable (HTTP ${res.status}). Please check that the server is running on port 8000.`
      } else {
        message = `Request failed with status ${res.status}`
      }
    }
    // If detail is an array (Pydantic validation errors)
    if (Array.isArray(data.detail)) {
      message = data.detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
    }
    const err = new Error(message)
    err.status = res.status
    throw err
  }
  return data
}

/**
 * Log in with either username or email and password.
 */
export async function login(identifier, password) {
  const res = await safeFetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: identifier.trim(),
      password,
    }),
  })
  const data = await parseOrThrow(res, '/api/login')
  saveSession(data)
  return data
}

/**
 * Register a new user with username, email, password, and optional display name.
 */
export async function register({ username, email, password, displayName = '' }) {
  const res = await safeFetch('/api/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: username.trim(),
      email: email.trim(),
      password,
      display_name: displayName.trim() || undefined,
    }),
  })
  const data = await parseOrThrow(res, '/api/register')
  saveSession(data)
  return data
}

/**
 * Fetch current user profile to verify valid session.
 */
export async function fetchCurrentUser() {
  const token = getToken()
  if (!token) return null

  try {
    const res = await safeFetch('/api/me', {
      headers: { ...authHeaders() },
    })

    if (!res.ok) {
      clearSession()
      return null
    }

    const user = await res.json()
    saveSession({ access_token: token, ...user })
    return user
  } catch {
    return null
  }
}
