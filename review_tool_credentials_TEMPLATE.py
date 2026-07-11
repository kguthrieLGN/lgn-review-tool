# =============================================================================
# LGN Review Generator — Private Credentials TEMPLATE
# =============================================================================
# This is a template showing the format of review_tool_credentials.py.
# It is safe to store in SharePoint (contains no real values).
#
# HOW TO USE THIS FILE:
# 1. Copy this file into the SAME local-only folder you already use for
#    db_credentials.py (the one LGN_CREDENTIALS_PATH points to).
# 2. Rename your copy to review_tool_credentials.py.
# 3. Fill in your real Anthropic (Claude) API key below.
# 4. Never save the real file back into a SharePoint-synced folder.
#
# This reuses the same LGN_CREDENTIALS_PATH environment variable as
# db_credentials.py — no new setup needed if you've already configured that.
# =============================================================================

# --- Anthropic (Claude) API key ---
# Used to generate review drafts from the client's chat answers.
# Get one at https://console.anthropic.com/ (Stewart/Kathryn: this is billed
# per API call, not a flat subscription — keep an eye on usage while testing).
ANTHROPIC_API_KEY = "REPLACE — your Claude API key"

# --- Resend API key ---
# Used to send a thank-you email when a client leaves their name/email.
# Get one at https://resend.com/ (free tier: 3,000 emails/month, 100/day).
# Only needed if you want the thank-you email feature to actually send —
# without it, the app just silently skips sending (never blocks the client).
RESEND_API_KEY = "REPLACE — your Resend API key"
