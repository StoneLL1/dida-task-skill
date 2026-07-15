## MCP Setup

This skill drives the **TickTick (滴答清单) MCP server**, a remote service at `https://mcp.dida365.com`. Claude Code must have it registered before any of its tools (`list_projects`, `create_task`, `search`, etc. — see `references/ticktick-mcp-tools-reference.md`) work. On Claude Code the tools appear as `mcp__dida365__<tool>`.

**Guardrail.** If the dida365 tools are absent, or a call fails with "tool not found" / "Needs authentication" / "MCP not connected", **stop and run the onboarding below** — never fabricate task data, never silently skip. (Detection is reactive — on a failed or missing tool call — not a check at task start.)

**Onboarding — do this automatically:**

1. Run the OAuth login helper shipped with this skill. It opens the user's browser to the TickTick login page and, after the user logs in and authorizes, prints a Bearer token (and saves it to `scripts/token.json`):
   ```bash
   python scripts/oauth_login.py login
   ```
   If the browser does not open automatically, the script prints the URL to visit manually. This bypasses the `/mcp` step entirely.
2. Register the MCP server with that token (use the exact `Authorization: Bearer …` line the script printed). If `dida365` is already registered, remove it first with `claude mcp remove dida365`:
   ```bash
   claude mcp add --transport http dida365 https://mcp.dida365.com --header "Authorization: Bearer <PRINTED_TOKEN>"
   ```
3. Retry the original task operation.

**Token expiry.** If a later call fails with 401 / "Needs authentication", the access token expired. dida365 does NOT support refresh tokens (its metadata advertises only the `authorization_code` grant and rejects `offline_access`), so there is no `refresh` subcommand. Re-run the login helper to get a fresh token, then re-register:
   ```bash
   python scripts/oauth_login.py login
   ```
   Then re-run step 2 with the new printed token.

**Bearer Token alternative** (long-lived, no browser): instead of the OAuth script, the user can create an API 口令 in 滴答清单 web → 头像 → 设置 → 账户与安全 → API 口令 and pass it directly to the `--header` in step 2. The token must come from the user — never invent one.

Official guide: https://help.dida365.com/articles/7438132116019216384
