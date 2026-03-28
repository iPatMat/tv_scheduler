# tv_scheduler

 📺 TV Scheduler

Automatically generates a daily sports TV schedule for a bar with 4 TVs and emails it every morning at 9am CT.

## How It Works

1. Fetches today's games from the ESPN API (free, no key required)
2. Sends the data to Claude AI to pick the best games for 4 TVs
3. Emails the schedule to a recipient every morning automatically via Gmail

## Stack

| Component | Tool | Cost |
|---|---|---|
| Game data | ESPN API | Free |
| AI scheduling | Anthropic Claude API | ~$1–2/month |
| Email delivery | Gmail SMTP | Free |
| Automation | GitHub Actions | Free |

## Files

- `tv_schedule.py` — main script that fetches games, builds schedule, sends email
- `requirements.txt` — Python dependencies (`anthropic`, `requests`)
- `.github/workflows/daily.yml` — GitHub Actions workflow that runs the script every morning

## Setup

### 1. API Keys Required

| Secret Name | Where to Get It |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| `GMAIL_ADDRESS` | Your full Gmail address |
| `GMAIL_APP_PASSWORD` | Google Account → Security → 2-Step Verification → App Passwords |
| `RECIPIENT_EMAIL` | Where to send the schedule |

### 2. Add Secrets to GitHub

Go to your repo → **Settings → Secrets and variables → Actions** and add each secret above.

### 3. Run It

The workflow runs automatically every morning at 9am CT. To trigger it manually, go to the **Actions** tab → **Daily Bar TV Schedule** → **Run workflow**.

## Customization

### Change the send time
Edit the cron line in `.github/workflows/daily.yml`:
```yaml
- cron: '0 14 * * *'  # 9am Central Time (UTC-5)
```

### Change sport priorities
Edit the priority guidelines in the prompt inside `tv_schedule.py`. Current hierarchy:
```
NFL > NBA Finals/Playoffs > MLB Playoffs/World Series > NHL Playoffs > NCAA March Madness > NBA regular season > MLB regular season > NHL regular season
```

### Add or remove sports
Edit the `SPORTS` list in `tv_schedule.py`. College football is commented out during the off-season — uncomment in September:
```python
SPORTS = [
    ("football",    "nfl"),
    ("basketball",  "nba"),
    ("baseball",    "mlb"),
    ("hockey",      "nhl"),
    ("basketball",  "mens-college-basketball"),
    ("football",  "college-football"), 
]
```

## Notes

- The ESPN API is an unofficial public endpoint — no signup or API key required
- Gmail requires an App Password (not your regular password) — enable 2-Step Verification first
- Anthropic API credits cost roughly $0.03–0.05 per day at this usage level
- The script runs at 7am CT to ensure ESPN has fully updated to the current day's schedule
