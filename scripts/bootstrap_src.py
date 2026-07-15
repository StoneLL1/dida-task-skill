"""One-shot: derive dida-task-skill/src/ (single source) from canonical assets.

Reads:
  - GLOBAL skill (~/.claude/skills/ticktick-task)        -> shared body/viz/refs/scripts/templates
  - ~/.claude/commands/{task-dashboard,week-report}.md   -> slash commands (claude-code only)
  - repo platform docs (codex/hermes/openclaw)           -> per-platform frontmatter / mcp-setup / tail

Writes dida-task-skill/src/ . After this, `scripts/build.py` regenerates the 4 platform
folders from src/ only — this bootstrap is not needed again unless src/ is rebuilt from
scratch.

NOT portable (reads a machine-specific global skill dir). Intended to be run once by the
maintainer who has the latest global skill installed.
"""
import os
import re
import shutil

HOME = os.path.expanduser("~")
GLOBAL_SKILL = os.path.join(HOME, ".claude", "skills", "ticktick-task")
COMMANDS = os.path.join(HOME, ".claude", "commands")
REPO = r"D:\Users\Aletta\Desktop\Works\dida-task-skill"
SRC = os.path.join(REPO, "src")


def rd(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def wd(p, content):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def cp(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def split_sections(text):
    """Return (preamble, {section_header: section_text}). Section header includes '## '."""
    parts = re.split(r"\n(?=## )", text)
    preamble = parts[0]
    sections = {}
    for p in parts[1:]:
        head = p.split("\n", 1)[0]
        sections[head] = p
    return preamble, sections


def get_frontmatter(preamble):
    m = re.match(r"---\r?\n.*?\r?\n---", preamble, re.DOTALL)
    return m.group(0) if m else ""


def main():
    assert os.path.isdir(GLOBAL_SKILL), f"global skill not found: {GLOBAL_SKILL}"
    g = rd(os.path.join(GLOBAL_SKILL, "SKILL.md"))

    intro_start = g.index("# TickTick Task Management")
    mcp_start = g.index("## MCP Setup")
    fts_start = g.index("## First-Time Setup")
    viz_start = g.index("## Visualization")

    intro = g[intro_start:mcp_start].strip()
    body = g[fts_start:viz_start].strip()
    viz = g[viz_start:].strip()

    # Drop the claude-code-only tool-prefix sentence; the shared reference doc already
    # explains naming generically ("on other runtimes the prefix differs").
    body = body.replace(" On Claude Code they appear as `mcp__dida365__<tool>`.", "")
    # Parameterize the platform-specific "write file + open browser" step.
    viz = re.sub(r"(?m)^5\. \*\*写出打开\*\*：.*$",
                 "5. **写出打开**：{{open_html_step}}", viz)

    wd(os.path.join(SRC, "intro.md"), intro + "\n")
    wd(os.path.join(SRC, "body.md"), body + "\n")
    wd(os.path.join(SRC, "visualization.md"), viz + "\n")

    # --- shared assets ---
    for name in ["ticktick-mcp-tools-reference.md", "visualization-reference.md"]:
        cp(os.path.join(GLOBAL_SKILL, "references", name),
           os.path.join(SRC, "references", name))
    cp(os.path.join(GLOBAL_SKILL, "scripts", "oauth_login.py"),
       os.path.join(SRC, "scripts", "oauth_login.py"))
    cp(os.path.join(GLOBAL_SKILL, "scripts", "config.example.json"),
       os.path.join(SRC, "scripts", "config.example.json"))
    for tpl in ["kanban-colorful.html", "kanban-claude.html", "kanban-notion.html", "weekly-report.html"]:
        cp(os.path.join(GLOBAL_SKILL, "scripts", "templates", tpl),
           os.path.join(SRC, "scripts", "templates", tpl))
    for cmd in ["task-dashboard.md", "week-report.md"]:
        cp(os.path.join(COMMANDS, cmd),
           os.path.join(SRC, "commands", cmd))

    # --- claude-code fragments come from the (latest) global SKILL.md ---
    cc_fm = get_frontmatter(g) + "\n"            # frontmatter block + trailing newline
    cc_mcp = g[g.index("## MCP Setup"):fts_start].strip() + "\n"
    wd(os.path.join(SRC, "platforms", "claude-code", "frontmatter.md"), cc_fm)
    wd(os.path.join(SRC, "platforms", "claude-code", "mcp-setup.md"), cc_mcp + "\n")

    # --- codex / hermes / openclaw fragments from their existing repo docs ---
    plat_docs = {
        "codex":   os.path.join(REPO, "codex", "codex.md"),
        "hermes":  os.path.join(REPO, "hermes", "ticktick-task", "SKILL.md"),
        "openclaw": os.path.join(REPO, "openclaw", ".agents", "skills", "ticktick-task", "SKILL.md"),
    }
    for plat, path in plat_docs.items():
        doc = rd(path)
        preamble, secs = split_sections(doc)
        fm = get_frontmatter(preamble)
        wd(os.path.join(SRC, "platforms", plat, "frontmatter.md"),
           (fm + "\n") if fm else "")
        wd(os.path.join(SRC, "platforms", plat, "mcp-setup.md"),
           secs["## MCP Setup"].strip() + "\n\n")
        # tail = platform-specific extras, appended AFTER visualization by build.py
        if plat == "codex":
            tail = secs["## Additional Tools"].strip()
        else:  # hermes / openclaw
            tail = secs["## Common Scenarios"].strip() + "\n\n" + secs["## Verification Checklist"].strip()
        wd(os.path.join(SRC, "platforms", plat, "tail.md"), tail + "\n")

    print("bootstrap OK -> src/")
    for root, _, files in os.walk(SRC):
        for fn in sorted(files):
            rel = os.path.relpath(os.path.join(root, fn), SRC)
            print(" ", rel.replace(os.sep, "/"))


if __name__ == "__main__":
    main()
