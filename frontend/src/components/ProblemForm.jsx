function Field({ label, children }) {
  return (
    <label className="block mb-4">
      <span className="block text-xs font-mono uppercase tracking-wider text-ink-600 dark:text-paper-200/60 mb-1.5">
        {label}
      </span>
      {children}
    </label>
  )
}

const inputCls =
  'w-full rounded-lg border border-paper-200 dark:border-ink-600 bg-paper-50 dark:bg-ink-800 px-3 py-2 text-sm ' +
  'focus:outline-none focus:ring-2 focus:ring-amber-400/60 placeholder:text-ink-600/40 dark:placeholder:text-paper-200/30'

export default function ProblemForm({ form, setForm }) {
  const update = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  return (
    <div className="panel p-5">
      <h2 className="font-mono font-bold text-sm mb-4 flex items-center gap-2">
        <span className="text-amber-500">01</span> Problem setup
      </h2>

      <Field label="Problem statement">
        <textarea
          rows={3}
          className={inputCls}
          placeholder="e.g. Given an array of integers, return indices of the two numbers that add up to target..."
          value={form.problemStatement}
          onChange={update('problemStatement')}
        />
      </Field>

      <Field label="Constraints">
        <textarea
          rows={2}
          className={inputCls}
          placeholder="e.g. 2 <= nums.length <= 10^4, -10^9 <= nums[i] <= 10^9"
          value={form.constraints}
          onChange={update('constraints')}
        />
      </Field>

      <div className="grid grid-cols-2 gap-3">
        <Field label="Your claimed time complexity">
          <input className={inputCls} placeholder="O(n)" value={form.claimedTimeComplexity} onChange={update('claimedTimeComplexity')} />
        </Field>
        <Field label="Your claimed space complexity">
          <input className={inputCls} placeholder="O(n)" value={form.claimedSpaceComplexity} onChange={update('claimedSpaceComplexity')} />
        </Field>
      </div>
    </div>
  )
}
