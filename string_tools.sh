#!/usr/bin/env bash
# =============================================================================
# ai_string_tools.sh
# AI-inspired string & file manipulation toolkit for bash/zsh
# =============================================================================
# Usage (source it):  source ai_string_tools.sh
# Usage (run demo):   bash ai_string_tools.sh --demo
# =============================================================================

# Color output helpers
_green()  { printf '\033[0;32m%s\033[0m\n' "$*"; }
_yellow() { printf '\033[0;33m%s\033[0m\n' "$*"; }
_red()    { printf '\033[0;31m%s\033[0m\n' "$*"; }
_bold()   { printf '\033[1m%s\033[0m\n'    "$*"; }
_dim()    { printf '\033[2m%s\033[0m\n'    "$*"; }


# =============================================================================
# 1. RENAME — replace substring(s) inside a string
# =============================================================================
# Usage: str_rename <text> <old> <new> [count]
#   count: number of replacements (default: all)
# Example:
#   str_rename "foo bar foo" "foo" "baz"       → "baz bar baz"
#   str_rename "foo bar foo" "foo" "baz" 1     → "baz bar foo"
# =============================================================================
str_rename() {
    local text="$1"
    local old="$2"
    local new="$3"
    local count="${4:-0}"   # 0 = all

    if [[ "$count" -eq 0 ]]; then
        # Replace all occurrences
        echo "${text//"$old"/"$new"}"
    else
        local result="$text"
        local i=0
        while [[ "$i" -lt "$count" && "$result" == *"$old"* ]]; do
            result="${result/"$old"/"$new"}"
            (( i++ ))
        done
        echo "$result"
    fi
}


# =============================================================================
# 2. RENAME FILE — rename a file or directory on disk
# =============================================================================
# Usage: rename_file <src_path> <new_name>
#   new_name: just the filename (parent dir is preserved)
# Example:
#   rename_file "/tmp/old.txt" "new.txt"
# =============================================================================
rename_file() {
    local src="$1"
    local new_name="$2"

    if [[ -z "$src" || -z "$new_name" ]]; then
        _red "rename_file: usage: rename_file <src_path> <new_name>"
        return 1
    fi
    if [[ ! -e "$src" ]]; then
        _red "rename_file: no such file or directory: '$src'"
        return 1
    fi

    local parent
    parent="$(dirname "$src")"
    local dst="${parent}/${new_name}"

    mv -- "$src" "$dst" && _green "Renamed: $src → $dst" || {
        _red "rename_file: mv failed"
        return 1
    }
}


