"""
piston_client.py
-----------------
Code execution sandbox for the Code Exec Agent.

As of Feb 15, 2026, the free public Piston API (emkc.org) stopped accepting
unauthenticated requests - it now requires a key manually approved by the
maintainer, which isn't practical for a class project on a deadline. So the
default executor here is Judge0 (https://judge0.com) via RapidAPI's free tier
(50 requests/day, no credit card needed).

Piston is kept as a secondary option (CODE_EXECUTOR=piston in .env) in case
you self-host it (https://github.com/engineer-man/piston#running-in-docker)
or get an authorized key from the maintainer.
"""

import os
import base64
import httpx

from config_loader import load_tools_config

try:
    _DEFAULT_PROVIDER = load_tools_config().get("code_sandbox", {}).get("provider", "judge0")
except Exception:
    _DEFAULT_PROVIDER = "judge0"

EXECUTOR = os.getenv("CODE_EXECUTOR", _DEFAULT_PROVIDER).lower()  # "judge0" | "piston"

# ---------------------------------------------------------------------------
# Judge0 (default) - https://judge0.com, via RapidAPI free tier
# ---------------------------------------------------------------------------
JUDGE0_HOST = os.getenv("JUDGE0_HOST", "judge0-ce.p.rapidapi.com")
JUDGE0_API_KEY = os.getenv("JUDGE0_API_KEY", "")

# Judge0 CE's standard language IDs (stable across CE versions)
JUDGE0_LANGUAGE_IDS = {
    "python": 71, "java": 62, "c": 50, "cpp": 54, "javascript": 63,
    "typescript": 74, "go": 60, "rust": 73, "csharp": 51, "ruby": 72,
    "kotlin": 78, "swift": 83,
}


def _b64(text: str) -> str:
    return base64.b64encode((text or "").encode()).decode()


def _unb64(text: str) -> str:
    if not text:
        return ""
    try:
        return base64.b64decode(text).decode(errors="replace")
    except Exception:
        return text


async def _run_judge0(language: str, source_code: str, stdin: str) -> dict:
    lang_id = JUDGE0_LANGUAGE_IDS.get(language.lower())
    if lang_id is None:
        return {
            "ran": False, "stdout": "", "stderr": "", "compile_stderr": None, "signal": None,
            "error": f"Language '{language}' isn't wired up for execution yet. "
                     f"Feedback will still be generated from static analysis.",
        }
    if not JUDGE0_API_KEY:
        return {
            "ran": False, "stdout": "", "stderr": "", "compile_stderr": None, "signal": None,
            "error": "JUDGE0_API_KEY is not set in backend/.env - see README for how to get a free key.",
        }

    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": JUDGE0_API_KEY,
        "X-RapidAPI-Host": JUDGE0_HOST,
    }
    payload = {
        "source_code": _b64(source_code),
        "stdin": _b64(stdin),
        "language_id": lang_id,
    }
    url = f"https://{JUDGE0_HOST}/submissions?base64_encoded=true&wait=true"

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        return {
            "ran": False, "stdout": "", "stderr": "", "compile_stderr": None, "signal": None,
            "error": f"Sandbox execution unavailable ({exc}). Falling back to static review only.",
        }

    status = (data.get("status") or {}).get("description", "")
    compile_output = _unb64(data.get("compile_output"))

    return {
        "ran": True,
        "stdout": _unb64(data.get("stdout")),
        "stderr": _unb64(data.get("stderr")),
        "compile_stderr": compile_output or None,
        "signal": status if status and status != "Accepted" else None,
        "error": None,
    }


# ---------------------------------------------------------------------------
# Piston (secondary/self-hosted option)
# ---------------------------------------------------------------------------
PISTON_URL = os.getenv("PISTON_URL", "https://emkc.org/api/v2/piston")

PISTON_LANGUAGE_MAP = {
    "python": ("python", "3.10.0", "main.py"),
    "java": ("java", "15.0.2", "Main.java"),
    "c": ("c", "10.2.0", "main.c"),
    "cpp": ("cpp", "10.2.0", "main.cpp"),
    "javascript": ("javascript", "18.15.0", "main.js"),
    "typescript": ("typescript", "5.0.3", "main.ts"),
    "go": ("go", "1.16.2", "main.go"),
    "rust": ("rust", "1.68.2", "main.rs"),
    "csharp": ("csharp", "6.12.0", "main.cs"),
    "ruby": ("ruby", "3.0.1", "main.rb"),
    "kotlin": ("kotlin", "1.8.20", "main.kt"),
    "swift": ("swift", "5.3.3", "main.swift"),
}


async def _run_piston(language: str, source_code: str, stdin: str) -> dict:
    lang_key = language.lower()
    if lang_key not in PISTON_LANGUAGE_MAP:
        return {
            "ran": False, "stdout": "", "stderr": "", "compile_stderr": None, "signal": None,
            "error": f"Language '{language}' is not wired up for execution yet.",
        }
    piston_lang, version, filename = PISTON_LANGUAGE_MAP[lang_key]
    payload = {
        "language": piston_lang, "version": version,
        "files": [{"name": filename, "content": source_code}],
        "stdin": stdin, "run_timeout": 8000, "compile_timeout": 10000,
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(f"{PISTON_URL}/execute", json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        return {
            "ran": False, "stdout": "", "stderr": "", "compile_stderr": None, "signal": None,
            "error": f"Piston unavailable ({exc}). Note: the free public Piston API has required "
                     f"an authorized key since Feb 2026 - see README.",
        }
    compile_stage = data.get("compile") or {}
    run_stage = data.get("run") or {}
    return {
        "ran": True,
        "stdout": run_stage.get("stdout", ""),
        "stderr": run_stage.get("stderr", ""),
        "compile_stderr": compile_stage.get("stderr") or None,
        "signal": run_stage.get("signal"),
        "error": None,
    }


# ---------------------------------------------------------------------------
# Public entrypoint - dispatches to whichever executor is configured
# ---------------------------------------------------------------------------
LANGUAGE_MAP = JUDGE0_LANGUAGE_IDS if EXECUTOR == "judge0" else PISTON_LANGUAGE_MAP


async def run_code(language: str, source_code: str, stdin: str = "") -> dict:
    if EXECUTOR == "piston":
        return await _run_piston(language, source_code, stdin)
    return await _run_judge0(language, source_code, stdin)
