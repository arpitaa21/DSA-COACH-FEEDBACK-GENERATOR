"""
streak_db.py
------------
Tiny SQLite-backed daily-practice tracker (the "green box" streak calendar).
Every time the Code Exec Agent finishes a feedback pass for a user, we log one
solve for that day. No external services needed - ships with the repo.
"""

import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "streaks.db"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS practice_log (
            username TEXT NOT NULL,
            day TEXT NOT NULL,
            problems_solved INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (username, day)
        )
        """
    )
    return conn


def log_practice(username: str, when: date | None = None) -> None:
    when = when or date.today()
    conn = _conn()
    conn.execute(
        """
        INSERT INTO practice_log (username, day, problems_solved)
        VALUES (?, ?, 1)
        ON CONFLICT(username, day)
        DO UPDATE SET problems_solved = problems_solved + 1
        """,
        (username, when.isoformat()),
    )
    conn.commit()
    conn.close()


def get_heatmap(username: str, days: int = 182) -> list[dict]:
    """Returns the last `days` days as [{date, count}], oldest first - ready for
    a GitHub/LeetCode-style contribution grid on the frontend."""
    conn = _conn()
    rows = dict(
        conn.execute(
            "SELECT day, problems_solved FROM practice_log WHERE username = ?",
            (username,),
        ).fetchall()
    )
    conn.close()

    today = date.today()
    out = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        out.append({"date": d.isoformat(), "count": rows.get(d.isoformat(), 0)})
    return out


def get_current_streak(username: str) -> int:
    heatmap = get_heatmap(username, days=400)
    streak = 0
    for entry in reversed(heatmap):
        if entry["count"] > 0:
            streak += 1
        else:
            break
    return streak
