import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { setTimeout as delay } from 'node:timers/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const frontendDir = path.dirname(fileURLToPath(import.meta.url))
const projectDir = path.resolve(frontendDir, '..')
const backendDir = path.join(projectDir, 'backend')
const mode = process.argv[2] === 'dev' ? 'dev' : 'preview'
const apiHealthUrl = 'http://127.0.0.1:8000/api/languages'
const pythonCandidates = [
  path.join(backendDir, 'venv', 'Scripts', 'python.exe'),
  path.join(backendDir, 'venv', 'bin', 'python'),
  path.join(backendDir, '.venv', 'Scripts', 'python.exe'),
  path.join(backendDir, '.venv', 'bin', 'python'),
]
const python = pythonCandidates.find(existsSync) ?? 'python'
const viteArgs = mode === 'dev'
  ? ['node_modules/vite/bin/vite.js', '--host', '127.0.0.1']
  : ['node_modules/vite/bin/vite.js', 'preview', '--host', '127.0.0.1']

let backendProcess
let viteProcess
let stopping = false

async function apiIsReady() {
  try {
    const response = await fetch(apiHealthUrl, { signal: AbortSignal.timeout(1500) })
    return response.ok
  } catch {
    return false
  }
}

async function stop() {
  if (stopping) return
  stopping = true
  if (viteProcess && viteProcess.exitCode === null) viteProcess.kill()
  if (backendProcess && backendProcess.exitCode === null) backendProcess.kill()
}

process.on('SIGINT', stop)
process.on('SIGTERM', stop)

if (!(await apiIsReady())) {
  console.log('Starting FastAPI backend on http://127.0.0.1:8000 ...')
  backendProcess = spawn(python, ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8000'], {
    cwd: backendDir,
    stdio: 'inherit',
    windowsHide: true,
  })

  backendProcess.once('error', (error) => {
    console.error(`Could not start the backend with ${python}: ${error.message}`)
    process.exitCode = 1
    void stop()
  })

  let ready = false
  for (let attempt = 0; attempt < 60 && !stopping; attempt += 1) {
    if (await apiIsReady()) {
      ready = true
      break
    }
    if (backendProcess.exitCode !== null) break
    await delay(500)
  }

  if (!ready) {
    console.error('Backend did not become ready. Check the backend startup output above.')
    await stop()
    process.exit(1)
  }
} else {
  console.log('Using existing FastAPI backend on http://127.0.0.1:8000.')
}

console.log(mode === 'dev' ? 'Starting Vite development server ...' : 'Starting Vite preview server ...')
viteProcess = spawn(process.execPath, viteArgs, { cwd: frontendDir, stdio: 'inherit', windowsHide: true })
viteProcess.once('error', (error) => {
  console.error(`Could not start Vite: ${error.message}`)
  process.exitCode = 1
  void stop()
})
viteProcess.once('exit', async (code) => {
  await stop()
  process.exitCode = code ?? 0
})

backendProcess?.once('exit', (code) => {
  if (!stopping && code !== 0) {
    console.error(`Backend exited with code ${code}.`)
    void stop()
    process.exitCode = 1
  }
})
