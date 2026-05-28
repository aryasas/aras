#!/usr/bin/env python3
"""
Multi-agent orchestration for aras project.

Workflow:
  1. Claude Code writes docs/handoff.md
  2. Run this script → backend agent + frontend agent implement tasks
  3. Agent reports appended to handoff.md, docs updated, run persisted to DB
  4. Claude reviews handoff.md and writes ## Claude Review
     - APPROVED → done
     - NEEDS-FIX → Claude adds ## Revision Tasks → re-run this script

Role defaults (edit DEFAULT_* vars to change permanently):
  orchestrator = sonnet   (-o flag to override)
  backend      = gemini   (-b flag to override)
  frontend     = haiku    (-f flag to override)
  mobile       = haiku    (-m flag to override)

Usage:
  python tools/multi_agent.py                          # run all (backend + frontend + mobile if tasks exist)
  python tools/multi_agent.py -b gemini-pro            # backend on Gemini Pro
  python tools/multi_agent.py -f sonnet                # frontend on Sonnet
  python tools/multi_agent.py -m sonnet                # mobile on Sonnet
  python tools/multi_agent.py --backend-only
  python tools/multi_agent.py --frontend-only
  python tools/multi_agent.py --mobile-only
  python tools/multi_agent.py --test "hello"

Available agent keys: gemini, gemini-pro, gemini-flash, gpt, sonnet, opus, haiku
"""

import argparse
import subprocess
import sys
import re
import warnings
warnings.filterwarnings("ignore", category=Warning, module="urllib3")
import requests
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT  = Path(__file__).parent.parent
HANDOFF_FILE  = PROJECT_ROOT / "docs" / "handoff.md"
FEATURE_FILE  = PROJECT_ROOT / "docs" / "feature.md"
FIX_FILE      = PROJECT_ROOT / "docs" / "fix.md"
ARAS_FILE     = PROJECT_ROOT / "docs" / "aras.md"

DATE = datetime.now().strftime("%Y-%m-%d")

BACKEND_SYSTEM = (
    "ARAS_AGENT_ROLE=backend-worker. Read docs/agents.md (Gemini Worker Rules section) for your full constraints. "
    "You are a backend developer for the Aras framework (FastAPI + SQLAlchemy 2.0). "
    "Read docs/aras.md first for framework patterns. "
    "ONLY implement tasks listed under '## Backend Tasks' or '## Revision Tasks > Backend' in the spec below. "
    "Do NOT implement frontend tasks. Do NOT write any code that was not explicitly requested. "
    "Claude (the orchestrator) has already designed the solution — your job is to implement it as specified, nothing more. "
    "After writing all files, output a structured report using EXACTLY this format:\n\n"
    "### AGENT REPORT\n"
    "- files_written: <comma-separated paths or 'none'>\n"
    "- features_added: <short description or 'none'>\n"
    "- fixes_applied: <short description or 'none'>\n"
    "- framework_changes: <short description or 'none'>\n"
    "- issues: <short description or 'none'>\n\n"
    "SPEC:\n\n"
)

FRONTEND_SYSTEM = (
    "ARAS_AGENT_ROLE=frontend-worker. Read docs/agents.md (Codex Worker Rules section) for your full constraints. "
    "You are a frontend developer for the Aras framework (React 19 + TypeScript + TailwindCSS 4). "
    "Read docs/aras.md first for framework patterns and component conventions. "
    "ONLY implement tasks listed under '## Frontend Tasks' or '## Revision Tasks > Frontend' in the spec below. "
    "Do NOT implement backend tasks. Do NOT implement mobile tasks. Do NOT write any code that was not explicitly requested. "
    "Claude (the orchestrator) has already designed the solution — your job is to implement it as specified, nothing more. "
    "After writing all files, output a structured report using EXACTLY this format:\n\n"
    "### AGENT REPORT\n"
    "- files_written: <comma-separated paths or 'none'>\n"
    "- features_added: <short description or 'none'>\n"
    "- fixes_applied: <short description or 'none'>\n"
    "- framework_changes: <short description or 'none'>\n"
    "- issues: <short description or 'none'>\n\n"
    "SPEC:\n\n"
)

