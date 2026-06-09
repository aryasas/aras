# claude-opus-4-7
"""Framework-level config sections registered under the 'core' namespace.

Imported at startup so the Settings page always shows the Framework namespace
regardless of whether `python manage.py sync` has been run yet.
"""
from .config_registry import config_registry, ConfigSection, ConfigField

CORE_SECTIONS = [
    ConfigSection(key="general", label="General", scope="core", level="system", fields=[
        ConfigField(key="site_name", type="string", default="Aras", label="Site Name"),
        ConfigField(key="site_url", type="string", default="http://localhost:5173", label="Public Site URL"),
        ConfigField(key="support_email", type="string", default="support@aras.local", label="Support Email"),
        ConfigField(key="default_language", type="choice", default="en", label="Default Language",
                    choices=[("en", "English"), ("id", "Indonesian")]),
        ConfigField(key="default_timezone", type="string", default="UTC", label="Default Timezone"),
        ConfigField(key="default_date_format", type="string", default="YYYY-MM-DD", label="Date Format"),
        ConfigField(key="default_time_format", type="choice", default="24h", label="Time Format",
                    choices=[("12h", "12-hour"), ("24h", "24-hour")]),
        ConfigField(key="default_number_format", type="string", default="#,###.##", label="Number Format"),
        ConfigField(key="first_day_of_week", type="choice", default="1", label="First Day of Week",
                    choices=[("0", "Sunday"), ("1", "Monday")]),
        # Default currency/timezone of the instance derive from the `is_default` row of
        # core_organizations — not stored here, to avoid duplicating per-org identity.
        ConfigField(key="default_currency", type="string", default="USD", label="Fallback Currency (ISO)",
                    help="Used only before any organization is configured."),
    ]),
    ConfigSection(key="email", label="Email", scope="core", level="system", fields=[
        ConfigField(key="backend", type="choice", default="console", label="Backend",
                    choices=[("console", "Console (dev)"), ("smtp", "SMTP"), ("resend", "Resend")]),
        ConfigField(key="from_address", type="string", label="From Address"),
        ConfigField(key="from_name", type="string", label="From Name"),
        ConfigField(key="smtp_host", type="string", label="SMTP Host"),
        ConfigField(key="smtp_port", type="number", default=587, label="SMTP Port"),
        ConfigField(key="smtp_user", type="string", label="SMTP Username"),
        ConfigField(key="smtp_password", type="secret", label="SMTP Password", secret=True),
        ConfigField(key="smtp_use_tls", type="bool", default=True, label="Use TLS"),
        ConfigField(key="resend_api_key", type="secret", label="Resend API Key", secret=True),
    ]),
    ConfigSection(key="branding", label="Branding", scope="core", level="system", fields=[
        ConfigField(key="primary_color", type="color", default="#4f46e5", label="Primary Color"),
        ConfigField(key="accent_color", type="color", default="#06b6d4", label="Accent Color"),
        ConfigField(key="logo_url", type="image", label="Logo URL"),
        ConfigField(key="logo_dark_url", type="image", label="Dark-Mode Logo URL"),
        ConfigField(key="favicon_url", type="image", label="Favicon URL"),
        ConfigField(key="login_background_url", type="image", label="Login Background URL"),
        ConfigField(key="default_theme", type="choice", default="system", label="Default Theme",
                    choices=[("light", "Light"), ("dark", "Dark"), ("system", "System")]),
    ]),
    ConfigSection(key="uploads", label="Uploads & Storage", scope="core", level="system", fields=[
        ConfigField(key="storage_backend", type="choice", default="local", label="Storage Backend",
                    choices=[("local", "Local Filesystem"), ("s3", "Amazon S3"), ("gcs", "Google Cloud Storage")]),
        ConfigField(key="max_upload_mb", type="number", default=10, label="Max Upload Size (MB)"),
        ConfigField(key="allowed_extensions", type="text", default="png,jpg,jpeg,gif,pdf,xlsx,csv,docx",
                    label="Allowed Extensions", help="Comma-separated"),
        ConfigField(key="s3_bucket", type="string", label="S3 Bucket"),
        ConfigField(key="s3_region", type="string", label="S3 Region"),
        ConfigField(key="s3_access_key", type="string", label="S3 Access Key ID"),
        ConfigField(key="s3_secret_key", type="secret", label="S3 Secret Access Key", secret=True),
    ]),
    ConfigSection(key="notifications", label="Notifications", scope="core", level="system", fields=[
        ConfigField(key="enable_email_notifications", type="bool", default=True, label="Enable Email Notifications"),
        ConfigField(key="enable_in_app_notifications", type="bool", default=True, label="Enable In-App Notifications"),
        ConfigField(key="enable_websocket", type="bool", default=True, label="Enable WebSocket Push"),
        ConfigField(key="digest_frequency", type="choice", default="daily", label="Digest Frequency",
                    choices=[("off", "Off"), ("hourly", "Hourly"), ("daily", "Daily"), ("weekly", "Weekly")]),
    ]),
    ConfigSection(key="i18n", label="Internationalization", scope="core", level="system", fields=[
        ConfigField(key="enabled_languages", type="text", default="en,id", label="Enabled Languages",
                    help="Comma-separated ISO codes"),
        ConfigField(key="auto_detect_browser_language", type="bool", default=True, label="Auto-Detect Browser Language"),
        ConfigField(key="fallback_language", type="string", default="en", label="Fallback Language"),
    ]),
    ConfigSection(key="developer", label="Developer", scope="core", level="system", fields=[
        ConfigField(key="log_level", type="choice", default="INFO", label="Log Level",
                    choices=[("DEBUG", "Debug"), ("INFO", "Info"), ("WARNING", "Warning"), ("ERROR", "Error")]),
        ConfigField(key="enable_api_docs", type="bool", default=True, label="Enable /docs (Swagger)"),
        ConfigField(key="enable_request_log", type="bool", default=False, label="Log All Requests"),
        ConfigField(key="slow_query_threshold_ms", type="number", default=500, label="Slow Query Threshold (ms)"),
        ConfigField(key="show_traceback_to_user", type="bool", default=False, label="Show Tracebacks to End Users (DEV ONLY)"),
    ]),
    ConfigSection(key="integrations", label="Integrations", scope="core", level="system", fields=[
        ConfigField(key="google_oauth_client_id", type="string", label="Google OAuth Client ID"),
        ConfigField(key="google_oauth_client_secret", type="secret", label="Google OAuth Client Secret", secret=True),
        ConfigField(key="github_oauth_client_id", type="string", label="GitHub OAuth Client ID"),
        ConfigField(key="github_oauth_client_secret", type="secret", label="GitHub OAuth Client Secret", secret=True),
        ConfigField(key="sentry_dsn", type="secret", label="Sentry DSN", secret=True),
        ConfigField(key="posthog_key", type="secret", label="PostHog API Key", secret=True),
        ConfigField(key="webhook_signing_secret", type="secret", label="Webhook Signing Secret", secret=True),
    ]),
    ConfigSection(key="maintenance", label="Maintenance", scope="core", level="system", fields=[
        ConfigField(key="maintenance_mode", type="bool", default=False, label="Maintenance Mode (read-only)"),
        ConfigField(key="maintenance_message", type="text",
                    default="We're performing scheduled maintenance. Back soon.", label="Maintenance Message"),
        ConfigField(key="banner_enabled", type="bool", default=False, label="Show Global Banner"),
        ConfigField(key="banner_text", type="text", label="Banner Text"),
        ConfigField(key="banner_level", type="choice", default="info", label="Banner Level",
                    choices=[("info", "Info"), ("warning", "Warning"), ("critical", "Critical")]),
    ]),
]


def register_core_sections() -> None:
    for section in CORE_SECTIONS:
        config_registry.register_section("core", section)


# Register at import time so any consumer (API, sync) sees them immediately.
register_core_sections()
