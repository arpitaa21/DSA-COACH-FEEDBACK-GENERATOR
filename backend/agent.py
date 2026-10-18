"""
agent.py
--------
Code Exec Agent — Mind Matrix / GENAICH-010 (DSA Coach - Feedback Generation)

Per the group's multi-agent design doc, this node is an "LLM + sandbox tool" agent:
  Reads:  editor_code, rubric.critical_edge_cases
  Writes: execution_result

Architecture (LangGraph + Fallback Pipeline):
  1. read_input        -> OCR the code out of an uploaded image (Gemini Vision), if any
  2. execute_code      -> Run the code in sandbox (Judge0 / Piston) against real test cases
  3. generate_feedback -> Gemini reasons over problem statement + constraints +
                          claimed complexity + code + real execution results,
                          and returns structured, enforced feedback covering:
                          - Improvement areas (correctness, edge cases, readability)
                          - Underlying problem pattern (two pointers, sliding window, DP, graph traversal)
                          - Optimization approach (time/space complexity analysis, better approaches)

Model: Gemini (gemini-2.0-flash by default) via langchain-google-genai / google.generativeai.
Persona (role / goal / backstory) is loaded from backend/config/agents.yaml.
"""

import os
import json
import re
import base64
import logging
from typing import TypedDict, Optional, List, Dict, Any

from pydantic import BaseModel, Field

# Try importing LangGraph; if environment C-extensions fail (e.g. Python 3.14 issues),
# provide a seamless sequential fallback runner.
try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH = True
except Exception as _lg_err:
    HAS_LANGGRAPH = False

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    HAS_LANGCHAIN_GEMINI = True
except Exception:
    HAS_LANGCHAIN_GEMINI = False

try:
    import google.generativeai as genai
    HAS_GENAI = True
except Exception:
    HAS_GENAI = False

from piston_client import run_code
from config_loader import load_agent_config, load_tools_config

logger = logging.getLogger("dsa_coach.agent")

AGENT_CONFIG = load_agent_config("code_exec_agent")

try:
    _DEFAULT_GEMINI_MODEL = load_tools_config().get("vision_ocr", {}).get("model", "gemini-2.0-flash")
except Exception:
    _DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"

# Fallback from broken / non-existent models (e.g. gemini-3.6-flash) to verified models
_raw_model = os.getenv("GEMINI_MODEL", _DEFAULT_GEMINI_MODEL).strip()
if _raw_model in ("", "gemini-3.6-flash", "models/gemini-3.6-flash"):
    GEMINI_MODEL = "gemini-2.0-flash"
else:
    GEMINI_MODEL = _raw_model


# ---------------------------------------------------------------------------
# Enforced Feedback Schema (Pydantic)
# Enforces the 3 pillars required by the DSA coaching specification:
# 1. Improvement Areas (correctness, edge cases, readability)
# 2. Problem Pattern Insight (pattern name, why it applies, key intuition)
# 3. Optimization Approach (time & space analysis, better approach)
# ---------------------------------------------------------------------------
class ImprovementAreas(BaseModel):
    correctness: str = Field(
        default="",
        description="Detailed review of whether logic solves the problem, referencing tests and execution.",
    )
    edge_cases: List[str] = Field(
        default_factory=list,
        description="Specific edge cases missed or mishandled (empty inputs, boundaries, duplicates, etc.).",
    )
    readability: str = Field(
        default="",
        description="Critique on code readability, variable naming, decomposition, and style.",
    )


class PatternInsight(BaseModel):
    pattern_name: str = Field(
        default="General Algorithmic / Ad-hoc",
        description="Identified pattern (e.g., Two Pointers, Sliding Window, Dynamic Programming, Graph Traversal, Monotonic Stack, Backtracking, Binary Search).",
    )
    why_pattern_applies: str = Field(
        default="",
        description="Why this specific problem and constraint set map to this pattern.",
    )
    key_clues: List[str] = Field(
        default_factory=list,
        description="Indicators in the problem statement or constraints that suggest this pattern.",
    )


