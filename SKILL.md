---
name: personalize-outreach
description: Personalizes cold outreach emails for YouTube channels. Reads a channels CSV, optionally enriches via Bright Data MCP scraping, writes personalized emails to output CSV. Use when asked to personalize outreach or run /personalize-outreach.
---

# YouTube Outreach Email Personalizer

Reads a CSV of YouTube channels, optionally enriches each channel by scraping their YouTube page via Bright Data MCP, then writes a personalized cold email for each channel. Outputs a ready-to-send CSV for Google Sheets + Apps Script.

## Workflow

### Step 1: Detect Files

Look for input files in the current working directory:

1. **Channels CSV**: Look for `channels.csv`, then `sample_channels.csv`. If neither found, ask the user for the path.
2. **Config JSON**: Look for `config.json`, then `config_example.json`. If neither found, ask the user for the path.

Use Glob to find these files. If multiple matches, prefer `channels.csv` over `sample_channels.csv` and `config.json` over `config_example.json`.

### Step 2: Read Config

Read the config JSON file. It should contain:

```json
{
  "sender_name": "Your Name",
  "product_name": "Your Product",
  "product_url": "https://yourproduct.com",
  "product_description": "Brief description of your product and who it's for",
  "credibility": "Your relevant experience",
  "cta": "Could you share your media kit and pricing?"
}
```

If any required field is missing or still has placeholder values (like "Your Name"), warn the user and ask if they want to continue with placeholders or provide real values.

### Step 3: Read Input CSV

Read the channels CSV. Expected columns:

- `channel_name` (required)
- `email` (required)
- `subscribers` (optional)
- `description` (optional)
- `channel_url` (optional, needed for enrichment)
- `keyword` (optional)

Skip rows with no email. Report how many channels were loaded.

### Step 4: Ask About Enrichment

Use AskUserQuestion to ask:

**Question:** "Want to enrich channel data by scraping YouTube pages before personalizing? This makes emails much more specific by referencing recent videos and about page details."

**Options:**

1. "Yes, enrich with Bright Data MCP" - Scrapes each channel's YouTube page for recent video titles, about info, and niche signals. Requires Bright Data MCP to be installed.
2. "No, use CSV data as-is" - Personalizes based only on the data already in your CSV (channel name, description, keyword, subscribers).

### Step 5: Enrich (if selected)

For each channel that has a `channel_url`:

1. Use `mcp__brightdata__scrape_as_markdown` to scrape the channel URL
2. From the scraped content, extract:
   - **Recent video titles** (last 3-5 visible on the page)
   - **About page text** or channel description
   - **Any niche signals** (topics, recurring themes)
3. Add the enriched data to the channel's context for personalization

If Bright Data MCP is not available or a scrape fails, fall back gracefully to CSV data only for that channel. Don't stop the whole batch.

### Step 6: Personalize Each Email

For each channel, write a personalized cold outreach email. Use all available context (CSV data + enrichment if available).

**Email guidelines:**

- **Subject line**: Short (under 60 chars), specific to their channel. Not clickbait. Examples: "Quick question about your tech tutorials", "Sponsorship idea for your Facebook ads content"
- **Opening line**: A specific, genuine compliment about their content. Reference something real — a video topic, their teaching style, their niche expertise. NOT generic ("I love your content").
- **Who you are**: One sentence. Name, what you built, URL.
- **Why it's relevant**: One sentence connecting your product to THEIR audience specifically.
- **CTA**: Use the CTA from config. Keep it as a question, not a demand.
- **Sign-off**: "Best," + sender name

**Rules:**

- Under 100 words total
- No fluff ("I hope this email finds you well", "I'm reaching out because...")
- Sound like a real person, not a template
- Each email must be genuinely different — don't just swap the channel name
- If enrichment data is available, reference specific recent video titles or about page details
- If only CSV data is available, work with description and keyword to make it specific

**Output format for each email:** Generate a subject line and body text.

### Step 7: Write Output CSV

Write the output CSV with these exact columns (matching the Apps Script format):

```
channel_name,email,subscribers,subject,body,status
```

- `channel_name`: From input CSV
- `email`: From input CSV
- `subscribers`: From input CSV
- `subject`: Generated subject line
- `body`: Generated email body (use proper CSV quoting for multi-line text)
- `status`: Leave empty (Apps Script fills this in when sending)

Save as `outreach.csv` in the current directory. If the file already exists, ask the user before overwriting.

### Step 8: Summary

Print a summary:

- Number of emails generated
- Number enriched vs. CSV-only (if enrichment was used)
- Output file path
- Next steps:
  1. Review the emails in `outreach.csv`
  2. Create a Google Sheet and import the CSV (File > Import)
  3. Set up Apps Script (see `apps_script.gs` in this repo)
  4. Send a test email, then start the drip campaign

## Important Notes

- This skill runs entirely within Claude Code — no API keys, no Python dependencies, no external scripts needed.
- Claude (you) ARE the personalization engine. You read the data and write each email directly.
- The Bright Data MCP enrichment is optional but significantly improves email quality.
- Always generate proper CSV with correct quoting (bodies contain newlines and commas).
- Never include real personal data in sample files — use fictional channels only.
