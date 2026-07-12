#!/usr/bin/env python3
"""Render compact Andrew6rant-style cards using Rehan's data and ASCII art."""
import html
import json
import math
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIRTH_DATE = date(2006, 8, 5)
RAMP = " .:-=+*#%@"


def uptime(today=None):
    today = today or date.today()
    months = (today.year - BIRTH_DATE.year) * 12 + today.month - BIRTH_DATE.month
    if today.day < BIRTH_DATE.day:
        months -= 1
    years, rem_months = divmod(months, 12)
    anchor_month = BIRTH_DATE.month + months
    anchor = date(BIRTH_DATE.year + (anchor_month - 1) // 12, (anchor_month - 1) % 12 + 1, BIRTH_DATE.day)
    days = (today - anchor).days
    return f"{years} years, {rem_months} months, {days} days"


def compact_ascii(cols=45, rows=25):
    """Crop the supplied art and density-resample it to Andrew's 45x25 pane."""
    raw = [line.rstrip() for line in (ROOT / "asci art updated.txt").read_text(encoding="utf-8", errors="replace").splitlines()]
    used = [i for i, line in enumerate(raw) if line.strip()]
    raw = raw[min(used):max(used) + 1]
    # The supplied export includes a low-contrast background/floor tail. Keep
    # the portrait region so the 45x25 card crop reads like Andrew's headshot.
    raw = raw[:max(1, round(len(raw) * 0.70))]
    left = min(len(line) - len(line.lstrip(" ")) for line in raw if line.strip())
    right = max(len(line) for line in raw if line.strip())
    grid = [line[left:right].ljust(right - left) for line in raw]
    h, w = len(grid), right - left
    weights = {c: i / (len(RAMP) - 1) for i, c in enumerate(RAMP)}
    weights.update({"`": .12, "_": .28, "c": .62, "s": .68})
    result = []
    for oy in range(rows):
        y0, y1 = math.floor(oy * h / rows), max(math.floor((oy + 1) * h / rows), 1)
        line = []
        for ox in range(cols):
            x0, x1 = math.floor(ox * w / cols), max(math.floor((ox + 1) * w / cols), 1)
            vals = [weights.get(grid[y][x], .35 if not grid[y][x].isspace() else 0) for y in range(y0, y1) for x in range(x0, x1)]
            density = sum(vals) / len(vals)
            density = 0 if density < .035 else min(1, density * 1.45)
            line.append(RAMP[round(density * (len(RAMP) - 1))])
        result.append("".join(line).rstrip())
    return result


def load_data():
    contributions = json.loads((ROOT / "data" / "contributions.json").read_text(encoding="utf-8"))
    stats_path = ROOT / "data" / "profile_stats.json"
    stats = json.loads(stats_path.read_text(encoding="utf-8")) if stats_path.exists() else {}
    return contributions, stats


def render(theme):
    c, s = load_data()
    dark = theme == "dark"
    bg, text, muted = (("#161b22", "#c9d1d9", "#616e7f") if dark else ("#ffffff", "#24292f", "#6e7781"))
    key, value = (("#ffa657", "#a5d6ff") if dark else ("#953800", "#0550ae"))
    green = "#3fb950" if dark else "#1a7f37"
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" font-family="Consolas,monospace" width="985" height="530" font-size="16">',
           '<style>.key{font-weight:700}text,tspan{white-space:pre}</style>',
           f'<rect width="985" height="530" fill="{bg}" rx="15"/>', f'<text x="15" y="30" fill="{text}">']
    for i, row_text in enumerate(compact_ascii()):
        out.append(f'<tspan x="15" y="{30 + i * 20}">{html.escape(row_text)}</tspan>')
    out.append('</text>')

    x, y = 390, 30
    def plain(line, yy=None, size=16):
        out.append(f'<text x="{x}" y="{yy or y}" fill="{text}" font-size="{size}">{line}</text>')
    def row(label, val, yy, color=None):
        plain(f'<tspan fill="{muted}">. </tspan><tspan class="key" fill="{key}">{html.escape(label)}</tspan>: '
              f'<tspan fill="{color or value}">{html.escape(str(val))}</tspan>', yy)

    plain('rehan@khan ------------------------------------------------')
    row("Uptime", uptime(), 50)
    row("Education", "Final-year BS Computer Science", 70)
    row("Role", "IEEE Computer Society Chair (Student Body)", 90)
    row("IDE", "VS Code (general) | PyCharm (Python)", 110)
    row("Skills.Programming", "Python | C++ | JavaScript", 150)
    row("Skills.Computer", "Bash | SQL | YAML", 170)
    row("Skills.Security", "Cybersecurity | Digital Forensics", 190)
    row("Activities", "CTFs | THM | PortSwigger Labs | Open Source", 210)
    plain('- Profiles ------------------------------------------------', 250)
    row("Portfolio", "devrehaann.vercel.app", 270)
    row("LinkedIn", "rehan-khan-606242404", 290)
    row("Instagram", "cpt_.rehan", 310)
    row("X", "dev_rehann", 330)
    row("TryHackMe", "gtavep18", 350)
    plain('- GitHub Stats --------------------------------------------', 390)
    row("Repos", f'{s.get("repos", "—")} | Stars: {s.get("stars", "—")}', 410)
    row("Commits (year)", s.get("commits_year", "—"), 430)
    row("Followers", s.get("followers", "—"), 450)
    row("Contributions", f'{c["total_contributions"]} | Streak: {c["current_streak"]["length"]} days', 470, green)
    row("Best day", f'{c["best_day"]["count"]} on {c["best_day"]["date"]}', 490)
    out.append('</svg>')
    return "".join(out)


if __name__ == "__main__":
    print(render(sys.argv[1] if len(sys.argv) > 1 else "dark"), end="")