MOBILE_SYSTEM = (
    "ARAS_AGENT_ROLE=mobile-worker. "
    "You are a mobile developer for the Aras framework (React Native + Expo + TypeScript). "
    "The mobile app lives in the mobile/ directory. "
    "Read docs/aras.md first for framework patterns. "
    "ONLY implement tasks listed under '## Mobile Tasks' or '## Revision Tasks > Mobile' in the spec below. "
    "Do NOT implement backend or web frontend tasks. Do NOT write any code that was not explicitly requested. "
    "Claude (the orchestrator) has already designed the solution — your job is to implement it as specified, nothing more. "
    "After writing all files, output a structured report using EXACTLY this format:\n\n"
    "### AGENT REPORT\n"
    "- files_written: <comma-separated paths or 'none'>\n"
    "- features_added: <short description or 'none'>\n"
    "- fixes_applied: <short description or 'none'>\n"
    "- framework_changes: <short description or 'none'>\n"
    "- issues: <short description or 'none'>\n\n"
    "SPEC:\n\n"
)


# ── Model constants ───────────────────────────────────────────────────────────
# Edit these to change a model globally — injected everywhere via AGENTS below.

MODEL_GEMINI_FLASH  = "gemini-2.5-flash"
MODEL_GEMINI_PRO    = "gemini-2.5-pro"
MODEL_CLAUDE_SONNET = "claude-sonnet-4-6"
MODEL_CLAUDE_OPUS   = "claude-opus-4-7"
MODEL_CLAUDE_HAIKU  = "claude-haiku-4-5-20251001"

# ── Agent registry ────────────────────────────────────────────────────────────
# key → {cli, model, label}  (model=None means the CLI picks it)

AGENTS: dict[str, dict] = {
    "gemini":       {"cli": "gemini",  "model": MODEL_GEMINI_FLASH,  "label": f"Gemini ({MODEL_GEMINI_FLASH})"},
    "gemini-flash": {"cli": "gemini",  "model": MODEL_GEMINI_FLASH,  "label": f"Gemini ({MODEL_GEMINI_FLASH})"},
    "gemini-pro":   {"cli": "gemini",  "model": MODEL_GEMINI_PRO,    "label": f"Gemini ({MODEL_GEMINI_PRO})"},
    "gpt":          {"cli": "codex",   "model": None,                "label": "GPT (codex)"},
    "codex":        {"cli": "codex",   "model": None,                "label": "GPT (codex)"},
    "sonnet":       {"cli": "claude",  "model": MODEL_CLAUDE_SONNET, "label": f"Claude ({MODEL_CLAUDE_SONNET})"},
    "opus":         {"cli": "claude",  "model": MODEL_CLAUDE_OPUS,   "label": f"Claude ({MODEL_CLAUDE_OPUS})"},
    "haiku":        {"cli": "claude",  "model": MODEL_CLAUDE_HAIKU,  "label": f"Claude ({MODEL_CLAUDE_HAIKU})"},
}

# ── Role defaults ─────────────────────────────────────────────────────────────
# Change these to permanently reassign which LLM handles each role.

DEFAULT_ORCHESTRATOR = "sonnet"
DEFAULT_BACKEND      = "gemini"
DEFAULT_FRONTEND     = "gpt"
DEFAULT_MOBILE       = "haiku"


def _resolve_agent(key, default: str) -> dict:
    k = (key or default).lower()
    if k not in AGENTS:
        raise SystemExit(f"Unknown agent '{k}'. Available: {', '.join(AGENTS)}")
    return {**AGENTS[k], "key": k}


# ── Runner ────────────────────────────────────────────────────────────────────

def run_agent(label: str, cmd: list) -> tuple:
    print(f"\n{'='*60}")
    print(f"  [{label}]")
    print(f"{'='*60}\n")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    lines = []
    for line in (proc.stdout or []):
        print(line, end="", flush=True)
        lines.append(line)
    proc.wait()
    if proc.returncode != 0:
        print(f"\n  x {label} exited with code {proc.returncode}")
    return "".join(lines), proc.returncode


