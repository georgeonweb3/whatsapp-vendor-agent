"""Webhook server for Meta WhatsApp Business API.
Stdlib only: http.server
Run: python3 server.py [port]   default 8000
Endpoints:
  GET  /health  -> {"status":"ok", ...}
  GET  /webhook?hub.mode=subscribe&hub.verify_token=...&hub.challenge=... -> verification
  POST /webhook -> Meta format messages, returns 200 and logs reply (in real deploy, reply is sent via Graph API - here we return reply in JSON for testing and log it)
Env:
  WHATSAPP_VERIFY_TOKEN (default: adaeze-verify-token for demo)
No credentials required for demo / local testing.
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from engine import VendorAgent

VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "adaeze-verify-token")
agent = VendorAgent()

def extract_messages(payload):
    """Extract (from_number, text) from Meta webhook payload. Returns list."""
    results = []
    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    sender = msg.get("from", "")
                    mtype = msg.get("type", "")
                    text = ""
                    if mtype == "text":
                        text = msg.get("text", {}).get("body", "")
                    results.append((sender, text, msg))
    except Exception:
        pass
    return results

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            body = json.dumps({"status": "ok", "vendor": agent.vendor.get("name"), "products": len(agent.products)}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path in ("/webhook", "/"):
            qs = parse_qs(parsed.query)
            mode = qs.get("hub.mode", [""])[0]
            token = qs.get("hub.verify_token", [""])[0]
            challenge = qs.get("hub.challenge", [""])[0]
            if mode == "subscribe" and token == VERIFY_TOKEN:
                body = challenge.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            else:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Forbidden")
                return
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            payload = {}
        messages = extract_messages(payload)
        replies = []
        for sender, text, _msg in messages:
            if text:
                reply = agent.respond(text)
                replies.append({"to": sender, "text": reply})
                print(f"[WhatsApp] {sender}: {text} -> {reply[:120]}...")
            else:
                replies.append({"to": sender, "text": "Sorry, I only handle text messages for now."})
        body = json.dumps({"status": "received", "replies": replies}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        sys.stderr.write("%s - - [%s] %s\n" % (self.client_address[0], self.log_date_time_string(), format % args))

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", "8000"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"WhatsApp Vendor Agent server listening on port {port}")
    print(f"Health: http://localhost:{port}/health")
    print(f"Verify token: {VERIFY_TOKEN}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()
