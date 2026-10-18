import { useEffect, useState } from 'react'
import Header from './components/Header.jsx'
import Login from './components/Login.jsx'
import ProblemForm from './components/ProblemForm.jsx'
import CodeEditor from './components/CodeEditor.jsx'
import ImageUpload from './components/ImageUpload.jsx'
import TestCases from './components/TestCases.jsx'
import FeedbackPanel from './components/FeedbackPanel.jsx'
import StreakTracker from './components/StreakTracker.jsx'
import { analyzeSubmission, fetchLanguages, fetchStreak } from './api.js'
import { getToken, getStoredUsername, logout as clearSession, fetchCurrentUser } from './auth.js'

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark')
  const [username, setUsername] = useState(() => (getToken() ? getStoredUsername() : null))

  const [languages, setLanguages] = useState([])
  const [form, setForm] = useState({
    problemStatement: '',
    constraints: '',
    claimedTimeComplexity: '',
    claimedSpaceComplexity: '',
  })
  const [language, setLanguage] = useState('python')
  const [code, setCode] = useState('')
  const [imageFile, setImageFile] = useState(null)
  const [testCases, setTestCases] = useState([])

  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [streak, setStreak] = useState({ heatmap: [], current_streak: 0 })

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem('theme', theme)
  }, [theme])

  // Validate session on app launch
  useEffect(() => {
    if (getToken()) {
      fetchCurrentUser().then((user) => {
        if (!user) {
          handleLogout()
        } else {
          setUsername(user.username)
        }
      }).catch(() => {
        handleLogout()
      })
    }
  }, [])

  useEffect(() => {
    fetchLanguages().then((d) => setLanguages(d.languages || [])).catch(() => {})
  }, [])

  useEffect(() => {
    if (username) refreshStreak()
  }, [username])

  function refreshStreak() {
    fetchStreak()
      .then(setStreak)
      .catch((err) => {
        if (err.status === 401) {
          handleLogout()
        }
      })
  }

  function handleLogout() {
    clearSession()
    setUsername(null)
    setResult(null)
    setStreak({ heatmap: [], current_streak: 0 })
  }

  async function handleSubmit() {
    // 1. Client-side input validation before contacting the agent
    const cleanProblem = form.problemStatement.trim()
    const cleanCode = code.trim()

    if (!cleanProblem) {
      setError('Please provide a problem statement so the coach knows what algorithm to evaluate.')
      return
    }

    if (!cleanCode && !imageFile) {
      setError('Please enter your solution code in the editor or upload an image of your code.')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await analyzeSubmission({
        language,
        problemStatement: cleanProblem,
        constraints: form.constraints.trim(),
        claimedTimeComplexity: form.claimedTimeComplexity.trim(),
        claimedSpaceComplexity: form.claimedSpaceComplexity.trim(),
        code: cleanCode,
        imageFile,
        testCases,
      })
      setResult(data)
      if (data.extracted_code) setCode(data.extracted_code)
      refreshStreak() // pulls the freshly-logged solve into today's box immediately
    } catch (e) {
      // Only logout if the user's JWT login session expired, NOT on Gemini API key errors
      if (e.status === 401 && (e.message?.includes('Not authenticated') || e.message?.includes('Session expired'))) {
        handleLogout()
      }
      setError(e.message || 'Something went wrong talking to the Code Exec Agent.')
    } finally {
      setLoading(false)
    }
  }

  if (!username) {
    return <Login theme={theme} setTheme={setTheme} onAuthed={setUsername} />
  }

  return (
    <div className="min-h-screen">
      <Header theme={theme} setTheme={setTheme} username={username} onLogout={handleLogout} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 md:px-10 py-5 sm:py-8">
        <div className="mb-6">
          <h1 className="font-mono text-xl sm:text-2xl md:text-3xl font-extrabold tracking-tight">
            Get honest feedback on your DSA solution
          </h1>
          <p className="text-xs sm:text-sm text-ink-600 dark:text-paper-200/60 mt-1">
            Type or upload your code, describe the problem, and the Code Exec Agent will
            run it in a real sandbox and review it like a strict interviewer would.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-6">
            <ProblemForm form={form} setForm={setForm} />
            <ImageUpload imageFile={imageFile} setImageFile={setImageFile} />
            <CodeEditor
              code={code}
              setCode={setCode}
              language={language}
              setLanguage={setLanguage}
              languages={languages}
              theme={theme}
            />

            <TestCases testCases={testCases} setTestCases={setTestCases} results={result?.test_results} />

            <button
              onClick={handleSubmit}
              disabled={loading || (!code.trim() && !imageFile)}
              className="w-full py-3 rounded-xl font-mono font-bold text-sm bg-ink-900 text-amber-400 dark:bg-amber-400 dark:text-ink-950 hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity cursor-pointer shadow-sm"
            >
              {loading ? 'Running Code Exec Agent…' : 'Get feedback →'}
            </button>

            <StreakTracker heatmap={streak.heatmap} currentStreak={streak.current_streak} />
          </div>

          <div>
            <h2 className="font-mono font-bold text-sm mb-4 flex items-center gap-2">
              <span className="text-amber-500">05</span> Feedback
            </h2>
            <FeedbackPanel loading={loading} result={result} error={error} />
          </div>
        </div>
      </main>

      <footer className="max-w-7xl mx-auto px-4 sm:px-6 md:px-10 py-5 sm:py-6 text-xs text-ink-600/60 dark:text-paper-200/30 font-mono text-center sm:text-left">
        DSA Coach — Feedback Generation · Mind Matrix · Created by ARPITA PANDA
      </footer>
    </div>
  )
}