def run_worker(role: str, agent: dict, prompt: str) -> str:
    label = f"{agent['label']} — {role.capitalize()}"
    if agent["cli"] == "gemini":
        cmd = ["gemini", "-m", agent["model"], "-y", "-p", prompt]
    elif agent["cli"] == "codex":
        cmd = ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox", prompt]
    elif agent["cli"] == "claude":
        cmd = ["claude", "-p", prompt, "--model", agent["model"]]
    else:
        raise SystemExit(f"Unknown CLI type: {agent['cli']}")
    output, _ = run_agent(label, cmd)
    return output


# ── Handoff helpers ───────────────────────────────────────────────────────────

def get_feature(handoff: str) -> str:
    for line in handoff.splitlines():
        if line.startswith("> Feature:"):
            return line.replace("> Feature:", "").strip()
    return "Unknown"


def has_revision_tasks(handoff: str) -> bool:
    return "## Revision Tasks" in handoff


def get_revision_count(handoff: str) -> int:
    """Count how many revision cycles have already run."""
    return handoff.count("## Agent Reports (revision")


# ── Report parser ─────────────────────────────────────────────────────────────

def parse_report(output: str) -> dict:
    report = {k: "none" for k in ["files_written", "features_added", "fixes_applied", "framework_changes", "issues"]}
    in_report = False
    for line in output.splitlines():
        if "### AGENT REPORT" in line:
            in_report = True
            continue
        if in_report:
            m = re.match(r"-\s+(\w+):\s*(.+)", line.strip())
            if m and m.group(1) in report:
                report[m.group(1)] = m.group(2).strip()
    return report


def parse_codex_tokens(output: str) -> int:
    """Parse 'tokens used\\n<number>' from codex CLI output. Returns total as int."""
    lines = output.splitlines()
    for i, line in enumerate(lines):
        if line.strip().lower() == "tokens used" and i + 1 < len(lines):
            try:
                # Codex outputs with dot as thousands separator (e.g. "1.470" = 1470)
                raw = lines[i + 1].strip().replace(".", "").replace(",", "")
                return int(raw)
            except ValueError:
                pass
    return 0


# ── Doc writers ───────────────────────────────────────────────────────────────

def _append(path: Path, text: str):
    with open(path, "a") as f:
        f.write("\n" + text)


def update_docs(br: dict, fr: dict, feature: str, backend_label: str, frontend_label: str,
                is_revision: bool = False, mr: "dict | None" = None, mobile_label: str = ""):
    label = f"{feature} — revision ({DATE})" if is_revision else f"{feature} ({DATE})"
    bl, fl = f"[{backend_label}]", f"[{frontend_label}]"
    ml = f"[{mobile_label}]" if mobile_label else "[Mobile]"

    feats = []
    if br["features_added"] != "none":
        feats.append(f"  - {bl} {br['features_added']}")
    if fr["features_added"] != "none":
        feats.append(f"  - {fl} {fr['features_added']}")
    if mr and mr["features_added"] != "none":
        feats.append(f"  - {ml} {mr['features_added']}")
    if feats:
        _append(FEATURE_FILE, f"\n## {label}\n" + "\n".join(feats) + "\n")
        print("  + feature.md updated")

    fixes = []
    if br["fixes_applied"] != "none":
        fixes.append(f"  - {bl} {br['fixes_applied']}")
    if fr["fixes_applied"] != "none":
        fixes.append(f"  - {fl} {fr['fixes_applied']}")
    if mr and mr["fixes_applied"] != "none":
        fixes.append(f"  - {ml} {mr['fixes_applied']}")
    if fixes:
        _append(FIX_FILE, f"\n## {label}\n" + "\n".join(fixes) + "\n")
        print("  + fix.md updated")

    fw = []
    if br["framework_changes"] != "none":
        fw.append(f"  - {bl} {br['framework_changes']}")
    if fr["framework_changes"] != "none":
        fw.append(f"  - {fl} {fr['framework_changes']}")
    if mr and mr["framework_changes"] != "none":
        fw.append(f"  - {ml} {mr['framework_changes']}")
    if fw:
        _append(ARAS_FILE, f"\n---\n## Framework Change: {label}\n" + "\n".join(fw) + "\n")
        print("  + aras.md updated (framework change)")

    rev_label = f"revision ({DATE})" if is_revision else DATE
    mobile_section = ""
    if mr:
        mobile_section = (
            f"### Mobile ({mobile_label})\n"
            f"- files_written: {mr['files_written']}\n"
            f"- features_added: {mr['features_added']}\n"
            f"- fixes_applied: {mr['fixes_applied']}\n"
            f"- framework_changes: {mr['framework_changes']}\n"
            f"- issues: {mr['issues']}\n\n"
        )
    summary = (
        f"\n---\n## Agent Reports ({rev_label})\n\n"
        f"### Backend ({backend_label})\n"
        f"- files_written: {br['files_written']}\n"
        f"- features_added: {br['features_added']}\n"
        f"- fixes_applied: {br['fixes_applied']}\n"
        f"- framework_changes: {br['framework_changes']}\n"
        f"- issues: {br['issues']}\n\n"
        f"### Frontend ({frontend_label})\n"
        f"- files_written: {fr['files_written']}\n"
        f"- features_added: {fr['features_added']}\n"
        f"- fixes_applied: {fr['fixes_applied']}\n"
        f"- framework_changes: {fr['framework_changes']}\n"
        f"- issues: {fr['issues']}\n\n"
        + mobile_section +
        f"## Claude Review\n"
        f"- verdict: <!-- APPROVED / NEEDS-FIX -->\n"
        f"- reviewed_by: Claude Code\n"
        f"- date: <!-- fill -->\n"
        f"- notes: <!-- none or describe -->\n\n"
        f"## Revision Tasks\n"
        f"<!-- If verdict is NEEDS-FIX, list tasks here then re-run multi_agent.py -->\n"
        f"<!-- Delete this section if APPROVED -->\n"
    )
    _append(HANDOFF_FILE, summary)
    print("  + handoff.md updated with agent reports + Claude Review template")


