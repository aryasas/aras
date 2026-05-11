"""
agent_runtime.py — Claude Agent SDK wrapper for aras agents.

Single source of truth for invoking Claude from any aras agent.
Authenticates via the user's Claude Pro/Max subscription (Claude Code CLI),
NOT via API key. Falls back to anthropic SDK only if explicitly forced via
ARAS_AGENT_BACKEND=anthropic + ANTHROPIC_API_KEY set.

Usage:
    from arasCore.lib.agent_runtime import run_agent

    result = run_agent(
        task="Build an invoice form",
        system_prompt="You are a senior Flask developer...",
        allowed_tools=["Read", "Write", "Bash"],
        cwd="/Users/aras/Dev/aras",
    )
"""
import os
from typing import Iterable, Optional

# Backend selection: 'sdk' (default, uses Pro/Max) or 'anthropic' (API key).
_BACKEND = os.getenv("ARAS_AGENT_BACKEND", "sdk").lower()


def _run_sdk(task, system_prompt, allowed_tools, cwd, model):
    """Invoke via claude-agent-sdk (Pro/Max subscription auth)."""
    try:
        from claude_agent_sdk import query, ClaudeAgentOptions
    except ImportError as e:
        raise RuntimeError(
            "claude-agent-sdk not installed. Run: pip install claude-agent-sdk\n"
            "Also requires Claude Code CLI: https://claude.ai/code"
        ) from e

    opts = ClaudeAgentOptions(
        system_prompt=system_prompt,
        allowed_tools=list(allowed_tools) if allowed_tools else None,
        cwd=cwd,
        model=model,
    )

    chunks = []
    import asyncio

    async def _run():
        async for msg in query(prompt=task, options=opts):
            text = _extract_text(msg)
            if text:
                chunks.append(text)

    asyncio.run(_run())
    return "\n".join(chunks)


def _extract_text(msg):
    """Pull text content from an SDK message of any shape."""
    if hasattr(msg, "content"):
        parts = []
        for block in msg.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts)
    if isinstance(msg, dict):
        return msg.get("text") or msg.get("content") or ""
    return str(msg) if msg else ""


def _run_anthropic(task, system_prompt, allowed_tools, cwd, model):
    """Fallback: anthropic SDK with API key. Tools must be pre-registered server-side."""
    try:
        import anthropic
    except ImportError as e:
        raise RuntimeError("anthropic package not installed.") from e

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ARAS_AGENT_BACKEND=anthropic requires ANTHROPIC_API_KEY.")

    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model or "claude-sonnet-4-5",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": task}],
    )
    return "".join(b.text for b in resp.content if hasattr(b, "text"))


def run_agent(
    task: str,
    system_prompt: str,
    allowed_tools: Optional[Iterable[str]] = None,
    cwd: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    Run a Claude agent and return its final text output.

    Args:
        task: User-facing task description.
        system_prompt: System prompt defining the agent's role.
        allowed_tools: Names of tools the agent may call (e.g. ['Read', 'Write']).
        cwd: Working directory; defaults to project root.
        model: Override model. Default lets the SDK/CLI choose.
    """
    cwd = cwd or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _BACKEND == "anthropic":
        return _run_anthropic(task, system_prompt, allowed_tools, cwd, model)
    return _run_sdk(task, system_prompt, allowed_tools, cwd, model)


def is_dev_mode() -> bool:
    """Check ARAS_MODE; agents must refuse to run outside development."""
    return os.getenv("ARAS_MODE", "production").lower() == "development"