# =============================================================================
# 3. SEARCH STRING — find all occurrences with positions
# =============================================================================
# Usage: str_search <text> <pattern> [--regex] [--ignore-case]
# Output: one line per match: "match=<m>  start=<s>  end=<e>  line=<l>  col=<c>"
# Example:
#   str_search "Hello World hello" "hello" --ignore-case
# =============================================================================
str_search() {
    local text=""
    local pattern=""
    local use_regex=false
    local ignore_case=false

    # Parse args
    local args=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --regex)       use_regex=true   ;;
            --ignore-case) ignore_case=true ;;
            *)             args+=("$1")     ;;
        esac
        shift
    done
    text="${args[0]:-}"
    pattern="${args[1]:-}"

    if [[ -z "$text" || -z "$pattern" ]]; then
        _red "str_search: usage: str_search <text> <pattern> [--regex] [--ignore-case]"
        return 1
    fi

    # Build grep flags
    local gflags="-ob"
    $use_regex  || gflags+="F"
    $ignore_case && gflags+="i"

    local matches
    matches=$(echo "$text" | grep $gflags "$pattern" 2>/dev/null) || true

    if [[ -z "$matches" ]]; then
        _dim "  (no matches found)"
        return 0
    fi

    while IFS=: read -r byte_off match_str; do
        local start="$byte_off"
        local end=$(( start + ${#match_str} ))

        # Compute line and column
        local prefix="${text:0:$start}"
        local line_no=$(( $(echo "$prefix" | wc -l | tr -d ' ') ))
        local last_nl="${prefix##*$'\n'}"
        local col="${#last_nl}"

        printf "match=%-15s start=%-5s end=%-5s line=%-4s col=%s\n" \
               "\"$match_str\"" "$start" "$end" "$line_no" "$col"
    done <<< "$matches"
}


# =============================================================================
# 4. SEARCH FIRST — return only the first match
# =============================================================================
# Usage: str_search_first <text> <pattern> [--regex] [--ignore-case]
# =============================================================================
str_search_first() {
    local result
    result=$(str_search "$@" 2>&1 | head -n 1)
    if [[ "$result" == *"(no matches"* || -z "$result" ]]; then
        _dim "  (no match found)"
        return 1
    fi
    echo "$result"
}


# =============================================================================
# 5. REPLACE STRING — replace pattern with replacement
# =============================================================================
# Usage: str_replace <text> <pattern> <replacement> [--regex] [--ignore-case] [--count N]
# Example:
#   str_replace "foo bar foo" "foo" "baz"
#   str_replace "Hello WORLD" "world" "Earth" --ignore-case
#   str_replace "2024-01-15" "([0-9]{4})-([0-9]{2})-([0-9]{2})" "\3/\2/\1" --regex
# =============================================================================
str_replace() {
    local text=""
    local pattern=""
    local replacement=""
    local use_regex=false
    local ignore_case=false
    local count=0

    local args=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --regex)       use_regex=true         ;;
            --ignore-case) ignore_case=true        ;;
            --count)       shift; count="${1:-0}"  ;;
            *)             args+=("$1")            ;;
        esac
        shift
    done
    text="${args[0]:-}"
    pattern="${args[1]:-}"
    replacement="${args[2]:-}"

    if [[ -z "$text" || -z "$pattern" ]]; then
        _red "str_replace: usage: str_replace <text> <pattern> <replacement> [--regex] [--ignore-case] [--count N]"
        return 1
    fi

    if $use_regex; then
        local sflags="g"
        $ignore_case && sflags="gi"
        [[ "$count" -gt 0 ]] && sflags=""   # no 'g' if limited count (sed handles per-line)
        if [[ "$count" -gt 0 ]]; then
            # Replace only first N via a loop
            local result="$text"
            local i=0
            while [[ "$i" -lt "$count" ]]; do
                result=$(echo "$result" | sed -E "s/${pattern}/${replacement}/")
                (( i++ ))
            done
            echo "$result"
        else
            echo "$text" | sed -E "s/${pattern}/${replacement}/g"
        fi
    else
        # Plain-text replace
        if $ignore_case; then
            # Case-insensitive plain replace via grep+sed escape
            local esc_pat
            esc_pat=$(printf '%s' "$pattern" | sed 's/[.[\*^$(){}+?|]/\\&/g')
            local sflags="gI"
            [[ "$count" -gt 0 ]] && sflags="I"
            echo "$text" | sed "s/${esc_pat}/${replacement}/${sflags}"
        else
            # Fast native bash replace (all or N)
            if [[ "$count" -eq 0 ]]; then
                echo "${text//"$pattern"/"$replacement"}"
            else
                local result="$text"
                local i=0
                while [[ "$i" -lt "$count" && "$result" == *"$pattern"* ]]; do
                    result="${result/"$pattern"/"$replacement"}"
                    (( i++ ))
                done
                echo "$result"
            fi
        fi
    fi
}


# =============================================================================
# 6. SEARCH AT POSITION — extract substring at a specific index
# =============================================================================
# Usage: str_search_at_pos <text> <position> <length>
#   position: 0-based index
# Example:
#   str_search_at_pos "Hello, World!" 7 5   → "World"
# =============================================================================
str_search_at_pos() {
    local text="$1"
    local position="${2:-0}"
    local length="${3:-1}"

    if [[ "$position" -lt 0 || "$position" -ge "${#text}" ]]; then
        _red "str_search_at_pos: position $position out of range (string length: ${#text})"
        return 1
    fi
    echo "${text:$position:$length}"
}


