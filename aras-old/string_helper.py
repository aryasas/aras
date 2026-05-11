"""
ai_string_tools.py
~~~~~~~~~~~~~~~~~~
A collection of AI-inspired utility functions for common string and file
manipulation tasks: rename, search, replace, positional search & replace, etc.
"""

import re
import os
from typing import Union


# ──────────────────────────────────────────────
# 1. RENAME
# ──────────────────────────────────────────────

def rename(text: str, old: str, new: str, count: int = -1) -> str:
    """
    Rename (replace) every occurrence of *old* with *new* inside *text*.

    Parameters
    ----------
    text  : The source string.
    old   : Substring to look for.
    new   : Replacement string.
    count : Maximum number of replacements. -1 means replace all (default).

    Returns
    -------
    str : Modified string.

    Example
    -------
    >>> rename("Hello World World", "World", "Python")
    'Hello Python Python'
    >>> rename("aaa", "a", "b", count=2)
    'bba'
    """
    if count == -1:
        return text.replace(old, new)
    return text.replace(old, new, count)


def rename_file(src_path: str, new_name: str) -> str:
    """
    Rename a file or directory on disk.

    Parameters
    ----------
    src_path : Full or relative path to the existing file / directory.
    new_name : New *name only* (not a full path). The parent directory is kept.

    Returns
    -------
    str : The new full path.

    Raises
    ------
    FileNotFoundError : If *src_path* does not exist.

    Example
    -------
    >>> new_path = rename_file("/tmp/old_name.txt", "new_name.txt")
    >>> print(new_path)   # /tmp/new_name.txt
    """
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"No such file or directory: '{src_path}'")
    parent = os.path.dirname(os.path.abspath(src_path))
    dst_path = os.path.join(parent, new_name)
    os.rename(src_path, dst_path)
    return dst_path


# ──────────────────────────────────────────────
# 2. SEARCH STRING
# ──────────────────────────────────────────────

def search(text: str, pattern: str, use_regex: bool = False,
           case_sensitive: bool = True) -> list[dict]:
    """
    Search for all occurrences of *pattern* in *text*.

    Parameters
    ----------
    text           : The source string to search in.
    pattern        : The substring or regex pattern to look for.
    use_regex      : Treat *pattern* as a regular expression (default False).
    case_sensitive : Case-sensitive matching (default True).

    Returns
    -------
    list[dict] : Each hit has keys 'match', 'start', 'end', 'line', 'col'.

    Example
    -------
    >>> results = search("Foo bar foo BAR", "foo", case_sensitive=False)
    >>> [(r['match'], r['start']) for r in results]
    [('Foo', 0), ('foo', 8)]
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    if not use_regex:
        pattern = re.escape(pattern)

    results = []
    for m in re.finditer(pattern, text, flags):
        start = m.start()
        # Compute line number and column
        prefix = text[:start]
        line_no = prefix.count('\n') + 1
        col = start - prefix.rfind('\n') - 1  # 0-based column
        results.append({
            'match': m.group(),
            'start': start,
            'end': m.end(),
            'line': line_no,
            'col': col,
        })
    return results


def search_first(text: str, pattern: str, use_regex: bool = False,
                 case_sensitive: bool = True) -> dict | None:
    """
    Return only the first match of *pattern*, or None if not found.

    Example
    -------
    >>> search_first("Hello World", "world", case_sensitive=False)
    {'match': 'World', 'start': 6, 'end': 11, 'line': 1, 'col': 6}
    """
    hits = search(text, pattern, use_regex=use_regex,
                  case_sensitive=case_sensitive)
    return hits[0] if hits else None


# ──────────────────────────────────────────────
# 3. REPLACE STRING
# ──────────────────────────────────────────────

def replace(text: str, pattern: str, replacement: str,
            use_regex: bool = False, case_sensitive: bool = True,
            count: int = 0) -> str:
    """
    Replace occurrences of *pattern* with *replacement* in *text*.

    Parameters
    ----------
    text          : The source string.
    pattern       : Substring or regex pattern to replace.
    replacement   : Replacement string (supports regex back-references when
                    use_regex=True, e.g. r'\\1').
    use_regex     : Treat *pattern* as a regular expression (default False).
    case_sensitive: Case-sensitive matching (default True).
    count         : Max replacements; 0 means replace all (default).

    Returns
    -------
    str : Modified string.

    Example
    -------
    >>> replace("foo bar foo", "foo", "baz")
    'baz bar baz'
    >>> replace("2024-01-15", r"(\\d{4})-(\\d{2})-(\\d{2})", r"\\3/\\2/\\1", use_regex=True)
    '15/01/2024'
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    if not use_regex:
        pattern = re.escape(pattern)
    return re.sub(pattern, replacement, text, count=count, flags=flags)


# ──────────────────────────────────────────────
# 4. SEARCH AT POSITION & REPLACE AT POSITION
# ──────────────────────────────────────────────

