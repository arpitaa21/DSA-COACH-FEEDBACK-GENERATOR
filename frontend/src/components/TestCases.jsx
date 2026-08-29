const inputCls =
  'w-full rounded-lg border border-paper-200 dark:border-ink-600 bg-paper-50 dark:bg-ink-800 px-3 py-2 text-xs font-mono ' +
  'focus:outline-none focus:ring-2 focus:ring-amber-400/60'

export default function TestCases({ testCases, setTestCases, results }) {
  const update = (i, key, value) => {
    setTestCases((tcs) => tcs.map((tc, idx) => (idx === i ? { ...tc, [key]: value } : tc)))
  }
  const addCase = () => setTestCases((tcs) => [...tcs, { input: '', expected_output: '' }])
  const removeCase = (i) => setTestCases((tcs) => tcs.filter((_, idx) => idx !== i))

  return (
    <div className="panel p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-mono font-bold text-sm flex items-center gap-2">
          <span className="text-amber-500">03</span> Test cases <span className="text-ink-600 dark:text-paper-200/40 font-normal">(optional, but recommended)</span>
        </h3>
        <button onClick={addCase} className="text-xs font-mono text-amber-500 hover:underline">+ add case</button>
      </div>

      {testCases.length === 0 && (
        <p className="text-xs text-ink-600 dark:text-paper-200/50">
          No test cases yet — without them, the agent verdict is based on a single execution, not verified pass/fail.
        </p>
      )}

      <div className="space-y-3">
        {testCases.map((tc, i) => {
          const result = results?.[i]
          return (
            <div key={i} className="rounded-lg border border-paper-200 dark:border-ink-600 p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-mono text-ink-600 dark:text-paper-200/50">Case {i + 1}</span>
                <div className="flex items-center gap-2">
                  {result && (
                    <span className={`text-[11px] font-mono px-2 py-0.5 rounded-full ${result.passed ? 'bg-teal-500/10 text-teal-500' : 'bg-coral-400/10 text-coral-400'}`}>
                      {result.passed ? 'PASS' : 'FAIL'}
                    </span>
                  )}
                  <button onClick={() => removeCase(i)} className="text-[11px] text-coral-400 hover:underline">remove</button>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <textarea rows={2} className={inputCls} placeholder="stdin input" value={tc.input} onChange={(e) => update(i, 'input', e.target.value)} />
                <textarea rows={2} className={inputCls} placeholder="expected stdout" value={tc.expected_output} onChange={(e) => update(i, 'expected_output', e.target.value)} />
              </div>
              {result && !result.passed && (
                <p className="text-[11px] font-mono mt-2 text-coral-400">
                  got: {result.actual_output || '(empty)'}{result.stderr ? ` · ${result.stderr.slice(0, 120)}` : ''}
                </p>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