# =============================================================================
# 7. REPLACE AT POSITION — replace N chars at a specific index
# =============================================================================
# Usage: str_replace_at_pos <text> <position> <length> <replacement>
# Example:
#   str_replace_at_pos "Hello, World!" 7 5 "Python"  → "Hello, Python!"
# =============================================================================
str_replace_at_pos() {
    local text="$1"
    local position="${2:-0}"
    local length="${3:-0}"
    local replacement="${4:-}"

    if [[ "$position" -lt 0 || "$position" -gt "${#text}" ]]; then
        _red "str_replace_at_pos: position $position out of range (string length: ${#text})"
        return 1
    fi
    local before="${text:0:$position}"
    local after="${text:$(( position + length ))}"
    echo "${before}${replacement}${after}"
}


# =============================================================================
# 8. INSERT AT POSITION — insert text without removing chars
# =============================================================================
# Usage: str_insert_at_pos <text> <position> <insertion>
# Example:
#   str_insert_at_pos "Hello World!" 6 "Beautiful "  → "Hello Beautiful World!"
# =============================================================================
str_insert_at_pos() {
    local text="$1"
    local position="${2:-0}"
    local insertion="${3:-}"
    str_replace_at_pos "$text" "$position" 0 "$insertion"
}


# =============================================================================
# 9. REPLACE NTH OCCURRENCE
# =============================================================================
# Usage: str_replace_nth <text> <pattern> <replacement> <n>
# Example:
#   str_replace_nth "a b a b a" "a" "X" 2   → "a b X b a"
# =============================================================================
str_replace_nth() {
    local text="$1"
    local pattern="$2"
    local replacement="$3"
    local n="${4:-1}"

    if [[ -z "$text" || -z "$pattern" || "$n" -lt 1 ]]; then
        _red "str_replace_nth: usage: str_replace_nth <text> <pattern> <replacement> <n>"
        return 1
    fi

    local count=0
    local result=""
    local remaining="$text"
    local found=false

    while [[ "$remaining" == *"$pattern"* ]]; do
        local before="${remaining%%"$pattern"*}"
        local after="${remaining#*"$pattern"}"
        (( count++ ))
        if [[ "$count" -eq "$n" ]]; then
            result+="${before}${replacement}"
            remaining="$after"
            found=true
            break
        else
            result+="${before}${pattern}"
            remaining="$after"
        fi
    done

    if ! $found; then
        _red "str_replace_nth: occurrence $n not found (only $count match(es) exist)"
        return 1
    fi
    echo "${result}${remaining}"
}


# =============================================================================
# 10. REPLACE BETWEEN MARKERS
# =============================================================================
# Usage: str_replace_between <text> <start_marker> <end_marker> <replacement> [--inclusive]
#   --inclusive: also replace the markers themselves
# Example:
#   str_replace_between "Say [HELLO] there" "[" "]" "HI" --inclusive
#   → "Say HI there"
# =============================================================================
str_replace_between() {
    local text="$1"
    local start_marker="$2"
    local end_marker="$3"
    local replacement="$4"
    local inclusive=false
    [[ "${5:-}" == "--inclusive" ]] && inclusive=true

    if [[ "$text" != *"$start_marker"* ]] || [[ "${text#*"$start_marker"}" != *"$end_marker"* ]]; then
        _dim "str_replace_between: markers not found, returning original string"
        echo "$text"
        return 0
    fi

    local before_start="${text%%"$start_marker"*}"
    local after_start="${text#*"$start_marker"}"
    local between="${after_start%%"$end_marker"*}"
    local after_end="${after_start#*"$end_marker"}"

    if $inclusive; then
        echo "${before_start}${replacement}${after_end}"
    else
        echo "${before_start}${start_marker}${replacement}${end_marker}${after_end}"
    fi
}


# =============================================================================
# FILE-LEVEL OPERATIONS (bonus)
# =============================================================================

# Search inside a file and print matching lines with line numbers
# Usage: file_search <file> <pattern> [--regex] [--ignore-case]
file_search() {
    local file="$1"; shift
    local pattern="$1"; shift
    local gflags="-n"
    for arg in "$@"; do
        [[ "$arg" == "--ignore-case" ]] && gflags+="i"
        [[ "$arg" == "--regex" ]]       || gflags+="F"
    done
    # Remove duplicate F if regex
    gflags="${gflags//FF/F}"
    grep $gflags "$pattern" "$file" || _dim "  (no matches in $file)"
}

