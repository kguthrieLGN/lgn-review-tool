import json
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler


def find_local_credentials_path():
    """Local-dev-only lookup, same convention as db_config.py. Not used on Vercel,
    where RESEND_API_KEY is set directly as a platform environment variable."""
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


def load_resend_api_key():
    env_key = os.environ.get("RESEND_API_KEY", "").strip()
    if env_key:
        return env_key

    path = find_local_credentials_path()
    if not path:
        return None
    if path not in sys.path:
        sys.path.insert(0, path)
    try:
        from review_tool_credentials import RESEND_API_KEY

        return RESEND_API_KEY
    except ImportError:
        return None


def send_thank_you_email(to_email, to_name, api_key):
    display_name = to_name if to_name else "there"
    text_body = (
        f"Hi {display_name},\n\n"
        "Thank you for taking the time to share your experience with The Liberty Group "
        "of Nevada. We read every piece of feedback we receive, and yours is appreciated.\n\n"
        "If anything comes up in the meantime, feel free to reach out.\n\n"
        "Best Regards,\n"
        "The Liberty Group of Nevada\n"
    )

    body = json.dumps(
        {
            "from": "The Liberty Group of Nevada <onboarding@resend.dev>",
            "to": [to_email],
            "subject": "Thank you for your feedback",
            "text": text_body,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def handle_send_thank_you_request(payload):
    """Shared request handling. Returns (status_code, response_dict).
    Always returns 200 with sent=false on any failure — this is a nice-to-have side
    effect and must never be treated as a hard error by the caller."""
    email = (payload.get("email") or "").strip()
    name = (payload.get("name") or "").strip()

    if not email:
        return 400, {"error": "missing_email", "message": "Email is required."}

    api_key = load_resend_api_key()
    if not api_key or api_key.startswith("REPLACE"):
        print("RESEND_API_KEY not configured; skipping thank-you email.")
        return 200, {"sent": False, "reason": "email_not_configured"}

    if any(ch in api_key for ch in ("\n", "\r", '"', "'")):
        print("RESEND_API_KEY appears malformed; skipping thank-you email.")
        return 200, {"sent": False, "reason": "credentials_malformed"}

    try:
        send_thank_you_email(email, name, api_key)
    except urllib.error.HTTPError as err:
        print(f"send_thank_you_email HTTP error: {err.code} {err.reason}")
        return 200, {"sent": False, "reason": "send_failed"}
    except Exception as err:
        print(f"send_thank_you_email failed: {err!r}")
        return 200, {"sent": False, "reason": "send_failed"}

    return 200, {"sent": True}


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid_json", "message": "Invalid JSON body."})
            return

        status, response = handle_send_thank_you_request(payload)
        self._send_json(status, response)

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass
