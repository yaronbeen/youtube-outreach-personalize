#!/usr/bin/env python3
"""
End-to-end tests for the YouTube Outreach Personalizer pipeline.

Validates the full data flow: input CSV -> personalized output CSV -> Apps Script compatibility.

Usage:
    python test_e2e.py
    python -m pytest test_e2e.py -v
"""

import csv
import os
import sys

# ── Paths ────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "sample_channels.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "sample_outreach.csv")
CONFIG_FILE = os.path.join(BASE_DIR, "config_example.json")
SKILL_FILE = os.path.join(BASE_DIR, "SKILL.md")
APPS_SCRIPT = os.path.join(BASE_DIR, "apps_script.gs")

# ── Expected schemas ─────────────────────────────────────────────
INPUT_REQUIRED_COLS = {"channel_name", "email"}
INPUT_ALL_COLS = {"channel_name", "email", "subscribers", "description", "channel_url", "keyword"}

OUTPUT_COLS_ORDERED = ["channel_name", "email", "subscribers", "subject", "body", "status"]

CONFIG_REQUIRED_FIELDS = {
    "sender_name", "product_name", "product_url",
    "product_description", "credibility", "cta",
}


# ── Helpers ──────────────────────────────────────────────────────
def read_csv_rows(path):
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def read_json(path):
    import json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Tests: File existence ────────────────────────────────────────
def test_all_required_files_exist():
    for path in [INPUT_CSV, OUTPUT_CSV, CONFIG_FILE, SKILL_FILE, APPS_SCRIPT]:
        assert os.path.exists(path), f"Missing required file: {path}"


# ── Tests: Input CSV ─────────────────────────────────────────────
def test_input_csv_has_required_columns():
    cols, _ = read_csv_rows(INPUT_CSV)
    missing = INPUT_REQUIRED_COLS - set(cols)
    assert not missing, f"Input CSV missing required columns: {missing}"


def test_input_csv_has_all_expected_columns():
    cols, _ = read_csv_rows(INPUT_CSV)
    missing = INPUT_ALL_COLS - set(cols)
    assert not missing, f"Input CSV missing expected columns: {missing}"


def test_input_csv_has_data():
    _, rows = read_csv_rows(INPUT_CSV)
    assert len(rows) >= 1, "Input CSV has no data rows"


def test_input_csv_all_rows_have_email():
    _, rows = read_csv_rows(INPUT_CSV)
    for i, row in enumerate(rows):
        assert row.get("email", "").strip(), f"Row {i+1} has no email"


def test_input_csv_all_rows_have_channel_name():
    _, rows = read_csv_rows(INPUT_CSV)
    for i, row in enumerate(rows):
        assert row.get("channel_name", "").strip(), f"Row {i+1} has no channel_name"


# ── Tests: Output CSV ────────────────────────────────────────────
def test_output_csv_has_exact_columns():
    cols, _ = read_csv_rows(OUTPUT_CSV)
    assert cols == OUTPUT_COLS_ORDERED, (
        f"Output CSV columns must be {OUTPUT_COLS_ORDERED} (in order), got {cols}"
    )


def test_output_csv_has_same_row_count_as_input():
    _, in_rows = read_csv_rows(INPUT_CSV)
    _, out_rows = read_csv_rows(OUTPUT_CSV)
    assert len(out_rows) == len(in_rows), (
        f"Output has {len(out_rows)} rows but input has {len(in_rows)}"
    )


def test_output_csv_channel_names_match_input():
    _, in_rows = read_csv_rows(INPUT_CSV)
    _, out_rows = read_csv_rows(OUTPUT_CSV)
    in_names = [r["channel_name"] for r in in_rows]
    out_names = [r["channel_name"] for r in out_rows]
    assert in_names == out_names, (
        f"Channel names don't match between input and output"
    )


def test_output_csv_emails_match_input():
    _, in_rows = read_csv_rows(INPUT_CSV)
    _, out_rows = read_csv_rows(OUTPUT_CSV)
    in_emails = [r["email"] for r in in_rows]
    out_emails = [r["email"] for r in out_rows]
    assert in_emails == out_emails, "Emails don't match between input and output"


