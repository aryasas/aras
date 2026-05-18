"""Generic agent test runner.

Sends a test prompt to gemini, codex, or both and prints their output.
The prompt can come from a file or be passed directly on the command line.

Usage:
    # From a prompt file
    python tools/agent_test.py --agent gemini --file tools/tests/test_trash.txt

    # Inline prompt
    python tools/agent_test.py --agent gemini --prompt "Test the /deleted endpoint..."

    # Both agents (run sequentially)
    python tools/agent_test.py --agent both --file tools/tests/test_api.txt

    # Pass extra params to the prompt file via key=value pairs
    python tools/agent_test.py --agent gemini --file tools/tests/test_trash.txt BASE_URL=http://0.0.0.0:8000

Options:
    --agent   gemini | codex | both  (default: gemini)
    --file    path to a .txt prompt file
    --prompt  inline prompt string
    --model   gemini model alias: flash | pro  (default: flash)
    --        any key=value pairs after -- are substituted into the prompt as {KEY}
"""

import argparse
import subprocess
import sys
from pathlib import Path


GEMINI_ALIASES = {
    "flash":      "gemini-2.5-flash",
    "pro":        "gemini-2.5-pro",
}
GEMINI_DEFAULT = "gemini-2.5-flash"


def _resolve_model(alias: str) -> str:
    return GEMINI_ALIASES.get((alias or "").lower(), alias or GEMINI_DEFAULT)


def _run(label: str, cmd: list) -> int:
    print(f"\n{'='*60}")
    print(f"  [{label}]")
    print(f"{'='*60}\n")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in (proc.stdout or []):
        print(line, end="", flush=True)
    proc.wait()
    if proc.returncode != 0:
        print(f"\n  x {label} exited with code {proc.returncode}")
    else:
        print(f"\n  + {label} completed successfully")
    return proc.returncode


def run_gemini(prompt: str, model: str) -> int:
    return _run(f"Gemini ({model})", ["gemini", "-m", model, "-y", "-p", prompt])


def run_codex(prompt: str) -> int:
    return _run("Codex GPT-5.5", [
        "codex", "exec", "--dangerously-bypass-approvals-and-sandbox", prompt
    ])


def load_prompt(args) -> str:
    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"Error: prompt file not found: {path}", file=sys.stderr)
            sys.exit(1)
        prompt = path.read_text()
    elif args.prompt:
        prompt = args.prompt
    else:
        print("Error: provide --file or --prompt", file=sys.stderr)
        sys.exit(1)

    # Substitute key=value pairs from --params
    for kv in (args.params or []):
        if "=" in kv:
            k, v = kv.split("=", 1)
            prompt = prompt.replace(f"{{{k}}}", v)

    return prompt


def main():
    parser = argparse.ArgumentParser(description="Generic agent test runner")
    parser.add_argument("--agent", default="gemini",
                        choices=["gemini", "codex", "both"],
                        help="Which agent to run (default: gemini)")
    parser.add_argument("--file", metavar="PATH",
                        help="Path to a .txt file containing the test prompt")
    parser.add_argument("--prompt", metavar="TEXT",
                        help="Inline prompt string")
    parser.add_argument("--model", default="flash",
                        help="Gemini model alias: flash | pro (default: flash)")
    parser.add_argument("params", nargs="*", metavar="KEY=VALUE",
                        help="Variable substitutions applied to the prompt: BASE_URL=http://...")
    args = parser.parse_args()

    prompt = load_prompt(args)
    model = _resolve_model(args.model)

    codes = []
    if args.agent in ("gemini", "both"):
        codes.append(run_gemini(prompt, model))
    if args.agent in ("codex", "both"):
        codes.append(run_codex(prompt))

    sys.exit(max(codes) if codes else 0)


if __name__ == "__main__":
    main()
