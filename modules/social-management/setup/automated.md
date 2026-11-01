# Social Management — automated setup

The scriptable portion installs a small Python CLI, validates every profile/provider/logo reference,
and tests OAuth state, redacted storage, and request routing without contacting a real account.
Both Tauri apps compile a shared Social tab and a narrow native bridge that bundles the catalog,
logos, and fixed loopback service. Selecting the module in desktop **Module setup** installs its
isolated Python environment; opening **Social** starts that service automatically.

The native bridge separately persists a validated Stream workspace and Content workspace. It
remembers each profile's brand/provider/capability/redacted connection route with atomic local
writes and exposes a compact switcher throughout both apps. Disconnect removes both the OS-vault
credential and redacted connection row through the fixed loopback service.

```bash
cd modules/social-management
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/python -m social_management profiles
cd ../..
python3 -m pytest -q tests/social_management
```

Windows PowerShell uses `.venv\Scripts\python.exe` in place of `.venv/bin/python`.

Automated setup does not create provider developer applications, accept platform terms, make a
channel live-eligible, pass TikTok/Meta/LinkedIn review, choose an account, or publish anything.
Those are account-owner actions in [`manual.md`](manual.md).

The [editorial portfolio controls](editorial.md) also run locally without provider credentials.
Their SQLite queue supports concept submission/review, account-route validation, production
briefs and JSON/Markdown reports for AgentWorkflows. Automated tests use synthetic sources
and accounts; they do not prove source rights, owner approval or provider delivery.
