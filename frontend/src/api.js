import { authHeaders } from './auth.js'

const BASE = '/api'

export async function fetchLanguages() {
  const res = await fetch(`${BASE}/languages`)
  return res.json()
}

export async function fetchStreak() {
  const res = await fetch(`${BASE}/streak`, { headers: { ...authHeaders() } })
  if (!res.ok) throw new Error('Could not load your streak - please log in again.')
  return res.json()
}

export async function analyzeSubmission({
  language, problemStatement, constraints,
  claimedTimeComplexity, claimedSpaceComplexity, code, stdin, imageFile, testCases,
}) {
  const form = new FormData()
  form.append('language', language)
  form.append('problem_statement', problemStatement)
  form.append('constraints', constraints)
  form.append('claimed_time_complexity', claimedTimeComplexity)
  form.append('claimed_space_complexity', claimedSpaceComplexity)
  form.append('code', code)
  form.append('stdin', stdin || '')
  form.append('test_cases_json', JSON.stringify((testCases || []).filter((tc) => tc.input || tc.expected_output)))
  if (imageFile) form.append('image', imageFile)

  const res = await fetch(`${BASE}/analyze`, {
    method: 'POST',
    body: form,
    headers: { ...authHeaders() },
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || `Analyze failed: ${res.status}`)
  }
  return res.json()
}