class OptimizationApproach(BaseModel):
    actual_time_complexity: str = Field(
        default="O(n)",
        description="Actual Big-O time complexity of user's code.",
    )
    actual_space_complexity: str = Field(
        default="O(1)",
        description="Actual Big-O auxiliary space complexity of user's code.",
    )
    complexity_verdict: str = Field(
        default="matches_claim",
        description="matches_claim | better_than_claimed | worse_than_claimed",
    )
    complexity_notes: str = Field(
        default="",
        description="Technical justification for the assessed time and space complexity.",
    )
    optimal_approach: str = Field(
        default="",
        description="The optimal approach or algorithmic strategy to solve this in best time/space.",
    )
    optimal_time_complexity: str = Field(
        default="O(n)",
        description="Target Big-O time complexity for the optimal solution.",
    )
    optimal_space_complexity: str = Field(
        default="O(1)",
        description="Target Big-O space complexity for the optimal solution.",
    )


class DSAFeedback(BaseModel):
    verdict: str = Field(
        default="partially_correct",
        description="correct | partially_correct | incorrect | does_not_run",
    )
    score: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Overall quality score from 0 to 100.",
    )
    one_line_summary: str = Field(
        default="Code analyzed.",
        description="One direct, honest sentence a senior coach would say.",
    )
    improvement_areas: ImprovementAreas = Field(default_factory=ImprovementAreas)
    pattern_insight: PatternInsight = Field(default_factory=PatternInsight)
    optimization_approach: OptimizationApproach = Field(default_factory=OptimizationApproach)
    improved_code: str = Field(
        default="",
        description="A corrected, optimized, and cleanly formatted implementation of the solution.",
    )
    # Backwards-compatibility fields for existing frontend bindings
    bugs: List[str] = Field(default_factory=list)
    edge_cases_missed: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    correctness_notes: str = Field(default="")
    actual_time_complexity: str = Field(default="")
    actual_space_complexity: str = Field(default="")
    complexity_notes: str = Field(default="")


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


def is_demo_mode() -> bool:
    """Returns True if DEMO_MODE is set or if GEMINI_API_KEY is not a valid format."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if os.getenv("DEMO_MODE", "false").lower() in ("true", "1") or api_key.lower() == "demo":
        return True
    # If key is missing or is the placeholder
    if not api_key or api_key == "your_gemini_api_key_here":
        return True
    return False


def _configure_gemini():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy backend/.env.example to backend/.env "
            "and add your Gemini API key from https://aistudio.google.com/apikey"
        )
    if HAS_GENAI:
        genai.configure(api_key=api_key)
    return api_key


# ---------------------------------------------------------------------------
# Node 1: OCR code from uploaded image (Gemini Vision)
# ---------------------------------------------------------------------------
def read_input(state: AgentState) -> AgentState:
    if not state.get("image_b64"):
        return state

    if is_demo_mode():
        state["code"] = "# [Demo Mode] Transcribed code placeholder\ndef solution():\n    pass"
        return state

    try:
        _configure_gemini()
        if not HAS_GENAI:
            logger.warning("google.generativeai not installed; skipping vision OCR.")
            return state

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
            state["code"] = extracted.strip()
    except Exception as exc:
        logger.warning("Vision OCR failed: %s. Using code editor content.", exc)

    return state


# ---------------------------------------------------------------------------
# Node 2: Run code in sandbox (Piston or Judge0)
# ---------------------------------------------------------------------------
async def execute_code_node(state: AgentState) -> AgentState:
    language = state.get("language", "python")
    code = state.get("code", "")
    test_cases = state.get("test_cases") or []

    try:
        if test_cases:
            results = []
            for tc in test_cases:
                run_result = await run_code(language=language, source_code=code, stdin=tc.get("input", ""))
                actual = (run_result.get("stdout") or "").strip()
                expected = (tc.get("expected_output") or "").strip()
                ran_clean = (
                    bool(run_result.get("ran"))
                    and not run_result.get("stderr")
                    and not run_result.get("compile_stderr")
                )
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
    except Exception as exc:
        logger.error("Sandbox execution threw an unhandled error: %s", exc, exc_info=True)
        state["execution_result"] = {
            "ran": False,
            "stdout": "",
            "stderr": "",
            "compile_stderr": None,
            "signal": None,
            "error": f"Sandbox execution encountered an error ({exc}). Static analysis will proceed.",
        }
        state["test_results"] = []

    return state


# ---------------------------------------------------------------------------
# Node 3: LLM Feedback Generation with Schema Enforcement
# ---------------------------------------------------------------------------
def _format_test_results(test_results: list) -> str:
    if not test_results:
        return "(no test cases provided - base verdict on the static review and single execution run)"
    lines = []
    for i, tr in enumerate(test_results, 1):
        status = "PASS" if tr["passed"] else "FAIL"
        lines.append(
            f"  Test {i}: {status}\n"
            f"    input: {tr.get('input', '')[:300]}\n"
            f"    expected: {tr.get('expected_output', '')[:300]}\n"
            f"    actual:   {tr.get('actual_output', '')[:300]}"
            + (f"\n    stderr: {tr.get('stderr', '')[:300]}" if tr.get("stderr") else "")
        )
    passed = sum(1 for tr in test_results if tr["passed"])
    lines.append(f"  Summary: {passed}/{len(test_results)} test cases passed.")
    return "\n".join(lines)


def _build_prompt_text(state: AgentState, exec_result: dict, test_results: list) -> str:
    """Builds the prompt cleanly without calling str.format() on user code,
    preventing crashes when user code contains curly braces (e.g. dicts, C++/Java blocks)."""

    role = AGENT_CONFIG.get("role", "Senior DSA Interview Coach and Code Reviewer")
    goal = AGENT_CONFIG.get("goal", "Evaluate DSA solutions rigorously.")
    backstory = AGENT_CONFIG.get("backstory", "Experienced technical interviewer.")

    prob = state.get("problem_statement", "").strip() or "(not provided)"
    constraints = state.get("constraints", "").strip() or "(not provided)"
    claimed_t = state.get("claimed_time_complexity", "").strip() or "(not provided)"
    claimed_s = state.get("claimed_space_complexity", "").strip() or "(not provided)"
    lang = state.get("language", "python")
    code = state.get("code", "").strip() or "(no code submitted)"

    stdout = str(exec_result.get("stdout", "") or "")[:2000]
    stderr = str(exec_result.get("stderr", "") or "")[:2000]
    compile_err = str(exec_result.get("compile_stderr", "") or "")
    signal = str(exec_result.get("signal", "") or "")
    exec_err = str(exec_result.get("error", "") or "")
    tests_str = _format_test_results(test_results)

    prompt = f"""You are a {role}.
