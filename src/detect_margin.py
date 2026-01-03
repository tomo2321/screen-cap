#!/usr/bin/env python3
"""
Script to detect image margins and display preview with margins removed

This script allows you to interactively detect left and right margins in an image
by clicking on the margin areas. The detected boundaries are displayed using
1-indexed pixel positions (leftmost pixel = 1).

Boundary definitions:
- Left boundary: Index of the first pixel of content (where content starts)
- Right boundary: Index of the last pixel of content (where content ends)

For example, if pixel 1 is white, pixels 2-3 are black (content), and pixel 4 is white:
- Left boundary = 2 (first content pixel)
- Right boundary = 3 (last content pixel)

Modes:
- enable_right=False (default): Click left half to detect left boundary.
  Right boundary is automatically detected from the mirrored position (symmetric to the click point
  relative to the image center) at the same y-coordinate.
- enable_right=True: Click left half for left boundary, right half for right boundary.
  Manual control of both boundaries.
- enable_same_margin=True: Apply the same margin width from left side to right side.
  Cannot be used with --enable-right. If both flags are specified, --enable-right takes priority.

Usage:
    python detect_margin.py <image_path> [--enable-right | --enable-same-margin]

Examples:
    # Automatic symmetric detection (default)
    python detect_margin.py image.png

    # Manual control for asymmetric margins
    python detect_margin.py image.png --enable-right

    # Apply same left margin width to right side
    python detect_margin.py image.png --enable-same-margin

How it works:
1. Click on a margin area (white/background region)
2. The script searches for brightness change in the appropriate direction
3. Detected boundaries are displayed in 1-indexed format
4. Preview window shows the image with margins removed
5. Press 'q' in the preview window to exit
"""

import argparse
import sys

import cv2


