import ThemeToggle from './ThemeToggle.jsx'

export default function Header({ theme, setTheme }) {
  return (
    <header className="flex items-center justify-between px-4 sm:px-6 md:px-10 py-3.5 sm:py-5 border-b border-paper-200 dark:border-ink-700 bg-paper-50/50 dark:bg-ink-950/50 backdrop-blur-sm sticky top-0 z-20">
      <div className="flex items-center gap-2.5 sm:gap-3">
        <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-lg bg-ink-900 dark:bg-amber-400 flex items-center justify-center font-mono font-extrabold text-amber-400 dark:text-ink-950 text-xs sm:text-sm shadow-sm flex-shrink-0">
          {'</>'}
        </div>
        <div className="min-w-0">
          <p className="font-mono font-bold text-base sm:text-lg tracking-tight leading-none truncate">
            DSA<span className="text-amber-500">Coach</span>
          </p>
          <p className="text-[9px] sm:text-[11px] uppercase tracking-[0.14em] sm:tracking-[0.18em] text-ink-600 dark:text-paper-200/60 leading-none mt-1 truncate">
            Mind Matrix &middot; GENAICH-010
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2.5 sm:gap-4 flex-shrink-0">
        <ThemeToggle theme={theme} setTheme={setTheme} />
      </div>
    </header>
  )
}
