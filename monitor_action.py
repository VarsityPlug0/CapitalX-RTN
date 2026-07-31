"""
CapitalX Site Monitor — GitHub Actions edition
Runs every 5 minutes. Checks critical pages. On failure: Claude Opus diagnoses
+ fixes, commits, pushes, redeploys Render, alerts via Telegram.
"""

import os
import json
import re
import subprocess
import requests
import anthropic
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
SITE_URL      = os.environ.get("SITE_URL", "https://capitalx-rtn.onrender.com")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TG_TOKEN      = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT       = os.environ.get("TELEGRAM_CHAT_ID", "")
RENDER_KEY    = os.environ.get("RENDER_API_KEY", "")
RENDER_SVC    = os.environ.get("RENDER_SERVICE_ID", "")

# Critical pages to check every run: (path, expected_status, description)
CRITICAL_PAGES = [
    ("/healthz/",  200, "Health check"),
    ("/",          200, "Homepage"),
    ("/login/",    200, "Login page"),
    ("/plans/",    200, "Plans page"),
    ("/register/", 200, "Register page"),
]

FIXABLE_FILES = [
    "core/views.py",
    "core/models.py",
    "core/urls.py",
    "core/admin_views.py",
    "safechain_ai/urls.py",
]

# ── Helpers ──────────────────────────────────────────────────────────────────

def notify(msg: str):
    clean = re.sub(r'[^\x00-\x7F]+', '', msg)
    print(clean)
    if TG_TOKEN and TG_CHAT:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                json={"chat_id": TG_CHAT, "text": msg, "parse_mode": "HTML"},
                timeout=10,
            )
        except Exception as e:
            print(f"Telegram error: {e}")


def check_page(path: str, expected: int) -> tuple[bool, int, str]:
    """Returns (ok, status_code, body_snippet)."""
    try:
        r = requests.get(SITE_URL + path, timeout=20, allow_redirects=True)
        ok = r.status_code == expected or (expected == 200 and r.status_code < 400)
        return ok, r.status_code, r.text[:2000]
    except requests.Timeout:
        return False, 0, "Timeout (20s)"
    except Exception as e:
        return False, 0, str(e)


def check_all_pages() -> list[dict]:
    """Check every critical page. Returns list of failures."""
    failures = []
    for path, expected, desc in CRITICAL_PAGES:
        ok, status, body = check_page(path, expected)
        if not ok:
            failures.append({
                "path": path,
                "description": desc,
                "status": status,
                "body": body,
            })
            print(f"  FAIL {path} — HTTP {status}")
        else:
            print(f"  OK   {path} — HTTP {status}")
    return failures


def is_suspended(body: str) -> bool:
    return "suspended" in body.lower()


def trigger_redeploy() -> bool:
    try:
        r = requests.post(
            f"https://api.render.com/v1/services/{RENDER_SVC}/deploys",
            headers={"Authorization": f"Bearer {RENDER_KEY}"},
            json={}, timeout=15,
        )
        return r.ok
    except Exception:
        return False


def get_render_deploys() -> str:
    try:
        r = requests.get(
            f"https://api.render.com/v1/services/{RENDER_SVC}/deploys",
            headers={"Authorization": f"Bearer {RENDER_KEY}"},
            params={"limit": 3}, timeout=10,
        )
        if r.ok:
            lines = []
            for d in r.json():
                dep = d.get("deploy", d)
                lines.append(
                    f"Deploy {dep.get('id')} | {dep.get('status')} | "
                    f"created={dep.get('createdAt')} finished={dep.get('finishedAt')}"
                )
            return "\n".join(lines)
    except Exception as e:
        return f"Render API error: {e}"
    return ""


def read_source_files() -> str:
    sections = []
    for rel in FIXABLE_FILES:
        p = Path(rel)
        if p.exists():
            sections.append(f"=== {rel} ===\n{p.read_text(encoding='utf-8')}")
    return "\n\n".join(sections)