# ── Terminal summary ──────────────────────────────────────────────────────────

def _print_summary(br: dict, fr: dict, backend_label: str, frontend_label: str,
                   mr: "dict | None" = None, mobile_label: str = ""):
    print(f"\n{'='*60}")
    print("  RUN SUMMARY")
    print(f"{'='*60}")
    rows = [(backend_label[:12].ljust(12), br), (frontend_label[:12].ljust(12), fr)]
    if mr:
        rows.append(((mobile_label or "Mobile")[:12].ljust(12), mr))
    for lbl, r in rows:
        print(f"  {lbl} files   : {r['files_written']}")
        print(f"  {lbl} features: {r['features_added']}")
        print(f"  {lbl} fixes   : {r['fixes_applied']}")
        print(f"  {lbl} fw      : {r['framework_changes']}")
        print(f"  {lbl} issues  : {r['issues']}")
        print(f"  {'─'*56}")
    print(f"{'='*60}\n")


# ── DB helpers ────────────────────────────────────────────────────────────────

def _get_token() -> str:
    login = requests.post(
        "http://localhost:8000/api/v1/auth/token",
        data={"username": "admin", "password": "admin"},
        timeout=5,
    )
    if login.status_code != 200:
        raise RuntimeError("Login failed")
    return login.json()["access_token"]


