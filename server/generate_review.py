import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))
from generate_review import handle_generate_request  # noqa: E402

PORT = 5174


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path != "/api/generate_review":
            self._send_json(404, {"error": "not_found"})
            return

        length = int(self.headers.get("Content-Length", 0) or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid_json", "message": "Invalid JSON body."})
            return

        status, response = handle_generate_request(payload)
        self._send_json(status, response)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    print(f"Review generation backend (local dev) listening on http://localhost:{PORT}")
    print("This is the same logic that runs as a Vercel function in production — see api/generate_review.py")
    ThreadingHTTPServer(("localhost", PORT), Handler).serve_forever()
