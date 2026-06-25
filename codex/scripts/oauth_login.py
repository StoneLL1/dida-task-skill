#!/usr/bin/env python3
"""TickTick (dida365) MCP OAuth login helper.

Opens the user's browser to the TickTick login page, completes the OAuth
authorization-code + PKCE flow against the dida365 authorization server, and
prints a Bearer token ready to wire into the platform's MCP server config.

Usage:
    python oauth_login.py login      # default: open browser, log in, print token

The script is pure Python standard library (no third-party packages).

Flow:
    1. Dynamic client registration  -> POST /oauth/register
    2. PKCE S256 verifier/challenge  -> local computation
    3. Open browser to /oauth/authorize (user logs in + authorizes)
    4. Catch the redirect on a local HTTP server (port 8765)
    5. Exchange the authorization code for tokens -> POST /oauth/token
    6. Persist the access token to token.json (gitignored) next to this script
    7. Print:  Authorization: Bearer <access_token>

Token expiry: dida365 does NOT support refresh tokens. The authorization-server
metadata advertises only the `authorization_code` grant, the protected-resource
metadata lists only the `tasks:read tasks:write` scopes (requesting
`offline_access` is rejected with `invalid_scope`), and login returns no
`refresh_token`. The access token therefore cannot be renewed silently — when it
expires (401 / "Needs authentication"), re-run `oauth_login.py login` to open
the browser and log in again. The script deliberately does NOT implement a
refresh subcommand to avoid implying renewal works.
"""

import base64
import hashlib
import http.server
import json
import os
import secrets
import socketserver
import sys
import time
import urllib.parse
import urllib.request
import webbrowser

RESOURCE = "https://mcp.dida365.com"
AS_METADATA_URL = "https://dida365.com/.well-known/oauth-authorization-server"
REGISTER_PATH = "/oauth/register"
AUTHORIZE_PATH = "/oauth/authorize"
TOKEN_PATH = "/oauth/token"
SCOPES = "tasks:read tasks:write"
REDIRECT_PORT = 8765
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"
CLIENT_NAME = "ticktick-skill-oauth-helper"
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token.json")
HTTP_TIMEOUT = 30


def http_json(method, url, body=None, headers=None, form=False):
    """Perform an HTTP request and return (status, json_or_text). Stdlib only."""
    data = None
    hdrs = dict(headers or {})
    if body is not None:
        if form:
            data = urllib.parse.urlencode(body).encode()
            hdrs["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            data = json.dumps(body).encode()
            hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", "replace")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


def register_client(as_base):
    body = {
        "client_name": CLIENT_NAME,
        "redirect_uris": [REDIRECT_URI],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
        "scope": SCOPES,
    }
    status, resp = http_json("POST", as_base + REGISTER_PATH, body=body)
    if status != 200 or not isinstance(resp, dict) or "client_id" not in resp:
        sys.stderr.write(f"Client registration failed ({status}): {resp}\n")
        sys.exit(1)
    return resp["client_id"]


def pkce_pair():
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    """Capture the ?code= from the OAuth redirect, then serve a result page."""

    captured = {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        code = qs.get("code", [None])[0]
        err = qs.get("error", [None])[0]
        if code:
            _CallbackHandler.captured["code"] = code
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h2>TickTick login successful</h2>"
                b"<p>You can close this tab and return to your agent.</p>"
                b"</body></html>"
            )
        else:
            _CallbackHandler.captured["error"] = err or "no_code"
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h2>Authorization failed</h2>"
                b"<p>Close this tab and re-run the script.</p></body></html>"
            )

    def log_message(self, *args):
        pass  # silence default request logging


def wait_for_callback():
    _CallbackHandler.captured = {}
    with socketserver.TCPServer(("127.0.0.1", REDIRECT_PORT), _CallbackHandler) as srv:
        srv.handle_request()  # one request, then stop
    return _CallbackHandler.captured


def exchange_code(as_base, client_id, code, verifier):
    body = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "code_verifier": verifier,
    }
    status, resp = http_json("POST", as_base + TOKEN_PATH, body=body, form=True)
    if status != 200 or not isinstance(resp, dict) or "access_token" not in resp:
        sys.stderr.write(f"Token exchange failed ({status}): {resp}\n")
        sys.exit(1)
    return resp


def save_token(token_resp):
    data = {
        "access_token": token_resp.get("access_token"),
        "expires_at": int(time.time()) + int(token_resp.get("expires_in", 3600)),
        "scope": token_resp.get("scope", SCOPES),
    }
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.chmod(TOKEN_FILE, 0o600)
    return data


def do_login(as_base):
    client_id = register_client(as_base)
    verifier, challenge = pkce_pair()
    state = secrets.token_urlsafe(16)
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "resource": RESOURCE,
    }
    auth_url = as_base + AUTHORIZE_PATH + "?" + urllib.parse.urlencode(params)
    print("Opening your browser to the TickTick login page...", file=sys.stderr)
    print("If it does not open, visit this URL manually:\n" + auth_url, file=sys.stderr)
    webbrowser.open(auth_url)

    captured = wait_for_callback()
    if "error" in captured:
        sys.stderr.write(f"Authorization error: {captured['error']}\n")
        sys.exit(1)
    code = captured["code"]

    token_resp = exchange_code(as_base, client_id, code, verifier)
    data = save_token(token_resp)
    print(f"# Token saved to {TOKEN_FILE}", file=sys.stderr)
    print(
        "# NOTE: dida365 does not issue refresh tokens. When this token expires, "
        "re-run `oauth_login.py login`.",
        file=sys.stderr,
    )
    print("Authorization: Bearer " + data["access_token"])


def main():
    as_base = "https://dida365.com"
    cmd = sys.argv[1] if len(sys.argv) > 1 else "login"
    if cmd in ("login", "--login", "-l"):
        do_login(as_base)
    else:
        sys.stderr.write(
            f"Unknown command: {cmd}\n"
            "Usage: oauth_login.py login   (refresh is not supported — dida365 "
            "issues no refresh_token; re-run `login` when the token expires)\n"
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
