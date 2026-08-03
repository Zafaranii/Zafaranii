"""Scrape the public GitHub contributions calendar (no token needed) and
write data/contributions.json with raw days plus derived stats."""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "Zafaranii"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "contributions.json"


def fetch_days():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        cells = soup.select("rect.ContributionCalendar-day")

    days = []
    for cell in cells:
        date = cell.get("data-date")
        level = cell.get("data-level")
        count_attr = cell.get("data-count")
        if date is None:
            continue
        if count_attr is not None:
            count = int(count_attr)
        else:
            tooltip_id = cell.get("id")
            count = 0
            if tooltip_id:
                tip = soup.select_one(f"tool-tip[for={tooltip_id}]")
                if tip:
                    m = re.search(r"([\d,]+)\s+contribution", tip.text)
                    if m:
                        count = int(m.group(1).replace(",", ""))
        days.append({
            "date": date,
            "count": count,
            "level": int(level) if level is not None else 0,
        })
    days.sort(key=lambda d: d["date"])
    return days


def derive_stats(days):
    total = sum(d["count"] for d in days)

    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    best_day = max(days, key=lambda d: d["count"]) if days else None

    monthly = {}
    for d in days:
        month = d["date"][:7]
        monthly[month] = monthly.get(month, 0) + d["count"]

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly": monthly,
    }


def main():
    days = fetch_days()
    if not days:
        print("no contribution cells found, GitHub markup may have changed", file=sys.stderr)
        sys.exit(1)

    stats = derive_stats(days)
    payload = {
        "username": USERNAME,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "days": days,
        "stats": stats,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"wrote {len(days)} days, {stats['total']} contributions -> {OUT_PATH}")


if __name__ == "__main__":
    main()
