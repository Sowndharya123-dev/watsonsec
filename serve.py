"""
Security Champion Dashboard — Python proxy server
Serves the dashboard on http://localhost:3000 and proxies
all /api/* calls to Anthropic Claude / IAM / ICA to bypass browser CORS.

Set your Anthropic API key before starting:
  Windows:  $env:ANTHROPIC_API_KEY = "sk-ant-..."
  Mac/Linux: export ANTHROPIC_API_KEY=sk-ant-...

Or create a .env file in the project root:
  ANTHROPIC_API_KEY=sk-ant-...
"""
import http.server, urllib.request, urllib.parse, json, os, sys

# ── Load .env file if present ────────────────────────────────────────────────
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                if _k.strip() not in os.environ:
                    os.environ[_k.strip()] = _v.strip()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL   = "claude-sonnet-4-5"
ANTHROPIC_URL     = "https://api.anthropic.com/v1/messages"

PORT = 3000
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "public")

# ── Known ICA REMEA API endpoint patterns to try in order ──────────────────
# These are attempted sequentially; the first 2xx wins.
# Add or reorder based on DevTools network-tab discovery.
ICA_ENDPOINT_CANDIDATES = [
    "https://remea.ica.ibm.com/ica/api/v1/assistants/{agent_id}/chat",
    "https://remea.ica.ibm.com/api/v1/assistants/{agent_id}/chat",
    "https://remea.ica.ibm.com/ica/curatorai/api/v1/assistants/{agent_id}/chat",
    "https://remea.ica.ibm.com/api/assistants/{agent_id}/message",
]

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=PUBLIC_DIR, **kw)

    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} — {fmt % args}")

    # ── Add CORS headers to every response ──────────────
    def add_cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers",
                         "Content-Type, Authorization, X-Agent-Id, X-ICA-Base, X-ICA-Url")

    def do_OPTIONS(self):
        self.send_response(200)
        self.add_cors()
        self.end_headers()

    def do_POST(self):
        # ── /api/chat  →  Anthropic Claude claude-sonnet-4-5 Sonnet ─────────────────
        if self.path == "/api/chat":
            if not ANTHROPIC_API_KEY:
                msg = json.dumps({"error": "AI not configured — set ANTHROPIC_API_KEY"}).encode()
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(msg)))
                self.add_cors()
                self.end_headers()
                self.wfile.write(msg)
                return

            length = int(self.headers.get("Content-Length", 0))
            body   = json.loads(self.rfile.read(length) or b"{}")

            all_messages = body.get("messages", [])
            system_msg   = next((m["content"] for m in all_messages if m["role"] == "system"), "")
            chat_msgs    = [m for m in all_messages if m["role"] != "system"]

            payload = json.dumps({
                "model":      ANTHROPIC_MODEL,
                "max_tokens": 1024,
                "system":     system_msg,
                "messages":   chat_msgs,
            }).encode()

            req = urllib.request.Request(
                ANTHROPIC_URL,
                data=payload,
                headers={
                    "Content-Type":      "application/json",
                    "x-api-key":         ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                },
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data   = json.loads(resp.read())
                    text   = (data.get("content") or [{}])[0].get("text", "")
                    result = json.dumps({"choices": [{"message": {"content": text}}]}).encode()
                    self.send_response(200)
                    self.send_header("Content-Type",   "application/json")
                    self.send_header("Content-Length", str(len(result)))
                    self.add_cors()
                    self.end_headers()
                    self.wfile.write(result)
            except urllib.error.HTTPError as e:
                err_body = e.read()
                try:
                    err_msg = json.loads(err_body).get("error", {}).get("message", err_body.decode())
                except Exception:
                    err_msg = err_body.decode()
                msg = json.dumps({"error": f"Anthropic {e.code}: {err_msg}"}).encode()
                self.send_response(e.code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(msg)))
                self.add_cors()
                self.end_headers()
                self.wfile.write(msg)
            return

        # ── /api/iam  →  IBM Cloud IAM token exchange ──
        elif self.path == "/api/iam":
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            req    = urllib.request.Request(
                "https://iam.cloud.ibm.com/identity/token",
                data=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST"
            )
            self._proxy(req)

        # ── /api/watsonx  →  IBM watsonx.ai chat endpoint ──
        elif self.path.startswith("/api/watsonx"):
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            auth   = self.headers.get("Authorization", "")
            model_id   = self.headers.get("X-Model-Id", "ibm/granite-3-8b-instruct")
            project_id = self.headers.get("X-Project-Id", "")
            region     = self.headers.get("X-Region", "us-south")

            target = f"https://{region}.ml.cloud.ibm.com/ml/v1/text/chat?version=2024-05-01"
            req = urllib.request.Request(
                target,
                data=body,
                headers={
                    "Content-Type":  "application/json",
                    "Authorization": auth,
                },
                method="POST"
            )
            self._proxy(req)

        # ── /api/ica  →  IBM Consulting Advantage REMEA agent ──────────────
        elif self.path == "/api/ica":
            length   = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length)
            auth     = self.headers.get("Authorization", "")
            agent_id = self.headers.get("X-Agent-Id", "")
            # Allow dashboard to override the ICA base URL at runtime
            ica_url_override = self.headers.get("X-ICA-Url", "")

            try:
                payload = json.loads(raw_body)
            except Exception:
                payload = {}

            # ── Build candidate URLs ───────────────────────────────────────
            if ica_url_override:
                candidates = [ica_url_override]
            else:
                candidates = [u.replace("{agent_id}", agent_id)
                              for u in ICA_ENDPOINT_CANDIDATES]

            last_error  = None
            last_status = 502
            last_body   = b""

            for url in candidates:
                try:
                    print(f"  [ICA] Trying: {url}")
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode(),
                        headers={
                            "Content-Type":  "application/json",
                            "Authorization": auth,
                            "Accept":        "application/json",
                        },
                        method="POST"
                    )
                    with urllib.request.urlopen(req, timeout=90) as resp:
                        data = resp.read()
                        print(f"  [ICA] ✅ Success ({resp.status}) — {url}")
                        self.send_response(resp.status)
                        ct = resp.headers.get("Content-Type", "application/json")
                        self.send_header("Content-Type",   ct)
                        self.send_header("Content-Length", str(len(data)))
                        self.add_cors()
                        self.end_headers()
                        self.wfile.write(data)
                        return                      # done — first winner wins

                except urllib.error.HTTPError as e:
                    last_status = e.code
                    last_body   = e.read()
                    last_error  = f"HTTP {e.code} from {url}"
                    print(f"  [ICA] ✗ {last_error}")
                    # 401/403 → wrong credentials, no point trying other paths
                    if e.code in (401, 403):
                        break
                except Exception as ex:
                    last_error = str(ex)
                    print(f"  [ICA] ✗ {last_error}")

            # ── All candidates failed — return diagnostic response ─────────
            diag = {
                "error":        "ICA endpoint not reachable",
                "detail":       last_error,
                "hint": (
                    "The ICA REMEA REST API path could not be confirmed automatically. "
                    "To fix: open https://remea.ica.ibm.com in your browser, open DevTools "
                    "(F12 → Network tab), send a test message to your agent, then find the "
                    "POST request. Copy that URL and add it as 'X-ICA-Url' header, or update "
                    "ICA_ENDPOINT_CANDIDATES in serve.py."
                ),
                "tried_urls":   candidates,
                "last_status":  last_status,
                "last_response": last_body.decode("utf-8", errors="replace")[:500],
            }
            msg = json.dumps(diag).encode()
            self.send_response(last_status if last_status != 502 else 502)
            self.send_header("Content-Type",   "application/json")
            self.send_header("Content-Length", str(len(msg)))
            self.add_cors()
            self.end_headers()
            self.wfile.write(msg)

        else:
            super().do_POST()

    def _proxy(self, req):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type",   resp.headers.get("Content-Type", "application/json"))
                self.send_header("Content-Length", str(len(data)))
                self.add_cors()
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            data = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type",   "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.add_cors()
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            msg = json.dumps({"error": str(e)}).encode()
            self.send_response(500)
            self.send_header("Content-Type",   "application/json")
            self.send_header("Content-Length", str(len(msg)))
            self.add_cors()
            self.end_headers()
            self.wfile.write(msg)

if __name__ == "__main__":
    print(f"\n  ✅  Security Champion Dashboard")
    print(f"  🌐  http://localhost:{PORT}")
    if ANTHROPIC_API_KEY:
        print(f"  🤖  Claude claude-sonnet-4-5 Sonnet ready on /api/chat")
    else:
        print(f"  ⚠   ANTHROPIC_API_KEY not set — set it in .env or as env var")
    print(f"  🤖  ICA REMEA proxy active on /api/ica  (agent auto-discovery)")
    print(f"  🤖  watsonx proxy active on  /api/iam and /api/watsonx")
    print(f"  ⏹   Press Ctrl+C to stop\n")
    with http.server.ThreadingHTTPServer(("", PORT), Handler) as srv:
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\n  Server stopped.")
