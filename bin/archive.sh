#!/bin/bash

# Script to archive each directory under the done directory as a zip file

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Move to project root
cd "$PROJECT_ROOT" || exit 1

DONE_DIR="done"
ARCHIVE_DIR="archive"

# Check if done directory exists
if [ ! -d "$DONE_DIR" ]; then
    echo "Error: ${DONE_DIR} directory not found"
    exit 1
fi

# Create archive directory if it doesn't exist
mkdir -p "$ARCHIVE_DIR"

# Process each subdirectory in the done directory
count=0
for dir in "$DONE_DIR"/*/; do
    # Skip if directory doesn't exist
    [ -d "$dir" ] || continue

    # Get directory name (remove trailing slash)
    dirname=$(basename "$dir")

    # Set zip file name
    zipfile="$ARCHIVE_DIR/${dirname}.zip"

    # Skip if zip file already exists
    if [ -f "$zipfile" ]; then
        echo "Skipping: $dirname (already archived)"
        continue
    fi

    echo "Compressing: $dirname -> ${zipfile}"

    # Compress directory with zip command
    # -r: recursive compression
    # -q: quiet mode (don't show progress)
    (cd "$DONE_DIR" && zip -r -q "../$zipfile" "$dirname")

    if [ $? -eq 0 ]; then
        echo "  ✓ Complete"
        ((count++))
    else
        echo "  ✗ Error"
    fi
done

echo ""
echo "Processing complete: Archived ${count} directories"
