# claude-opus-4-8
# Guard against silent CSP/index.html drift: the security-headers middleware allows the inline
# theme-bootstrap script in ui/index.html via a sha256 hash. If someone edits that script (or adds
# an attribute to its <script> tag so the extractor regex stops matching), the hash silently goes
# None and the script is BLOCKED in production -> white-screen FOUC bug. This test makes that
# failure loud at CI time instead.
import re
from core.api.middleware.security_headers import _get_ui_inline_script_hash


# claude-opus-4-8
def test_inline_theme_script_hash_is_resolvable():
    """The CSP middleware must be able to hash the index.html inline script."""
    h = _get_ui_inline_script_hash()
    assert h is not None, (
        "CSP cannot hash the inline <script> in ui/index.html — the extractor regex did not match. "
        "Did someone add an attribute to the <script> tag or move the script? "
        "Either keep it a bare `<script>...</script>` or move it to an external /theme-init.js "
        "(covered by script-src 'self')."
    )
    assert re.fullmatch(r"'sha256-[A-Za-z0-9+/]+=*'", h), f"unexpected hash format: {h}"