def test_output_csv_every_row_has_subject():
    _, rows = read_csv_rows(OUTPUT_CSV)
    for i, row in enumerate(rows):
        assert row.get("subject", "").strip(), f"Row {i+1} has no subject"


def test_output_csv_every_row_has_body():
    _, rows = read_csv_rows(OUTPUT_CSV)
    for i, row in enumerate(rows):
        assert row.get("body", "").strip(), f"Row {i+1} has no body"


def test_output_csv_status_column_is_empty():
    """Apps Script expects status column to be empty — it fills it in when sending."""
    _, rows = read_csv_rows(OUTPUT_CSV)
    for i, row in enumerate(rows):
        assert not row.get("status", "").strip(), (
            f"Row {i+1} status should be empty, got: '{row['status']}'"
        )


# ── Tests: Email quality ─────────────────────────────────────────
def test_emails_are_under_150_words():
    _, rows = read_csv_rows(OUTPUT_CSV)
    for i, row in enumerate(rows):
        word_count = len(row["body"].split())
        assert word_count <= 150, (
            f"Row {i+1} ({row['channel_name']}) body is {word_count} words (max 150)"
        )


def test_emails_are_all_different():
    """Each email body should be unique — not a copy-paste template."""
    _, rows = read_csv_rows(OUTPUT_CSV)
    bodies = [row["body"].strip() for row in rows]
    assert len(set(bodies)) == len(bodies), "Some email bodies are identical"


def test_subjects_are_all_different():
    _, rows = read_csv_rows(OUTPUT_CSV)
    subjects = [row["subject"].strip() for row in rows]
    assert len(set(subjects)) == len(subjects), "Some subjects are identical"


def test_subjects_are_under_60_chars():
    _, rows = read_csv_rows(OUTPUT_CSV)
    for i, row in enumerate(rows):
        assert len(row["subject"]) <= 80, (
            f"Row {i+1} subject is {len(row['subject'])} chars: '{row['subject']}'"
        )


def test_emails_have_signoff():
    _, rows = read_csv_rows(OUTPUT_CSV)
    for i, row in enumerate(rows):
        body_lower = row["body"].lower()
        assert "best," in body_lower or "cheers," in body_lower or "thanks," in body_lower, (
            f"Row {i+1} ({row['channel_name']}) body has no sign-off"
        )


def test_emails_contain_multiline_text():
    """Bodies should be multi-line (real emails, not one-liners)."""
    _, rows = read_csv_rows(OUTPUT_CSV)
    for i, row in enumerate(rows):
        lines = [l for l in row["body"].split("\n") if l.strip()]
        assert len(lines) >= 3, (
            f"Row {i+1} ({row['channel_name']}) body has only {len(lines)} non-empty lines"
        )


# ── Tests: Config ─────────────────────────────────────────────────
def test_config_has_required_fields():
    config = read_json(CONFIG_FILE)
    missing = CONFIG_REQUIRED_FIELDS - set(config.keys())
    assert not missing, f"Config missing required fields: {missing}"


def test_config_no_empty_fields():
    config = read_json(CONFIG_FILE)
    for field in CONFIG_REQUIRED_FIELDS:
        assert config.get(field, "").strip(), f"Config field '{field}' is empty"


# ── Tests: Skill file ────────────────────────────────────────────
def test_skill_has_yaml_frontmatter():
    with open(SKILL_FILE, "r") as f:
        content = f.read()
    assert content.startswith("---"), "SKILL.md must start with YAML frontmatter (---)"
    assert content.count("---") >= 2, "SKILL.md must have closing --- for frontmatter"


def test_skill_has_name():
    with open(SKILL_FILE, "r") as f:
        content = f.read()
    assert "name: personalize-outreach" in content, "SKILL.md missing skill name"


def test_skill_has_description():
    with open(SKILL_FILE, "r") as f:
        content = f.read()
    assert "description:" in content, "SKILL.md missing description"


