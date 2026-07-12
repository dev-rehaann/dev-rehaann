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
    # Use the earlier full compact portrait crop on the left.
    grid = grid[:max(1, round(len(grid) * 0.70))]
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
    _, s = load_data()
    dark = theme == "dark"
    bg, text, muted = (("#161b22", "#c9d1d9", "#616e7f") if dark else ("#ffffff", "#24292f", "#6e7781"))
    key, value = (("#ffa657", "#a5d6ff") if dark else ("#953800", "#0550ae"))
    green = "#3fb950" if dark else "#1a7f37"
    red = "#f85149" if dark else "#cf222e"
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="985px" height="530px" font-size="16px">',
           '<style>@font-face{src:local(\'Consolas\'),local(\'Consolas Bold\');font-family:\'ConsolasFallback\';font-display:swap;-webkit-size-adjust:109%;size-adjust:109%}'
           f'.key{{fill:{key}}}.value{{fill:{value}}}.addColor{{fill:{green}}}.delColor{{fill:{red}}}.cc{{fill:{muted}}}text,tspan{{white-space:pre}}</style>',
           f'<rect width="985px" height="530px" fill="{bg}" rx="15"/>', f'<text x="15" y="30" fill="{text}" class="ascii">']
    for i, row_text in enumerate(compact_ascii()):
        out.append(f'<tspan x="15" y="{30 + i * 20}">{html.escape(row_text)}</tspan>')
    out.append('</text>')

    def number(name):
        value_ = s.get(name, "--")
        return f"{value_:,}" if isinstance(value_, int) else str(value_)

    def leader(label, val, target=68):
        count = max(1, target - len(label) - 2 - len(val))
        return " " + "." * count + " "

    def row(label, val, yy):
        label_e, val_e = html.escape(label), html.escape(val)
        out.append(f'<tspan x="390" y="{yy}" class="cc">. </tspan><tspan class="key">{label_e}</tspan>:'
                   f'<tspan class="cc">{leader(label, val)}</tspan><tspan class="value">{val_e}</tspan>')

    out.append(f'<text x="390" y="30" fill="{text}">')
    out.append('<tspan x="390" y="30">Rehan.khan@info</tspan> _______________________________________________')
    row("OS", "Windows 11, iOS 26.5.2, Linux", 50)
    row("Uptime", uptime(), 70)
    row("Host", "Student at Barrett Hodgson University", 90)
    row("IDE", "VS Code 1.127.0", 110)
    out.append('<tspan x="390" y="130" class="cc">. </tspan>')
    row("Languages", "Java, MySQL, Python, C++, C, YAML, Bash", 150)
    row("Activities", "CTFs, TryHackMe, PortSwigger Labs, Open Source", 170)
    row("Security", "Nmap, Wireshark, Metasploit, YARA", 190)
    out.append('<tspan x="390" y="210" class="cc">. </tspan>')
    row("Hobbies.Software", "Open Source Contribution, Gaming", 230)
    row("Hobbies.Hardware", "ESP32", 250)
    out.append('<tspan x="390" y="270" class="cc">. </tspan>')
    out.append('<tspan x="390" y="290">- Contact</tspan> ______________________________________________')
    row("Email", "dev.rehaann@gmail.com", 310)
    row("Insta", "cpt_.rehan", 330)
    out.append('<tspan x="390" y="350" class="cc">. </tspan>')
    out.append('<tspan x="390" y="370">- GitHub Stats</tspan> _________________________________________')
    repos, contributed, stars = number("repos"), number("contributed_repos"), number("stars")
    commits, followers = number("commits_total"), number("followers")
    out.append(f'<tspan x="390" y="390" class="cc">. </tspan><tspan class="key">Repos</tspan>:'
               f'<tspan class="cc">{leader("Repos", repos, 13)}</tspan><tspan class="value">{repos}</tspan> '
               f'{{<tspan class="key">Contributed</tspan>: <tspan class="value">{contributed}</tspan>}} | '
               f'<tspan class="key">Stars</tspan>:<tspan class="cc">{leader("Stars", stars, 17)}</tspan><tspan class="value">{stars}</tspan>')
    out.append(f'<tspan x="390" y="410" class="cc">. </tspan><tspan class="key">Commits</tspan>:'
               f'<tspan class="cc">{leader("Commits", commits, 28)}</tspan><tspan class="value">{commits}</tspan> | '
               f'<tspan class="key">Followers</tspan>:<tspan class="cc">{leader("Followers", followers, 20)}</tspan><tspan class="value">{followers}</tspan>')
    loc, added, removed = number("loc"), number("loc_added"), number("loc_removed")
    out.append(f'<tspan x="390" y="430" class="cc">. </tspan><tspan class="key">Lines of Code on GitHub</tspan>:'
               f'<tspan class="cc">{leader("Lines of Code on GitHub", loc, 35)}</tspan><tspan class="value">{loc}</tspan> ( '
               f'<tspan class="addColor">{added}++</tspan>, <tspan class="delColor">{removed}--</tspan> )')
    out.append('</text></svg>')
    return "".join(out)


if __name__ == "__main__":
    print(render(sys.argv[1] if len(sys.argv) > 1 else "dark"), end="")
