const VERDICT_STYLE = {
  correct: 'bg-teal-500/10 text-teal-500 border-teal-500/30',
  partially_correct: 'bg-amber-400/10 text-amber-500 border-amber-400/30',
  incorrect: 'bg-coral-400/10 text-coral-400 border-coral-400/30',
  does_not_run: 'bg-coral-400/10 text-coral-400 border-coral-400/30',
}

const VERDICT_LABEL = {
  correct: 'Correct',
  partially_correct: 'Partially correct',
  incorrect: 'Incorrect',
  does_not_run: "Doesn't run",
}

export default function FeedbackPanel({ loading, result, error }) {
  if (loading) {
    return (
      <div className="panel p-5">
        <div className="flex items-center gap-2 text-sm font-mono text-ink-600 dark:text-paper-200/60">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          Code Exec Agent is running your code and reviewing it…
        </div>
        <div className="mt-4 space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-3 rounded bg-paper-200/70 dark:bg-ink-700/70 animate-pulse" style={{ width: `${90 - i * 12}%` }} />
          ))}
        </div>
      </div>
    )
  }

  if (error && !result) {
    const isApiKeyError = error.includes('API_KEY') || error.includes('API key') || error.includes('401')
    const isModelError = error.includes('model') || error.includes('404')
    const isValidationError = error.includes('required') || error.includes('Missing') || error.includes('Please provide')

    return (
      <div className="panel p-5 border-coral-400/40 bg-coral-500/5">
        <div className="flex items-center gap-2 mb-2">
          <span className="w-2.5 h-2.5 rounded-full bg-coral-400" />
          <h3 className="font-mono text-sm font-bold text-coral-400">
            {isValidationError
              ? 'Input Validation Notice'
              : isApiKeyError
              ? 'Gemini API Key Notice'
              : isModelError
              ? 'Model Notice'
              : 'Feedback Notice'}
          </h3>
        </div>

        <p className="text-sm mt-1 text-ink-800 dark:text-paper-100 font-medium">
          {error}
        </p>

        <div className="mt-4 pt-3 border-t border-paper-200 dark:border-ink-700/60 text-xs text-ink-600 dark:text-paper-200/60 font-mono space-y-1">
          <p className="font-bold text-amber-500 uppercase tracking-wider">Troubleshooting Steps:</p>
          {isApiKeyError ? (
            <ul className="list-disc list-inside space-y-0.5">
              <li>Add a valid key in <code className="text-amber-400">backend/.env</code> (<code className="text-ink-900 dark:text-paper-100">GEMINI_API_KEY=AIzaSy...</code>).</li>
              <li>Or set <code className="text-amber-400">DEMO_MODE=true</code> in <code className="text-ink-900 dark:text-paper-100">backend/.env</code> for fast local evaluation.</li>
            </ul>
          ) : (
            <ul className="list-disc list-inside space-y-0.5">
              <li>Ensure both a problem statement and solution code are provided.</li>
              <li>Check your backend terminal console for detailed diagnostic logs.</li>
            </ul>
          )}
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="panel p-8 text-center">
        <p className="font-mono text-sm text-ink-600 dark:text-paper-200/50">
          Submit your solution to get structured feedback from the Code Exec Agent →
        </p>
      </div>
    )
  }

  const fb = result.feedback || {}
  const exec = result.execution_result || {}
  const testResults = result.test_results || []

  // Extract structured pillars
  const pattern = fb.pattern_insight || {}
  const improvement = fb.improvement_areas || {}
  const optimization = fb.optimization_approach || {}

  const edgeCases = improvement.edge_cases?.length ? improvement.edge_cases : (fb.edge_cases_missed || [])
  const correctnessText = improvement.correctness || fb.correctness_notes || ''
  const readabilityText = improvement.readability || ''

  const actualTime = optimization.actual_time_complexity || fb.actual_time_complexity || '—'
  const actualSpace = optimization.actual_space_complexity || fb.actual_space_complexity || '—'
  const complexityNotes = optimization.complexity_notes || fb.complexity_notes || ''
  const optimalApproach = optimization.optimal_approach || ''
  const optimalTime = optimization.optimal_time_complexity || ''
  const optimalSpace = optimization.optimal_space_complexity || ''

  return (
    <div className="space-y-4">
      {/* 1. Verdict & Summary Header */}
      <div className="panel p-4 sm:p-5">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <span className={`text-xs font-mono px-2.5 py-1 rounded-full border ${VERDICT_STYLE[fb.verdict] || 'bg-ink-100 text-ink-600'}`}>
            {VERDICT_LABEL[fb.verdict] || fb.verdict || 'Unknown'}
          </span>
          <span className="font-mono text-2xl font-bold">
            {fb.score ?? '—'}<span className="text-sm text-ink-600 dark:text-paper-200/40">/100</span>
          </span>
        </div>
        <p className="mt-3 text-sm italic text-ink-800 dark:text-paper-100">"{fb.one_line_summary}"</p>
      </div>

      {/* 2. Problem Pattern Insight Pillar */}
      {pattern.pattern_name && (
        <div className="panel p-4 sm:p-5 border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-mono uppercase tracking-wider text-amber-500 font-bold flex items-center gap-1.5">
              <span>🧠</span> Underlying Problem Pattern
            </p>
            <span className="text-xs font-mono font-bold bg-amber-400/10 text-amber-500 px-2.5 py-0.5 rounded-full border border-amber-400/20">
              {pattern.pattern_name}
            </span>
          </div>
          {pattern.why_pattern_applies && (
            <p className="text-sm text-ink-700 dark:text-paper-200/80 mb-2">
              {pattern.why_pattern_applies}
            </p>
          )}
          {pattern.key_clues?.length > 0 && (
            <div className="mt-2 text-xs">
              <span className="font-mono font-semibold text-ink-600 dark:text-paper-200/60">Key Pattern Clues: </span>
              <span className="text-ink-800 dark:text-paper-100">{pattern.key_clues.join(' · ')}</span>
            </div>
          )}
        </div>
      )}

      {/* 3. Where Code Can Be Improved Pillar (Correctness, Edge Cases, Readability) */}
      <div className="panel p-4 sm:p-5 space-y-3">
        <p className="text-xs font-mono uppercase tracking-wider text-coral-400 font-bold flex items-center gap-1.5">
          <span>🔍</span> Improvement Areas (Correctness, Edge Cases, Readability)
        </p>

        {correctnessText && (
          <div>
            <p className="text-xs font-mono text-ink-600 dark:text-paper-200/50 mb-0.5 font-semibold">Correctness Assessment</p>
            <p className="text-sm text-ink-800 dark:text-paper-100">{correctnessText}</p>
          </div>
        )}

        {edgeCases.length > 0 && (
          <div>
            <p className="text-xs font-mono text-amber-500 mb-1 font-semibold">Edge Cases Missed / Untested</p>
            <ul className="text-sm space-y-1 list-disc list-inside text-ink-800 dark:text-paper-100">
              {edgeCases.map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
          </div>
        )}

        {readabilityText && (
          <div>
            <p className="text-xs font-mono text-ink-600 dark:text-paper-200/50 mb-0.5 font-semibold">Code Readability & Modularity</p>
            <p className="text-sm text-ink-800 dark:text-paper-100">{readabilityText}</p>
          </div>
        )}

        {fb.bugs?.length > 0 && (
          <div>
            <p className="text-xs font-mono text-coral-400 mb-1 font-semibold">Bugs / Logic Risks</p>
            <ul className="text-sm space-y-1 list-disc list-inside text-ink-800 dark:text-paper-100">
              {fb.bugs.map((b, i) => (
                <li key={i}>{b}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* 4. Optimization Approach Pillar (Time & Space, Better Approaches) */}
      <div className="panel p-4 sm:p-5 space-y-3 border-l-4 border-l-teal-500">
        <p className="text-xs font-mono uppercase tracking-wider text-teal-500 font-bold flex items-center gap-1.5">
          <span>⚡</span> Optimization Approach & Complexity Analysis
        </p>

        <div className="grid grid-cols-2 gap-3">
          <div className="bg-paper-100 dark:bg-ink-800 p-2.5 rounded-lg border border-paper-200 dark:border-ink-700">
            <p className="text-xs font-mono uppercase text-ink-600 dark:text-paper-200/50">Actual Time</p>
            <p className="font-mono text-base font-bold mt-0.5 text-ink-900 dark:text-paper-50">{actualTime}</p>
          </div>
          <div className="bg-paper-100 dark:bg-ink-800 p-2.5 rounded-lg border border-paper-200 dark:border-ink-700">
            <p className="text-xs font-mono uppercase text-ink-600 dark:text-paper-200/50">Actual Space</p>
            <p className="font-mono text-base font-bold mt-0.5 text-ink-900 dark:text-paper-50">{actualSpace}</p>
          </div>
        </div>

        {complexityNotes && (
          <p className="text-sm text-ink-600 dark:text-paper-200/70">{complexityNotes}</p>
        )}

        {optimalApproach && (
          <div className="mt-2 pt-2 border-t border-paper-200 dark:border-ink-700/60">
            <p className="text-xs font-mono font-semibold text-teal-500 mb-1">Recommended Optimization:</p>
            <p className="text-sm text-ink-800 dark:text-paper-100 mb-2">{optimalApproach}</p>
            {(optimalTime || optimalSpace) && (
              <div className="text-xs font-mono text-ink-600 dark:text-paper-200/60">
                Target Optimal: <span className="font-bold text-teal-500">{optimalTime}</span> time · <span className="font-bold text-teal-500">{optimalSpace}</span> space
              </div>
            )}
          </div>
        )}
      </div>

      {/* Test Cases Run Result */}
      {testResults.length > 0 && (
        <div className="panel p-4 sm:p-5">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-mono uppercase tracking-wider text-ink-600 dark:text-paper-200/50">
              Test cases
            </p>
            <span className="text-xs font-mono text-ink-600 dark:text-paper-200/50">
              {testResults.filter((t) => t.passed).length}/{testResults.length} passed
            </span>
          </div>
          <div className="space-y-2">
            {testResults.map((t, i) => (
              <div key={i} className="flex items-start justify-between gap-3 text-xs font-mono rounded-lg border border-paper-200 dark:border-ink-600 p-2.5">
                <div className="min-w-0">
                  <p className="truncate">in: {t.input || '(empty)'}</p>
                  <p className="truncate text-ink-600 dark:text-paper-200/50">
                    expected: {t.expected_output || '(empty)'} {t.passed ? '' : `· got: ${t.actual_output || '(empty)'}`}
                  </p>
                </div>
                <span className={`shrink-0 px-2 py-0.5 rounded-full ${t.passed ? 'bg-teal-500/10 text-teal-500' : 'bg-coral-400/10 text-coral-400'}`}>
                  {t.passed ? 'PASS' : 'FAIL'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Concrete Actionable Suggestions */}
      {fb.improvement_suggestions?.length > 0 && (
        <div className="panel p-4 sm:p-5">
          <p className="text-xs font-mono uppercase tracking-wider text-ink-600 dark:text-paper-200/50 mb-2 font-bold">
            Concrete Action Items
          </p>
          <ul className="text-sm space-y-1.5 list-disc list-inside text-ink-800 dark:text-paper-100">
            {fb.improvement_suggestions.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Suggested Rewrite */}
      {fb.improved_code && (
        <div className="panel overflow-hidden">
          <p className="text-xs font-mono uppercase tracking-wider px-4 sm:px-5 pt-3.5 sm:pt-4 text-ink-600 dark:text-paper-200/50 font-bold">
            Suggested Clean Rewrite
          </p>
          <pre className="text-xs font-mono p-3.5 sm:p-5 overflow-x-auto scrollbar-thin bg-paper-100/50 dark:bg-ink-950/40">
            {fb.improved_code}
          </pre>
        </div>
      )}

      {/* Sandbox Output */}
      {(exec.stdout || exec.stderr || exec.compile_stderr) && (
        <div className="panel overflow-hidden">
          <p className="text-xs font-mono uppercase tracking-wider px-4 sm:px-5 pt-3.5 sm:pt-4 text-ink-600 dark:text-paper-200/50 font-bold">
            Sandbox execution log
          </p>
          <pre className="text-xs font-mono p-3.5 sm:p-5 overflow-x-auto scrollbar-thin whitespace-pre-wrap">
            {exec.compile_stderr && <span className="text-coral-400">{exec.compile_stderr}\n</span>}
            {exec.stdout}
            {exec.stderr && <span className="text-coral-400">{exec.stderr}</span>}
          </pre>
        </div>
      )}
    </div>
  )
}