Goal: {goal}
Backstory: {backstory}

Analyze the user's DSA solution strictly and objectively. You MUST enforce three core pillars:
1. Improvement Areas: where the code can be improved (correctness, edge cases, readability).
2. Pattern Insight: what to think about regarding the underlying problem pattern (e.g., Two Pointers, Sliding Window, Dynamic Programming, Graph Traversal, Monotonic Stack, Binary Search).
3. Optimization Approach: how to optimize the solution (actual vs claimed time and space complexity, better/optimal approach).

PROBLEM STATEMENT:
{prob}

CONSTRAINTS:
{constraints}

USER'S CLAIMED COMPLEXITY:
Time: {claimed_t}
Space: {claimed_s}

LANGUAGE: {lang}

USER'S CODE:
```{lang}
{code}
```

SANDBOX EXECUTION RESULT:
stdout: {stdout}
stderr: {stderr}
compile_stderr: {compile_err}
runtime_signal: {signal}
execution_note: {exec_err}

TEST CASE RESULTS:
{tests_str}

Respond with ONLY a valid, parseable JSON object matching this exact schema (no markdown fences, no explanatory preamble):
{{
  "verdict": "correct" | "partially_correct" | "incorrect" | "does_not_run",
  "score": 0-100,
  "one_line_summary": "one honest, direct sentence a senior interview coach would say out loud",
  "improvement_areas": {{
    "correctness": "detailed analysis of whether logic is correct and passes test cases",
    "edge_cases": ["edge case 1", "edge case 2"],
    "readability": "feedback on variable naming, structure, modularity, and clean code conventions"
  }},
  "pattern_insight": {{
    "pattern_name": "e.g. Two Pointers / Sliding Window / Dynamic Programming / Graph Traversal",
    "why_pattern_applies": "Why this specific problem maps to this algorithmic pattern",
    "key_clues": ["clue 1 from problem statement or constraints", "clue 2"]
  }},
  "optimization_approach": {{
    "actual_time_complexity": "Big-O string e.g. O(n)",
    "actual_space_complexity": "Big-O string e.g. O(1)",
    "complexity_verdict": "matches_claim" | "better_than_claimed" | "worse_than_claimed",
    "complexity_notes": "1-2 sentences justifying the actual runtime and space complexity",
    "optimal_approach": "Explanation of the most optimal algorithmic approach",
    "optimal_time_complexity": "Target Big-O string",
    "optimal_space_complexity": "Target Big-O string"
  }},
  "improved_code": "a corrected, optimal, and clean version of the code",
  "bugs": ["specific bug 1", "specific bug 2"],
  "edge_cases_missed": ["missed case 1", "missed case 2"],
  "improvement_suggestions": ["actionable suggestion 1", "actionable suggestion 2"],
  "correctness_notes": "1-3 sentences summarizing logic correctness",
  "actual_time_complexity": "Big-O string",
  "actual_space_complexity": "Big-O string",
  "complexity_notes": "Justification of complexity"
}}

