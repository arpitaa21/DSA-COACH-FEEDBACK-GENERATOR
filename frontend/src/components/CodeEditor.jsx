import CodeMirror from '@uiw/react-codemirror'
import { langs } from '@uiw/codemirror-extensions-langs'
import { EditorView } from '@codemirror/view'

const LANGUAGE_LABELS = {
  python: 'Python', java: 'Java', c: 'C', cpp: 'C++', javascript: 'JavaScript',
  typescript: 'TypeScript', go: 'Go', rust: 'Rust', csharp: 'C#', ruby: 'Ruby',
  kotlin: 'Kotlin', swift: 'Swift',
}

// map our language keys -> codemirror-extensions-langs keys
const CM_LANG = {
  python: 'python', java: 'java', c: 'c', cpp: 'cpp', javascript: 'javascript',
  typescript: 'typescript', go: 'go', rust: 'rust', csharp: 'csharp', ruby: 'ruby',
  kotlin: 'kotlin', swift: 'swift',
}

const makeEditorTheme = (dark) => EditorView.theme({
  '&': { fontSize: '13px', backgroundColor: 'transparent', color: dark ? '#f2eee2' : '#0f1620' },
  '.cm-content': { fontFamily: "'JetBrains Mono', monospace", padding: '12px 0', caretColor: dark ? '#f2b134' : '#0f1620' },
  '.cm-gutters': { backgroundColor: 'transparent', border: 'none', color: dark ? 'rgba(242,238,226,0.4)' : 'rgba(15,22,32,0.4)' },
  '.cm-activeLine': { backgroundColor: 'rgba(242,177,52,0.06)' },
  '.cm-activeLineGutter': { backgroundColor: 'transparent' },
}, { dark })

export default function CodeEditor({ code, setCode, language, setLanguage, languages, theme }) {
  const isDark = theme === 'dark'
  const extensions = [makeEditorTheme(isDark)]
  const langFn = langs[CM_LANG[language]]
  if (langFn) extensions.unshift(langFn())

  return (
    <div className="panel overflow-hidden flex flex-col">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-paper-200 dark:border-ink-700 bg-paper-100/60 dark:bg-ink-800/60">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-coral-400" />
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
          <span className="w-2.5 h-2.5 rounded-full bg-teal-400" />
          <span className="ml-2 text-xs font-mono text-ink-600 dark:text-paper-200/50">solution.{ext(language)}</span>
        </div>
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="text-xs font-mono bg-transparent border border-paper-200 dark:border-ink-600 rounded-md px-2 py-1 focus:outline-none"
        >
          {(languages.length ? languages : Object.keys(LANGUAGE_LABELS)).map((l) => (
            <option key={l} value={l}>{LANGUAGE_LABELS[l] || l}</option>
          ))}
        </select>
      </div>

      <CodeMirror
        value={code}
        onChange={setCode}
        height="280px"
        theme={isDark ? 'dark' : 'light'}
        extensions={extensions}
        basicSetup={{ lineNumbers: true, foldGutter: false, highlightActiveLine: true }}
        placeholder={`# paste or type your ${LANGUAGE_LABELS[language] || language} solution here`}
        className="scrollbar-thin"
      />
    </div>
  )
}

function ext(lang) {
  const map = { python: 'py', java: 'java', c: 'c', cpp: 'cpp', javascript: 'js', typescript: 'ts', go: 'go', rust: 'rs', csharp: 'cs', ruby: 'rb', kotlin: 'kt', swift: 'swift' }
  return map[lang] || 'txt'
}
