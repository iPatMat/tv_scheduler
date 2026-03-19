import anthropic
import requests
from datetime import date, datetime
import smtplib
from email.mime.text import MIMEText
import os

SPORTS = [
    ("football",    "nfl"),
    ("basketball",  "nba"),
    ("baseball",    "mlb"),
    ("hockey",      "nhl"),
    ("basketball",  "mens-college-basketball"),
    ("football",    "college-football"),
]

def fetch_todays_games():
    all_games = []
    for sport, league in SPORTS:
        try:
            url = f"http://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"
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

def build_schedule(games: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    today = date.today().strftime("%A, %B %d, %Y")

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": f"""
Today is {today}. Here are all sports games on TV today (times are UTC):

{games}

Create an optimized TV schedule for a sports bar with 4 TVs.

Guidelines:
- Convert times to Central Time (UTC-5 or UTC-6 depending on DST)
- Prioritize: NFL > NBA playoffs > MLB > NHL > College sports > Other
- Favor big-market teams, rivalries, and playoff/meaningful games
- Avoid showing same sport on multiple TVs simultaneously when possible
- Primetime window (5pm-11pm CT) is most important
- When a game ends, suggest what to switch to

Format as a clean schedule like:
TV 1: [Game name] [Time CT] [Network]
TV 2: [Game name] [Time CT] [Network]
...then show time blocks for the full day.
"""}]
    )
    return message.content[0].text

def send_email(schedule: str):
    today_str = date.today().strftime("%A, %B %d")
    msg = MIMEText(f"Good morning!\n\nHere is today's recommended TV schedule:\n\n{schedule}\n\n— Your Bar Scheduler Bot")
    msg["Subject"] = f"📺 TV Schedule for {today_str}"
    msg["From"] = os.environ["GMAIL_ADDRESS"]
    msg["To"] = os.environ["RECIPIENT_EMAIL"]

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.environ["GMAIL_ADDRESS"], os.environ["GMAIL_APP_PASSWORD"])
        server.send_message(msg)
    print("Email sent successfully!")

if __name__ == "__main__":
    print("Fetching today's games...")
    games = fetch_todays_games()
    print(f"Found {len(games.splitlines())} games")
    print("Building schedule with Claude...")
    schedule = build_schedule(games)
    print("Sending email...")
    send_email(schedule)
    print("Done!")
