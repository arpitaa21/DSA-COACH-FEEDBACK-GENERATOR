"""
agent.py
--------
Code Exec Agent — Mind Matrix / GENAICH-010 (DSA Coach - Feedback Generation)

Per the group's multi-agent design doc, this node is an "LLM + sandbox tool" agent:
  Reads:  editor_code, rubric.critical_edge_cases
  Writes: execution_result

This build keeps ONLY the Code Exec Agent, wired as a small LangGraph graph:

  1. read_input        -> OCR the code out of an uploaded image (Gemini Vision), if any
  2. execute_code       -> run the code for real (Piston sandbox); if the user supplied
                            test cases (input -> expected output), run the code against
                            EVERY one of them and record pass/fail - this is what turns
                            "verdict: correct" from an LLM's guess into a checked fact
  3. generate_feedback  -> Gemini reasons over problem statement + constraints +
                            claimed complexity + code + real execution/test results,
                            and returns structured, genuine feedback (not just praise)

Model: Gemini (gemini-3.6-flash by default) via langchain-google-genai.

Persona (role / goal / backstory) is NOT hardcoded here - it's loaded from
backend/config/agents.yaml via config_loader.load_agent_config(). Edit that
YAML file to change how the agent talks or what it prioritizes, no code
changes needed.
"""

import os
import json
import base64
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai

from piston_client import run_code
from config_loader import load_agent_config, load_tools_config

AGENT_CONFIG = load_agent_config("code_exec_agent")

try:
    _DEFAULT_GEMINI_MODEL = load_tools_config().get("vision_ocr", {}).get("model", "gemini-3.6-flash")
except Exception:
    _DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"

GEMINI_MODEL = os.getenv("GEMINI_MODEL", _DEFAULT_GEMINI_MODEL)


def _configure_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy backend/.env.example to backend/.env "
            "and add your Gemini API key."
        )
    genai.configure(api_key=api_key)
    return api_key


class AgentState(TypedDict, total=False):
    language: str
    problem_statement: str
    constraints: str
    claimed_time_complexity: str
    claimed_space_complexity: str
    code: str
    image_b64: Optional[str]        # raw base64 of an uploaded photo/screenshot of code
    stdin: str                      # used only when no test cases are supplied
    test_cases: list                # [{"input": "...", "expected_output": "..."}]
    test_results: list              # [{"input","expected_output","actual_output","passed","stderr"}]
    execution_result: dict
    feedback: dict


# ---------------------------------------------------------------------------
# Node 1: pull code out of an uploaded image, if the user submitted one instead
# of / in addition to typing it in.
# ---------------------------------------------------------------------------
def read_input(state: AgentState) -> AgentState:
    if not state.get("image_b64"):
        return state

    _configure_gemini()
    model = genai.GenerativeModel(GEMINI_MODEL)

    image_bytes = base64.b64decode(state["image_b64"])
    response = model.generate_content(
        [
            {"mime_type": "image/png", "data": image_bytes},
            "Transcribe ONLY the source code visible in this image, exactly as written "
            "(preserve indentation, don't fix bugs, don't add comments). "
            "Return raw code with no markdown fences and no explanation.",
        ]
    )

    extracted = (response.text or "").strip()
    if extracted.startswith("```"):
        extracted = extracted.split("\n", 1)[-1]
        if extracted.endswith("```"):
            extracted = extracted.rsplit("```", 1)[0]

    if extracted:
        state["code"] = extracted
    return state


# ---------------------------------------------------------------------------
# Node 2: run the code for real in the sandbox (Piston).
#
# If the user supplied test cases, run the code once per case, feeding
# `input` as stdin and comparing trimmed stdout to `expected_output` -
# this is real, checked pass/fail, not an LLM's impression of the code.
# If no test cases were supplied, fall back to a single run with the
# optional freeform stdin field (previous behaviour).
# ---------------------------------------------------------------------------
async def execute_code_node(state: AgentState) -> AgentState:
    language = state.get("language", "python")
    code = state.get("code", "")
    test_cases = state.get("test_cases") or []

    if test_cases:
        results = []
        for tc in test_cases:
            run_result = await run_code(language=language, source_code=code, stdin=tc.get("input", ""))
            actual = (run_result.get("stdout") or "").strip()
            expected = (tc.get("expected_output") or "").strip()
            ran_clean = bool(run_result.get("ran")) and not run_result.get("stderr") and not run_result.get("compile_stderr")
            results.append(
                {
                    "input": tc.get("input", ""),
                    "expected_output": expected,
                    "actual_output": actual,
                    "passed": ran_clean and actual == expected,
                    "stderr": run_result.get("stderr") or run_result.get("compile_stderr") or run_result.get("error") or "",
                }
            )
        state["test_results"] = results

        passed = sum(1 for r in results if r["passed"])
        state["execution_result"] = {
            "ran": True,
            "stdout": f"{passed}/{len(results)} test cases passed",
            "stderr": "",
            "compile_stderr": next((r["stderr"] for r in results if r["stderr"]), None),
            "signal": None,
            "error": None,
        }
    else:
        state["execution_result"] = await run_code(
            language=language, source_code=code, stdin=state.get("stdin", "")
        )
        state["test_results"] = []

    return state


