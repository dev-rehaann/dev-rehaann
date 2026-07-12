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
    left = min(len(line) - len(line.lstrip(" ")) for line in raw if line.strip())
    right = max(len(line) for line in raw if line.strip())
    grid = [line[left:right].ljust(right - left) for line in raw]
    # Face-focused crop: exclude the oversized torso and background before
    # reducing to Andrew's compact 45x25 portrait pane.
    grid = [line[15:135].ljust(120) for line in grid[10:62]]
    h, w = len(grid), len(grid[0])
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

    plain('rehan@info ------------------------------------------------')
    row("OS", "Windows 11 | iOS | Linux", 50)
    row("Uptime", uptime(), 70)
    row("Host", "Student at Barrett Hodgson University", 90)
    row("IDE", "VS Code 1.127.0", 110)
    row("Languages", "Java | MySQL | Python | C++ | C | YAML | Bash", 150)
    row("Security", "Nmap | Wireshark | Metasploit | YARA", 170)
    row("Hobbies.Software", "Open Source Contribution | Gaming", 210)
    row("Hobbies.Hardware", "ESP32", 230)
    plain('- Contact -------------------------------------------------', 270)
    row("Email", "dev.rehaann@gmail.com", 290)
    row("Insta", "cpt_.rehan", 310)
    plain('- GitHub Stats --------------------------------------------', 350)
    row("My repos", f'{s.get("repos", "—")} (Contribution: {s.get("contributed_repos", "—")}) | Stars: {s.get("stars", "—")}', 370)
    row("Commits", f'{s.get("commits_total", "—")} | Followers: {s.get("followers", "—")}', 390)
    loc = s.get("loc", "—")
    added = s.get("loc_added", "—")
    removed = s.get("loc_removed", "—")
    row("Lines of code on GitHub", f'{loc} ({added}++, {removed}--)', 410, green)
    out.append('</svg>')
    return "".join(out)


if __name__ == "__main__":
    print(render(sys.argv[1] if len(sys.argv) > 1 else "dark"), end="")
