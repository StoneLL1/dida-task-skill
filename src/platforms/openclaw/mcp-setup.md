## MCP Setup

This skill drives the **TickTick (滴答清单) MCP server**, a remote Streamable HTTP service at `https://mcp.dida365.com` (server name `dida365`). It must be registered with OpenClaw before any of its tools (`list_projects`, `create_task`, `search`, etc. — see `references/ticktick-mcp-tools-reference.md`) work.

**Guardrail.** If the dida365 tools are absent, or a call fails with "tool not found" / "Needs authentication" / "MCP not connected", **stop and run the onboarding below** — never fabricate task data, never silently skip. (Detection is reactive — on a failed or missing tool call — not a check at task start.)

**Onboarding — guide the user through this immediately when tools are missing:**

1. Run the OAuth login helper shipped with this skill. It opens the user's browser to the TickTick login page and, after the user logs in and authorizes, prints a Bearer token (and saves it to `scripts/token.json`):
   ```bash
   python scripts/oauth_login.py login
   ```
2. Tell the user to add the `dida365` HTTP MCP server to OpenClaw's MCP config using the printed token. If `dida365` is already registered, update its `headers` instead. Give them the exact snippet to paste (replace `<PRINTED_TOKEN>` with the script's output):
   ```json
   {
     "mcpServers": {
       "dida365": {
         "url": "https://mcp.dida365.com",
         "headers": {
           "Authorization": "Bearer <PRINTED_TOKEN>"
         }
       }
     }
   }
   ```
3. Once the user confirms the server is connected, retry the original task operation.

**Token expiry.** If a later call fails with 401 / "Needs authentication", the access token expired. dida365 does NOT support refresh tokens (re-login is the only renewal path), so re-run `python scripts/oauth_login.py login` to open the browser again, then tell the user to update the Bearer token in OpenClaw's config with the new printed value.

**Bearer Token alternative** (long-lived, no browser): instead of the OAuth script, the user can create an API 口令 in 滴答清单 web → 头像 → 设置 → 账户与安全 → API 口令 and paste it directly as the Bearer value in the snippet above. The token must come from the user — never invent one.

Official guide: https://help.dida365.com/articles/7438132116019216384
