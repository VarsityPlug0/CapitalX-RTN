"""
CapitalX Site Monitor — GitHub Actions edition
Runs every 5 minutes. On failure: asks Claude Opus to diagnose + fix,
commits the fix, pushes it back, triggers Render redeploy, Telegram alert.
"""

import os
import json
import re
import subprocess
import requests
import anthropic
from pathlib import Path

# ── Config (from GitHub Actions secrets) ──────────────────────────────────
SITE_URL        = os.environ.get("SITE_URL", "https://capitalx-rtn.onrender.com")
ANTHROPIC_KEY   = os.environ.get("ANTHROPIC_API_KEY", "")
TG_TOKEN        = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT         = os.environ.get("TELEGRAM_CHAT_ID", "")
RENDER_KEY      = os.environ.get("RENDER_API_KEY", "")
RENDER_SVC      = os.environ.get("RENDER_SERVICE_ID", "")

FIXABLE_FILES = [
    "core/views.py",
    "core/models.py",
    "core/urls.py",
    "core/admin_views.py",
    "safechain_ai/urls.py",
]

# ── Helpers ────────────────────────────────────────────────────────────────

def notify(msg: str):
    print(re.sub(r'[^\x00-\x7F]+', '', msg))
    if TG_TOKEN and TG_CHAT:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                json={"chat_id": TG_CHAT, "text": msg, "parse_mode": "HTML"},
                timeout=10,
            )
        except Exception as e:
            print(f"Telegram error: {e}")


def check_site() -> tuple[bool, str, str]:
    """Returns (is_up, error_msg, response_body)."""
    try:
        r = requests.get(SITE_URL, timeout=20, allow_redirects=True)
        if r.status_code < 500:
            return True, "", ""
        return False, f"HTTP {r.status_code}", r.text[:3000]
    except requests.Timeout:
        return False, "Timeout (20s)", ""
    except Exception as e:
        return False, str(e), ""


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


def get_diagnostics(error_body: str) -> str:
    parts = [f"[Site error body]\n{error_body}"]
    try:
        r = requests.get(
            f"https://api.render.com/v1/services/{RENDER_SVC}/deploys",
            headers={"Authorization": f"Bearer {RENDER_KEY}"},
            params={"limit": 3}, timeout=10,
        )
        if r.ok:
            deploys = r.json()
            lines = []
            for d in deploys:
                dep = d.get("deploy", d)
                lines.append(
                    f"Deploy {dep.get('id')} | status={dep.get('status')} | "
                    f"created={dep.get('createdAt')} | finished={dep.get('finishedAt')}"
                )
            parts.append("[Recent Render deploys]\n" + "\n".join(lines))
    except Exception as e:
        parts.append(f"[Render API error: {e}]")
    return "\n\n".join(parts)


def read_source_files() -> str:
    sections = []
    for rel in FIXABLE_FILES:
        p = Path(rel)
        if p.exists():
            sections.append(f"=== {rel} ===\n{p.read_text(encoding='utf-8')}")
    return "\n\n".join(sections)


def ask_claude(diagnostics: str) -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    source = read_source_files()

    prompt = f"""You are an expert Django SRE. The CapitalX investment platform at {SITE_URL} is DOWN.

## Diagnostics:
{diagnostics[:6000]}

## Source Files:
{source}

Identify the root cause and provide a fix. Only fix broken code — no refactoring.

Respond ONLY with JSON:
{{
  "diagnosis": "brief root cause",
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

    # Extract JSON
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


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    print(f"Checking {SITE_URL}...")
    is_up, error, body = check_site()

    if is_up:
        print("Site is UP. All good.")
        return

    print(f"Site DOWN: {error}")

    # Render free-tier suspension — just redeploy
    if is_suspended(body):
        notify(
            f"<b>Service suspended (Render free tier)</b>\n"
            f"Triggering redeploy to wake it up..."
        )
        ok = trigger_redeploy()
        notify("Redeploy triggered. Site back in ~2 min." if ok else "Redeploy failed. Check Render dashboard.")
        return

    # Real error — ask Claude
    notify(
        f"<b>Site DOWN</b>\n"
        f"URL: {SITE_URL}\n"
        f"Error: {error}\n\n"
        f"Asking Claude Opus to diagnose..."
    )

    if not ANTHROPIC_KEY:
        notify("ANTHROPIC_API_KEY not set. Cannot auto-diagnose.")
        return

    diagnostics = get_diagnostics(body)

    try:
        fix = ask_claude(diagnostics)
    except Exception as e:
        notify(f"<b>Claude diagnosis failed:</b>\n{e}")
        return

    diagnosis = fix.get("diagnosis", "Unknown")
    notify(f"<b>Claude's Diagnosis:</b>\n{diagnosis}")

    if not fix.get("fix_needed"):
        notify("No code fix needed. Monitoring for recovery...")
        return

    files = ", ".join(f["file_path"] for f in fix.get("files_to_fix", []))
    notify(f"<b>Applying fix to:</b> {files}\nCommit: {fix.get('commit_message')}")

    try:
        success = apply_fix(fix)
        if success:
            notify(f"<b>Fix deployed!</b>\nSite should recover in ~2 min.")
        else:
            notify("<b>Fix applied but redeploy failed.</b> Check Render.")
    except Exception as e:
        notify(f"<b>Failed to apply fix:</b>\n{e}")


if __name__ == "__main__":
    main()
