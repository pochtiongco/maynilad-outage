# Maynilad Outage Monitor

Automated monitor that checks Maynilad Water Services' public interruption feed (emergency, scheduled, and rotational cutoffs) and posts a Discord alert whenever something changes for a specific account/area.

## How it works

1. `checker.py` queries three Maynilad interruption endpoints:
   - `emergency`
   - `scheduled`
   - `rotational`
2. Each response is parsed for a table of active interruptions (city, barangay, area, time window, reason).
3. The combined result is compared against the last known state (`state.json`).
   - If nothing changed since the last run, no notification is sent.
   - If something changed (new interruption, or interruptions cleared), a message is posted to Discord and `state.json` is updated.
4. `state.json` is committed back to the repo by the workflow so state persists between runs.

## Files

| File | Purpose |
|---|---|
| `checker.py` | Main script: fetches, parses, diffs, and notifies |
| `state.json` | Last-sent message, used to detect changes between runs |
| `.github/workflows/monitor.yml` | GitHub Actions workflow that runs the checker |

## Setup

1. **Discord webhook**
   - Create a webhook in your target Discord channel (Channel Settings → Integrations → Webhooks).
   - Add it as a repository secret named `DISCORD_WEBHOOK_URL`:
     `Settings → Secrets and variables → Actions → New repository secret`

2. **Account number (CAN)**
   - `checker.py` currently has the Maynilad account number hardcoded at the top of the file (`CAN = "..."`). Update this to your own account number if you fork this for a different address.

3. **Dependencies**
   - `requests`, `beautifulsoup4` (installed automatically by the workflow)

## Running it

**Manually:**
Go to the **Actions** tab → **Maynilad Monitor** → **Run workflow**.

**On a schedule:**
The workflow file includes a `schedule:` trigger, but GitHub's native cron scheduler was unreliable for this repo (runs simply never fired, even with a `*/5 * * * *` interval — a known reliability gap in GitHub Actions' scheduler, especially on lower-traffic repos). As a workaround, an external cron service ([cron-job.org](https://cron-job.org)) pings the workflow every 30 minutes via the GitHub API instead: