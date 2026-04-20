#!/bin/bash
# smart_read.sh - Prevents AI from reading same file twice, returns diffs, tracks stats.

CACHE_DIR="../.claude_cache"
STATS_FILE="$CACHE_DIR/stats.env"
mkdir -p "$CACHE_DIR"

# Initialize or load stats
if [ -f "$STATS_FILE" ]; then
    source "$STATS_FILE"
else
    TOTAL_READS=0; CACHE_HITS=0; FIRST_READS=0; CHANGED_FILES=0; TOKENS_SAVED=0; TOTAL_TOKENS=0
fi

# ---------------------------------------------------------
# Handle the 'stats' command
# ---------------------------------------------------------
if [ "$1" == "stats" ]; then
    SAVINGS=0
    if [ "$TOTAL_TOKENS" -gt 0 ]; then
        SAVINGS=$(( (TOKENS_SAVED * 100) / TOTAL_TOKENS ))
    fi

    echo "smart_read — file read deduplication & tracking"
    echo ""
    echo "  Total file reads:    $TOTAL_READS"
    echo "  Cache hits:          $CACHE_HITS (blocked re-reads)"
    echo "  First reads:         $FIRST_READS"
    echo "  Changed files:       $CHANGED_FILES (diffs returned after modification)"
    echo ""
    echo "  Tokens saved:        ~$TOKENS_SAVED"
    echo "  Read token total:    ~$TOTAL_TOKENS"
    echo "  Savings:             $SAVINGS%"
    echo ""
    exit 0
fi

# ---------------------------------------------------------
# Handle normal file reading logic
# ---------------------------------------------------------
if [ -z "$1" ]; then
    echo "Usage: ./smart_read.sh <filepath> OR ./smart_read.sh stats"
    exit 1
fi

FILE="$1"
if [ ! -f "$FILE" ]; then
    echo "Error: File '$FILE' not found."
    exit 1
fi

CACHE_FILE="$CACHE_DIR/$(echo "$FILE" | sed 's/\//_/g')"
TOTAL_READS=$((TOTAL_READS + 1))

# Estimate tokens (roughly 1 token per 4 characters in code)
TOKENS=$(wc -c < "$FILE" | awk '{print int($1/4)}')
TOTAL_TOKENS=$((TOTAL_TOKENS + TOKENS))

if [ ! -f "$CACHE_FILE" ]; then
    FIRST_READS=$((FIRST_READS + 1))
    cat "$FILE"
    cp "$FILE" "$CACHE_FILE"
else
    DIFF_OUTPUT=$(diff -U 3 "$CACHE_FILE" "$FILE" || true)

    if [ -z "$DIFF_OUTPUT" ]; then
        CACHE_HITS=$((CACHE_HITS + 1))
        TOKENS_SAVED=$((TOKENS_SAVED + TOKENS))
        echo "⚠️ FILE ALREADY IN CONTEXT. NO CHANGES DETECTED."
    else
        CHANGED_FILES=$((CHANGED_FILES + 1))
        # Calculate tokens of the diff to find accurate savings
        DIFF_TOKENS=$(echo "$DIFF_OUTPUT" | wc -c | awk '{print int($1/4)}')

        # Prevent negative savings if diff is somehow larger than original file
        if [ "$DIFF_TOKENS" -lt "$TOKENS" ]; then
            TOKENS_SAVED=$((TOKENS_SAVED + (TOKENS - DIFF_TOKENS)))
        fi

        echo "⚠️ FILE ALREADY IN CONTEXT. SHOWING ONLY NEW CHANGES:"
        echo "$DIFF_OUTPUT"
        cp "$FILE" "$CACHE_FILE"
    fi
fi

# Save stats back to the environment file
cat > "$STATS_FILE" <<EOF
TOTAL_READS=$TOTAL_READS
CACHE_HITS=$CACHE_HITS
FIRST_READS=$FIRST_READS
CHANGED_FILES=$CHANGED_FILES
TOKENS_SAVED=$TOKENS_SAVED
TOTAL_TOKENS=$TOTAL_TOKENS
EOF
