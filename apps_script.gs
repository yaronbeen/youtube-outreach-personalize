/**
 * YouTube Outreach Email Sender (Drip Mode)
 *
 * Sends ONE email at a time with random delays between sends.
 * Runs entirely in the background on Google's servers - close your tab, close your laptop.
 *
 * SETUP:
 * 1. Create a Google Sheet and paste your outreach CSV data into it
 * 2. Go to Extensions > Apps Script
 * 3. Delete everything in the editor and paste this entire script
 * 4. Click Save (floppy disk icon)
 * 5. Go back to your spreadsheet - you'll see a new "Outreach" menu
 * 6. Click Outreach > Send Test Email (check your inbox first!)
 * 7. Click Outreach > Start Drip Campaign
 * 8. Close the tab. It runs on Google's servers.
 *
 * SHEET FORMAT (columns A-F):
 *   A: channel_name
 *   B: email
 *   C: subscribers
 *   D: subject
 *   E: body
 *   F: status (leave empty - script fills this in)
 *
 * The first row should be headers. Data starts from row 2.
 */

// ── CONFIG (customize these) ─────────────────────────────────
const SENDER_NAME = "Your Name";       // <-- Change to your name
const MIN_DELAY_MINUTES = 10;          // Minimum wait between emails
const MAX_DELAY_MINUTES = 30;          // Maximum wait between emails
const SHEET_NAME = "Sheet1";           // Name of the sheet tab
const STATUS_COL = 6;                  // Column F = status
// ─────────────────────────────────────────────────────────────

function onOpen() {
  SpreadsheetApp.getUi().createMenu("Outreach")
    .addItem("Start Drip Campaign", "startDrip")
    .addItem("Stop Drip Campaign", "stopDrip")
    .addItem("Send Test Email to Myself", "sendTestEmail")
    .addSeparator()
    .addItem("Campaign Status", "campaignStatus")
    .addItem("Reset All Statuses", "resetStatuses")
    .addItem("Check Gmail Daily Quota", "checkQuota")
    .addToUi();
}

/**
 * Convert plain text body to HTML (preserves line breaks, linkifies URLs)
 */
function toHtml(body) {
  return body.toString()
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>")
    .replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1">$1</a>');
}

/**
 * Send ONE pending email, then schedule the next one
 */
function sendNextEmail() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  if (!sheet) return;

  var data = sheet.getDataRange().getValues();

  // Find next unsent row (skip header row 0)
  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    var channelName = row[0];
    var email = row[1];
    var subject = row[3];
    var body = row[4];
    var status = row[5];

    // Skip rows that already have a status
    if (status && status.toString().trim() !== "") continue;

    // Skip empty email or body
    if (!email || email.toString().trim() === "") {
      sheet.getRange(i + 1, STATUS_COL).setValue("SKIP - no email");
      continue;
    }
    if (!body || body.toString().trim() === "") {
      sheet.getRange(i + 1, STATUS_COL).setValue("SKIP - no body");
      continue;
    }

    // Send this email
    try {
      GmailApp.sendEmail(email.toString().trim(), subject, body, {
        name: SENDER_NAME,
        htmlBody: toHtml(body)
      });

      var timestamp = new Date().toLocaleString();
      sheet.getRange(i + 1, STATUS_COL).setValue("SENT - " + timestamp);
      Logger.log("Sent to: " + channelName + " (" + email + ") at " + timestamp);

      // Schedule next email with random delay
      scheduleNext();
      return;

    } catch (e) {
      sheet.getRange(i + 1, STATUS_COL).setValue("ERROR: " + e.message);
      Logger.log("Error: " + email + " - " + e.message);
      scheduleNext();
      return;
    }
  }

  // All emails sent
  clearTriggers();
  Logger.log("All emails sent! Campaign complete.");
}

/**
 * Schedule the next email with a random delay
 */
function scheduleNext() {
  clearTriggers();
  var delayMinutes = MIN_DELAY_MINUTES + Math.floor(Math.random() * (MAX_DELAY_MINUTES - MIN_DELAY_MINUTES));
  ScriptApp.newTrigger("sendNextEmail")
    .timeBased()
    .after(delayMinutes * 60 * 1000)
    .create();
  Logger.log("Next email scheduled in " + delayMinutes + " minutes");
}

