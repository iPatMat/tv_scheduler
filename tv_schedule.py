import anthropic
import json
import re
import requests
from datetime import date, datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER

SPORTS = [
    ("football",    "nfl"),
    ("basketball",  "nba"),
    ("baseball",    "mlb"),
    ("hockey",      "nhl"),
    ("basketball",  "mens-college-basketball"),
    ("football",   "college-football"),
    ("soccer", "fifa.world"),
]

def fetch_todays_games():
    all_games = []
    today_str = date.today().strftime("%Y%m%d")

    for sport, league in SPORTS:
        try:
            url = f"http://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard?dates={today_str}"
            data = requests.get(url, timeout=10).json()
            for event in data.get("events", []):
                name = event.get("name", "Unknown")
                time_utc = event.get("date", "")
                competitions = event.get("competitions", [{}])
                broadcast = competitions[0].get("broadcast", "Unknown") if competitions else "Unknown"
                all_games.append(f"{name} | {time_utc} | {broadcast}")
        except Exception as e:
            print(f"Error fetching {league}: {e}")
    return "\n".join(all_games) if all_games else "No games found today."

def build_schedule(games: str) -> tuple:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    today = date.today().strftime("%A, %B %d, %Y")

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": f"""Today is {today}. Here are all sports games on TV today (times are UTC):

{games}

Create an optimized TV schedule for a sports bar with 6 TVs.

Guidelines:
- Convert times to Central Time (UTC-5 or UTC-6 depending on DST)
- Prioritize based on the time of year and what is culturally significant that day.
  General hierarchy: NFL > NBA Finals/Playoffs > MLB Playoffs/World Series > NHL Playoffs > NCAA March Madness > NBA regular season > MLB regular season > NHL regular season > Other
- HOWEVER, use common sense seasonal logic:
  If it is March, NCAA Men's Basketball Tournament games (March Madness) should be treated as must-show events. March Madness is college BASKETBALL, not football. College football is out of season in March - ignore any college football data as it will be future schedules.
  If it is October, MLB playoff/World Series games outrank everything except NFL.
  If it is June, NBA Finals outrank everything except NFL.
  If there are only a few tournament/playoff games on, dedicate TVs to them before filling with regular season games.
- Always flag when a game is a tournament or playoff game vs regular season.
- This bar is located in Dallas, Texas. Always prioritize local Dallas teams
  when they are playing: Dallas Cowboys (NFL), Dallas Mavericks (NBA),
  Dallas Stars (NHL), and Texas Rangers (MLB). Treat any Dallas team game
  as must-show on at least one TV regardless of opponent.
- After Dallas teams, favor big-market teams, rivalries, and playoff/meaningful games
- Also note Texas college teams (Texas, Texas A&M, TCU, Baylor, Texas Tech) have strong
  local interest and should be prioritized over out-of-market college games when equal
- Avoid showing same sport on multiple TVs simultaneously when possible
- Primetime window (5pm-11pm CT) is most important
- When a game ends, suggest what to switch to in switching_notes
- For each game, include the DirecTV channel number in parentheses after
  the network name. This bar uses DirecTV in Dallas, Texas.
  Common mappings: CBS = 4, NBC = 5, ABC = 7, ESPN = 206, ESPN2 = 209,
  FS1 = 219, FS2 = 618, TNT = 245, TBS = 247, truTV = 246,
  NHL Network = 215, NBA TV = 216, MLB Network = 213,
  NFL Network = 212, CBS Sports Network = 221

Return ONLY valid JSON with no markdown, no code fences, no extra text. Use exactly this structure:

{{
  "summary": "3-5 plain English sentences for a bar manager. What are the big games, what should staff prioritize, any key switching times.",
  "time_blocks": [
    {{
      "label": "MORNING",
      "time_range": "11am - 3pm CT",
      "assignments": [
        {{
          "tv": 1,
          "game": "Team A vs Team B",
          "time": "12:05pm CT",
          "network": "ESPN (206)",
          "league": "MLB",
          "is_playoff": false
        }}
      ],
      "switching_notes": "Optional note about what to switch to when a game ends"
    }}
  ]
}}

