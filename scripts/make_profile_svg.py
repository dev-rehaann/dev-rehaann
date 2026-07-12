#!/usr/bin/env python3
"""Build Andrew6rant-style profile cards from Rehan's supplied ASCII art."""
import html
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASCII_PATH = ROOT / "asci art updated.txt"
DATA_PATH = ROOT / "data" / "contributions.json"
BIRTH_DATE = date(2006, 8, 5)


def uptime(today=None):
    """Return calendar-accurate age in years, months and days."""
    today = today or date.today()
    total_months = (today.year - BIRTH_DATE.year) * 12 + today.month - BIRTH_DATE.month
    if today.day < BIRTH_DATE.day:
        total_months -= 1
    years, months = divmod(total_months, 12)
    anchor_month = BIRTH_DATE.month + total_months
    anchor_year = BIRTH_DATE.year + (anchor_month - 1) // 12
    anchor_month = (anchor_month - 1) % 12 + 1
    anchor = date(anchor_year, anchor_month, BIRTH_DATE.day)
    days = (today - anchor).days
    return f"{years} years, {months} months, {days} days"


def ascii_rows():
    lines = ASCII_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    lines = [line.rstrip() for line in lines]
    nonblank = [i for i, line in enumerate(lines) if line.strip()]
    lines = lines[min(nonblank):max(nonblank) + 1]
    left = min(len(line) - len(line.lstrip(" ")) for line in lines if line.strip())
    right = max(len(line) for line in lines if line.strip())
    return [line[left:right] for line in lines]


def render(theme):
    rows = ascii_rows()
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    dark = theme == "dark"
    bg = "#161b22" if dark else "#ffffff"
    text = "#c9d1d9" if dark else "#24292f"
    muted = "#768390" if dark else "#57606a"
    key = "#ffa657" if dark else "#953800"
    value = "#a5d6ff" if dark else "#0550ae"
    green = "#3fb950" if dark else "#1a7f37"

    # Match Andrew6rant's compact 985x530 terminal-card footprint. The original
    # high-resolution ASCII stays intact, but is scaled into the portrait pane.
    width, height = 985, 530
    native_w = max(len(row) for row in rows) * 8
    native_h = len(rows) * 15
    scale = min(355 / native_w, 490 / native_h)
    art_x = 15
    art_y = (height - native_h * scale) / 2

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        'font-family="Consolas, ui-monospace, SFMono-Regular, Menlo, monospace">',
        '<style>text,tspan{white-space:pre}.key{font-weight:700}</style>',
        f'<rect width="{width}" height="{height}" rx="18" fill="{bg}"/>',
        f'<g transform="translate({art_x:.2f} {art_y:.2f}) scale({scale:.5f})" fill="{text}">',
    ]
    for i, row in enumerate(rows):
        out.append(f'<text xml:space="preserve" x="0" y="{(i + 1) * 15}" font-size="12.9">{html.escape(row)}</text>')
    out.append('</g>')

    x, y, line = 390, 30, 20
    total = data["total_contributions"]
    current = data["current_streak"]["length"]
    longest = data["longest_streak"]["length"]
    best = data["best_day"]

    def row(label, val, color=value):
        nonlocal y
        out.append(f'<text x="{x}" y="{y}" fill="{text}" font-size="16">'
                   f'<tspan fill="{muted}">. </tspan><tspan class="key" fill="{key}">{html.escape(label)}</tspan>: '
                   f'<tspan fill="{color}">{html.escape(str(val))}</tspan></text>')
        y += line

    out.append(f'<text x="{x}" y="{y}" fill="{text}" font-size="17" font-weight="700">rehan@github</text>')
    y += 30
    row("Name", "Rehan Khan")
    row("Uptime", uptime())
    row("Education", "Final-year BS Computer Science")
    row("Role", "IEEE Computer Society Chair (Student Body)")
    row("Interests", "Cybersecurity | Digital Forensics")
    row("IDE", "VS Code (general) | PyCharm (Python)")
    row("Programming", "Python | C++ | JavaScript")
    row("Computer", "Bash | SQL | YAML")
    row("Activities", "CTFs | TryHackMe | PortSwigger Labs | Open Source")
    y += 10
    out.append(f'<text x="{x}" y="{y}" fill="{text}" font-size="16" font-weight="700">- Profiles ------------------------------------</text>')
    y += 26
    row("Portfolio", "devrehaann.vercel.app")
    row("LinkedIn", "rehan-khan-606242404")
    row("Instagram", "cpt_.rehan")
    row("X", "dev_rehann")
    row("TryHackMe", "gtavep18")
    y += 10
    out.append(f'<text x="{x}" y="{y}" fill="{text}" font-size="16" font-weight="700">- GitHub Stats --------------------------------</text>')
    y += 26
    row("Contributions", f"{total:,} in the last year", green)
    row("Current streak", f"{current} days")
    row("Longest streak", f"{longest} days")
    row("Best day", f'{best["count"]} on {best["date"]}')
    out.append('</svg>')
    return "".join(out)


if __name__ == "__main__":
    print(render(sys.argv[1] if len(sys.argv) > 1 else "dark"), end="")
