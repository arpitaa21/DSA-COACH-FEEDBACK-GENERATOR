// Two-tone heatmap: dim teal = attempted but not solved, full teal = solved.
// A day with zero attempts stays neutral. This is what makes the streak honest -
// spamming broken submissions lights up "attempted" but never "solved", and the
// streak counter (backend) only advances on solved days.

function cellClass(day) {
  if (day.solved > 0) {
    if (day.solved >= 4) return 'bg-teal-400'
    if (day.solved >= 2) return 'bg-teal-400/80'
    return 'bg-teal-400/55'
  }
  if (day.attempted > 0) return 'bg-amber-400/35'
  return 'bg-paper-200 dark:bg-ink-700'
}

export default function StreakTracker({ heatmap, currentStreak, totals }) {
  const weeks = []
  for (let i = 0; i < heatmap.length; i += 7) {
    weeks.push(heatmap.slice(i, i + 7))
  }

  return (
    <div className="panel p-5">
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <h3 className="font-mono font-bold text-sm flex items-center gap-2">
          <span className="text-amber-500">04</span> Daily practice streak
        </h3>
        <div className="flex items-center gap-4 text-xs font-mono text-ink-600 dark:text-paper-200/60">
          <span>🔥 {currentStreak}-day streak</span>
          <span>{totals?.solved ?? 0} solved / {totals?.attempted ?? 0} attempted (6 mo)</span>
        </div>
      </div>

      <div className="flex gap-[3px] overflow-x-auto scrollbar-thin pb-1">
        {weeks.map((week, wi) => (
          <div key={wi} className="flex flex-col gap-[3px]">
            {week.map((day) => (
              <div
                key={day.date}
                title={`${day.date}: ${day.solved} solved / ${day.attempted} attempted`}
                className={`w-[10px] h-[10px] rounded-sm ${cellClass(day)}`}
              />
            ))}
          </div>
        ))}
      </div>

      <div className="flex items-center gap-4 mt-3 text-[11px] text-ink-600 dark:text-paper-200/40">
        <span className="flex items-center gap-1.5"><span className="w-[10px] h-[10px] rounded-sm bg-amber-400/35 inline-block" /> attempted, not solved</span>
        <span className="flex items-center gap-1.5"><span className="w-[10px] h-[10px] rounded-sm bg-teal-400 inline-block" /> solved</span>
      </div>
    </div>
  )
}
