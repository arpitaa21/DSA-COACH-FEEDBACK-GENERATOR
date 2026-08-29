"""
main.py
-------
DSA Coach - Feedback Generation
Group: Mind Matrix (GENAICH-010)
Agent: Code Exec Agent (LLM + sandbox tool) - powered by Gemini

FastAPI app exposing:
  POST /api/register, /api/login  -> username/password auth
  POST /api/analyze               -> run the Code Exec Agent, optionally against
                                       real test cases (input -> expected output)
  GET  /api/streak                -> the logged-in user's daily-practice heatmap
  GET  /api/languages             -> supported languages for the editor dropdown
"""

import base64
import json
import os
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Form, File, UploadFile, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import run_code_exec_agent
from piston_client import LANGUAGE_MAP
import streak_db
import auth
from rag.ingestion import run_ingestion
from rag.evaluation import evaluate_retrieval
from config_loader import load_agent_config, load_tools_config

app = FastAPI(title="DSA Coach - Feedback Generation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your frontend origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Auth: every streak / analyze call is tied to a real logged-in user, taken
# from the JWT, never from a client-supplied username field. This is what
# makes the daily-practice streak track correctly per person.
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    username: str
    display_name: str


async def get_current_username(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated. Please log in.")
    token = authorization.split(" ", 1)[1]
    username = auth.decode_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    return username


@app.post("/api/register", response_model=AuthResponse)
def register(payload: RegisterRequest):
    try:
        user = auth.create_user(payload.username, payload.password, payload.display_name)
    except auth.AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    token = auth.create_access_token(user["username"])
    return {"access_token": token, "username": user["username"], "display_name": user["display_name"]}


@app.post("/api/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    try:
        user = auth.verify_user(payload.username, payload.password)
    except auth.AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    token = auth.create_access_token(user["username"])
    return {"access_token": token, "username": user["username"], "display_name": user["display_name"]}


@app.get("/api/languages")
def languages():
    return {"languages": sorted(LANGUAGE_MAP.keys())}


class StreakResponse(BaseModel):
    username: str
    current_streak: int
    heatmap: list


@app.get("/api/streak", response_model=StreakResponse)
def get_streak(username: str = Depends(get_current_username)):
    return {
        "username": username,
        "current_streak": streak_db.get_current_streak(username),
        "heatmap": streak_db.get_heatmap(username),
    }


@app.post("/api/analyze")
async def analyze(
    language: str = Form("python"),
    problem_statement: str = Form(""),
    constraints: str = Form(""),
    claimed_time_complexity: str = Form(""),
    claimed_space_complexity: str = Form(""),
    code: str = Form(""),
    stdin: str = Form(""),
    test_cases_json: str = Form("[]"),
    image: Optional[UploadFile] = File(None),
    username: str = Depends(get_current_username),
):
    image_b64 = None
    if image is not None:
        raw = await image.read()
        image_b64 = base64.b64encode(raw).decode("utf-8")

    try:
        test_cases = json.loads(test_cases_json) if test_cases_json else []
        if not isinstance(test_cases, list):
            test_cases = []
    except json.JSONDecodeError:
        test_cases = []

    result = await run_code_exec_agent(
        language=language,
        problem_statement=problem_statement,
        constraints=constraints,
        claimed_time_complexity=claimed_time_complexity,
        claimed_space_complexity=claimed_space_complexity,
        code=code,
        stdin=stdin,
        test_cases=test_cases,
        image_b64=image_b64,
    )

    # one solve attempt logged for the streak tracker - tied to the real
    # authenticated user, so streaks can never leak between accounts.
    streak_db.log_practice(username)

    return {
        "extracted_code": result.get("code"),
        "execution_result": result.get("execution_result"),
        "test_results": result.get("test_results", []),
        "feedback": result.get("feedback"),
    }


@app.post("/api/rag/ingest")
def rag_ingest():
    """Rebuilds the local DSA knowledge-base index: loaders -> chunking ->
    embeddings -> indexing. Not tied to any user - this is a maintenance/setup
    operation, run it once after cloning (or after editing the knowledge base
    files in backend/rag/data/knowledge_base/)."""
    try:
        stats = run_ingestion()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return stats


@app.get("/api/rag/evaluate")
def rag_evaluate(top_k: Optional[int] = None):
    """Runs the retrieval-quality evaluation (hit-rate@k, MRR, avg similarity)
    against the small gold query set in rag/evaluation.py. Requires ingestion
    to have been run at least once. If top_k isn't given, uses
    rag_retrieval.top_k_default from config/tools.yaml."""
    try:
        k = top_k or int(load_tools_config().get("rag_retrieval", {}).get("top_k_default", 3))
        report = evaluate_retrieval(top_k=k)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return report


@app.get("/api/tools/config")
def tools_config():
    """Read-only view of config/tools.yaml - the tool provider defaults,
    sandbox settings, and RAG data-source manifest currently in effect."""
    try:
        return load_tools_config()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/agent/config")
def agent_config():
    """Read-only view of the Code Exec Agent's role/goal/backstory, as loaded
    from backend/config/agents.yaml - useful for a demo, or for confirming a
    YAML edit actually took effect."""
    try:
        return load_agent_config("code_exec_agent")
    except (FileNotFoundError, KeyError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/")
def root():
    return {
        "status": "ok",
        "project": "DSA Coach - Feedback Generation",
        "group": "Mind Matrix (GENAICH-010)",
        "agent": "Code Exec Agent",
    }