# Replace pattern in a file (in-place)
# Usage: file_replace <file> <old> <new> [--regex] [--ignore-case]
file_replace() {
    local file="$1"
    local old="$2"
    local new="$3"
    local use_regex=false
    local ignore_case=false
    for arg in "${@:4}"; do
        [[ "$arg" == "--regex" ]]       && use_regex=true
        [[ "$arg" == "--ignore-case" ]] && ignore_case=true
    done

    if [[ ! -f "$file" ]]; then
        _red "file_replace: file not found: '$file'"
        return 1
    fi

    local sflags="g"
    $ignore_case && sflags="gi"

    if $use_regex; then
        sed -i.bak -E "s/${old}/${new}/${sflags}" "$file"
    else
        local esc_old
        esc_old=$(printf '%s' "$old" | sed 's/[.[\*^$(){}+?|]/\\&/g')
        local esc_new
        esc_new=$(printf '%s' "$new" | sed 's/[&/\]/\\&/g')
        sed -i.bak "s/${esc_old}/${esc_new}/${sflags}" "$file"
    fi
    _green "file_replace: updated '$file' (backup: ${file}.bak)"
}


 file_count
        match_count=$(echo "$results" | wc -l | tr -d ' ')
        file_count=$(echo "$results" | cut -d: -f1 | sort -u | wc -l | tr -d ' ')
        _green "$match_count match(es) across $file_count file(s)"
    fi
}


# Replace pattern across ALL files in a folder (recursive, in-place with backup)
# Usage: folder_replace <folder> <old> <new> [--regex] [--ignore-case] [--ext EXT] [--dry-run]
#   --dry-run : preview changes without modifying files
# Example:
#   folder_replace ./src "oldFunc" "newFunc"
#   folder_replace ./src "TODO" "DONE" --dry-run --ext sh
folder_replace() {
    local folder=""
    local old=""
    local new=""
    local use_regex=false
    local ignore_case=false
    local ext=""
    local dry_run=false

    local args=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --regex)       use_regex=true   ;;
            --ignore-case) ignore_case=true ;;
            --dry-run)     dry_run=true     ;;
            --ext)         shift; ext="${1:-}" ;;
            *)             args+=("$1")     ;;
        esac
        shift
    done
    folder="${args[0]:-}"
    old="${args[1]:-}"
    new="${args[2]:-}"

    if [[ -z "$folder" || -z "$old" ]]; then
        _red "folder_replace: usage: folder_replace <folder> <old> <new> [--regex] [--ignore-case] [--ext EXT] [--dry-run]"
        return 1
    fi
    if [[ ! -d "$folder" ]]; then
        _red "folder_replace: directory not found: '$folder'"
        return 1
    fi

    _bold "\n Replacing \"$old\" -> \"$new\" in: $folder"
    [[ -n "$ext" ]] && _dim "   Filter: *.${ext}"
    $dry_run         && _yellow "   Mode: DRY RUN (no files modified)"
    echo ""

    local sflags="g"
    $ignore_case && sflags="${sflags}i"

    local esc_old esc_new
    if $use_regex; then
        esc_old="$old"
        esc_new="$new"
    else
        esc_old=$(printf '%s' "$old" | sed 's/[.[\*^$(){}+?|]/\\&/g')
        esc_new=$(printf '%s' "$new" | sed 's/[&/\]/\\&/g')
    fi

    local changed=0

    while IFS= read -r file; do
        local has_match=false
        if $use_regex; then
            grep -qE "$esc_old" "$file" 2>/dev/null && has_match=true
        else
            grep -qF "$old" "$file" 2>/dev/null && has_match=true
        fi

        if $has_match; then
            if $dry_run; then
                _yellow "  [would update] $file"
                grep -nF "$old" "$file" 2>/dev/null | head -3 | while IFS= read -r line; do
                    _dim "    $line"
                done
            else
                if $use_regex; then
                    sed -i.bak -E "s/${esc_old}/${esc_new}/${sflags}" "$file"
                else
                    sed -i.bak "s/${esc_old}/${esc_new}/${sflags}" "$file"
                fi
                _green "  updated: $file"
            fi
            (( changed++ ))
        fi
    done < <(find "$folder" -type f ${ext:+-name "*.${ext}"})

    echo ""
    if $dry_run; then
        _yellow "Dry run complete: $changed file(s) would be modified"
    else
        _green "Done: $changed file(s) updated (backups saved as *.bak)"
    fi
}