# ---------------------------------------------------------------------------
# Node 3: generate genuine, specific feedback - correctness, real complexity vs
# claimed complexity, edge cases, and a concrete improvement suggestion.
# ---------------------------------------------------------------------------
FEEDBACK_PROMPT = """You are a {role}.

Your goal: {goal}

Backstory: {backstory}

Stay in that voice, but never let it soften the verdict - be specific and honest.

PROBLEM STATEMENT:
{problem_statement}

CONSTRAINTS:
{constraints}

USER'S CLAIMED COMPLEXITY:
Time: {claimed_time_complexity}
Space: {claimed_space_complexity}

LANGUAGE: {language}

USER'S CODE:
```{language}
{code}
```

SANDBOX EXECUTION RESULT (ground truth - trust this over the code's appearance):
stdout: {stdout}
stderr: {stderr}
compile_stderr: {compile_stderr}
runtime_signal: {signal}
execution_note: {exec_error}

TEST CASE RESULTS (ground truth - if any were provided, trust these over your own
read of the code when deciding the verdict):
{test_results_block}

Respond with ONLY valid JSON (no markdown fences), matching this exact schema:
{{
  "verdict": "correct" | "partially_correct" | "incorrect" | "does_not_run",
  "correctness_notes": "1-3 sentences on whether the logic actually solves the stated problem, referencing the execution result and test results where relevant",
  "actual_time_complexity": "Big-O string",
  "actual_space_complexity": "Big-O string",
  "complexity_verdict": "matches_claim" | "better_than_claimed" | "worse_than_claimed",
  "complexity_notes": "1-2 sentences justifying the actual complexity",
  "edge_cases_missed": ["short phrase", "short phrase"],
  "bugs": ["short phrase describing a real bug or risk, if any"],
  "improvement_suggestions": ["concrete, specific suggestion", "concrete, specific suggestion"],
  "improved_code": "a corrected/optimized version of the code, or empty string if no change needed",
  "score": 0-100,
  "one_line_summary": "one honest sentence a coach would actually say out loud"
}}

Important: if test case results are provided and NOT all of them passed, the verdict
MUST be "incorrect" or "partially_correct" - never "correct". If all provided test
cases passed and there's no execution error, the verdict should be "correct" unless
you see a clear, specific logic problem the tests didn't happen to catch.
"""


def _format_test_results(test_results: list) -> str:
    if not test_results:
        return "(no test cases were provided - base the verdict on the single execution run above)"
    lines = []
    for i, tr in enumerate(test_results, 1):
        status = "PASS" if tr["passed"] else "FAIL"
        lines.append(
            f"  Test {i}: {status}\n"
            f"    input: {tr['input'][:300]}\n"
            f"    expected: {tr['expected_output'][:300]}\n"
            f"    actual:   {tr['actual_output'][:300]}"
            + (f"\n    stderr: {tr['stderr'][:300]}" if tr.get("stderr") else "")
        )
    passed = sum(1 for tr in test_results if tr["passed"])
    lines.append(f"  Summary: {passed}/{len(test_results)} test cases passed.")
    return "\n".join(lines)


def _build_llm():
    _configure_gemini()
    api_key = os.getenv("GEMINI_API_KEY")
    return ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=api_key, temperature=0.3)


def generate_feedback_node(state: AgentState) -> AgentState:
    llm = _build_llm()
    exec_result = state.get("execution_result", {}) or {}
    test_results = state.get("test_results", []) or []

    prompt = FEEDBACK_PROMPT.format(
        role=AGENT_CONFIG["role"],
        goal=AGENT_CONFIG["goal"],
        backstory=AGENT_CONFIG["backstory"],
        problem_statement=state.get("problem_statement", "").strip() or "(not provided)",
        constraints=state.get("constraints", "").strip() or "(not provided)",
        claimed_time_complexity=state.get("claimed_time_complexity", "").strip() or "(not provided)",
        claimed_space_complexity=state.get("claimed_space_complexity", "").strip() or "(not provided)",
        language=state.get("language", "python"),
        code=state.get("code", "").strip() or "(no code submitted)",
        stdout=exec_result.get("stdout", "")[:2000],
        stderr=exec_result.get("stderr", "")[:2000],
        compile_stderr=exec_result.get("compile_stderr") or "",
        signal=exec_result.get("signal") or "",
        exec_error=exec_result.get("error") or "",
        test_results_block=_format_test_results(test_results),
    )

    response = llm.invoke(prompt)
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]

    try:
        feedback = json.loads(raw)
    except json.JSONDecodeError:
        feedback = {
            "verdict": "incorrect",
            "correctness_notes": "The agent's response could not be parsed as JSON. Raw output included for debugging.",
            "raw_output": raw,
            "score": 0,
            "one_line_summary": "Something went wrong generating structured feedback - please retry.",
        }

    state["feedback"] = feedback
    return state


# ---------------------------------------------------------------------------
# Wire the three nodes into a LangGraph graph - this IS the Code Exec Agent.
# ---------------------------------------------------------------------------
def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("read_input", read_input)
    graph.add_node("execute_code", execute_code_node)
    graph.add_node("generate_feedback", generate_feedback_node)

    graph.set_entry_point("read_input")
    graph.add_edge("read_input", "execute_code")
    graph.add_edge("execute_code", "generate_feedback")
    graph.add_edge("generate_feedback", END)

    return graph.compile()


code_exec_agent = build_graph()


async def run_code_exec_agent(**kwargs) -> AgentState:
    """Public entrypoint used by main.py"""
    initial_state: AgentState = dict(**kwargs)  # type: ignore
    final_state = await code_exec_agent.ainvoke(initial_state)
    return final_state