class MarginDetector:
    """
    Interactive margin detector for images

    This class provides interactive margin detection by clicking on margin areas.
    All boundary values are stored and displayed as 1-indexed pixel positions.

    Attributes:
        left_boundary (int): 1-indexed position of first content pixel (None if not detected)
        right_boundary (int): 1-indexed position of last content pixel (None if not detected)
        enable_right (bool): If False, automatically detects right boundary from mirrored position
                           (symmetric to left click point relative to image center)
                           If True, requires manual right-side click for right boundary
        enable_same_margin (bool): If True, applies the same margin width from left side to right side.
                                   Mutually exclusive with enable_right. If both are True,
                                   enable_right takes priority and this flag is ignored.
    
    Internal processing uses 0-indexed coordinates, but all user-facing values
    (display and boundary storage) use 1-indexed positions.
    """
    def __init__(self, image_path, enable_right=False, enable_same_margin=False):
        self.image_path = image_path
        self.enable_right = enable_right
        
        # If both flags are specified, prioritize enable_right
        if enable_right and enable_same_margin:
            print("Warning: Both --enable-right and --enable-same-margin specified.")
            print("Prioritizing --enable-right. --enable-same-margin will be ignored.")
            self.enable_same_margin = False
        else:
            self.enable_same_margin = enable_same_margin
        
        self.image = None
        self.gray = None
        self.left_boundary = None
        self.right_boundary = None
        self.main_window_name = "Click image to detect margin"
        self.preview_window_name = "Margin Removed Preview"

    def load_image(self):
        """Load image"""
        self.image = cv2.imread(self.image_path)
        if self.image is None:
            print(f"Error: Failed to load image: {self.image_path}")
            sys.exit(1)

        # Convert to grayscale for brightness comparison
        self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        print(f"Image loaded: {self.image.shape[1]}x{self.image.shape[0]}")

    def find_boundary_right(self, x, y):
        """
        Search for brightness change to the right from the specified position

        Searches rightward from click position until brightness changes.
        Returns the position of the first pixel with different brightness.

        Args:
            x, y: Click position (0-indexed)

        Returns:
            int: 1-indexed x-coordinate of first changed pixel (left boundary)
                 None if no boundary found before right edge

        Example:
            If pixels 0-99 are white (255) and pixels 100-511 are gray (128),
            clicking at x=50 returns 101 (1-indexed position of pixel at 0-indexed 100)
        """
        height, width = self.gray.shape

        # Use the brightness value at click position as reference
        base_value = self.gray[y, x]

        # Search to the right
        for i in range(x + 1, width):
            current_value = self.gray[y, i]
            # Consider it a boundary when brightness changes
            if current_value != base_value:
                # Convert to 1-indexed and return
                return i + 1

        return None

    def find_boundary_left(self, x, y):
        """
        Search for brightness change to the left from the specified position

        Searches leftward from click position until brightness changes.
        Returns the position of the last pixel before brightness changes.

        Args:
            x, y: Click position (0-indexed)

        Returns:
            int: 1-indexed x-coordinate of last pixel before change (right boundary)
                 None if no boundary found before left edge

        Example:
            If pixels 0-99 are gray (128) and pixels 100-511 are white (255),
            clicking at x=450 returns 100 (1-indexed position of pixel at 0-indexed 99)
        """
        # Use the brightness value at click position as reference
        base_value = self.gray[y, x]

        # Search to the left
        for i in range(x - 1, -1, -1):
            current_value = self.gray[y, i]
            # Consider it a boundary when brightness changes
            if current_value != base_value:
                # Convert to 1-indexed and return (last pixel before change)
                return i + 1

        return None

    def mouse_callback(self, event, x, y, flags, param):
        """Mouse click event callback"""
        if event != cv2.EVENT_LBUTTONDOWN:
            return

        height, width = self.gray.shape
        half_width = width // 2

        # Display coordinates in 1-indexed
        print(f"\nClick position: ({x + 1}, {y + 1})")

        # Left half click
        if x < half_width:
            print("Left half clicked: Searching to the right")
            boundary = self.find_boundary_right(x, y)
            if boundary:
                self.left_boundary = boundary
                print(f"Left boundary detected: x = {boundary} (first pixel of content, 1-indexed)")
            else:
                print("Boundary not found")

            # When enable_right is False, automatically search from the mirror position on the right side
            if not self.enable_right:
                # Calculate the mirror position of the click point relative to the center
                # Center is at half_width (0-indexed)
                # Distance from center to click point
                distance_from_center = half_width - x
                # Mirror position on the right side
                right_x = half_width + distance_from_center
                # Clamp to valid range
                right_x = min(right_x, width - 1)
                print(f"Automatically searching from mirrored position x = {right_x + 1} (1-indexed) at y = {y + 1}")
                boundary = self.find_boundary_left(right_x, y)
                if boundary:
                    self.right_boundary = boundary
                    print(f"Right boundary detected: x = {boundary} (last pixel of content, 1-indexed)")
                else:
                    print("Right boundary not found")

        # Right half click
        elif self.enable_right:
            print("Right half clicked: Searching to the left")
            boundary = self.find_boundary_left(x, y)
            if boundary:
                self.right_boundary = boundary
                print(f"Right boundary detected: x = {boundary} (last pixel of content, 1-indexed)")
            else:
                print("Boundary not found")
        else:
            print("Right half processing is disabled (use --enable-right flag)")

        # Show preview when boundary is detected
        if self.left_boundary or self.right_boundary:
            self.show_preview()

    def show_preview(self):
        """
        Display preview with margins removed

        Crops the image based on detected boundaries and displays the result.

        Cropping logic:
        - If right_boundary is set:
          * With enable_same_margin=True (and enable_right=False): Overrides right boundary
            with left margin width
          * Otherwise: Uses detected right boundary directly
        - If only left_boundary is set:
          * With enable_same_margin=True: Applies left margin width to right side
          * With enable_right=False (default): Applies left margin width to right side
          * Otherwise: No cropping on right side
        - Otherwise: No cropping on respective side

        Boundary to slice conversion:
        - left_boundary (1-indexed) -> left = left_boundary - 1 (0-indexed slice start)
        - right_boundary (1-indexed) -> right = right_boundary (slice end, exclusive)

        Example:
            left_boundary=101, right_boundary=412 (1-indexed)
            -> image[:, 100:412] crops pixels 100-411 (0-indexed)
            -> Cropped width = 312 pixels
        """
        height, width = self.image.shape[:2]

        # Determine crop range (convert to 0-indexed)
        left = (self.left_boundary - 1) if self.left_boundary else 0

        # Determine right boundary
        if self.right_boundary:
            # When enable_right is False and enable_same_margin is True, override right boundary
            if not self.enable_right and self.enable_same_margin and self.left_boundary:
                left_margin = self.left_boundary - 1
                right = width - left_margin
                print(f"Applying left margin width ({left_margin}px) to right side (--enable-same-margin)")
            else:
                # right_boundary is 1-indexed last pixel, so use it directly for slice end
                right = self.right_boundary
        elif self.enable_same_margin and self.left_boundary:
            # Apply same margin width from left to right
            left_margin = self.left_boundary - 1
            right = width - left_margin
            print(f"Applying left margin width ({left_margin}px) to right side (--enable-same-margin)")
        elif self.left_boundary and not self.enable_right:
            # When --enable-right is false, remove same width from right as left
            left_margin = self.left_boundary - 1
            right = width - left_margin
            print(f"Applying left margin width ({left_margin}px) to right side")
        else:
            right = width

        # Check if left boundary is to the right of right boundary
        if left >= right:
            print("Error: Invalid boundary range")
            return

        # Crop image
        cropped = self.image[:, left:right].copy()

        print(f"\nDisplaying preview with margins removed...")
        print(f"Original width: {width}, Cropped width: {cropped.shape[1]}")
        print(f"Left boundary (first pixel): {self.left_boundary or 'None'}, Right boundary (last pixel): {self.right_boundary or right}")
        print("Press 'q' to exit")

        # Display preview window
        cv2.imshow(self.preview_window_name, cropped)

        # Wait until 'q' key is pressed
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                cv2.destroyAllWindows()
                print("Exiting program")
                sys.exit(0)

    def run(self):
        """Main processing"""
        self.load_image()

        # Create window and set mouse callback
        cv2.namedWindow(self.main_window_name)
        cv2.setMouseCallback(self.main_window_name, self.mouse_callback)

        print("\nUsage:")
        print("- Click left half: Search boundary to the right")
        if self.enable_right:
            print("- Click right half: Search boundary to the left")
        else:
            print("- Right half processing is disabled (enable with --enable-right)")
        print("- Preview will be displayed after boundary detection")
        print("- Press 'q' to exit during preview\n")

        # Display image
        cv2.imshow(self.main_window_name, self.image)

        # Wait for key input
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(
        description="Detect image margins and display preview with margins removed"
    )
    parser.add_argument(
        "image",
        help="Path to the image file to process"
    )
    parser.add_argument(
        "--enable-right",
        action="store_true",
        help="Enable right half click processing"
    )
    parser.add_argument(
        "--enable-same-margin",
        action="store_true",
        help="Apply the same margin width from left side to right side"
    )

    args = parser.parse_args()

    detector = MarginDetector(args.image, args.enable_right, args.enable_same_margin)
    detector.run()


if __name__ == "__main__":
    main()
