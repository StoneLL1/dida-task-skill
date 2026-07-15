#!/usr/bin/env python3
"""Single-source generator for the ticktick-task skill across 4 AI platforms.

Source of truth: dida-task-skill/src/  (intro/body/visualization + references + scripts +
templates + commands + per-platform frontmatter/mcp-setup/tail + adapter YAML).

Output: regenerates each platform's self-contained folder (claude-code / codex / hermes /
openclaw) so it can be copied wholesale by users.

Deterministic & idempotent: no timestamps; LF-only output; every file ends with exactly
one trailing newline; running twice produces zero diff.

Usage:
    python scripts/build.py            # regenerate all 4 platform folders
    python scripts/build.py --check    # exit 0 iff working tree matches generator (gofmt -l)

`src/` itself is never touched. The 4 platform output_root dirs are made to match the
generated fileset exactly (write mode also prunes files the generator no longer emits).
"""
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
PLATFORMS = ["claude-code", "codex", "hermes", "openclaw"]

REF_FILES = ["ticktick-mcp-tools-reference.md", "visualization-reference.md"]
SCRIPT_FILES = ["oauth_login.py", "config.example.json"]
TEMPLATE_FILES = ["kanban-colorful.html", "kanban-claude.html",
                  "kanban-notion.html", "weekly-report.html"]
COMMAND_FILES = ["task-dashboard.md", "week-report.md"]


def rd(p):
    with open(p, "r", encoding="utf-8") as f:  # universal newlines -> \n
        return f.read()


def asset(p):
    """Read a source asset, LF-normalized, single trailing newline."""
    return rd(p).rstrip("\n") + "\n"


def compose_doc(A, plat):
    intro = asset(os.path.join(SRC, "intro.md"))
    body = asset(os.path.join(SRC, "body.md"))
    viz = asset(os.path.join(SRC, "visualization.md")).replace(
        "{{open_html_step}}", A["open_html_step"])
    pdir = os.path.join(SRC, "platforms", plat)

    parts = []
    if A["has_frontmatter"]:
        parts.append(asset(os.path.join(pdir, "frontmatter.md")).strip())
    parts.append(intro.strip())
    parts.append(asset(os.path.join(pdir, "mcp-setup.md")).strip())
    parts.append(body.strip())
    parts.append(viz.strip())
    if A["has_tail"]:
        parts.append(asset(os.path.join(pdir, "tail.md")).strip())
    return "\n\n".join(parts).rstrip("\n") + "\n"


def render_fileset(plat):
    """Return {abs_output_path: text_content} for everything this platform should own."""
    A = yaml.safe_load(rd(os.path.join(SRC, "platforms", f"{plat}.yml")))
    out_root = os.path.join(ROOT, A["output_root"])
    files = {}
    files[os.path.join(out_root, A["skill_relpath"])] = compose_doc(A, plat)
    for fn in REF_FILES:
        files[os.path.join(out_root, A["references_relpath"], fn)] = \
            asset(os.path.join(SRC, "references", fn))
    for fn in SCRIPT_FILES:
        files[os.path.join(out_root, A["scripts_relpath"], fn)] = \
            asset(os.path.join(SRC, "scripts", fn))
    for fn in TEMPLATE_FILES:
        files[os.path.join(out_root, A["templates_relpath"], fn)] = \
            asset(os.path.join(SRC, "scripts", "templates", fn))
    if A["emits_slash_commands"]:
        for fn in COMMAND_FILES:
            files[os.path.join(out_root, A["commands_relpath"], fn)] = \
                asset(os.path.join(SRC, "commands", fn))
    return A, {os.path.normpath(k): v for k, v in files.items()}


def walk_files(root):
    out = []
    for dirpath, _, names in os.walk(root):
        for n in names:
            out.append(os.path.join(dirpath, n))
    return out


def main():
    check = "--check" in sys.argv
    drift = False

    for plat in PLATFORMS:
        A, files = render_fileset(plat)
        out_root = os.path.join(ROOT, A["output_root"])
        expected = set(os.path.normpath(p) for p in files)
        actual = set(os.path.normpath(p) for p in walk_files(out_root)) if os.path.isdir(out_root) else set()

        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        diff = sorted(p for p in (expected & actual) if rd(p) != files[p])

        if check:
            if missing or extra or diff:
                drift = True
                print(f"[DRIFT] {plat}")
                for p in missing:
                    print(f"  - missing: {os.path.relpath(p, ROOT)}")
                for p in extra:
                    print(f"  - extra:   {os.path.relpath(p, ROOT)}")
                for p in diff:
                    print(f"  - diff:    {os.path.relpath(p, ROOT)}")
            else:
                print(f"[OK] {plat}")
        else:
            for p, content in files.items():
                rel = os.path.relpath(p, ROOT)
                existed = os.path.isfile(p)
                same = existed and rd(p) == content
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w", encoding="utf-8", newline="\n") as f:
                    f.write(content)
                tag = "=" if same else ("+" if not existed else "M")
                print(f"  [{tag}] {rel.replace(os.sep, '/')}")
            for p in extra:  # prune files the generator no longer emits
                os.remove(p)
                print(f"  [-] {os.path.relpath(p, ROOT).replace(os.sep, '/')} (pruned)")

    if check and drift:
        print("\nDRIFT: working tree != generator output. Run `python scripts/build.py`.")
        sys.exit(1)
    if check:
        print("\nAll 4 platforms match generator output.")


if __name__ == "__main__":
    main()
