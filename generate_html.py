import json
import sys
from datetime import date
from html import escape

def generate_html(schedule_path="schedule.json", output_path="index.html"):
    with open(schedule_path) as f:
        data = json.load(f)

    date_str = escape(data.get("date", date.today().strftime("%A, %B %d, %Y")))
    summary = escape(data.get("summary", ""))
    time_blocks = data.get("time_blocks", [])

    blocks_html = ""
    for block in time_blocks:
        label = escape(block.get("label", ""))
        time_range = escape(block.get("time_range", ""))
        assignments = block.get("assignments", [])
        switching_notes = block.get("switching_notes", "").strip()

        rows_html = ""
        for a in assignments:
            tv = int(a.get("tv", 0))
            game = escape(str(a.get("game", "")))
            time = escape(str(a.get("time", "")))
            network = escape(str(a.get("network", "")))
            league = escape(str(a.get("league", "")))
            is_playoff = a.get("is_playoff", False)

            playoff_badge = (
                '<span class="playoff-badge">Playoff / Tournament</span>'
                if is_playoff else ""
            )

            rows_html += f"""
      <div class="row">
        <div class="tv-badge">TV {tv}</div>
        <div class="game-info">
          <div class="game">{game}{playoff_badge}</div>
          <div class="meta">{time}&nbsp;&nbsp;·&nbsp;&nbsp;{network}&nbsp;&nbsp;·&nbsp;&nbsp;{league}</div>
        </div>
      </div>"""

        switching_html = ""
        if switching_notes:
            switching_html = f'<div class="switching">&#x21B3; {escape(switching_notes)}</div>'

        blocks_html += f"""
  <div class="block">
    <details open>
      <summary>
        {label}
        <span class="time-range">{time_range}</span>
      </summary>
      <div class="assignments">{rows_html}
      </div>{switching_html}
    </details>
  </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TV Schedule &mdash; {date_str}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0f0f0f;
      color: #e0e0e0;
      min-height: 100vh;
    }}

    header {{
      background: #1a1a2e;
      padding: 1.5rem 1rem 1.25rem;
      text-align: center;
      border-bottom: 3px solid #e94560;
    }}
    header h1 {{
      font-size: 1.6rem;
      letter-spacing: 3px;
      text-transform: uppercase;
      color: #ffffff;
      font-weight: 800;
    }}
    header .date {{
      color: #9090a8;
      margin-top: 0.3rem;
      font-size: 0.9rem;
      letter-spacing: 1px;
    }}

    .summary {{
      background: #1e1e2e;
      border-left: 4px solid #e94560;
      border-radius: 0 8px 8px 0;
      padding: 1rem 1.25rem;
      margin: 1rem;
      font-size: 0.95rem;
      line-height: 1.65;
      color: #c0c0d0;
    }}

    .block {{
      margin: 0.75rem 1rem;
    }}

    details {{
      background: #1e1e2e;
      border-radius: 10px;
      overflow: hidden;
      border: 1px solid #2a2a40;
    }}

    summary {{
      padding: 0.9rem 1rem;
      cursor: pointer;
      font-weight: 700;
      font-size: 0.95rem;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      color: #e94560;
      list-style: none;
      display: flex;
      align-items: center;
      justify-content: space-between;
      user-select: none;
    }}
    summary::-webkit-details-marker {{ display: none; }}
    summary::after {{
      content: "\\25BE";
      font-size: 1.1rem;
      transition: transform 0.2s ease;
      color: #555;
    }}
    details[open] summary::after {{
      transform: rotate(-180deg);
    }}

    .time-range {{
      font-weight: 400;
      font-size: 0.78rem;
      color: #666;
      letter-spacing: 0.5px;
      margin-left: 0.5rem;
      text-transform: none;
    }}

    .assignments {{
      padding-bottom: 0.25rem;
    }}

    .row {{
      display: grid;
      grid-template-columns: 52px 1fr;
      gap: 0.75rem;
      padding: 0.65rem 1rem;
      border-top: 1px solid #252538;
      align-items: start;
    }}
    .row:hover {{
      background: #23233a;
    }}

    .tv-badge {{
      background: #e94560;
      color: #fff;
      font-weight: 700;
      font-size: 0.75rem;
      padding: 0.2rem 0.4rem;
      border-radius: 5px;
      text-align: center;
      margin-top: 3px;
      letter-spacing: 0.5px;
      white-space: nowrap;
    }}

    .game-info .game {{
      font-weight: 600;
      font-size: 0.95rem;
      color: #e8e8f0;
      line-height: 1.3;
    }}
    .game-info .meta {{
      color: #666;
      font-size: 0.8rem;
      margin-top: 3px;
    }}

    .playoff-badge {{
      display: inline-block;
      background: #f4a261;
      color: #111;
      font-size: 0.65rem;
      font-weight: 800;
      padding: 2px 7px;
      border-radius: 4px;
      margin-left: 7px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      vertical-align: middle;
      position: relative;
      top: -1px;
    }}

    .switching {{
      padding: 0.6rem 1rem;
      color: #666;
      font-size: 0.82rem;
      font-style: italic;
      border-top: 1px solid #252538;
      background: #191926;
    }}

    footer {{
      text-align: center;
      padding: 2.5rem 1rem 2rem;
      color: #444;
      font-size: 0.78rem;
    }}

    @media (min-width: 640px) {{
      header h1 {{ font-size: 2rem; }}
      .summary, .block {{ max-width: 700px; margin-left: auto; margin-right: auto; }}
    }}
  </style>
</head>
<body>

<header>
  <h1>&#128250; TV Schedule</h1>
  <div class="date">{date_str}</div>
</header>

<div class="summary">{summary}</div>

{blocks_html}

<footer>Generated by Bar Scheduler Bot</footer>

</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated {output_path}")

if __name__ == "__main__":
    schedule_path = sys.argv[1] if len(sys.argv) > 1 else "schedule.json"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "index.html"
    generate_html(schedule_path, output_path)
