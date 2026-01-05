#!/usr/bin/env python3
"""
Script to crop images based on specified pixel boundaries

This script crops an image horizontally and optionally vertically using 1-indexed pixel positions.
Both start and end positions are inclusive in the output.

Usage:
    python crop.py <input_image> <output_image> <start_pos> <end_pos> [--top|-t TOP] [--bottom|-b BOTTOM]

Arguments:
    input_image: Path to input image file
    output_image: Path to output image file
    start_pos: Starting horizontal pixel position (1-indexed, inclusive)
    end_pos: Ending horizontal pixel position (1-indexed, inclusive)
    --top|-t: Starting vertical pixel position (1-indexed, inclusive, optional, defaults to 1)
    --bottom|-b: Ending vertical pixel position (1-indexed, inclusive, optional, defaults to image height)

Example:
    python crop.py input.png output.png 101 412
    python crop.py input.png output.png 101 412 --top 50 --bottom 300

    The first example crops horizontally from pixel 101 to 412.
    The second example also crops vertically from pixel 50 to 300.
"""

import argparse
import sys

import cv2


def crop_image(input_path, output_path, start_pos, end_pos, top=None, bottom=None):
    """
    Crop image horizontally and optionally vertically

    Args:
        input_path (str): Input image file path
        output_path (str): Output image file path
        start_pos (int): Horizontal start position (1-indexed, inclusive)
        end_pos (int): Horizontal end position (1-indexed, inclusive)
        top (int, optional): Vertical start position (1-indexed, inclusive), defaults to 1
        bottom (int, optional): Vertical end position (1-indexed, inclusive), defaults to image height
    """
    # Load image
    image = cv2.imread(input_path)
    if image is None:
        print(f"Error: Failed to load image: {input_path}")
        sys.exit(1)
    assert image is not None

    height, width = image.shape[:2]

    # Validate positions
    if start_pos < 1 or end_pos < 1:
        print(
            f"Error: Positions must be 1 or greater (start={start_pos}, end={end_pos})"
        )
        sys.exit(1)

    if start_pos > width or end_pos > width:
        print(
            f"Error: Positions exceed image width {width} (start={start_pos}, end={end_pos})"
        )
        sys.exit(1)

    if start_pos > end_pos:
        print(
            f"Error: Start position must be <= end position (start={start_pos}, end={end_pos})"
        )
        sys.exit(1)

    # Set default values for top and bottom if not provided
    if top is None:
        top = 1
    if bottom is None:
        bottom = height

    # Validate vertical positions
    if top < 1 or bottom < 1:
        print(
            f"Error: Top and bottom positions must be 1 or greater (top={top}, bottom={bottom})"
        )
        sys.exit(1)

    if top > height or bottom > height:
        print(
            f"Error: Top/bottom positions exceed image height {height} (top={top}, bottom={bottom})"
        )
        sys.exit(1)

    if top > bottom:
        print(
            f"Error: Top position must be <= bottom position (top={top}, bottom={bottom})"
        )
        sys.exit(1)

    # Convert 1-indexed positions to 0-indexed slice indices
    # start_pos (1-indexed) -> left (0-indexed)
    # end_pos (1-indexed, inclusive) -> right (0-indexed, exclusive for slice)
    left = start_pos - 1
    right = end_pos  # end_pos is inclusive, so use it directly for exclusive slice end

    # Vertical crop indices
    top_idx = top - 1
    bottom_idx = (
        bottom  # bottom is inclusive, so use it directly for exclusive slice end
    )

    # Crop image
    assert image is not None
    cropped = image[top_idx:bottom_idx, left:right]

    # Save cropped image
    success = cv2.imwrite(output_path, cropped)
    if not success:
        print(f"Error: Failed to save image: {output_path}")
        sys.exit(1)

    print(f"Cropped image saved: {output_path}")
    print(
        f"Original size: {width}x{height}, Cropped size: {cropped.shape[1]}x{cropped.shape[0]}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Crop image horizontally and optionally vertically based on pixel positions (1-indexed, inclusive)"
    )
    parser.add_argument("input_image", help="Path to input image file")
    parser.add_argument("output_image", help="Path to output image file")
    parser.add_argument(
        "start_pos",
        type=int,
        help="Starting horizontal pixel position (1-indexed, inclusive)",
    )
    parser.add_argument(
        "end_pos",
        type=int,
        help="Ending horizontal pixel position (1-indexed, inclusive)",
    )
    parser.add_argument(
        "--top",
        "-t",
        type=int,
        default=None,
        help="Starting vertical pixel position (1-indexed, inclusive, defaults to 1)",
    )
    parser.add_argument(
        "--bottom",
        "-b",
        type=int,
        default=None,
        help="Ending vertical pixel position (1-indexed, inclusive, defaults to image height)",
    )

    args = parser.parse_args()

    crop_image(
        args.input_image,
        args.output_image,
        args.start_pos,
        args.end_pos,
        args.top,
        args.bottom,
    )


if __name__ == "__main__":
    main()
