# gemini-flash
from dataclasses import dataclass, field
from typing import List, Optional, Any, Callable, Tuple
from .base_registry import Registry

@dataclass
class ConfigField:
    key: str
    type: str  # "string" | "text" | "number" | "bool" | "choice" | "color" | "image" | "secret" | "list"
    default: Any = None
    label: str = ""
    required: bool = False
    validator: Optional[Callable[[Any], bool]] = None
    help: str = ""
    depends_on: Optional[str] = None
    secret: bool = False
    choices: Optional[List[Tuple[str, str]]] = None
    resource: Optional[str] = None  # for type="resource": e.g. "config/currencies"

@dataclass
class ConfigSection:
    key: str
    label: str
    icon: str = "Settings"
    order: int = 100
    scope: str = "module"  # "core" | "module" | "shared" | "feature"
    fields: List[ConfigField] = field(default_factory=list)
    setup_step: Optional[int] = None
    required_by: Tuple[str, ...] = ()
    extends: Optional[str] = None
    read_hook: Optional[Callable] = None
    write_hook: Optional[Callable] = None
    hidden: bool = False
    # When True, the section accepts arbitrary field keys not declared in `fields`
    # (e.g. core_config.numbering, whose keys are document series seeded at runtime).
    dynamic: bool = False

class ConfigRegistry(Registry[ConfigSection]):
    """Registry for configuration sections and fields."""
    
    def register_section(self, app_name: str, section: ConfigSection):
        self.register(app_name, section.key, section)

    def by_scope(self, scope: str) -> List[ConfigSection]:
        return [s for s in self.all() if s.scope == scope]

    def register_from_manifest(self, app_name: str, manifest: dict):
        sections = manifest.get("config_sections", [])
        for section in sections:
            if isinstance(section, dict):
                # Convert dict fields to ConfigField objects if necessary
                fields = []
                for f in section.get("fields", []):
                    if isinstance(f, dict):
                        fields.append(ConfigField(**f))
                    else:
                        fields.append(f)
                section_obj = ConfigSection(
                    key=section["key"],
                    label=section["label"],
                    icon=section.get("icon", "Settings"),
                    order=section.get("order", 100),
                    scope=section.get("scope", "module"),
                    fields=fields,
                    setup_step=section.get("setup_step"),
                    required_by=section.get("required_by", ()),
                    extends=section.get("extends"),
                    read_hook=section.get("read_hook"),
                    write_hook=section.get("write_hook"),
                    hidden=section.get("hidden", False)
                )
                self.register_section(app_name, section_obj)
            elif isinstance(section, ConfigSection):
                self.register_section(app_name, section)

# Singleton instance
config_registry = ConfigRegistry()
