"""
main.py
-------
DSA Coach - Feedback Generation
Group: Mind Matrix (GENAICH-010)
Agent: Code Exec Agent (LLM + sandbox tool) - powered by Gemini

FastAPI app exposing:
  POST /api/analyze               -> run the Code Exec Agent, optionally against
                                       real test cases (input -> expected output)
  GET  /api/languages             -> supported languages for the editor dropdown
"""

import base64
import json
import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("dsa_coach.main")

from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from agent import _emergency_feedback, run_code_exec_agent
from piston_client import LANGUAGE_MAP
from config_loader import load_agent_config, load_tools_config

app = FastAPI(title="DSA Coach - Feedback Generation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your frontend origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/languages")
def languages():
    return {"languages": sorted(LANGUAGE_MAP.keys())}


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
):
    # 1. UI Input Validation - catch empty/malformed inputs before hitting the agent
    clean_code = code.strip()
    clean_problem = problem_statement.strip()
    clean_constraints = constraints.strip()

    if not clean_code and image is None:
        logger.warning("Analyze rejected: no code or image submitted.")
        raise HTTPException(
            status_code=400,
            detail="Code solution is required. Please type your code in the editor or upload an image.",
        )

    if not clean_problem:
        logger.warning("Analyze rejected: empty problem statement.")
        raise HTTPException(
            status_code=400,
            detail="Problem statement is required so the coach can evaluate your solution's correctness.",
        )

    if not clean_constraints:
        logger.info("Submission received without explicit constraints.")

    image_b64 = None
    if image is not None:
        try:
            raw = await image.read()
            image_b64 = base64.b64encode(raw).decode("utf-8")
        except Exception as img_err:
            logger.error("Failed to read uploaded image: %s", img_err)
            raise HTTPException(
                status_code=400,
                detail=f"Uploaded image could not be processed: {img_err}",
            )

    try:
        test_cases = json.loads(test_cases_json) if test_cases_json else []
        if not isinstance(test_cases, list):
            test_cases = []
    except json.JSONDecodeError as json_err:
        logger.warning("Malformed test_cases_json: %s", json_err)
        test_cases = []

    logger.info("Executing Code Exec Agent [lang=%s, code_len=%d, tests=%d]", language, len(clean_code), len(test_cases))

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
        logger.exception("Agent execution encountered an unhandled exception: %s", exc)
        try:
            from agent import _generate_demo_feedback
            fallback_fb = _generate_demo_feedback(
                {
                    "code": clean_code,
                    "problem_statement": clean_problem,
                    "constraints": clean_constraints,
                    "language": language,
                    "claimed_time_complexity": claimed_time_complexity,
                    "claimed_space_complexity": claimed_space_complexity,
                },
                {},
                test_cases,
            )
        except Exception as fallback_exc:
            logger.exception("Static feedback fallback also failed: %s", fallback_exc)
            fallback_fb = _emergency_feedback()
        result = {
            "code": clean_code,
            "execution_result": {"ran": False, "error": f"Agent fallback active ({exc})"},
            "test_results": [],
            "feedback": fallback_fb,
        }

    if not isinstance(result, dict):
        logger.error("Agent returned an invalid response type: %s", type(result).__name__)
        result = {}

    return {
        "extracted_code": result.get("code") or clean_code,
        "execution_result": result.get("execution_result") or {
            "ran": False,
            "error": "The code execution result was unavailable.",
        },
        "test_results": result.get("test_results") or [],
        "feedback": result.get("feedback") or _emergency_feedback(),
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


frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.is_dir() and (frontend_dist / "index.html").is_file():
    # Mount production frontend build directly
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "status": "ok",
            "project": "DSA Coach - Feedback Generation",
            "group": "Mind Matrix (GENAICH-010)",
            "agent": "Code Exec Agent",
        }
