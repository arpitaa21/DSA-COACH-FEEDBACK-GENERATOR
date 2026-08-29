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
  if (error) {
    return (
      <div className="panel p-5 border-coral-400/40">
        <p className="font-mono text-sm text-coral-400">Agent error</p>
        <p className="text-sm mt-1 text-ink-600 dark:text-paper-200/70">{error}</p>
      </div>
    )
  }

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

  if (!result) {
    return (
      <div className="panel p-8 text-center">
        <p className="font-mono text-sm text-ink-600 dark:text-paper-200/50">
          Submit your solution to get feedback from the Code Exec Agent →
        </p>
      </div>
    )
  }

  const fb = result.feedback || {}
  const exec = result.execution_result || {}
  const testResults = result.test_results || []

  return (
    <div className="space-y-4">
      <div className="panel p-5">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <span className={`text-xs font-mono px-2.5 py-1 rounded-full border ${VERDICT_STYLE[fb.verdict] || 'bg-ink-100 text-ink-600'}`}>
            {VERDICT_LABEL[fb.verdict] || fb.verdict || 'Unknown'}
          </span>
          <span className="font-mono text-2xl font-bold">
            {fb.score ?? '—'}<span className="text-sm text-ink-600 dark:text-paper-200/40">/100</span>
          </span>
        </div>
        <p className="mt-3 text-sm italic text-ink-800 dark:text-paper-100">"{fb.one_line_summary}"</p>
        <p className="mt-2 text-sm text-ink-600 dark:text-paper-200/70">{fb.correctness_notes}</p>
      </div>

      {testResults.length > 0 && (
        <div className="panel p-5">
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

      <div className="panel p-5 grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs font-mono uppercase tracking-wider text-ink-600 dark:text-paper-200/50">Actual time</p>
          <p className="font-mono text-lg mt-1">{fb.actual_time_complexity || '—'}</p>
        </div>
        <div>
          <p className="text-xs font-mono uppercase tracking-wider text-ink-600 dark:text-paper-200/50">Actual space</p>
          <p className="font-mono text-lg mt-1">{fb.actual_space_complexity || '—'}</p>
        </div>
        {fb.complexity_notes && (
          <p className="col-span-2 text-sm text-ink-600 dark:text-paper-200/70">{fb.complexity_notes}</p>
        )}
      </div>

      {(fb.bugs?.length > 0 || fb.edge_cases_missed?.length > 0) && (
        <div className="panel p-5">
          {fb.bugs?.length > 0 && (
            <>
              <p className="text-xs font-mono uppercase tracking-wider text-coral-400 mb-2">Bugs / risks</p>
              <ul className="text-sm space-y-1 mb-3 list-disc list-inside text-ink-800 dark:text-paper-100">
                {fb.bugs.map((b, i) => <li key={i}>{b}</li>)}
              </ul>
            </>
          )}
          {fb.edge_cases_missed?.length > 0 && (
            <>
              <p className="text-xs font-mono uppercase tracking-wider text-amber-500 mb-2">Edge cases missed</p>
              <ul className="text-sm space-y-1 list-disc list-inside text-ink-800 dark:text-paper-100">
                {fb.edge_cases_missed.map((b, i) => <li key={i}>{b}</li>)}
              </ul>
            </>
          )}
        </div>
      )}

      {fb.improvement_suggestions?.length > 0 && (
        <div className="panel p-5">
          <p className="text-xs font-mono uppercase tracking-wider text-teal-500 mb-2">How to improve</p>
          <ul className="text-sm space-y-1.5 list-disc list-inside text-ink-800 dark:text-paper-100">
            {fb.improvement_suggestions.map((s, i) => <li key={i}>{s}</li>)}
          </ul>
        </div>
      )}

      {fb.improved_code && (
        <div className="panel overflow-hidden">
          <p className="text-xs font-mono uppercase tracking-wider px-5 pt-4 text-ink-600 dark:text-paper-200/50">Suggested rewrite</p>
          <pre className="text-xs font-mono p-5 overflow-x-auto scrollbar-thin">{fb.improved_code}</pre>
        </div>
      )}

      {(exec.stdout || exec.stderr || exec.compile_stderr) && (
        <div className="panel overflow-hidden">
          <p className="text-xs font-mono uppercase tracking-wider px-5 pt-4 text-ink-600 dark:text-paper-200/50">Sandbox output</p>
          <pre className="text-xs font-mono p-5 overflow-x-auto scrollbar-thin whitespace-pre-wrap">
            {exec.compile_stderr && <span className="text-coral-400">{exec.compile_stderr}\n</span>}
            {exec.stdout}
            {exec.stderr && <span className="text-coral-400">{exec.stderr}</span>}
          </pre>
        </div>
      )}
    </div>
  )
}
