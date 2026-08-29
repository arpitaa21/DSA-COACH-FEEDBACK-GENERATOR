<div align="center">

# 🧠 DSA Coach — Feedback Generation

### *Genuine, execution-grounded code review for DSA practice — not AI flattery.*

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react&logoColor=black)
![Gemini](https://img.shields.io/badge/Gemini-3.6--flash-8E75B2?logo=googlegemini&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent%20Orchestration-1C3C3C)
![Judge0](https://img.shields.io/badge/Judge0-Code%20Sandbox-F7931E)
![Status](https://img.shields.io/badge/Status-Academic%20Project-lightgrey)


</div>

---

An AI-powered coding platform where a learner pastes (or photographs) a DSA
solution, states the problem, constraints, and their claimed time/space
complexity — and gets **genuine, specific feedback**, from an agent that
actually *runs* the code before reviewing it, instead of guessing from
appearances.


---

## ✅ Why This Covers the Brief

| Requirement | How it's covered |
|---|---|
| **Generative AI / LLM applications** | Gemini (`gemini-3.6-flash`) reasons over the problem + code + real execution trace |
| **Prompt Engineering** | Structured JSON-schema prompt in `backend/agent.py` (`FEEDBACK_PROMPT`) |
| **AI-based automation** | The whole review pipeline (OCR → execute → critique) runs as one LangGraph graph, no manual steps |
| **AI-enabled full-stack project** | FastAPI backend + React/Tailwind frontend, wired end to end |

> Of the seven-node architecture explored during design (Supervisor, RAG
> Retrieval, Rubric Generator, Step Evaluator, **Code Exec Agent**,
> Hint/Socratic Agent, Rank Aggregator, Gamification Agent), this build
> intentionally keeps **only the Code Exec Agent**, per the brief — and gives
> it everything it needs to stand alone: image OCR, real sandboxed execution,
> and structured critique.

## 🏗️ Architecture

```
                  ┌─────────────────────────────────────────────┐
                  │              Code Exec Agent                │
                  │              (LangGraph graph)              │
User submits ──▶  │   1. read_input        (Gemini Vision OCR)   │
 problem +        │   2. execute_code      (Judge0 sandbox)     │
 constraints +    │   3. generate_feedback (Gemini reasoning)   │  ──▶ structured feedback JSON
 code/image      └──────────────────────────────────────────────┘         │
                                                                          ▼
                                                                React feedback panel
                                                              + daily streak heatmap
```

| Step | What happens |
|---|---|
| 🖼️ **`read_input`** | If the user uploaded an image instead of typing code, Gemini's multimodal vision transcribes it exactly as written (no auto-fixing bugs). |
| ⚙️ **`execute_code`** | The code actually runs via [Judge0](https://judge0.com) (Python, Java, C, C++, JS, TS, Go, Rust, C#, Ruby, Kotlin, Swift...) — feedback is grounded in what the code *really* does. |
| 🧾 **`generate_feedback`** | Gemini receives the problem, constraints, claimed Big-O, code, and real stdout/stderr, and returns strict JSON: verdict, actual complexity, missed edge cases, bugs, concrete fixes, and an optional rewrite. |

## 📁 Project Structure

```
dsa-coach-mindmatrix/
├── backend/
│   ├── main.py               # FastAPI app: /api/analyze, /api/streak, /api/languages, /api/rag/*
│   ├── agent.py                # Code Exec Agent (LangGraph + Gemini)
│   ├── piston_client.py       # multi-language sandbox execution (Judge0 default, Piston secondary)
│   ├── auth.py                  # username/password auth (bcrypt + JWT)
│   ├── config/
│   │   ├── agents.yaml           # agent persona: role / goal / backstory (CrewAI-style)
│   │   └── tools.yaml             # tool config: sandbox provider, vision model, RAG settings
│   ├── config_loader.py         # loads + validates agents.yaml and tools.yaml
│   ├── streak_db.py             # SQLite daily-practice tracker
│   ├── rag/                      # RAG ingestion/indexing pipeline
│   │   ├── loaders.py, chunking.py, embeddings.py, indexing.py
│   │   ├── ingestion.py, evaluation.py
│   │   └── data/
│   │       ├── knowledge_base/            # DSA pattern write-ups (bundled, markdown)
│   │       └── pdf/
│   │           ├── tech_interview_handbook/   # empty — add your own PDF export
│   │           └── neetcode_leetcode/          # empty — add your own PDF export
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

## 🚀 Quick Start

### 1. Get a free Gemini API key
Create one at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

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

Open **http://localhost:5173** — the Vite dev server proxies `/api` to the
backend on port `8000` (see `vite.config.js`).

## ✨ Features

| | Feature | Details |
|---|---|---|
| 🔐 | **Login / sign up** | bcrypt-hashed passwords + JWT session tokens. Every solve and streak box is tied to the logged-in user's own account — no one can see or extend another user's streak. |
| 📸 | **Upload a photo of your code** | Gemini Vision reads handwritten notes, IDE screenshots, or notebook photos. |
| 🌐 | **12+ languages** | Python, Java, C, C++, JavaScript, TypeScript, Go, Rust, C#, Ruby, Kotlin, Swift — real-executed via Judge0. |
| 🎯 | **Genuine feedback, not flattery** | Actual vs. claimed Big-O, missed edge cases, real bugs from the sandbox run, concrete "how to improve" steps. |
| ✅ | **Real test-case verification** | Add input → expected-output pairs; the agent runs your code against each one and reports actual PASS/FAIL. If any case fails, the verdict is forced to `partially_correct`/`incorrect` — never inflated. |
| 🌗 | **Light + dark theme** | Toggle persisted in `localStorage`. |
| 🔥 | **Daily practice streak** | GitHub/LeetCode-style green heatmap, correctly scoped per authenticated user via JWT — never spoofable from the client. |
| 📝 | **Problem-first UI** | Problem statement, constraints, and claimed complexity sit right next to the editor, so the agent always reviews your code *against the actual problem*. |

## 🔑 Auth Flow

1. `POST /api/register` or `POST /api/login` returns `{ access_token, username }`. Passwords are bcrypt-hashed in `backend/users.db`, never stored in plaintext.
2. The frontend stores the token in `localStorage` and attaches `Authorization: Bearer <token>` to every protected call.
3. `get_current_username()` in `backend/main.py` decodes the JWT on every request — the username used to log a streak always comes from the verified token, never a client-editable field.
4. Sessions expire after 7 days (`TOKEN_EXPIRY_SECONDS` in `backend/auth.py`).

## 🤖 Agent Config

The Code Exec Agent's persona — **role**, **goal**, and **backstory** — lives
in `backend/config/agents.yaml`, not hardcoded in `agent.py`. Same shape
CrewAI uses for `Agent()` definitions.

> **To change how the agent talks or what it prioritizes, edit the YAML — no
> code changes needed.**

```
GET /api/agent/config    # verify what's currently loaded
```

## 🛠️ Tool Config

`backend/config/tools.yaml` holds tool-level defaults: sandbox provider,
vision-OCR model, RAG chunk size/overlap/top-k, and the **RAG data-source
manifest**. Where a `.env` variable exists for the same setting, `.env` wins
at runtime — `tools.yaml` supplies the fallback + documents everything else.

```
GET /api/tools/config     # verify what's currently loaded
```

| Path | Type | Notes |
|---|---|---|
| `rag/data/knowledge_base/` | markdown | Bundled — 6 hand-written DSA pattern notes |
| `rag/data/pdf/tech_interview_handbook/` | pdf | Empty by default — add your own PDF export |
| `rag/data/pdf/neetcode_leetcode/` | pdf | Empty by default — add your own notes/exports |

## 📚 RAG Module

A small, self-contained retrieval pipeline over a local DSA knowledge base
(two pointers, sliding window, binary search, DP, graph traversal,
backtracking). Scoped to exactly six pieces:

| File | Responsibility |
|---|---|
| `loaders.py` | Reads `.md`/`.txt`/`.pdf` sources into a common `Document` shape |
| `chunking.py` | Splits documents into overlapping chunks on paragraph boundaries |
| `embeddings.py` | Embeds chunks/queries with Gemini's embedding model |
| `indexing.py` | Lightweight local vector store — plain numpy cosine similarity, no extra native dependencies |
| `ingestion.py` | Orchestrates the pipeline: `run_ingestion()` |
| `evaluation.py` | RAGAS-inspired retrieval metrics (hit-rate@k, MRR, avg similarity) against a gold query set |

```bash
cd backend
python -m rag.ingestion     # build/rebuild the index
python -m rag.evaluation    # check retrieval quality
```

<details>
<summary><strong>Or via the API</strong></summary>

```
POST /api/rag/ingest
GET  /api/rag/evaluate?top_k=3
```

</details>

> **Intentionally not included:** `retriever.py` / `hybrid_retriever.py` /
> `reranker.py` / `generator.py` / `prompts.py` — wiring retrieved context
> into the Code Exec Agent's live feedback is a deliberately separate,
> not-yet-built piece. `indexing.py`'s `VectorIndex.search()` is the only
> retrieval happening right now, exercised by `evaluation.py`.

## 🧭 Notes on Scope

- The code sandbox defaults to **Judge0** via RapidAPI's free tier (50 requests/day, no card needed). Piston is kept as a secondary option (`CODE_EXECUTOR=piston`), but its free public API has required an authorized key since Feb 2026.
- `streaks.db` and `users.db` are local SQLite files for demo purposes — swap for Postgres/MongoDB for multi-user production deployments.
- Set a real `JWT_SECRET` in `.env` before deploying anywhere public.

---

<div align="center">

**DSA COACH FEEDBACK GENERATOR**

</div>
