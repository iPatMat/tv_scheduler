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
    #("football",    "college-football"),
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

Format the output as a simple, easy-to-read briefing for bar staff.
Use plain text only - no markdown, no asterisks, no hashtags, no table formatting.

Structure it like this example:

MORNING (11am - 3pm)
TV 1 | Cubs vs Cardinals | 12:05pm | MLB.TV
TV 2 | Lakers vs Warriors | 1:00pm | ESPN
TV 3 | ...
TV 4 | ...

AFTERNOON (3pm - 6pm)
TV 1 | ...

PRIMETIME (6pm - close) 
TV 1 | ...

At the end include a 3-5 sentence plain English summary of the day -
what the big games are, what to prioritize, and any switching recommendations.
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
