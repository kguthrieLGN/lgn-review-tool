import json
import os
import sys
import urllib.error
import urllib.request

QUESTIONS = [
    {
        "id": "goal",
        "text": "What did you come to The Liberty Group of Nevada for — buying a business, "
        "selling a business, a valuation, or something else?",
    },
    {"id": "team", "text": "Which team member(s) did you primarily work with?"},
    {"id": "standout", "text": "What stood out most about working with them or the process?"},
    {
        "id": "surprise",
        "text": "Was there anything that surprised you along the way — good or challenging?",
    },
    {"id": "outcome", "text": "How did things turn out, and how do you feel about it?"},
    {
        "id": "recommend",
        "text": "Would you recommend The Liberty Group of Nevada to someone else buying or "
        "selling a business? Why or why not?",
    },
    {"id": "more", "text": "Anything else you'd like to add?"},
]

PLATFORM_NAMES = {"google": "Google", "facebook": "Facebook", "bbb": "BBB"}


def find_local_credentials_path():
    """Local-dev-only lookup — same convention as db_config.py. Not used on Vercel,
    where ANTHROPIC_API_KEY is set directly as a platform environment variable."""
    env_path = os.environ.get("LGN_CREDENTIALS_PATH", "").strip()
    if env_path and os.path.isfile(os.path.join(env_path, "review_tool_credentials.py")):
        return env_path

    fallbacks = [
        r"C:\Users\sguthrie\Claude Search",
        r"C:\Users\kathryn\LGN_Local",
        r"C:\Users\kguthrie\LGN_Local",
        r"C:\Users\kathrynguthrie\LGN_Local",
        r"C:\Users\kelly\LGN_Local",
        r"C:\Users\kbrandon\LGN_Local",
        os.path.expanduser("~/LGN_Local"),
    ]
    for path in fallbacks:
        if os.path.isfile(os.path.join(path, "review_tool_credentials.py")):
            return path

    return None


def load_api_key():
    # Production (Vercel): the key is set directly as a project environment variable —
    # no local file involved.
    env_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if env_key:
        return env_key

    # Local dev fallback: same local-only credentials file used by other LGN tooling.
    path = find_local_credentials_path()
    if not path:
        return None
    if path not in sys.path:
        sys.path.insert(0, path)
    try:
        from review_tool_credentials import ANTHROPIC_API_KEY

        return ANTHROPIC_API_KEY
    except ImportError:
        return None


def build_prompt(answers, platform_key, prior_drafts):
    platform_name = PLATFORM_NAMES[platform_key]

    qa_lines = []
    for q in QUESTIONS:
        answer = (answers.get(q["id"]) or "").strip()
        if answer:
            qa_lines.append(f"Q: {q['text']}\nA: {answer}")
    qa_block = "\n\n".join(qa_lines)

    prior_block = ""
    if prior_drafts:
        joined = "\n\n---\n\n".join(prior_drafts)
        prior_block = (
            "\n\nThe client already posted the following review text on another site. Write "
            "distinctly different wording this time — vary sentence structure and word choice "
            "— while keeping every fact identical to what's below and to the Q&A above. Do not "
            f"introduce new facts.\n\nPrevious version(s):\n{joined}\n"
        )

    return (
        "You are drafting an online business review in the voice of a real customer, based "
        "only on their own answers below. Write in first person, past tense, as if the "
        f"customer is posting this on {platform_name}.\n\n"
        "Rules:\n"
        "- Use only the facts and details mentioned in the answers below. Never invent names, "
        "dollar amounts, timelines, or details that weren't stated.\n"
        "- Do not use superlative marketing language (e.g. \"exceeded all expectations!!!\"). "
        "Keep it natural, like something a real person would write.\n"
        "- Aim for roughly 60-120 words.\n"
        "- If the answers describe a mixed or negative experience, reflect that honestly — do "
        "not steer the tone more positive than what the customer actually said.\n"
        "- Output only the review text itself: no preamble, no quotation marks, no signature.\n"
        f"\nCustomer's answers:\n{qa_block}"
        f"{prior_block}"
    )


def call_claude(prompt, api_key):
    body = json.dumps(
        {
            "model": "claude-sonnet-5",
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["content"][0]["text"].strip()


def handle_generate_request(payload):
    """Shared request handling: validate, build prompt, call Claude.
    Returns (status_code, response_dict)."""
    answers = payload.get("answers", {})
    platform_key = payload.get("platform")
    prior_drafts = payload.get("priorDrafts", [])

    if platform_key not in PLATFORM_NAMES:
        return 400, {"error": "bad_platform", "message": "Unknown platform."}

    api_key = load_api_key()
    if not api_key or api_key.startswith("REPLACE"):
        return 500, {
            "error": "credentials_missing",
            "message": (
                "ANTHROPIC_API_KEY is not configured. Locally: save review_tool_credentials.py "
                "in your LGN credentials folder. On Vercel: set ANTHROPIC_API_KEY in the "
                "project's Environment Variables."
            ),
        }

    prompt = build_prompt(answers, platform_key, prior_drafts)

    try:
        review_text = call_claude(prompt, api_key)
    except urllib.error.HTTPError as err:
        return 502, {
            "error": "claude_api_error",
            "message": f"Claude API returned {err.code}: {err.reason}",
        }
    except Exception as err:  # network errors, timeouts, malformed responses
        return 502, {"error": "claude_api_error", "message": str(err)}

    return 200, {"review": review_text}
