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
import logging
import os
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("dsa_coach.main")

from fastapi import FastAPI, Form, File, UploadFile, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import run_code_exec_agent
from piston_client import LANGUAGE_MAP
import streak_db
import auth
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
    email: str
    password: str
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    email: str
    display_name: str


class UserProfileResponse(BaseModel):
    username: str
    email: str
    display_name: str


async def get_current_username(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated. Please log in.")
    token = authorization.split(" ", 1)[1]
    payload = auth.decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    return payload["sub"]


@app.post("/api/register", response_model=AuthResponse)
def register(payload: RegisterRequest):
    try:
        user = auth.create_user(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
        )
    except auth.AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    token = auth.create_access_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"],
        "email": user["email"],
        "display_name": user["display_name"],
    }


@app.post("/api/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    try:
        user = auth.verify_user(payload.username, payload.password)
    except auth.AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    token = auth.create_access_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"],
        "email": user["email"],
        "display_name": user["display_name"],
    }


@app.get("/api/me", response_model=UserProfileResponse)
def get_me(username: str = Depends(get_current_username)):
    user = auth.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


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
    # 1. UI Input Validation - catch empty/malformed inputs before hitting the agent
    clean_code = code.strip()
    clean_problem = problem_statement.strip()
    clean_constraints = constraints.strip()

    if not clean_code and image is None:
        logger.warning("Analyze rejected for user '%s': no code or image submitted.", username)
        raise HTTPException(
            status_code=400,
            detail="Code solution is required. Please type your code in the editor or upload an image.",
        )

    if not clean_problem:
        logger.warning("Analyze rejected for user '%s': empty problem statement.", username)
        raise HTTPException(
            status_code=400,
            detail="Problem statement is required so the coach can evaluate your solution's correctness.",
        )

    if not clean_constraints:
        logger.info("User '%s' submitted without explicit constraints.", username)

    image_b64 = None
    if image is not None:
        try:
            raw = await image.read()
            image_b64 = base64.b64encode(raw).decode("utf-8")
        except Exception as img_err:
            logger.error("Failed to read uploaded image for user '%s': %s", username, img_err)
            raise HTTPException(
                status_code=400,
                detail=f"Uploaded image could not be processed: {img_err}",
            )

    try:
        test_cases = json.loads(test_cases_json) if test_cases_json else []
        if not isinstance(test_cases, list):
            test_cases = []
    except json.JSONDecodeError as json_err:
        logger.warning("Malformed test_cases_json for user '%s': %s", username, json_err)
        test_cases = []

    # 2. Check API Key & Demo Mode configuration
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    demo_mode = os.getenv("DEMO_MODE", "false").lower() in ("true", "1") or api_key.lower() == "demo"
    if not demo_mode and (not api_key or api_key == "your_gemini_api_key_here"):
        logger.warning("Analyze rejected: GEMINI_API_KEY missing or placeholder.")
        raise HTTPException(
            status_code=401,
            detail="Gemini API Key is missing or using placeholder in backend/.env. Please set GEMINI_API_KEY with your key from https://aistudio.google.com/apikey, or enable DEMO_MODE=true in backend/.env for local evaluation.",
        )

    logger.info("Executing Code Exec Agent for user '%s' [lang=%s, code_len=%d, tests=%d]", username, language, len(clean_code), len(test_cases))

    try:
        result = await run_code_exec_agent(
            language=language,
            problem_statement=clean_problem,
            constraints=clean_constraints,
            claimed_time_complexity=claimed_time_complexity,
            claimed_space_complexity=claimed_space_complexity,
            code=clean_code,
            stdin=stdin,
            test_cases=test_cases,
            image_b64=image_b64,
        )
    except Exception as exc:
        # Full traceback logging on server console/logs
        logger.exception("Agent execution failed for user '%s': %s", username, exc)
        err_str = str(exc)

        # Map to descriptive, actionable HTTP responses instead of generic agent error
        if any(tok in err_str for tok in ("API key not valid", "API_KEY_INVALID", "UNAUTHENTICATED", "ACCESS_TOKEN_TYPE_UNSUPPORTED")):
            raise HTTPException(
                status_code=401,
                detail="Your GEMINI_API_KEY in backend/.env is invalid or unsupported. Verify and update it with a valid key from https://aistudio.google.com/apikey (keys typically start with 'AIzaSy...'), or set DEMO_MODE=true in backend/.env.",
            )
        elif "404" in err_str or "not found" in err_str.lower():
            raise HTTPException(
                status_code=404,
                detail=f"The configured Gemini model was not found ({err_str}). Verify GEMINI_MODEL in backend/.env (recommend 'gemini-2.0-flash' or 'gemini-1.5-flash').",
            )
        elif any(tok in err_str for tok in ("429", "RESOURCE_EXHAUSTED", "quota")):
            raise HTTPException(
                status_code=429,
                detail="Gemini API rate limit or quota exceeded. Please wait a moment before trying again, or check your quota at https://aistudio.google.com.",
            )
        elif "timeout" in err_str.lower():
            raise HTTPException(
                status_code=504,
                detail="Sandbox or LLM execution timed out. Please simplify your solution or test cases and retry.",
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Agent analysis encountered an unexpected error: {err_str}. Full traceback has been logged on the server.",
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
    embeddings -> indexing."""
    try:
        from rag.ingestion import run_ingestion
        stats = run_ingestion()
    except Exception as exc:
        logger.exception("RAG ingestion failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    return stats


@app.get("/api/rag/evaluate")
def rag_evaluate(top_k: Optional[int] = None):
    """Runs the retrieval-quality evaluation against the gold query set."""
    try:
        from rag.evaluation import evaluate_retrieval
        k = top_k or int(load_tools_config().get("rag_retrieval", {}).get("top_k_default", 3))
        report = evaluate_retrieval(top_k=k)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("RAG evaluation failed: %s", exc)
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
