## MCP Setup

This skill drives the **TickTick (滴答清单) MCP server**, a remote service at `https://mcp.dida365.com`. Codex must have it registered before any of its tools (`list_projects`, `create_task`, `search`, etc. — see `references/ticktick-mcp-tools-reference.md`) work.

**Guardrail.** If the dida365 tools are absent, or a call fails with "tool not found" / "Needs authentication" / "MCP not connected", **stop and run the onboarding below** — never fabricate task data, never silently skip. (Detection is reactive — on a failed or missing tool call — not a check at task start.)

**Onboarding — do this automatically:**

1. Run the registration command directly (do not ask first — it only adds a local config entry). If `dida365` is already registered, skip this and go to step 2:
   ```bash
   codex mcp add dida365 --url https://mcp.dida365.com
   ```
2. OAuth login is prompted automatically right after the command runs — **hand off to the user** to complete it in the browser. (The agent cannot complete OAuth itself.)
3. Once the user confirms the `dida365` server is connected, retry the original task operation.

**Fallback if Codex's auto-OAuth does not fire.** Run the login helper shipped with this skill — it opens the browser and prints a Bearer token:
   ```bash
   python scripts/oauth_login.py login
   ```
   Codex reads the token from an environment variable, so export it and re-add the server with `--bearer-token-env-var`:
   ```bash
   codex mcp remove dida365
   export DIDA365_TOKEN="<the access token printed by the script>"
   codex mcp add dida365 --url https://mcp.dida365.com --bearer-token-env-var DIDA365_TOKEN
   ```
   **Token expiry:** if a call fails with 401, re-run `python scripts/oauth_login.py login` (dida365 does NOT support refresh tokens — re-login is the only renewal path), update the env var with the new printed token, and retry.

**Bearer Token alternative** (long-lived, no browser): the user can create an API 口令 in 滴答清单 web → 头像 → 设置 → 账户与安全 → API 口令 and use it in place of the script-printed token above (same `--bearer-token-env-var` wiring). The token must come from the user — never invent one.

Official guide: https://help.dida365.com/articles/7438132116019216384
