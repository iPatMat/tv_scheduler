import anthropic
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
    #("football",   "college-football"),
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

Create an optimized TV schedule for a sports bar with 4 TVs.

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
- Favor big-market teams, rivalries, and playoff/meaningful games
- Avoid showing same sport on multiple TVs simultaneously when possible
- Primetime window (5pm-11pm CT) is most important
- When a game ends, suggest what to switch to

Format your response EXACTLY like this with both sections clearly labeled:

SUMMARY:
Write 3-5 plain English sentences summarizing the day. What are the big games, what should staff prioritize, any key switching times to know about. Write this for a bar manager reading a quick morning email.

SCHEDULE:
Write the full day schedule here as simple clean text for bar staff to print and follow.
Use plain text only - no markdown, no asterisks, no hashtags, no table formatting.

Structure the schedule like this example:

MORNING (11am - 3pm)
TV 1 | Cubs vs Cardinals | 12:05pm | MLB.TV
TV 2 | Lakers vs Warriors | 1:00pm | ESPN
TV 3 | ...
TV 4 | ...

AFTERNOON (3pm - 6pm)
TV 1 | ...

PRIMETIME (6pm - close)
TV 1 | ...

Include switching instructions under each time block where relevant.
"""}]
    )

    full_response = message.content[0].text

    # Split into summary and schedule
    summary = ""
    schedule = ""

    if "SUMMARY:" in full_response and "SCHEDULE:" in full_response:
        parts = full_response.split("SCHEDULE:")
        summary = parts[0].replace("SUMMARY:", "").strip()
        schedule = parts[1].strip()
    else:
        # Fallback if Claude doesn't follow the format
        summary = full_response[:500]
        schedule = full_response

    return summary, schedule

def create_pdf(schedule: str, filename: str):
    today_str = date.today().strftime("%A, %B %d, %Y")
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

    for line in schedule.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
        elif line.isupper() or (line.endswith(")") and len(line) < 40):
            story.append(Paragraph(line, section_style))
        else:
            story.append(Paragraph(line, body_style))

    doc.build(story)

def send_email(summary: str, pdf_path: str):
    today_str = date.today().strftime("%A, %B %d")

    msg = MIMEMultipart()
    msg["Subject"] = f"📺 TV Schedule for {today_str}"
    msg["From"] = os.environ["GMAIL_ADDRESS"]
    recipients = os.environ["RECIPIENT_EMAIL"].split(",")
    msg["To"] = os.environ["RECIPIENT_EMAIL"]

    # Email body is just the summary
    body = MIMEText(f"Good morning!\n\n{summary}\n\nFull schedule attached.\n\n— Your Bar Scheduler Bot")
    msg.attach(body)

    # Attach the PDF
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
    summary, schedule = build_schedule(games)

    print("Creating PDF...")
    pdf_path = "/tmp/tv_schedule.pdf"
    create_pdf(schedule, pdf_path)

    print("Sending email...")
    send_email(summary, pdf_path)
    print("Done!")
