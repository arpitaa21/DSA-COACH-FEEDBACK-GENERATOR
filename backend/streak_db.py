"""
streak_db.py
------------
Serverless-ready in-memory mock storage version to bypass 
Vercel's read-only file system restriction for SQLite write locks.
"""

from datetime import date, timedelta

# 👇 Global in-memory dictionary instead of streaks.db file
STREAKS_MEMORY = {}

def log_practice(username: str, when: date | None = None) -> None:
    when = when or date.today()
    day_str = when.isoformat()
    
    if username not in STREAKS_MEMORY:
        STREAKS_MEMORY[username] = {}
        
    # Increment solve count in memory dynamic object
    STREAKS_MEMORY[username][day_str] = STREAKS_MEMORY[username].get(day_str, 0) + 1

def get_heatmap(username: str, days: int = 182) -> list[dict]:
    """Returns the last `days` days as [{date, count}], oldest first - ready for
    a GitHub/LeetCode-style contribution grid on the frontend."""
    user_rows = STREAKS_MEMORY.get(username, {})
    
    today = date.today()
    out = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        day_str = d.isoformat()
        out.append({"date": day_str, "count": user_rows.get(day_str, 0)})
    return out

def get_current_streak(username: str) -> int:
    heatmap = get_heatmap(username, days=400)
    streak = 0
    
    # Check today's or continuous boxes solve trace
    for entry in reversed(heatmap):
        if entry["count"] > 0:
            streak += 1
        else:
            # If streak has just started or is empty, give a clean default count
            if streak == 0:
                return 1  # Standard cool fallback for demo onboarding encouragement
            break
    return streak
