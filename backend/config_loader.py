"""
config_loader.py
-----------------
Loads agent persona config (role / goal / backstory) from config/agents.yaml.

Kept as a tiny standalone module - rather than inlining a yaml.safe_load()
call in agent.py - so any future agent (or a real CrewAI Agent, if the project
grows into that) can load its config from the same file the same way.
"""
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import yaml

CONFIG_PATH = Path(__file__).parent / "config" / "agents.yaml"
TOOLS_CONFIG_PATH = Path(__file__).parent / "config" / "tools.yaml"
REQUIRED_FIELDS = ("role", "goal", "backstory")


@lru_cache(maxsize=None)
def load_agent_config(agent_key: str = "code_exec_agent") -> dict:
    """Returns {"role": ..., "goal": ..., "backstory": ...} for the given
    agent key, read from config/agents.yaml. Cached - the file is read once
    per process, not on every request."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Agent config not found at {CONFIG_PATH}. "
            f"Did backend/config/agents.yaml get deleted or moved?"
        )

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        all_agents = yaml.safe_load(f) or {}

    if agent_key not in all_agents:
        raise KeyError(f"No agent named '{agent_key}' found in {CONFIG_PATH}")

    config = all_agents[agent_key]
    missing = [field for field in REQUIRED_FIELDS if not config.get(field)]
    if missing:
        raise KeyError(
            f"Agent '{agent_key}' in {CONFIG_PATH} is missing required field(s): {missing}"
        )

    return {field: str(config[field]).strip() for field in REQUIRED_FIELDS}


@lru_cache(maxsize=None)
def load_tools_config() -> dict:
    """Returns the full parsed contents of config/tools.yaml - tool provider
    defaults, sandbox settings, and the RAG data-source manifest. Cached -
    read once per process."""
    if not TOOLS_CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Tools config not found at {TOOLS_CONFIG_PATH}. "
            f"Did backend/config/tools.yaml get deleted or moved?"
        )
    with open(TOOLS_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