/**
 * Clear all sendNextEmail triggers
 */
function clearTriggers() {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === "sendNextEmail") {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }
}

/**
 * START the drip campaign
 */
function startDrip() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  var data = sheet.getDataRange().getValues();

  var pending = 0;
  for (var i = 1; i < data.length; i++) {
    var status = data[i][5];
    if (!status || status.toString().trim() === "") pending++;
  }

  if (pending === 0) {
    SpreadsheetApp.getUi().alert("No pending emails to send. All rows have a status.");
    return;
  }

  var ui = SpreadsheetApp.getUi();
  var response = ui.alert(
    "Start Drip Campaign",
    pending + " emails will be sent with " + MIN_DELAY_MINUTES + "-" + MAX_DELAY_MINUTES +
    " minute random delays between each.\n\n" +
    "Estimated time: " + Math.round(pending * (MIN_DELAY_MINUTES + MAX_DELAY_MINUTES) / 2 / 60) +
    " hours.\n\n" +
    "You can close this tab - it runs in the background.\n\nStart?",
    ui.ButtonSet.YES_NO
  );

  if (response !== ui.Button.YES) return;

  sendNextEmail();

  ui.alert("Campaign started! First email sent.\n\nThe rest will drip out automatically. You can close this tab.");
}

/**
 * STOP the drip campaign
 */
function stopDrip() {
  clearTriggers();
  SpreadsheetApp.getUi().alert("Drip campaign stopped.\n\nAlready-sent emails are not affected. Use 'Start Drip Campaign' to resume from where it left off.");
}

/**
 * Show campaign progress
 */
function campaignStatus() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  var data = sheet.getDataRange().getValues();

  var sent = 0, pending = 0, errors = 0, skipped = 0;
  for (var i = 1; i < data.length; i++) {
    var status = (data[i][5] || "").toString().trim();
    if (status === "") pending++;
    else if (status.startsWith("SENT")) sent++;
    else if (status.startsWith("ERROR")) errors++;
    else skipped++;
  }

  var triggers = ScriptApp.getProjectTriggers();
  var active = false;
  for (var j = 0; j < triggers.length; j++) {
    if (triggers[j].getHandlerFunction() === "sendNextEmail") active = true;
  }

  SpreadsheetApp.getUi().alert(
    "Campaign Status\n\n" +
    "Sent: " + sent + "\n" +
    "Pending: " + pending + "\n" +
    "Errors: " + errors + "\n" +
    "Skipped: " + skipped + "\n\n" +
    "Campaign active: " + (active ? "YES - next email is scheduled" : "NO - stopped or complete")
  );
}

/**
 * Send a test email to yourself (uses first data row)
 */
function sendTestEmail() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  var data = sheet.getDataRange().getValues();

  if (data.length < 2) {
    SpreadsheetApp.getUi().alert("No data found. Add at least one row of data below the header.");
    return;
  }

  var row = data[1];
  var subject = "[TEST] " + row[3];
  var body = row[4];
  var myEmail = Session.getActiveUser().getEmail();

  GmailApp.sendEmail(myEmail, subject, body, {
    name: SENDER_NAME,
    htmlBody: toHtml(body)
  });

  SpreadsheetApp.getUi().alert("Test email sent to " + myEmail + "\n\nCheck your inbox.");
}

/**
 * Reset all statuses (allows re-sending)
 */
function resetStatuses() {
  var ui = SpreadsheetApp.getUi();
  var response = ui.alert("Reset All Statuses",
    "This clears all statuses, allowing re-sending.\n\nAre you sure?",
    ui.ButtonSet.YES_NO);

  if (response !== ui.Button.YES) return;

  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  var lastRow = sheet.getLastRow();
  if (lastRow > 1) {
    sheet.getRange(2, STATUS_COL, lastRow - 1, 1).clearContent();
    ui.alert("All statuses cleared.");
  }
}

/**
 * Check remaining Gmail daily quota
 */
function checkQuota() {
  var remaining = MailApp.getRemainingDailyQuota();
  SpreadsheetApp.getUi().alert(
    "Gmail Daily Quota\n\n" +
    "Emails remaining today: " + remaining + "\n\n" +
    "Free Gmail: 100/day\n" +
    "Google Workspace: 1,500/day"
  );
}
