# antigravity
from core.registry.config_registry import config_registry, ConfigSection, ConfigField

ADMIN_SECTIONS = [
    ConfigSection(key="security", label="Security", scope="core", level="security", fields=[
        ConfigField(key="session_timeout_minutes", type="number", default=60, label="Session Timeout (minutes)"),
        ConfigField(key="access_token_expire_minutes", type="number", default=30, label="Access Token Expire (minutes)"),
        ConfigField(key="password_reset_expire_minutes", type="number", default=15, label="Password Reset Expire (minutes)"),
        ConfigField(key="enforce_2fa", type="bool", default=False, label="Enforce 2FA for All Users"),
        ConfigField(key="password_min_length", type="number", default=8, label="Password Minimum Length"),
        ConfigField(key="password_require_uppercase", type="bool", default=True, label="Require Uppercase in Password"),
        ConfigField(key="password_require_number", type="bool", default=True, label="Require Number in Password"),
        ConfigField(key="password_require_symbol", type="bool", default=False, label="Require Symbol in Password"),
        ConfigField(key="max_login_attempts", type="number", default=5, label="Max Login Attempts Before Lockout"),
        ConfigField(key="lockout_minutes", type="number", default=15, label="Lockout Duration (minutes)"),
        ConfigField(key="allow_signup", type="bool", default=True, label="Allow Self-Signup"),
        ConfigField(key="rbac_enabled", type="bool", default=True, label="Enforce RBAC"),
        ConfigField(key="cors_origins", type="text", default="http://localhost:5173",
                    label="CORS Allowed Origins", help="Comma-separated list"),
    ]),
    ConfigSection(key="retention", label="Data Retention", scope="core", level="security", fields=[
        ConfigField(key="retention_days", type="number", default=365, label="Audit Log Retention (Days)",
                    help="Number of days to retain system audit logs before cleanup"),
    ]),
]

def register_admin_sections() -> None:
    for section in ADMIN_SECTIONS:
        config_registry.register_section("admin", section)


register_admin_sections()
