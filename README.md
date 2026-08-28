# DSA Coach — Feedback Generation

**Group:** Mind Matrix (`GENAICH-010`)
**Members:** Deep Sikha Baliyarsingh, Taniprava Sahoo, Arpita Panda
**Domain:** DSA · Generative AI / LLM applications
**Agent kept from the original architecture:** `Code Exec Agent` (LLM + sandbox tool)

An AI-powered coding platform where a learner pastes (or photographs) a DSA solution,
states the problem, constraints, and their claimed time/space complexity, and gets
**genuine, specific feedback** — not generic praise — from a Gemini-backed agent that
actually *runs* the code before reviewing it.

---

## Why this covers the brief

| Requirement | How it's covered |
|---|---|
| Generative AI / LLM applications | Gemini (`gemini-3.6-flash`) reasons over the problem + code + real execution trace |
| Prompt Engineering | Structured JSON-schema prompt in `backend/agent.py` (`FEEDBACK_PROMPT`) |
| AI-based automation | The whole review pipeline (OCR → execute → critique) runs as one LangGraph graph, no manual steps |
| AI-enabled full-stack project | FastAPI backend + React/Tailwind frontend, wired end to end |

Of the seven-node architecture explored during design (Supervisor, RAG Retrieval,
Rubric Generator, Step Evaluator, **Code Exec Agent**, Hint/Socratic Agent, Rank
Aggregator, Gamification Agent — see `/docs` images), this build intentionally keeps
**only the Code Exec Agent**, per the brief, and gives it everything it needs to stand
alone: image OCR, real sandboxed execution, and structured critique.

## Architecture

```
                 ┌─────────────────────────────────────────┐
                 │              Code Exec Agent             │
                 │              (LangGraph graph)            │
User submits ──▶ │  1. read_input        (Gemini Vision OCR) │
 problem +       │  2. execute_code      (Piston sandbox)    │
 constraints +   │  3. generate_feedback (Gemini reasoning)  │──▶ structured feedback JSON
 code/image      └─────────────────────────────────────────┘         │
                                                                        ▼
                                                              React feedback panel
                                                            + daily streak heatmap
```

- **`read_input`** — if the user uploaded an image instead of typing code, Gemini's
  multimodal vision transcribes the code exactly as written (no auto-fixing bugs).
- **`execute_code`** — the code is actually run via [Piston](https://github.com/engineer-man/piston),
  a free multi-language execution API (Python, Java, C, C++, JS, TS, Go, Rust, C#,
  Ruby, Kotlin, Swift, ...), so feedback is grounded in what the code *really* does,
  not just how it looks.
- **`generate_feedback`** — Gemini receives the problem statement, constraints, the
  user's claimed Big-O, the code, and the real stdout/stderr, and returns strict JSON:
  verdict, actual complexity, missed edge cases, bugs, concrete improvement steps, and
  an optional rewritten solution.

## Project structure

```
dsa-coach-mindmatrix/
├── backend/
│   ├── main.py          # FastAPI app: /api/analyze, /api/streak, /api/languages, /api/rag/*
│   ├── agent.py          # Code Exec Agent (LangGraph + Gemini)
│   ├── piston_client.py  # multi-language sandbox execution (Judge0 default, Piston secondary)
│   ├── auth.py            # username/password auth (bcrypt + JWT)
│   ├── config/
│   │   ├── agents.yaml     # agent persona: role / goal / backstory (CrewAI-style)
│   │   └── tools.yaml       # tool config: sandbox provider, vision model, RAG settings + data-source manifest
│   ├── config_loader.py   # loads + validates agents.yaml and tools.yaml
│   ├── streak_db.py       # SQLite daily-practice tracker
│   ├── rag/                # RAG ingestion/indexing pipeline (see "RAG module" below)
│   │   ├── loaders.py, chunking.py, embeddings.py, indexing.py
│   │   ├── ingestion.py, evaluation.py
│   │   └── data/
│   │       ├── knowledge_base/          # DSA pattern write-ups (bundled, markdown)
│   │       └── pdf/
│   │           ├── tech_interview_handbook/   # empty - add your own PDF export
│   │           └── neetcode_leetcode/          # empty - add your own PDF export
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── api.js
    │   └── components/
    │       ├── Header.jsx, ThemeToggle.jsx
    │       ├── ProblemForm.jsx, CodeEditor.jsx, ImageUpload.jsx
    │       ├── FeedbackPanel.jsx, StreakTracker.jsx
    ├── tailwind.config.js
    └── package.json
```

## Setup

### 1. Get a Gemini API key
Create one free at https://aistudio.google.com/apikey

### 2. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then paste your GEMINI_API_KEY into .env
uvicorn main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 — the Vite dev server proxies `/api` to the backend on
port 8000 (see `vite.config.js`).

## Features

0. **Login / sign up** — a real account system (username + password, bcrypt-hashed,
   JWT session tokens). Every solve and every streak box is tied to the logged-in
   user's own account, `backend/auth.py` + `backend/main.py` (`/api/register`,
   `/api/login`) + `frontend/src/components/Login.jsx`. No one can see or extend
   another user's streak.
