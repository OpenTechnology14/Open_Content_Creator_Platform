"""Loopback-only profile picker and OAuth callback UI."""

from __future__ import annotations

import json
import html
import re
import socketserver
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .connections import complete_connection, disconnect_connection
from .http import HttpTransport
from .oauth import begin_authorization, consume_session
from .profiles import ProfileStore
from .registry import load_catalog, profile_options, provider_options
from .vault import ConnectionStore, KeyringVault

PAGE = """<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Social Management</title>
<style>
:root{font-family:system-ui;color:#f6f7fb;background:#10131a}main{max-width:760px;margin:5vh auto;padding:28px}
.card{background:#191e29;border:1px solid #303849;border-radius:18px;padding:24px;box-shadow:0 12px 44px #0006}
h1{margin-top:0}label{display:block;margin:18px 0 7px;color:#b9c4d8}select,button{width:100%;padding:12px;border-radius:10px;border:1px solid #48536a;background:#111620;color:white;font-size:16px}
button{margin-top:22px;background:#4d65ff;border:0;font-weight:700;cursor:pointer}button:disabled{opacity:.45}.brand{display:flex;align-items:center;gap:12px}.brand img{width:54px;height:54px;object-fit:contain;border-radius:12px;background:white;padding:4px}.note{color:#9aa8c0;font-size:14px}#status{min-height:24px;margin-top:15px}
</style><main><div class="card"><h1>Social Management</h1><p class="note">Choose the identity, logo, account destination, and permission for this connection.</p>
<label for="profile">Profile</label><select id="profile"></select><label for="brand">Brand</label><div class="brand"><img id="logo" alt="Selected brand logo"><select id="brand"></select></div>
<label for="provider">Platform</label><select id="provider"></select><label for="capability">Connection purpose</label><select id="capability"></select>
<button id="connect">Connect account</button><div id="status" role="status" aria-live="polite"></div></div></main>
<script>
let data; const el=id=>document.getElementById(id); const option=(v,l)=>new Option(l,v);
async function start(){data=await(await fetch('/api/options')).json(); data.profiles.forEach(p=>el('profile').add(option(p.value,p.label))); refreshProfile()}
function refreshProfile(){let p=data.profiles.find(x=>x.value===el('profile').value);el('brand').replaceChildren(...p.brands.map(x=>option(x.value,x.label)));el('brand').value=p.default_brand_id;refreshLogo();let ps=data.providers[p.value];el('provider').replaceChildren(...ps.map(x=>option(x.value,`${x.label} — ${x.connection_status}`)));refreshProvider()}
function refreshLogo(){let p=data.profiles.find(x=>x.value===el('profile').value),b=p.brands.find(x=>x.value===el('brand').value);el('logo').src='/'+b.logo_path}
function refreshProvider(){let p=data.providers[el('profile').value].find(x=>x.value===el('provider').value);el('capability').replaceChildren(...p.capabilities.filter(x=>x!=='account-read').map(x=>option(x,x)));el('connect').disabled=p.connection_status!=='available';el('status').textContent=p.connection_status==='available'?'Ready to connect.':'This provider needs registration or a future adapter.'}
el('profile').onchange=refreshProfile;el('brand').onchange=refreshLogo;el('provider').onchange=refreshProvider;
el('connect').onclick=async()=>{el('connect').disabled=true;let q=new URLSearchParams({profile:el('profile').value,provider:el('provider').value,capability:el('capability').value});let r=await fetch('/api/authorize?'+q);let x=await r.json();if(!r.ok){el('status').textContent=x.error;refreshProvider();return}location.href=x.authorization_url};start();
</script></html>"""


class LoopbackThreadingHTTPServer(ThreadingHTTPServer):
    """Bind without HTTPServer's reverse-DNS lookup, which can stall native macOS launches."""

    def server_bind(self) -> None:
        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = str(host)
        self.server_port = int(port)