def _persist_new(mode: str, handoff: str, backend_out: str, frontend_out: str, br: dict, fr: dict,
                 backend_label: str = "", frontend_label: str = "") -> int:
    """Create a new DB record. Returns the record id."""
    feature = get_feature(handoff)
    bl = backend_label or "Backend"
    fl = frontend_label or "Frontend"
    payload = {
        "feature": feature,
        "mode": mode,
        "status": "success",
        "run_date": datetime.now(timezone.utc).isoformat(),
        "prompt_md": handoff,
        "backend_files": br["files_written"],
        "frontend_files": fr["files_written"],
        "output_md": f"## Backend Output ({bl})\n{backend_out}\n\n## Frontend Output ({fl})\n{frontend_out}",
        "issues": " | ".join(x for x in [br["issues"], fr["issues"]] if x != "none"),
        "gemini_prompt_tokens": 0, "gemini_completion_tokens": 0,
        "gpt_prompt_tokens": parse_codex_tokens(frontend_out), "gpt_completion_tokens": 0,
        "total_tokens": parse_codex_tokens(frontend_out),
        "total_requests": 2,
        "revision_count": 0,
    }
    try:
        token = _get_token()
        res = requests.post(
            "http://localhost:8000/api/v1/dev/dev_handoff_runs",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if res.status_code in (200, 201):
            run_id = res.json().get("id")
            print(f"  + Run persisted to DB (id={run_id})")
            return run_id
        else:
            print(f"  x Failed to persist: {res.status_code} {res.text[:200]}")
    except Exception as e:
        print(f"  x Could not persist (API offline?): {e}")
    return -1


def _patch_run(run_id: int, patch: dict):
    """PATCH an existing DB record (for revisions + Claude review)."""
    if run_id < 0:
        return
    try:
        token = _get_token()
        res = requests.patch(
            f"http://localhost:8000/api/v1/dev/dev_handoff_runs/{run_id}",
            json=patch,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if res.status_code in (200, 201):
            print(f"  + DB record {run_id} updated")
        else:
            print(f"  x PATCH failed: {res.status_code} {res.text[:200]}")
    except Exception as e:
        print(f"  x Could not update DB (API offline?): {e}")


def _parse_claude_review(handoff: str) -> dict:
    """Extract verdict + notes from ## Claude Review in handoff.md."""
    verdict = notes = ""
    in_review = False
    for line in handoff.splitlines():
        if line.strip() == "## Claude Review":
            in_review = True
            continue
        if in_review:
            if line.startswith("##"):
                break
            if "verdict:" in line:
                verdict = line.split("verdict:")[-1].strip().lstrip("<!-").rstrip("->").strip()
            if "notes:" in line:
                notes = line.split("notes:")[-1].strip().lstrip("<!-").rstrip("->").strip()
    return {"verdict": verdict, "notes": notes}


# ── Main run logic ────────────────────────────────────────────────────────────

def run_agents(args, handoff: str, is_revision: bool = False) -> tuple:
    empty = {k: "none" for k in ["files_written", "features_added", "fixes_applied", "framework_changes", "issues"]}
    br = fr = mr = empty.copy()
    backend_out = frontend_out = mobile_out = ""

    b_agent = _resolve_agent(getattr(args, "backend",  None), DEFAULT_BACKEND)
    f_agent = _resolve_agent(getattr(args, "frontend", None), DEFAULT_FRONTEND)
    m_agent = _resolve_agent(getattr(args, "mobile",   None), DEFAULT_MOBILE)

    mobile_only  = getattr(args, "mobile_only",  False)
    frontend_only = getattr(args, "frontend_only", False)
    backend_only  = getattr(args, "backend_only",  False)

    if mobile_only:
        mobile_out = run_worker("mobile", m_agent, MOBILE_SYSTEM + handoff)
        mr = parse_report(mobile_out)
    elif frontend_only:
        frontend_out = run_worker("frontend", f_agent, FRONTEND_SYSTEM + handoff)
        fr = parse_report(frontend_out)
    elif backend_only:
        backend_out = run_worker("backend", b_agent, BACKEND_SYSTEM + handoff)
        br = parse_report(backend_out)
    else:
        backend_out = run_worker("backend", b_agent, BACKEND_SYSTEM + handoff)
        br = parse_report(backend_out)
        frontend_out = run_worker("frontend", f_agent, FRONTEND_SYSTEM + handoff)
        fr = parse_report(frontend_out)
        if _has_mobile_tasks(handoff):
            mobile_out = run_worker("mobile", m_agent, MOBILE_SYSTEM + handoff)
            mr = parse_report(mobile_out)

    mr_out = mr if any(v != "none" for v in mr.values()) else None
    _print_summary(br, fr, b_agent["label"], f_agent["label"], mr_out, m_agent["label"])
    update_docs(br, fr, get_feature(handoff), b_agent["label"], f_agent["label"],
                is_revision=is_revision, mr=mr_out, mobile_label=m_agent["label"])
    return backend_out, frontend_out, br, fr, b_agent["label"], f_agent["label"], mobile_out, mr, m_agent["label"]


def _has_mobile_tasks(handoff: str) -> bool:
    """Return True if handoff contains a non-empty ## Mobile Tasks section."""
    import re
    m = re.search(r"##\s+Mobile Tasks\s*\n(.*?)(?=\n##|\Z)", handoff, re.DOTALL)
    if not m:
        return False
    body = m.group(1).strip()
    return bool(body) and body.lower() != "none"


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    keys = ", ".join(AGENTS)
    parser = argparse.ArgumentParser(description="aras multi-agent — reads docs/handoff.md")
    parser.add_argument("--backend-only",  action="store_true")
    parser.add_argument("--frontend-only", action="store_true")
    parser.add_argument("--mobile-only",   action="store_true")
    parser.add_argument("-b", "--backend",      metavar="AGENT", default=None,
                        help=f"Backend agent key (default: {DEFAULT_BACKEND}). Options: {keys}")
    parser.add_argument("-f", "--frontend",     metavar="AGENT", default=None,
                        help=f"Frontend agent key (default: {DEFAULT_FRONTEND}). Options: {keys}")
    parser.add_argument("-m", "--mobile",       metavar="AGENT", default=None,
                        help=f"Mobile agent key (default: {DEFAULT_MOBILE}). Options: {keys}")
    parser.add_argument("-o", "--orchestrator", metavar="AGENT", default=None,
                        help=f"Orchestrator agent key (default: {DEFAULT_ORCHESTRATOR}, informational). Options: {keys}")
    parser.add_argument("--test", metavar="PROMPT", help="Smoke-test both CLIs")
    parser.add_argument("--submit-review", action="store_true",
                        help="Parse ## Claude Review from handoff.md and PATCH verdict to DB")
    parser.add_argument("--log-manual", nargs="+", metavar="KEY=VALUE",
                        help="Log a manual/direct change to docs/feature.md and DB. "
                             "Keys: feature, author, mode, files, features, fixes, framework, issues, notes")
    args = parser.parse_args()

    if args.test:
        b = _resolve_agent(args.backend, DEFAULT_BACKEND)
        f = _resolve_agent(args.frontend, DEFAULT_FRONTEND)
        run_worker("backend",  b, BACKEND_SYSTEM  + args.test)
        run_worker("frontend", f, FRONTEND_SYSTEM + args.test)
        return

    if args.log_manual:
        data = _parse_kv_args(args.log_manual)
        _log_manual_to_docs(data)
        _persist_manual(data)
        return

    if args.submit_review:
        if not HANDOFF_FILE.exists():
            print(f"ERROR: {HANDOFF_FILE} not found.")
            sys.exit(1)
        handoff = HANDOFF_FILE.read_text()
        review = _parse_claude_review(handoff)
        run_id = _get_run_id_from_handoff(handoff)
        _patch_run(run_id, {
            "claude_verdict": review["verdict"],
            "claude_review": review["notes"],
        })
        print(f"  + Claude review submitted: verdict={review['verdict']}")
        return

    if not HANDOFF_FILE.exists():
        print(f"ERROR: {HANDOFF_FILE} not found.")
        sys.exit(1)

    handoff = HANDOFF_FILE.read_text()
    feature = get_feature(handoff)
    is_revision = has_revision_tasks(handoff)
    rev_num = get_revision_count(handoff)
    mode = (
        "mobile-only"   if args.mobile_only else
        "backend-only"  if args.backend_only else
        "frontend-only" if args.frontend_only else
        "full"
    )

    b_agent = _resolve_agent(args.backend,  DEFAULT_BACKEND)
    f_agent = _resolve_agent(args.frontend, DEFAULT_FRONTEND)
    m_agent = _resolve_agent(args.mobile,   DEFAULT_MOBILE)
    o_agent = _resolve_agent(args.orchestrator, DEFAULT_ORCHESTRATOR)

    print(f"\n{'='*60}")
    print(f"  Handoff      : {HANDOFF_FILE}")
    print(f"  Feature      : {feature}")
    print(f"  Mode         : {mode}")
    print(f"  Revision     : {'yes #' + str(rev_num + 1) if is_revision else 'no (initial run)'}")
    print(f"  Orchestrator : {o_agent['label']}")
    print(f"  Backend      : {b_agent['label']}")
    print(f"  Frontend     : {f_agent['label']}")
    print(f"  Mobile       : {m_agent['label']}")
    print(f"{'='*60}")

    backend_out, frontend_out, br, fr, b_label, f_label, mobile_out, mr, m_label = run_agents(args, handoff, is_revision=is_revision)

    all_issues = " | ".join(x for x in [br["issues"], fr["issues"], mr["issues"]] if x != "none")

    if is_revision:
        run_id = _get_run_id_from_handoff(handoff)
        _patch_run(run_id, {
            "revision_count": rev_num + 1,
            "output_md": (
                f"## Revision {rev_num + 1} — Backend ({b_label})\n{backend_out}\n\n"
                f"## Revision {rev_num + 1} — Frontend ({f_label})\n{frontend_out}\n\n"
                f"## Revision {rev_num + 1} — Mobile ({m_label})\n{mobile_out}"
            ),
            "issues": all_issues,
        })
    else:
        run_id = _persist_new(mode, handoff, backend_out, frontend_out, br, fr, b_label, f_label)
        _inject_run_id(run_id)

    print("=" * 60)
    print(f"  NEXT: tell Claude Code: rhf")
    print("=" * 60)


def _get_run_id_from_handoff(handoff: str) -> int:
    for line in handoff.splitlines():
        if line.startswith("> run_id:"):
            try:
                return int(line.replace("> run_id:", "").strip())
            except ValueError:
                pass
    return -1


def _inject_run_id(run_id: int):
    if run_id < 0:
        return
    content = HANDOFF_FILE.read_text()
    lines = content.split("\n", 1)
    new_content = lines[0] + f"\n> run_id: {run_id}" + ("\n" + lines[1] if len(lines) > 1 else "")
    HANDOFF_FILE.write_text(new_content)
    print(f"  + run_id {run_id} injected into handoff.md")


def _persist_manual(data: dict) -> int:
    """POST a manual/direct change record to dev_handoff_runs (same table, mode=manual)."""
    payload = {
        "feature": data.get("feature", "manual change"),
        "author":  data.get("author", "Claude Code"),
        "mode":    data.get("mode", "claude-direct"),   # manual | claude-direct | human-direct
        "status":  "done",
        "run_date": datetime.now(timezone.utc).isoformat(),
        "backend_files":    data.get("files", "none"),
        "frontend_files":   "none",
        "features_added":   data.get("features", "none"),
        "fixes_applied":    data.get("fixes", "none"),
        "framework_changes": data.get("framework", "none"),
        "issues":  data.get("issues", "none"),
        "notes":   data.get("notes", ""),
        "total_requests": 0,
        "revision_count": 0,
    }
    try:
        token = _get_token()
        res = requests.post(
            "http://localhost:8000/api/v1/dev/dev_handoff_runs",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if res.status_code in (200, 201):
            run_id = res.json().get("id")
            print(f"  + Manual run persisted to DB (id={run_id})")
            return run_id
        else:
            print(f"  x Failed to persist manual run: {res.status_code} {res.text[:200]}")
    except Exception as e:
        print(f"  x Could not persist (API offline?): {e}")
    return -1


def _log_manual_to_docs(data: dict):
    """Append manual change to feature.md / fix.md."""
    label = f"{data.get('feature', 'manual')} ({DATE})"
    author = data.get("author", "Claude Code")

    feats = data.get("features", "none")
    if feats != "none":
        _append(FEATURE_FILE, f"\n## {label}\n  - [{author}] {feats}\n")
        print("  + feature.md updated")

    fixes = data.get("fixes", "none")
    if fixes != "none":
        _append(FIX_FILE, f"\n## {label}\n  - [{author}] {fixes}\n")
        print("  + fix.md updated")

    fw = data.get("framework", "none")
    if fw != "none":
        _append(ARAS_FILE, f"\n---\n## Framework Change: {label}\n  - [{author}] {fw}\n")
        print("  + aras.md updated (framework change)")


def _parse_kv_args(kv_list: list) -> dict:
    """Parse ['feature=Foo bar', 'files=a.py,b.py'] → dict."""
    result = {}
    for item in kv_list:
        if "=" in item:
            k, v = item.split("=", 1)
            result[k.strip()] = v.strip()
    return result


if __name__ == "__main__":
    main()
