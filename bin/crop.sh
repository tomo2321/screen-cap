#!/bin/bash
#
# Batch crop images based on margin detection
#
# This script detects margins from a sample image using detect_margin.py,
# then applies the detected crop boundaries to all images in the same directory.
#
# Usage:
#   ./crop.sh [--enable-right|-r] [--enable-vertical|-v] [--remove|-R] <sample_image_path>
#
# Arguments:
#   --enable-right, -r: Enable right margin detection (optional)
#   --enable-vertical, -v: Enable vertical margin detection (optional)
#   --remove, -R: Remove source image directory without confirmation (optional)
#   sample_image_path: Path to a sample image for margin detection
#
# Output:
#   Cropped images are saved to done/<directory_name>/
#   Example: If sample_image_path is /User/user/hoge/fuga/page_001.png, output goes to done/fuga/
#
# Example:
#   ./crop.sh ./figs/sample/page_001.png
#   ./crop.sh --enable-right ./figs/sample/page_001.png
#   ./crop.sh --enable-vertical ./figs/sample/page_001.png
#   ./crop.sh -v ./figs/sample/page_001.png
#   ./crop.sh -r -v ./figs/sample/page_001.png
#   ./crop.sh -r ./figs/sample/page_001.png
#   ./crop.sh --remove ./figs/sample/page_001.png
#   ./crop.sh -r -v -R ./figs/sample/page_001.png
#

set -e

# Parse options
ENABLE_RIGHT_CLICK=""
ENABLE_VERTICAL=""
REMOVE_SOURCE=""
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --enable-right|-r)
            ENABLE_RIGHT_CLICK="--enable-right"
            shift
            ;;
        --enable-vertical|-v)
            ENABLE_VERTICAL="--enable-vertical"
            shift
            ;;
        --remove|-R)
            REMOVE_SOURCE="true"
            shift
            ;;
        *)
            SAMPLE_IMAGE="$1"
            shift
            ;;
    esac
done

# Check arguments
if [ -z "$SAMPLE_IMAGE" ]; then
    echo "Usage: $0 [--enable-right|-r] [--enable-vertical|-v] <sample_image_path>"
    exit 1
fi
IMAGE_DIR="$(dirname "$SAMPLE_IMAGE")"

# Check if sample image exists
if [ ! -f "$SAMPLE_IMAGE" ]; then
    echo "Error: Sample image not found: $SAMPLE_IMAGE"
    exit 1
fi

# Check if image directory exists
if [ ! -d "$IMAGE_DIR" ]; then
    echo "Error: Image directory not found: $IMAGE_DIR"
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Run detect_margin.py and capture output
echo "Detecting margins from sample image: $SAMPLE_IMAGE"
DETECT_OUTPUT=$(python "$PROJECT_ROOT/src/detect_margin.py" $ENABLE_RIGHT_CLICK $ENABLE_VERTICAL "$SAMPLE_IMAGE" 2>&1 || true)

# Extract left and right boundary values
# Expected format: "Left boundary (first pixel): 101, Right boundary (last pixel): 412"
LEFT_BOUNDARY=$(echo "$DETECT_OUTPUT" | grep -oE "Left boundary \(first pixel\): [0-9]+" | grep -oE "[0-9]+$" | tail -1 || echo "")
RIGHT_BOUNDARY=$(echo "$DETECT_OUTPUT" | grep -oE "Right boundary \(last pixel\): [0-9]+" | grep -oE "[0-9]+$" | tail -1 || echo "")

# Check if boundaries were detected
if [ -z "$LEFT_BOUNDARY" ] || [ -z "$RIGHT_BOUNDARY" ]; then
    echo "Error: Failed to detect boundaries"
    echo "Output from detect_margin.py:"
    echo "$DETECT_OUTPUT"
    exit 1
fi

echo "Detected boundaries: Left=$LEFT_BOUNDARY, Right=$RIGHT_BOUNDARY"

# Extract vertical boundary values if --enable-vertical is set
# Expected format: "Top boundary (first pixel): 101, Bottom boundary (last pixel): 512"
TOP_BOUNDARY=""
BOTTOM_BOUNDARY=""
VERTICAL_FLAGS=""
if [ -n "$ENABLE_VERTICAL" ]; then
    TOP_BOUNDARY=$(echo "$DETECT_OUTPUT" | grep -oE "Top boundary \(first pixel\): [0-9]+" | grep -oE "[0-9]+$" | tail -1 || echo "")
    BOTTOM_BOUNDARY=$(echo "$DETECT_OUTPUT" | grep -oE "Bottom boundary \(last pixel\): [0-9]+" | grep -oE "[0-9]+$" | tail -1 || echo "")
    
    if [ -z "$TOP_BOUNDARY" ] || [ -z "$BOTTOM_BOUNDARY" ]; then
        echo "Error: Failed to detect vertical boundaries"
        echo "Output from detect_margin.py:"
        echo "$DETECT_OUTPUT"
        exit 1
    fi
    
    echo "Detected vertical boundaries: Top=$TOP_BOUNDARY, Bottom=$BOTTOM_BOUNDARY"
    VERTICAL_FLAGS="--top $TOP_BOUNDARY --bottom $BOTTOM_BOUNDARY"
fi

# Extract directory name from image_directory path
DIR_NAME=$(basename "$IMAGE_DIR")

# Create output directory
OUTPUT_DIR="$PROJECT_ROOT/done/$DIR_NAME"
mkdir -p "$OUTPUT_DIR"

echo "Output directory: $OUTPUT_DIR"

# Process all images in the directory
IMAGE_COUNT=0
for IMAGE_FILE in "$IMAGE_DIR"/*; do
    # Skip if not a file
    if [ ! -f "$IMAGE_FILE" ]; then
        continue
    fi

    # Check if it's an image file (by extension)
    EXT="${IMAGE_FILE##*.}"
    EXT_LOWER=$(echo "$EXT" | tr '[:upper:]' '[:lower:]')
    if [[ ! "$EXT_LOWER" =~ ^(jpg|jpeg|png|bmp|tiff|tif)$ ]]; then
        continue
    fi

    # Get filename
    FILENAME=$(basename "$IMAGE_FILE")
    OUTPUT_FILE="$OUTPUT_DIR/$FILENAME"

    # Crop image
    echo "Processing: $FILENAME"
    python "$PROJECT_ROOT/src/crop.py" "$IMAGE_FILE" "$OUTPUT_FILE" $LEFT_BOUNDARY $RIGHT_BOUNDARY $VERTICAL_FLAGS

    IMAGE_COUNT=$((IMAGE_COUNT + 1))
done

echo ""
echo "Batch crop completed!"
echo "Processed $IMAGE_COUNT images"
echo "Output location: $OUTPUT_DIR"

# Handle source directory removal
if [ -n "$REMOVE_SOURCE" ]; then
    echo "Removing source directory: $IMAGE_DIR"
    rm -rf "$IMAGE_DIR"
    echo "Source directory removed."
else
    echo ""
    read -p "Do you want to remove the source image directory? ($IMAGE_DIR) [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing source directory: $IMAGE_DIR"
        rm -rf "$IMAGE_DIR"
        echo "Source directory removed."
    else
        echo "Source directory kept."
    fi
fi