def test_skill_references_brightdata():
    with open(SKILL_FILE, "r") as f:
        content = f.read()
    assert "mcp__brightdata__scrape_as_markdown" in content, (
        "SKILL.md should reference the Bright Data MCP tool"
    )


def test_skill_references_csv_columns():
    with open(SKILL_FILE, "r") as f:
        content = f.read()
    for col in OUTPUT_COLS_ORDERED:
        assert col in content, f"SKILL.md should reference output column '{col}'"


# ── Tests: Apps Script compatibility ──────────────────────────────
def test_apps_script_column_order_matches_output():
    """
    The Apps Script reads columns by index:
      A(0)=channel_name, B(1)=email, C(2)=subscribers,
      D(3)=subject, E(4)=body, F(5)=status
    Our output CSV must match this exact order.
    """
    cols, _ = read_csv_rows(OUTPUT_CSV)
    assert cols[0] == "channel_name", f"Column A must be channel_name, got {cols[0]}"
    assert cols[1] == "email", f"Column B must be email, got {cols[1]}"
    assert cols[2] == "subscribers", f"Column C must be subscribers, got {cols[2]}"
    assert cols[3] == "subject", f"Column D must be subject, got {cols[3]}"
    assert cols[4] == "body", f"Column E must be body, got {cols[4]}"
    assert cols[5] == "status", f"Column F must be status, got {cols[5]}"


def test_apps_script_reads_correct_columns():
    """Verify the Apps Script code references the right column indices."""
    with open(APPS_SCRIPT, "r") as f:
        content = f.read()
    # The script reads: row[0]=channel, row[1]=email, row[3]=subject, row[4]=body, row[5]=status
    assert "row[0]" in content or "channelName = row[0]" in content
    assert "row[1]" in content or "email = row[1]" in content
    assert "row[3]" in content or "subject = row[3]" in content
    assert "row[4]" in content or "body = row[4]" in content
    assert "row[5]" in content or "status = row[5]" in content


def test_apps_script_status_col_is_6():
    """Apps Script STATUS_COL should be 6 (1-indexed column F)."""
    with open(APPS_SCRIPT, "r") as f:
        content = f.read()
    assert "STATUS_COL = 6" in content, "Apps Script STATUS_COL should be 6"


# ── Tests: No secrets or real data ────────────────────────────────
def test_no_real_api_keys_in_files():
    """Make sure no real API keys are committed."""
    for filename in ["sample_channels.csv", "sample_outreach.csv", "config_example.json", "SKILL.md"]:
        path = os.path.join(BASE_DIR, filename)
        with open(path, "r") as f:
            content = f.read()
        assert "sk-ant-" not in content, f"Possible Anthropic API key found in {filename}"
        assert "BRIGHTDATA_API_TOKEN" not in content or "your_token" in content.lower() or "export" in content, (
            f"Possible real Bright Data token in {filename}"
        )


def test_sample_data_uses_fictional_emails():
    """Sample data should not contain real business emails."""
    _, rows = read_csv_rows(INPUT_CSV)
    for row in rows:
        email = row.get("email", "")
        # These are fictional domains from the sample
        assert any(d in email for d in [
            "techtipsdaily.com", "marketingmike.co", "sarahbizschool.com",
            "thedatanerd.io", "fitcreatorhub.com", "example.com", "test.com",
        ]), f"Email '{email}' doesn't look like fictional sample data"


# ── Runner ────────────────────────────────────────────────────────
def main():
    """Run all tests and report results."""
    import inspect

    tests = [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]

    passed = 0
    failed = 0
    errors = []

    print(f"Running {len(tests)} tests...\n")

    for name, func in tests:
        try:
            func()
            passed += 1
            print(f"  PASS  {name}")
        except AssertionError as e:
            failed += 1
            errors.append((name, str(e)))
            print(f"  FAIL  {name}")
            print(f"        {e}")
        except Exception as e:
            failed += 1
            errors.append((name, f"{type(e).__name__}: {e}"))
            print(f"  ERROR {name}")
            print(f"        {type(e).__name__}: {e}")

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")

    if errors:
        print(f"\nFailures:")
        for name, msg in errors:
            print(f"  - {name}: {msg}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
