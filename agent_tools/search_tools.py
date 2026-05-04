import os


def search_codebase(keyword: str, directory: str = ".") -> str:
    """Search for a keyword across all .py and .html files in the project."""
    matches = []
    for root, _, files in os.walk(directory):
        for fname in files:
            if fname.endswith((".py", ".html", ".css")):
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        for i, line in enumerate(f, 1):
                            if keyword.lower() in line.lower():
                                matches.append(f"{fpath}:{i}: {line.rstrip()}")
                except Exception:
                    pass
    if not matches:
        return f"No matches found for '{keyword}'"
    return "\n".join(matches[:50])
