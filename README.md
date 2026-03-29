# tv_scheduler

 📺 TV Scheduler

Automatically generates a daily sports TV schedule for a bar with 6 TVs, publishes it to a live web page, and emails a summary every morning at 7am CT.

## How It Works

1. Fetches today's games from the ESPN API (free, no key required)
2. Sends the data to Claude AI to pick the best games for 6 TVs and write a manager summary
3. Saves the output to `schedule.json` and generates a styled HTML schedule page
4. Publishes the page to GitHub Pages automatically
5. Emails the summary to recipients every morning with a link to the live page and a PDF attachment

## Output

| Output | Description |
|---|---|
| **Web page** | Live schedule at `https://<username>.github.io/tv_scheduler/` — updates daily |
| **Email** | Morning summary with a link to the page and a printable PDF attached |
| **schedule.json** | Raw data output used to generate the HTML |

## Stack

| Component | Tool | Cost |
|---|---|---|
| Game data | ESPN API | Free |
| AI scheduling | Anthropic Claude API | ~$1–2/month |
| Web hosting | GitHub Pages | Free |
| Email delivery | Gmail SMTP | Free |
| Automation | GitHub Actions | Free |

## Files

- `tv_schedule.py` — fetches games, builds schedule with Claude, saves `schedule.json`, sends email
- `generate_html.py` — reads `schedule.json` and produces the styled `index.html`
- `requirements.txt` — Python dependencies (`anthropic`, `requests`, `reportlab`)
- `.github/workflows/daily.yml` — runs the scripts every morning and deploys to GitHub Pages

## Setup

### 1. API Keys Required

| Secret Name | Where to Get It |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| `GMAIL_ADDRESS` | Your full Gmail address |
| `GMAIL_APP_PASSWORD` | Google Account → Security → 2-Step Verification → App Passwords |
| `RECIPIENT_EMAIL` | Where to send the schedule (comma-separated for multiple) |

### 2. Add Secrets to GitHub

Go to your repo → **Settings → Secrets and variables → Actions** and add each secret above.

### 3. Enable GitHub Pages

After the first successful workflow run, go to **Settings → Pages** and set the source to the `gh-pages` branch, root folder. The page will be live at `https://<username>.github.io/tv_scheduler/`.

### 4. Run It

The workflow runs automatically every morning at 7am CT. To trigger it manually, go to the **Actions** tab → **Daily Bar TV Schedule** → **Run workflow**.

## Local Development

Copy the example env file and fill in your values:
```bash
cp .env.example .env
```

Then run the scripts:
```bash
export $(cat .env | xargs) && python tv_schedule.py
python generate_html.py schedule.json index.html
```

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
Edit the `SPORTS` list in `tv_schedule.py`:
```python
SPORTS = [
    ("football",    "nfl"),
    ("basketball",  "nba"),
    ("baseball",    "mlb"),
    ("hockey",      "nhl"),
    ("basketball",  "mens-college-basketball"),
    ("football",   "college-football"),
]
```

## Notes

- The ESPN API is an unofficial public endpoint — no signup or API key required
- Gmail requires an App Password (not your regular password) — enable 2-Step Verification first
- Anthropic API credits cost roughly $0.03–0.05 per day at this usage level
- The script runs at 7am CT to ensure ESPN has fully updated to the current day's schedule
- The `gh-pages` branch is managed automatically by the workflow — do not edit it manually