def search_at_position(text: str, position: int, length: int) -> str:
    """
    Extract *length* characters from *text* starting at *position*.

    Parameters
    ----------
    text     : The source string.
    position : Zero-based start index.
    length   : Number of characters to extract.

    Returns
    -------
    str : Extracted substring.

    Raises
    ------
    IndexError : If *position* is out of bounds.

    Example
    -------
    >>> search_at_position("Hello, World!", 7, 5)
    'World'
    """
    if position < 0 or position >= len(text):
        raise IndexError(
            f"Position {position} is out of range for string of length {len(text)}."
        )
    return text[position: position + length]


def replace_at_position(text: str, position: int, length: int,
                        replacement: str) -> str:
    """
    Replace *length* characters at *position* with *replacement*.

    Parameters
    ----------
    text        : The source string.
    position    : Zero-based start index where replacement begins.
    length      : Number of characters to remove before inserting *replacement*.
    replacement : The string to insert.

    Returns
    -------
    str : Modified string.

    Raises
    ------
    IndexError : If *position* is out of bounds.

    Example
    -------
    >>> replace_at_position("Hello, World!", 7, 5, "Python")
    'Hello, Python!'
    """
    if position < 0 or position > len(text):
        raise IndexError(
            f"Position {position} is out of range for string of length {len(text)}."
        )
    return text[:position] + replacement + text[position + length:]


def insert_at_position(text: str, position: int, insertion: str) -> str:
    """
    Insert *insertion* into *text* at *position* without removing any chars.

    Example
    -------
    >>> insert_at_position("Hello World!", 6, "Beautiful ")
    'Hello Beautiful World!'
    """
    return replace_at_position(text, position, 0, insertion)


# ──────────────────────────────────────────────
# 5. BONUS HELPERS
# ──────────────────────────────────────────────

def find_and_replace_nth(text: str, pattern: str, replacement: str,
                         n: int, use_regex: bool = False,
                         case_sensitive: bool = True) -> str:
    """
    Replace only the *n*-th occurrence (1-based) of *pattern* in *text*.

    Example
    -------
    >>> find_and_replace_nth("a b a b a", "a", "X", n=2)
    'a b X b a'
    """
    hits = search(text, pattern, use_regex=use_regex,
                  case_sensitive=case_sensitive)
    if n < 1 or n > len(hits):
        raise ValueError(
            f"Occurrence {n} not found; only {len(hits)} match(es) exist."
        )
    hit = hits[n - 1]
    return replace_at_position(text, hit['start'],
                               hit['end'] - hit['start'], replacement)


def replace_between(text: str, start_marker: str, end_marker: str,
                    replacement: str, inclusive: bool = False) -> str:
    """
    Replace the content between *start_marker* and *end_marker*.

    Parameters
    ----------
    inclusive : If True, the markers themselves are also replaced.

    Example
    -------
    >>> replace_between("Say [HELLO] there", "[", "]", "HI", inclusive=True)
    'Say HI there'
    >>> replace_between("Say [HELLO] there", "[", "]", "BYE", inclusive=False)
    'Say [BYE] there'
    """
    s_idx = text.find(start_marker)
    e_idx = text.find(end_marker, s_idx + len(start_marker))
    if s_idx == -1 or e_idx == -1:
        return text  # markers not found; return unchanged

    if inclusive:
        return text[:s_idx] + replacement + text[e_idx + len(end_marker):]
    else:
        inner_start = s_idx + len(start_marker)
        return text[:inner_start] + replacement + text[e_idx:]


# ──────────────────────────────────────────────
# QUICK DEMO
# ──────────────────────────────────────────────

if __name__ == "__main__":
    sample = "The quick brown fox jumps over the lazy dog. The fox is fast."

    print("=== rename (replace all) ===")
    print(rename(sample, "fox", "cat"))

    print("\n=== search ===")
    hits = search(sample, "fox")
    for h in hits:
        print(h)

    print("\n=== search (case-insensitive regex) ===")
    hits = search(sample, r"the\s+\w+", use_regex=True, case_sensitive=False)
    for h in hits:
        print(h)

    print("\n=== replace ===")
    print(replace(sample, "fox", "🦊"))

    print("\n=== search_at_position ===")
    print(search_at_position(sample, 4, 5))   # 'quick'

    print("\n=== replace_at_position ===")
    print(replace_at_position(sample, 4, 5, "slow"))

    print("\n=== insert_at_position ===")
    print(insert_at_position(sample, 4, "very "))

    print("\n=== find_and_replace_nth (2nd 'fox') ===")
    print(find_and_replace_nth(sample, "fox", "wolf", n=2))

    print("\n=== replace_between (inclusive) ===")
    tagged = "Hello [NAME] how are [YOU]?"
    print(replace_between(tagged, "[", "]", "Alice", inclusive=True))