1. **Upload a photo of your code** (or paste a file's contents) — Gemini Vision reads
   handwritten notes, IDE screenshots, or notebook photos.
2. **12+ languages** — Python, Java, C, C++, JavaScript, TypeScript, Go, Rust, C#,
   Ruby, Kotlin, Swift, real-executed via Piston.
3. **Genuine feedback, not flattery** — actual vs. claimed Big-O, missed edge cases,
   real bugs from the sandbox run, and concrete "how to improve" steps.
3.5. **Real test-case verification** — add input → expected-output pairs
   (`frontend/src/components/TestCases.jsx`); the Code Exec Agent runs your code
   against every one of them in the Piston sandbox and reports actual PASS/FAIL,
   not a guess. If any case fails, the verdict is forced to `partially_correct` or
   `incorrect` — Gemini is not allowed to call it "correct" on vibes
   (`backend/agent.py`, `execute_code_node` + the verdict rule in `FEEDBACK_PROMPT`).
4. **Light + dark theme**, toggle persisted in `localStorage`.
5. **Daily practice streak, tracked correctly per user** — a GitHub/LeetCode-style
   green heatmap. Every `/api/analyze` call is authenticated (JWT bearer token), so
   the backend always knows exactly whose solve to log — `streak_db.log_practice(username)`
   uses the username decoded from the token, never a value the client can spoof.
   The heatmap and current-streak count (`/api/streak`) are likewise scoped to the
   logged-in user only.
6. **Problem-first UI** — problem statement, constraints, and your claimed
   time/space complexity sit right next to the editor, so the agent always reviews
   your code *against the actual problem*, not in a vacuum.

## Auth flow

1. `POST /api/register` (username, password) or `POST /api/login` returns
   `{ access_token, username }`. Passwords are bcrypt-hashed in `backend/users.db`,
   never stored in plaintext.
2. The frontend stores the token in `localStorage` (`frontend/src/auth.js`) and
   attaches `Authorization: Bearer <token>` to every `/api/analyze` and `/api/streak`
   call.
3. `get_current_username()` in `backend/main.py` decodes the JWT on every protected
   request — the username used to log a streak or fetch a heatmap always comes from
   the verified token, never from a form field the client could edit.
4. Logging out (`Header.jsx`) just clears the local token; the session naturally
   expires after 7 days either way (`TOKEN_EXPIRY_SECONDS` in `backend/auth.py`).

## Agent config (`backend/config/agents.yaml`)

The Code Exec Agent's persona - **role**, **goal**, and **backstory** - lives
in `backend/config/agents.yaml`, not hardcoded in `agent.py`. This is the same
shape CrewAI uses for `Agent()` definitions, so it'd plug straight into an
actual `crewai.Agent(**config)` call later without changing the file format.

`config_loader.py` reads and validates it (fails loudly if a field is
missing), and `agent.py` loads it once at import time into `AGENT_CONFIG`,
then injects `role`/`goal`/`backstory` into the top of `FEEDBACK_PROMPT` on
every request.

**To change how the agent talks or what it prioritizes, edit the YAML - no
code changes needed.** Restart the backend (or let `--reload` pick it up) for
the change to take effect.

Check it's loading correctly any time via:
```
GET /api/agent/config
```

## Tool config (`backend/config/tools.yaml`)

Separate from the agent's persona (`config/agents.yaml`), this file holds
**tool** defaults: which sandbox provider to use, the vision-OCR model, RAG
chunk size/overlap/top-k, and - importantly - the **RAG data-source
manifest**: the full list of places `rag/ingestion.py` reads from.

Where a `.env` variable exists for the same setting (`CODE_EXECUTOR`,
`GEMINI_MODEL`, `RAG_EMBEDDING_MODEL`), `.env` wins at runtime - `tools.yaml`
only supplies the fallback default, and documents settings that have no
`.env` equivalent at all (chunk size/overlap, top-k, the data-source list).

Check what's currently loaded via:
```
GET /api/tools/config
```

**Data sources** (`rag_retrieval.data_sources` in the YAML):
| Path | Type | Notes |
|---|---|---|
| `rag/data/knowledge_base/` | markdown | Bundled - 6 hand-written DSA pattern notes |
| `rag/data/pdf/tech_interview_handbook/` | pdf | **Empty by default** - [Tech Interview Handbook](https://www.techinterviewhandbook.org/) content is copyrighted by its authors and isn't bundled here. Drop your own PDF export in and re-run ingestion. |
| `rag/data/pdf/neetcode_leetcode/` | pdf | **Empty by default** - same reasoning for NeetCode/LeetCode content. Add your own notes/exports. |

`rag/loaders.py`'s `load_all_sources()` reads this manifest and loads every
listed source automatically - `load_pdf_documents()` extracts text page by
page via `pypdf`, and gracefully returns an empty list (not an error) for the
two PDF folders until you actually put a PDF in them.

## RAG module (`backend/rag/`)

A small, self-contained retrieval pipeline over a local DSA "knowledge base"
(pattern write-ups: two pointers, sliding window, binary search, DP, graph
traversal, backtracking - `backend/rag/data/knowledge_base/`). Scoped to
exactly six pieces, deliberately **not** wired into the Code Exec Agent's live
feedback yet:

| File | Responsibility |
|---|---|
| `loaders.py` | Reads `.md`/`.txt` files from the knowledge base into a common `Document` shape |
| `chunking.py` | Splits documents into ~800-character overlapping chunks on paragraph boundaries |
| `embeddings.py` | Embeds chunks/queries with Gemini's `text-embedding-004` (same `GEMINI_API_KEY`, no extra key) |
| `indexing.py` | A lightweight local vector store (`VectorIndex`, plain numpy cosine similarity, persisted to JSON) - chosen over FAISS/Chroma to avoid another native-dependency install on Windows |
| `ingestion.py` | Orchestrates the four pieces above into one pipeline: `run_ingestion()` |
| `evaluation.py` | RAGAS-inspired retrieval metrics (hit-rate@k, MRR, avg top-1 similarity) against a small hand-labeled gold query set |

**Run it:**
```bash
cd backend
python -m rag.ingestion     # builds/rebuilds the index from the knowledge base
python -m rag.evaluation    # reports retrieval quality against the gold set
```

Or via the API (also exposed for convenience, not tied to a logged-in user):
```
POST /api/rag/ingest
GET  /api/rag/evaluate?top_k=3
```

**Intentionally not included:** `retriever.py` / `hybrid_retriever.py` /
`reranker.py` / `generator.py` / `prompts.py` — those would wire retrieved
context into the Code Exec Agent's feedback generation, which is a separate
piece of work. Right now the RAG pipeline is a standalone, testable
ingestion+indexing system; `indexing.py`'s `VectorIndex.search()` is the only
retrieval happening, and it's currently only exercised by `evaluation.py`.

## Notes on scope

- The code sandbox defaults to **Judge0** via RapidAPI's free tier (50 requests/day,
  no card needed) — see `backend/.env.example` for how to get a key. Piston is kept
  as a secondary option (`CODE_EXECUTOR=piston`), but as of Feb 2026 its free public
  API requires an authorized key from the maintainer, so it won't work out of the box.
- `streaks.db` and `users.db` are local SQLite files for demo purposes — swap for
  Postgres/Mongo for multi-user production deployments.
- Set a real `JWT_SECRET` in `.env` before deploying anywhere public — the default
  in `.env.example` is for local development only.
# DSA-COACH-FEEDBACK-GENERATOR