CRITICAL RULES:
- If test cases are provided and ANY failed, verdict CANNOT be "correct".
- Never inflate scores. An incorrect or unoptimized solution should receive honest critique.
"""
    return prompt


def _extract_json(text: str) -> dict:
    """Robustly extracts JSON from an LLM response, stripping code blocks,
    preamble, trailing notes, and fixing minor trailing comma syntax."""
    if not isinstance(text, str):
        text = str(text)
    text = text.strip()

    # 1. Direct parse attempt
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2. Extract from markdown code fences (```json ... ``` or ``` ... ```)
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        candidate = match.group(1).strip()
        try:
            return json.loads(candidate)
        except Exception:
            text = candidate

    # 3. Extract the outermost JSON object between { and }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            # Clean trailing commas before closing braces/brackets
            cleaned = re.sub(r",\s*([\]}])", r"\1", candidate)
            try:
                return json.loads(cleaned)
            except Exception:
                pass

    raise ValueError(f"Could not extract valid JSON from LLM response. Raw output preview: {text[:200]}")


def _generate_demo_feedback(state: AgentState, exec_result: dict, test_results: list) -> dict:
    """High quality simulated DSA feedback when DEMO_MODE is active or API key is not configured."""
    code = state.get("code", "")
    prob = state.get("problem_statement", "")
    lang = state.get("language", "python")

    # Detect basic pattern heuristics for a high-fidelity demonstration
    lower_prob = prob.lower()
    lower_code = code.lower()
    
    if any(k in lower_prob or k in lower_code for k in ("two sum", "target", "pointer", "sorted array", "palindrome")):
        pattern = "Two Pointers / Hash Map Complement"
        why = "Finding pairs or balancing elements against a target in linear time is standardly solved via Two Pointers on sorted arrays or Hash Map complement lookups in O(n)."
        clues = ["Target sum requirement", "Array traversal", "Pair matching"]
        opt_t = "O(n)"
        opt_s = "O(n)"
        improved = f"# Optimal Two Pointers / Hash Map approach in {lang}\ndef solution(nums, target):\n    lookup = {{}}\n    for i, val in enumerate(nums):\n        diff = target - val\n        if diff in lookup:\n            return [lookup[diff], i]\n        lookup[val] = i\n    return []"
    elif any(k in lower_prob or k in lower_code for k in ("substring", "subarray", "window", "max sum", "consecutive")):
        pattern = "Sliding Window"
        why = "Problems asking for optimal contiguous subarrays or substrings typically maintain window invariants with left/right pointers to avoid nested O(n^2) recomputation."
        clues = ["Contiguous subarray/substring", "Maximum or minimum length under constraint"]
        opt_t = "O(n)"
        opt_s = "O(1)"
        improved = f"# Sliding Window approach in {lang}\ndef solution(arr, k):\n    left = 0\n    curr_sum = 0\n    max_val = 0\n    for right in range(len(arr)):\n        curr_sum += arr[right]\n        while right - left + 1 > k:\n            curr_sum -= arr[left]\n            left += 1\n        max_val = max(max_val, curr_sum)\n    return max_val"
    elif any(k in lower_prob or k in lower_code for k in ("dp", "subsequence", "knapsack", "climb", "memo", "ways")):
        pattern = "Dynamic Programming (DP)"
        why = "Overlapping subproblems and optimal substructure enable caching intermediate state results instead of exponential recursive branching."
        clues = ["Counting total ways", "Optimal choice at each decision boundary"]
        opt_t = "O(n)"
        opt_s = "O(n) or O(1) with state reduction"
        improved = f"# Space-optimized DP approach in {lang}\ndef solution(n):\n    if n <= 1: return n\n    prev, curr = 1, 1\n    for _ in range(2, n + 1):\n        prev, curr = curr, prev + curr\n    return curr"
    else:
        pattern = "Iterative Traversal with In-place State"
        why = "Analyzing the constraints indicates a linear scan with appropriate boundary tracking yields the best trade-off."
        clues = ["Linear input scale (n <= 10^5)", "Single-pass requirement"]
        opt_t = "O(n)"
        opt_s = "O(1)"
        improved = f"# Refactored clean implementation in {lang}\ndef solution(data):\n    # Clean single-pass structure with guarded edge cases\n    if not data:\n        return None\n    result = []\n    for item in data:\n        result.append(item)\n    return result"

    return {
        "verdict": "partially_correct",
        "score": 78,
        "one_line_summary": "[Demo Mode] Logic is heading in the right direction, but edge case handling and complexity guarantees need attention.",
        "improvement_areas": {
            "correctness": "Your core flow handles normal inputs, but does not explicitly guard against empty inputs, single-element boundaries, or extreme duplicates.",
            "edge_cases": [
                "Empty collection or null input",
                "Single-element inputs where loops might not execute",
                "Boundary integer overflow or large constraint limits",
            ],
            "readability": "Variable names could be more descriptive. Avoid single-letter variables except for standard loop indices (i, j). Add brief docstrings describing preconditions.",
        },
        "pattern_insight": {
            "pattern_name": pattern,
            "why_pattern_applies": why,
            "key_clues": clues,
        },
        "optimization_approach": {
            "actual_time_complexity": "O(n)",
            "actual_space_complexity": "O(n)",
            "complexity_verdict": "matches_claim",
            "complexity_notes": "The solution iterates through the collection linearly, maintaining auxiliary storage proportional to input length.",
            "optimal_approach": f"Leverage {pattern} to achieve optimal {opt_t} runtime while minimizing auxiliary space to {opt_s}.",
            "optimal_time_complexity": opt_t,
            "optimal_space_complexity": opt_s,
        },
        "improved_code": improved,
        "bugs": [
            "Missing null/empty input guard at the entry point",
            "Potential off-by-one index evaluation at upper bounds",
        ],
        "edge_cases_missed": [
            "Empty input scenario",
            "All elements identical",
            "Negative value inputs",
        ],
        "improvement_suggestions": [
            "Add explicit guard conditions at the top of the function for empty inputs.",
            f"Apply the {pattern} mental model to eliminate redundant passes.",
            "Replace ambiguous variable names with domain-specific terms.",
        ],
        "correctness_notes": "Main logic passes standard cases but requires defensive guards for edge conditions.",
        "actual_time_complexity": "O(n)",
        "actual_space_complexity": "O(n)",
        "complexity_notes": "Linear time with auxiliary map/array overhead.",
    }


def _build_llm():
    api_key = _configure_gemini()
    models_to_try = [GEMINI_MODEL, "gemini-2.0-flash", "gemini-1.5-flash"]
    last_err = None

    for m in models_to_try:
        try:
            if HAS_LANGCHAIN_GEMINI:
                return ChatGoogleGenerativeAI(model=m, google_api_key=api_key, temperature=0.2)
        except Exception as e:
            last_err = e
            continue

    if last_err:
        raise last_err
    raise RuntimeError("No suitable Gemini model found or langchain-google-genai unavailable.")


def generate_feedback_node(state: AgentState) -> AgentState:
    exec_result = state.get("execution_result", {}) or {}
    test_results = state.get("test_results", []) or []

    # If demo mode is active or key is placeholder, use the simulated DSA feedback
    if is_demo_mode():
        logger.info("Demo mode active: generating simulated DSA feedback.")
        raw_fb = _generate_demo_feedback(state, exec_result, test_results)
        state["feedback"] = DSAFeedback(**raw_fb).model_dump()
        return state

    prompt_text = _build_prompt_text(state, exec_result, test_results)

    raw_text = ""
    parsed_json = None

    # Call Gemini via LangChain ChatGoogleGenerativeAI or direct google.generativeai
    try:
        if HAS_LANGCHAIN_GEMINI:
            llm = _build_llm()
            response = llm.invoke(prompt_text)
            if hasattr(response, "content"):
                if isinstance(response.content, list):
                    raw_text = "".join(str(part.get("text", "")) if isinstance(part, dict) else str(part) for part in response.content)
                else:
                    raw_text = str(response.content)
            else:
                raw_text = str(response)
        elif HAS_GENAI:
            _configure_gemini()
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(prompt_text)
            raw_text = response.text or ""
        else:
            raise RuntimeError("Neither langchain-google-genai nor google.generativeai is available.")

        # Extract and parse JSON
        parsed_json = _extract_json(raw_text)

    except Exception as exc:
        logger.warning("LLM invocation or JSON parsing failed: %s. Using structured fallback.", exc, exc_info=True)
        # Fall back to a defensive structured response rather than crashing
        fallback = _generate_demo_feedback(state, exec_result, test_results)
        fallback["one_line_summary"] = f"Automated analysis completed with static fallback ({type(exc).__name__})."
        parsed_json = fallback

    # Validate against Pydantic schema to strictly enforce the output contract
    try:
        validated = DSAFeedback(**parsed_json)
        # Ensure backwards-compatibility fields are populated
        res_dict = validated.model_dump()
        if not res_dict.get("correctness_notes"):
            res_dict["correctness_notes"] = validated.improvement_areas.correctness
        if not res_dict.get("actual_time_complexity"):
            res_dict["actual_time_complexity"] = validated.optimization_approach.actual_time_complexity
        if not res_dict.get("actual_space_complexity"):
            res_dict["actual_space_complexity"] = validated.optimization_approach.actual_space_complexity
        if not res_dict.get("complexity_notes"):
            res_dict["complexity_notes"] = validated.optimization_approach.complexity_notes
        if not res_dict.get("edge_cases_missed") and validated.improvement_areas.edge_cases:
            res_dict["edge_cases_missed"] = validated.improvement_areas.edge_cases

        state["feedback"] = res_dict
    except Exception as parse_exc:
        logger.error("Schema validation failed on feedback dict: %s", parse_exc)
        fallback = _generate_demo_feedback(state, exec_result, test_results)
        state["feedback"] = fallback

    return state


# ---------------------------------------------------------------------------
# Graph Construction & Sequential Fallback
# ---------------------------------------------------------------------------
async def _run_sequential(state: AgentState) -> AgentState:
    """Fallback runner if LangGraph is not installed or encounters runtime C-extension issues."""
    state = read_input(state)
    state = await execute_code_node(state)
    state = generate_feedback_node(state)
    return state


def build_graph():
    if not HAS_LANGGRAPH:
        return None
    try:
        graph = StateGraph(AgentState)
        graph.add_node("read_input", read_input)
        graph.add_node("execute_code", execute_code_node)
        graph.add_node("generate_feedback", generate_feedback_node)

        graph.set_entry_point("read_input")
        graph.add_edge("read_input", "execute_code")
        graph.add_edge("execute_code", "generate_feedback")
        graph.add_edge("generate_feedback", END)

        return graph.compile()
    except Exception as exc:
        logger.warning("Could not compile LangGraph (%s). Falling back to sequential execution.", exc)
        return None


code_exec_agent = build_graph()


async def run_code_exec_agent(**kwargs) -> AgentState:
    """Public entrypoint used by main.py"""
    initial_state: AgentState = dict(**kwargs)  # type: ignore
    if code_exec_agent is not None:
        try:
            return await code_exec_agent.ainvoke(initial_state)
        except Exception as exc:
            logger.warning("LangGraph ainvoke failed (%s), running sequential fallback.", exc)
            return await _run_sequential(initial_state)
    else:
        return await _run_sequential(initial_state)