def serve(*, host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("the account picker may only bind to loopback")
    state_root = Path.home() / ".hybrid-creator-platform" / "social"
    catalog = ProfileStore(state_root / "profiles.json", load_catalog()).catalog()
    sessions = state_root / "oauth-sessions"
    store = ConnectionStore(state_root / "connections.json")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        def send_json(self, status: int, value: dict) -> None:
            payload = json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                payload = PAGE.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header(
                    "Content-Security-Policy",
                    "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'self' data:",
                )
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            if parsed.path.startswith("/assets/brands/"):
                asset = (Path(__file__).resolve().parents[1] / parsed.path.lstrip("/")).resolve()
                root = (Path(__file__).resolve().parents[1] / "assets" / "brands").resolve()
                if not asset.is_relative_to(root) or not asset.is_file():
                    self.send_error(404)
                    return
                payload = asset.read_bytes()
                self.send_response(200)
                self.send_header(
                    "Content-Type", "image/svg+xml" if asset.suffix == ".svg" else "image/png"
                )
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            if parsed.path == "/api/options":
                self.send_json(
                    200,
                    {
                        "profiles": profile_options(catalog),
                        "providers": {
                            p.id: provider_options(catalog, p.id) for p in catalog.profiles
                        },
                    },
                )
                return
            if parsed.path == "/api/health":
                self.send_json(
                    200,
                    {"service": "hybrid-creator-social", "schema_version": 1},
                )
                return
            if parsed.path == "/api/connections":
                self.send_json(
                    200,
                    {
                        "connections": [
                            item.model_dump(mode="json") for item in store.read()
                        ]
                    },
                )
                return
            if parsed.path == "/api/authorize":
                values = {key: item[0] for key, item in parse_qs(parsed.query).items()}
                try:
                    url, _ = begin_authorization(
                        catalog,
                        profile_id=values["profile"],
                        provider_id=values["provider"],
                        capability=values["capability"],
                        redirect_uri=f"http://127.0.0.1:{port}/oauth/callback",
                        session_dir=sessions,
                    )
                    self.send_json(200, {"authorization_url": url})
                except (KeyError, ValueError) as exc:
                    self.send_json(400, {"error": str(exc)})
                return
            if parsed.path == "/oauth/callback":
                values = {key: item[0] for key, item in parse_qs(parsed.query).items()}
                try:
                    state = values["state"]
                    if re.fullmatch(r"[A-Za-z0-9_-]{32,256}", state) is None:
                        raise ValueError("invalid OAuth state")
                    session = consume_session(sessions / f"{state}.json", returned_state=state)
                    record = complete_connection(
                        catalog,
                        session,
                        code=values["code"],
                        http=HttpTransport(),
                        vault=KeyringVault(),
                        store=store,
                    )
                    message = f"Connected {html.escape(record.account_name)} to {html.escape(record.profile_id)}. You may close this tab."
                    payload = f"<!doctype html><meta charset=utf-8><title>Connected</title><p>{message}</p>".encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except (KeyError, OSError, ValueError) as exc:
                    self.send_json(400, {"error": str(exc)})
                return
            self.send_error(404)

        def do_DELETE(self) -> None:
            parsed = urlparse(self.path)
            prefix = "/api/connections/"
            if not parsed.path.startswith(prefix):
                self.send_error(404)
                return
            connection_id = parsed.path.removeprefix(prefix)
            if re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", connection_id) is None:
                self.send_json(400, {"error": "invalid connection ID"})
                return
            try:
                record = disconnect_connection(
                    connection_id=connection_id,
                    vault=KeyringVault(),
                    store=store,
                )
                self.send_json(
                    200,
                    {
                        "disconnected": record.id,
                        "profile_id": record.profile_id,
                        "provider_id": record.provider_id,
                    },
                )
            except (OSError, ValueError) as exc:
                self.send_json(400, {"error": str(exc)})

    server = LoopbackThreadingHTTPServer((host, port), Handler)
    if open_browser:
        webbrowser.open(f"http://127.0.0.1:{port}/")
    sys.stdout.write(f"Social Management: http://127.0.0.1:{port}/\n")
    server.serve_forever()