# =============================================================================
# DEMO
# =============================================================================
_run_demo() {
    local sample="The quick brown fox jumps over the lazy dog. The fox is fast."

    _bold "\n════════════════════════════════════"
    _bold " ai_string_tools.sh — DEMO"
    _bold "════════════════════════════════════"
    echo  "Sample: \"$sample\""

    _bold "\n[1] str_rename — replace all 'fox' → 'cat'"
    str_rename "$sample" "fox" "cat"

    _bold "\n[2] str_rename — replace first 'fox' only"
    str_rename "$sample" "fox" "cat" 1

    _bold "\n[3] str_search — find all 'fox'"
    str_search "$sample" "fox"

    _bold "\n[4] str_search — case-insensitive regex 'the\\s+\\w+'"
    str_search "$sample" "the[[:space:]]+[[:alpha:]]+" --regex --ignore-case

    _bold "\n[5] str_search_first — first match of 'fox'"
    str_search_first "$sample" "fox"

    _bold "\n[6] str_replace — replace all 'fox' → '🦊'"
    str_replace "$sample" "fox" "🦊"

    _bold "\n[7] str_replace — case-insensitive 'THE' → 'A'"
    str_replace "$sample" "The" "A" --ignore-case

    _bold "\n[8] str_replace — regex date reformat"
    echo "Date: 2024-01-15" | sed -E 's/([0-9]{4})-([0-9]{2})-([0-9]{2})/\3\/\2\/\1/'

    _bold "\n[9] str_search_at_pos — 5 chars at position 4"
    str_search_at_pos "$sample" 4 5

    _bold "\n[10] str_replace_at_pos — replace 5 chars at pos 4 with 'slow'"
    str_replace_at_pos "$sample" 4 5 "slow"

    _bold "\n[11] str_insert_at_pos — insert 'very ' at position 4"
    str_insert_at_pos "$sample" 4 "very "

    _bold "\n[12] str_replace_nth — replace 2nd 'fox' with 'wolf'"
    str_replace_nth "$sample" "fox" "wolf" 2

    _bold "\n[13] str_replace_between — replace content inside [...] (inclusive)"
    str_replace_between "Hello [NAME] how are [YOU]?" "[" "]" "Alice" --inclusive

    _bold "\n[14] str_replace_between — replace content inside [...] (keep markers)"
    str_replace_between "Hello [NAME] how are you?" "[" "]" "Bob"

    _bold "\n════════════════════════════════════\n"
}

# Run demo if executed directly with --demo flag
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ "${1:-}" == "--demo" || $# -eq 0 ]]; then
        _run_demo
    fi
fi

# ---- injected folder demo ----
_run_folder_demo() {
    local tmpdir
    tmpdir=$(mktemp -d)
    echo "The fox is quick. The fox jumps." > "$tmpdir/file1.txt"
    echo "No match here."                   > "$tmpdir/file2.txt"
    echo "Another fox sighting."            > "$tmpdir/file3.log"
    mkdir -p "$tmpdir/sub"
    echo "Sub-folder fox found."            > "$tmpdir/sub/file4.txt"

    _bold "\n[15] folder_search — find 'fox' in all files recursively"
    folder_search "$tmpdir" "fox"

    _bold "\n[16] folder_search — only in .txt files"
    folder_search "$tmpdir" "fox" --ext txt

    _bold "\n[17] folder_search — list files only"
    folder_search "$tmpdir" "fox" --list-files

    _bold "\n[18] folder_replace — dry run: 'fox' → 'cat'"
    folder_replace "$tmpdir" "fox" "cat" --dry-run

    _bold "\n[19] folder_replace — replace 'fox' → 'cat' in .txt only"
    folder_replace "$tmpdir" "fox" "cat" --ext txt

    _bold "\n    file1.txt after replace:"
    cat "$tmpdir/file1.txt"

    rm -rf "$tmpdir"
    _bold "\n════════════════════════════════════\n"
}
