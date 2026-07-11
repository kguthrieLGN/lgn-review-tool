import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))
from generate_review import handle_generate_request  # noqa: E402
from send_thank_you import handle_send_thank_you_request  # noqa: E402

PORT = 5174

ROUTES = {
    "/api/generate_review": handle_generate_request,
    "/api/send_thank_you": handle_send_thank_you_request,
}


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
        route = ROUTES.get(self.path)
        if not route:
            self._send_json(404, {"error": "not_found"})
            return

        length = int(self.headers.get("Content-Length", 0) or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid_json", "message": "Invalid JSON body."})
            return

        status, response = route(payload)
        self._send_json(status, response)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    print(f"Local dev backend listening on http://localhost:{PORT}")
    print("Routes: " + ", ".join(ROUTES.keys()))
    print("Same logic that runs as Vercel functions in production — see api/*.py")
    ThreadingHTTPServer(("localhost", PORT), Handler).serve_forever()
