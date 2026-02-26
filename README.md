# YouTube Outreach Personalizer & Sender

Turn scraped YouTube channels into personalized cold emails and send them — no Instantly, no Lemlist, no n8n, no Clay no API keys, just Claude Code + Google Sheets.

## The Problem

You scraped 500 YouTube channels with emails using [bright-data-youtube-outreach](https://github.com/yaronbeen/bright-data-youtube-outreach). Now what?

Writing personalized emails one by one takes hours. Paying for Instantly or Lemlist costs $50-100+/month. And setting up Python scripts with API keys is friction you don't need.

## The Solution

1. **Type `/personalize-outreach` in Claude Code** — Claude reads your CSV and writes personalized emails directly (no API keys, no Python, no dependencies)
2. **Optional: Bright Data MCP enrichment** — scrape each channel's YouTube page for recent video titles and about info, making emails way more specific
3. **Google Apps Script sends them from YOUR Gmail** with random delays
4. **Total cost: $0**

## How It Works

```
Scraper Output CSV
       |
       v
Claude Code skill (/personalize-outreach)
  |                         |
  v                         v
CSV data only         + Bright Data MCP enrichment
  |                    (scrapes YouTube pages for
  |                     recent videos, about info)
  |                         |
  +----------+--------------+
             |
             v
       Outreach CSV
             |
             v
  Google Sheets + Apps Script --> Drip-sent from your Gmail
```

## Prerequisites

### 1. Claude Code (required)

Install Claude Code if you haven't already:

```bash
npm install -g @anthropic-ai/claude-code
```

### 2. Bright Data MCP (optional, recommended)

The Bright Data MCP lets Claude scrape each channel's YouTube page for recent video titles, about page details, and niche signals. This makes emails significantly more specific and personalized.

**Install it:**

```bash
claude mcp add brightdata -- npx @anthropic-ai/mcp-server-brightdata
```

**Set your API token:**

```bash
export BRIGHTDATA_API_TOKEN=your_token_here
```

Get your token at [brightdata.com](https://brightdata.com/) (free trial available).

**What it adds:** Without enrichment, emails reference channel name, subscriber count, and niche keyword. With enrichment, emails reference specific recent video titles, about page details, and content themes. See the [enrichment comparison](#with-vs-without-enrichment) below.

### 3. Install the Skill

```bash
mkdir -p ~/.agents/skills/personalize-outreach
cp SKILL.md ~/.agents/skills/personalize-outreach/SKILL.md
```

## Quick Start

### 1. Clone this repo

```bash
git clone https://github.com/yaronbeen/youtube-outreach-personalize.git
cd youtube-outreach-personalize
```

### 2. Set up your config

```bash
cp config_example.json config.json
```

Edit `config.json` with your details:

```json
{
  "sender_name": "Yaron Been",
  "product_name": "RoasPig",
  "product_url": "https://roaspig.com",
  "product_description": "Real-time ROAS tracking across Meta and Google for e-commerce brands",
  "credibility": "10 years in performance marketing",
  "cta": "Could you share your media kit and pricing?"
}
```

### 3. Add your channels CSV

Place your `channels.csv` (from the [scraper](https://github.com/yaronbeen/bright-data-youtube-outreach)) in this directory. Expected columns:

| Column         | Required | Description                                 |
| -------------- | -------- | ------------------------------------------- |
| `channel_name` | Yes      | YouTube channel name                        |
| `email`        | Yes      | Contact email                               |
| `subscribers`  | No       | Subscriber count                            |
| `description`  | No       | Channel description                         |
| `channel_url`  | No       | YouTube channel URL (needed for enrichment) |
| `keyword`      | No       | Niche keyword                               |

### 4. Run the skill

Open Claude Code in this directory and type:

```
/personalize-outreach
```

Claude will:

1. Find your `channels.csv` and `config.json`
2. Ask if you want to enrich with Bright Data MCP
3. Write a personalized email for each channel
4. Save everything to `outreach.csv`

### 5. Upload to Google Sheets

1. Create a new Google Sheet
2. Go to **File > Import > Upload** and select `outreach.csv`
3. Choose "Replace spreadsheet" and click Import

### 6. Set up Apps Script (sends the emails)

See the [Apps Script Setup](#apps-script-setup) section below.

## Apps Script Setup

This is the part that actually sends your emails from Gmail, one at a time, with random delays.

### Step-by-step:

1. **Open your Google Sheet** (the one with your outreach CSV data)

2. **Go to Extensions > Apps Script**

3. **Delete the default code** in the editor (select all, delete)

4. **Paste the contents of `apps_script.gs`** from this repo

5. **Edit line 29** — change `SENDER_NAME` to your name:

   ```javascript
   const SENDER_NAME = "Yaron Been"; // <-- Your name here
   ```

6. **Save** (Ctrl+S or click the floppy disk icon)

7. **Close the Apps Script tab** and **refresh** your spreadsheet

8. **You'll see a new "Outreach" menu** in the toolbar (may take a few seconds to appear)

9. **Click Outreach > Send Test Email to Myself** — check your inbox to make sure it looks right

10. **Click Outreach > Start Drip Campaign** — it'll confirm the count, then start sending

11. **Close the tab** — it runs on Google's servers in the background. Your laptop can be off.

### Managing your campaign:

| Menu Item                     | What it does                                            |
| ----------------------------- | ------------------------------------------------------- |
| **Start Drip Campaign**       | Confirms count, sends first email, schedules the rest   |
| **Stop Drip Campaign**        | Stops sending. Already-sent emails are not affected     |
| **Send Test Email to Myself** | Sends the first row's email to YOUR inbox for review    |
| **Campaign Status**           | Shows sent/pending/error counts and whether it's active |
| **Reset All Statuses**        | Clears all statuses so you can re-send (careful!)       |
| **Check Gmail Daily Quota**   | Shows how many emails you can still send today          |

### How drip sending works:

- Sends **one email at a time**
- Waits **10-30 minutes** (random) between each email
- Marks each row's status column as `SENT`, `ERROR`, or `SKIP`
- If you stop and restart, it picks up where it left off (skips rows with a status)
- Runs entirely on Google's servers — no need to keep anything open

## With vs. Without Enrichment

### Without enrichment (CSV data only):

```
Subject: Quick question about your tech tutorials

Hi there,

Your tech tutorial content covering AI tools is consistently useful.
I'm Yaron, founder of RoasPig (roaspig.com), a tool that tracks
ad performance across Meta and Google in one dashboard. A lot of
your audience runs paid ads alongside their tech stack — could be
a natural fit. Could you share your media kit and pricing?

Best,
Yaron
```

### With Bright Data MCP enrichment:

```
Subject: Loved your Notion AI workflow video

Hi there,

Your breakdown of the Notion AI + Zapier automation workflow last
week was one of the clearest I've seen — especially the part about
trigger conditions. I'm Yaron, founder of RoasPig (roaspig.com),
which gives marketers real-time ROAS dashboards across Meta and
Google. Your audience already optimizes their workflow — ad tracking
is the next piece. Could you share your media kit and pricing?

Best,
Yaron
```

The enriched version references a specific recent video and details from the about page, making it feel like you actually watch their channel.

## Example

**Input** (from scraper CSV):

```
channel_name: Marketing Mike
email: mike@marketingmike.co
subscribers: 12,000
description: Performance marketing strategies and Facebook ads breakdowns
keyword: facebook ads
```

**Output** (personalized email):

```
Subject: Sponsorship idea for your Facebook ads content

Hi Mike,

Your Meta ads audit videos are seriously detailed — the breakdown
of campaign structures is something most marketers charge for. I'm
Yaron, I built RoasPig (roaspig.com) which gives e-commerce brands
real-time ROAS tracking across ad platforms. Your audience is
exactly who we built this for. Could you share your media kit and
pricing?

Best,
Yaron
```

## Config Fields

| Field                 | What it does                                 | Example                                            |
| --------------------- | -------------------------------------------- | -------------------------------------------------- |
| `sender_name`         | Your name in the sign-off                    | `"Yaron Been"`                                     |
| `product_name`        | What you're promoting                        | `"RoasPig"`                                        |
| `product_url`         | Your website URL                             | `"https://roaspig.com"`                            |
| `product_description` | One sentence — what it does and who it's for | `"Real-time ROAS tracking across Meta and Google"` |
| `credibility`         | Why they should care (optional social proof) | `"10 years in performance marketing"`              |
| `cta`                 | The ask — what you want them to do           | `"Could you share your media kit and pricing?"`    |

## Cold Email Tips

- **Keep it short** — under 100 words. Nobody reads long cold emails.
- **Be specific in the first line** — reference something real about their channel, not "I love your content."
- **One clear CTA** — don't give them 3 things to do. One ask.
- **Send from a real, aged inbox** — not a brand new Gmail you created yesterday.
- **10-30 min delays look natural** — that's what the Apps Script does automatically.
- **Follow up** — most replies come from follow-up #2 or #3 (not covered in this repo yet).
- **Review before sending** — always check `outreach.csv` and send a test email to yourself first.

## Cost Breakdown

| Component                     | Cost                                   |
| ----------------------------- | -------------------------------------- |
| Claude Code (personalization) | **$0** (runs in your existing session) |
| Bright Data MCP (enrichment)  | Free trial, then per-scrape pricing    |
| Gmail (free)                  | 100 emails/day                         |
| Gmail (Workspace)             | 1,500 emails/day ($6/mo)               |
| **vs. Instantly**             | $30-97/month                           |
| **vs. Lemlist**               | $59-99/month                           |

The personalization itself costs nothing — Claude Code does it as part of your session. No separate API calls, no Python script, no `ANTHROPIC_API_KEY` needed.

## File Structure

```
├── README.md               # This file
├── SKILL.md                # Claude Code skill definition (the main deliverable)
├── apps_script.gs          # Google Apps Script drip sender
├── config_example.json     # Example config (copy to config.json)
├── sample_channels.csv     # Example input (5 fictional channels)
├── sample_outreach.csv     # Example output (personalized emails)
└── .gitignore
```

## Related

- [bright-data-youtube-outreach](https://github.com/yaronbeen/bright-data-youtube-outreach) — the scraper that finds YouTube channels and their emails (Step 1)
- This repo is Step 2: personalize and send

## Disclaimer

This tool is for legitimate business outreach. Be respectful — don't spam, honor unsubscribe requests, and follow applicable email laws (CAN-SPAM, GDPR). The authors are not responsible for how you use this tool.

## License

MIT
