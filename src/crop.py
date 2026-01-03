#!/usr/bin/env python3
"""
Script to crop images based on specified pixel boundaries

This script crops an image horizontally using 1-indexed pixel positions.
Both start and end positions are inclusive in the output.

Usage:
    python crop.py <input_image> <output_image> <start_pos> <end_pos>

Arguments:
    input_image: Path to input image file
    output_image: Path to output image file
    start_pos: Starting pixel position (1-indexed, inclusive)
    end_pos: Ending pixel position (1-indexed, inclusive)

Example:
    python crop.py input.png output.png 101 412

    This will crop the image from pixel 101 to pixel 412 (both inclusive).
"""

import argparse
import sys

import cv2


def crop_image(input_path, output_path, start_pos, end_pos):
    """
    Crop image horizontally

    Args:
        input_path (str): Input image file path
        output_path (str): Output image file path
        start_pos (int): Start position (1-indexed, inclusive)
        end_pos (int): End position (1-indexed, inclusive)
    """
    # Load image
    image = cv2.imread(input_path)
    if image is None:
        print(f"Error: Failed to load image: {input_path}")
        sys.exit(1)

    height, width = image.shape[:2]

    # Validate positions
    if start_pos < 1 or end_pos < 1:
        print(f"Error: Positions must be 1 or greater (start={start_pos}, end={end_pos})")
        sys.exit(1)

    if start_pos > width or end_pos > width:
        print(f"Error: Positions exceed image width {width} (start={start_pos}, end={end_pos})")
        sys.exit(1)

    if start_pos > end_pos:
        print(f"Error: Start position must be <= end position (start={start_pos}, end={end_pos})")
        sys.exit(1)

    # Convert 1-indexed positions to 0-indexed slice indices
    # start_pos (1-indexed) -> left (0-indexed)
    # end_pos (1-indexed, inclusive) -> right (0-indexed, exclusive for slice)
    left = start_pos - 1
    right = end_pos  # end_pos is inclusive, so use it directly for exclusive slice end

    # Crop image
    cropped = image[:, left:right]

    # Save cropped image
    success = cv2.imwrite(output_path, cropped)
    if not success:
        print(f"Error: Failed to save image: {output_path}")
        sys.exit(1)

    print(f"Cropped image saved: {output_path}")
    print(f"Original size: {width}x{height}, Cropped size: {cropped.shape[1]}x{cropped.shape[0]}")


def main():
    parser = argparse.ArgumentParser(
        description="Crop image horizontally based on pixel positions (1-indexed, inclusive)"
    )
    parser.add_argument(
        "input_image",
        help="Path to input image file"
    )
    parser.add_argument(
        "output_image",
        help="Path to output image file"
    )
    parser.add_argument(
        "start_pos",
        type=int,
        help="Starting pixel position (1-indexed, inclusive)"
    )
    parser.add_argument(
        "end_pos",
        type=int,
        help="Ending pixel position (1-indexed, inclusive)"
    )

    args = parser.parse_args()

    crop_image(args.input_image, args.output_image, args.start_pos, args.end_pos)


if __name__ == "__main__":
    main()
