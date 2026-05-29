import re
import unicodedata

# claude-opus-4-7
def to_label_case(name: str) -> str:
    """
    Converts a snake_case string to Label Case (e.g., 'created_at' -> 'Created At').
    """
    return name.replace("_", " ").title()

# gemini-2-5-flash
def slugify(value: str) -> str:
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)