def ask_claude(failures: list[dict]) -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

    failures_text = "\n\n".join(
        f"Page: {f['path']} ({f['description']})\n"
        f"HTTP status: {f['status']}\n"
        f"Response body:\n{f['body'][:1500]}"
        for f in failures
    )

    deploys = get_render_deploys()
    source  = read_source_files()

    prompt = f"""You are an expert Django SRE. The CapitalX investment platform has failing pages.

## Failing Pages:
{failures_text}

## Recent Render Deploys:
{deploys}

## Source Files:
{source}

Identify the root cause and provide the exact fix. Only fix broken code.

Respond ONLY with JSON (no extra text):
{{
  "diagnosis": "brief root cause description",
  "fix_needed": true,
  "files_to_fix": [{{"file_path": "core/views.py", "new_content": "..."}}],
  "commit_message": "Fix: ..."
}}
If no code fix is needed, set fix_needed to false and files_to_fix to [].
"""

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=32000,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        response = stream.get_final_message()

    text = next((b.text for b in response.content if b.type == "text"), "")
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    else:
        start, end = text.find("{"), text.rfind("}") + 1
        if start != -1:
            text = text[start:end]
    return json.loads(text)


def apply_fix(fix: dict) -> bool:
    if not fix.get("fix_needed") or not fix.get("files_to_fix"):
        return False

    for f in fix["files_to_fix"]:
        Path(f["file_path"]).write_text(f["new_content"], encoding="utf-8")
        print(f"Wrote: {f['file_path']}")

    subprocess.run(["git", "config", "user.email", "monitor@capitalx-rtn.com"], check=True)
    subprocess.run(["git", "config", "user.name", "CapitalX Monitor"], check=True)

    file_paths = [f["file_path"] for f in fix["files_to_fix"]]
    subprocess.run(["git", "add"] + file_paths, check=True)

    commit_msg = fix.get("commit_message", "Auto-fix by Claude monitor")
    subprocess.run(
        ["git", "commit", "-m", f"{commit_msg}\n\nAuto-applied by Claude site monitor"],
        check=True,
    )
    subprocess.run(["git", "push"], check=True)
    return trigger_redeploy()


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    print(f"Checking {SITE_URL}...")

    # Quick site-down check first
    ok, status, body = check_page("/healthz/", 200)

    if not ok and is_suspended(body):
        notify(
            f"<b>Service suspended (Render free tier)</b>\n"
            f"Triggering redeploy to wake it up..."
        )
        ok = trigger_redeploy()
        notify("Redeploy triggered. Site back in ~2 min." if ok else "Redeploy failed. Check Render dashboard.")
        return

    # Check all critical pages
    print("Checking critical pages...")
    failures = check_all_pages()

    if not failures:
        print("All pages OK.")
        return

    # Build failure summary
    pages_list = "\n".join(f"  • {f['description']} ({f['path']}) — HTTP {f['status']}" for f in failures)
    notify(
        f"<b>{len(failures)} page(s) failing on CapitalX</b>\n"
        f"{pages_list}\n\n"
        f"Asking Claude Opus to diagnose..."
    )

    if not ANTHROPIC_KEY:
        notify("ANTHROPIC_API_KEY not set. Cannot auto-diagnose.")
        return

    try:
        fix = ask_claude(failures)
    except Exception as e:
        notify(f"<b>Claude diagnosis failed:</b>\n{e}")
        return

    diagnosis = fix.get("diagnosis", "Unknown")
    notify(f"<b>Claude's Diagnosis:</b>\n{diagnosis}")

    if not fix.get("fix_needed"):
        notify("No code fix needed. Could be a transient error or infrastructure issue.")
        return

    files = ", ".join(f["file_path"] for f in fix.get("files_to_fix", []))
    commit_msg = fix.get("commit_message", "Auto-fix")
    notify(f"<b>Applying fix to:</b> {files}\nCommit: {commit_msg}")

    try:
        success = apply_fix(fix)
        if success:
            notify(f"<b>Fix deployed!</b>\nSite should recover in ~2 min.")
        else:
            notify("<b>Fix applied but redeploy failed.</b> Check Render dashboard.")
    except Exception as e:
        notify(f"<b>Failed to apply fix:</b>\n{e}")


if __name__ == "__main__":
    main()