Include all three time blocks in order: MORNING (11am-3pm CT), AFTERNOON (3pm-6pm CT), PRIMETIME (6pm-close CT).
Omit a time block entirely if there are no games in that window.
"""}]
    )

    full_response = message.content[0].text.strip()

    try:
        data = json.loads(full_response)
    except json.JSONDecodeError:
        # Try to extract JSON if there's stray text around it
        match = re.search(r'\{.*\}', full_response, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            print("Warning: Claude did not return valid JSON. Using fallback.")
            data = {"summary": full_response[:500], "time_blocks": []}

    summary = data.get("summary", "")
    return summary, data

def save_schedule_json(data: dict, filename: str):
    today = date.today().strftime("%A, %B %d, %Y")
    output = {"date": today, **data}
    with open(filename, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Saved schedule to {filename}")

def schedule_data_to_text(data: dict) -> str:
    """Reconstruct a plain-text schedule from structured JSON for PDF generation."""
    lines = []
    for block in data.get("time_blocks", []):
        label = block.get("label", "")
        time_range = block.get("time_range", "")
        lines.append(f"{label} ({time_range})")
        for a in block.get("assignments", []):
            playoff_tag = " [PLAYOFF/TOURNAMENT]" if a.get("is_playoff") else ""
            lines.append(
                f"TV {a['tv']} | {a['game']} | {a['time']} | {a['network']}{playoff_tag}"
            )
        switching = block.get("switching_notes", "").strip()
        if switching:
            lines.append(f">> {switching}")
        lines.append("")
    return "\n".join(lines)

def create_pdf(schedule_data: dict, filename: str):
    today_str = date.today().strftime("%A, %B %d, %Y")
    schedule_text = schedule_data_to_text(schedule_data)

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=16,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=6
    )

    date_style = ParagraphStyle(
        "Date",
        parent=styles["Normal"],
        fontSize=11,
        fontName="Helvetica",
        alignment=TA_CENTER,
        spaceAfter=16
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontSize=12,
        fontName="Helvetica-Bold",
        spaceBefore=14,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica",
        spaceBefore=2,
        spaceAfter=2,
        leading=14
    )

    story = []
    story.append(Paragraph("TV Schedule", title_style))
    story.append(Paragraph(today_str, date_style))

    for line in schedule_text.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
        elif line.isupper() or (line.endswith(")") and len(line) < 40):
            story.append(Paragraph(line, section_style))
        else:
            story.append(Paragraph(line, body_style))

    doc.build(story)

def send_email(summary: str, pdf_path: str, pages_url: str = ""):
    today_str = date.today().strftime("%A, %B %d")

    msg = MIMEMultipart()
    msg["Subject"] = f"📺 TV Schedule for {today_str}"
    msg["From"] = os.environ["GMAIL_ADDRESS"]
    recipients = os.environ["RECIPIENT_EMAIL"].split(",")
    msg["To"] = os.environ["RECIPIENT_EMAIL"]

    footer = "\n\nFull schedule attached as PDF."
    if pages_url:
        footer += f"\nView online: {pages_url}"

    body = MIMEText(f"Good morning!\n\n{summary}{footer}\n\n— Your Bar Scheduler Bot")
    msg.attach(body)

    with open(pdf_path, "rb") as f:
        attachment = MIMEBase("application", "octet-stream")
        attachment.set_payload(f.read())
        encoders.encode_base64(attachment)
        attachment.add_header(
            "Content-Disposition",
            f"attachment; filename=TV_Schedule_{date.today().strftime('%Y%m%d')}.pdf"
        )
        msg.attach(attachment)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.environ["GMAIL_ADDRESS"], os.environ["GMAIL_APP_PASSWORD"])
        server.sendmail(os.environ["GMAIL_ADDRESS"], recipients, msg.as_string())
    print("Email sent successfully!")

if __name__ == "__main__":
    print("Fetching today's games...")
    games = fetch_todays_games()
    print(f"Found {len(games.splitlines())} games")

    print("Building schedule with Claude...")
    summary, schedule_data = build_schedule(games)

    print("Saving schedule JSON...")
    save_schedule_json(schedule_data, "schedule.json")

    print("Creating PDF...")
    pdf_path = "/tmp/tv_schedule.pdf"
    create_pdf(schedule_data, pdf_path)

    # Build GH Pages URL from the built-in GITHUB_REPOSITORY env var
    github_repo = os.environ.get("GITHUB_REPOSITORY", "")
    pages_url = ""
    if github_repo and "/" in github_repo:
        owner, repo = github_repo.split("/", 1)
        pages_url = f"https://{owner}.github.io/{repo}/"

    print("Sending email...")
    send_email(summary, pdf_path, pages_url)
    print("Done!")
