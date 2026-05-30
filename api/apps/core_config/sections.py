# gemini-flash
from core.registry.config_registry import ConfigSection, ConfigField

sections = [
    ConfigSection(
        key="core_config.company",
        label="Company",
        icon="Home",
        order=10,
        scope="core",
        fields=[
            ConfigField(key="name", type="string", default="My Workspace", label="Workspace Name"),
            ConfigField(key="legal_name", type="string", label="Legal Name"),
            ConfigField(key="logo", type="image", label="Logo"),
            ConfigField(key="address", type="text", label="Address"),
            ConfigField(key="city", type="string", label="City"),
            ConfigField(key="country", type="string", label="Country"),
            ConfigField(key="tax_id", type="string", label="Tax ID"),
            ConfigField(key="base_currency", type="choice", default="USD", label="Base Currency", 
                        choices=[("USD", "US Dollar"), ("IDR", "Indonesian Rupiah"), ("EUR", "Euro")]),
            ConfigField(key="fiscal_year_start", type="number", default=1, label="Fiscal Year Start (Month)"),
            ConfigField(key="timezone", type="string", default="UTC", label="Timezone"),
            ConfigField(key="locale", type="string", default="en", label="Locale"),
        ]
    ),
    ConfigSection(
        key="core_config.localization",
        label="Localization",
        icon="Globe",
        order=20,
        scope="core",
        fields=[
            ConfigField(key="date_format", type="string", default="YYYY-MM-DD", label="Date Format"),
            ConfigField(key="time_format", type="string", default="HH:mm", label="Time Format"),
            ConfigField(key="number_format", type="string", default="#,###.##", label="Number Format"),
            ConfigField(key="first_day_of_week", type="choice", default="1", label="First Day of Week",
                        choices=[("0", "Sunday"), ("1", "Monday")]),
        ]
    ),
    ConfigSection(
        key="core_config.numbering",
        label="Numbering",
        icon="Hash",
        order=30,
        scope="shared",
        fields=[] # Populated dynamically by apps
    ),
    ConfigSection(
        key="core_config.tax",
        label="Tax",
        icon="Percent",
        order=40,
        scope="shared",
        fields=[
            ConfigField(key="default_tax_rate", type="number", default=0, label="Default Tax Rate (%)"),
            ConfigField(key="tax_inclusive", type="bool", default=False, label="Prices are Tax Inclusive"),
            ConfigField(key="tax_registration_number", type="string", label="Tax Registration Number"),
        ]
    ),
    ConfigSection(
        key="core_config.smtp",
        label="SMTP",
        icon="Mail",
        order=50,
        scope="core",
        fields=[
            ConfigField(key="host", type="string", label="SMTP Host"),
            ConfigField(key="port", type="number", default=587, label="SMTP Port"),
            ConfigField(key="username", type="string", label="Username"),
            ConfigField(key="password", type="secret", label="Password", secret=True),
            ConfigField(key="use_tls", type="bool", default=True, label="Use TLS"),
            ConfigField(key="from_address", type="string", label="From Address"),
            ConfigField(key="from_name", type="string", label="From Name"),
        ]
    ),
    ConfigSection(
        key="core_config.branding",
        label="Branding",
        icon="Palette",
        order=60,
        scope="core",
        fields=[
            ConfigField(key="primary_color", type="color", default="#4f46e5", label="Primary Color"),
            ConfigField(key="accent_color", type="color", default="#06b6d4", label="Accent Color"),
            ConfigField(key="login_logo", type="image", label="Login Logo"),
            ConfigField(key="favicon", type="image", label="Favicon"),
        ]
    ),
    ConfigSection(
        key="core_config.menu",
        label="Menu Order",
        order=999,
        scope="core",
        hidden=True,
        fields=[
            ConfigField(key="order", type="list", default=[], label="Menu Order")
        ]
    )
]
