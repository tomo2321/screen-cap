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
- enable_right=False (default): Click left margin area to detect left boundary.
  The same margin width from the left side is automatically applied to the right side.
- enable_right=True: Click left margin area for left boundary, click right margin area for right boundary.
  Manual control of both boundaries.
- enable_vertical=False (default): Vertical margin detection disabled.
- enable_vertical=True: Click content area once to detect both top and bottom boundaries.
  Single click automatically detects both vertical boundaries.

Usage:
    python detect_margin.py <image_path> [--enable-right|-r] [--enable-vertical|-v]

Examples:
    # Automatic detection with same margin width applied to right side (default)
    python detect_margin.py image.png

    # Manual control for asymmetric horizontal margins
    python detect_margin.py image.png --enable-right

    # Detect vertical margins with single click
    python detect_margin.py image.png --enable-vertical

    # Detect both horizontal and vertical margins
    python detect_margin.py image.png --enable-right --enable-vertical

How it works:
Horizontal (left/right):
1. Click on a margin area (white/background region)
2. The script searches for brightness change toward content
3. Left: searches right, Right: searches left

Vertical (top/bottom):
1. Click on the content area (non-margin region)
2. The script searches both upward and downward for brightness changes
3. Both top and bottom boundaries are detected from a single click

All detected boundaries are displayed in 1-indexed format.
Preview window shows the image with margins removed.
Press 'q' in any window to exit.
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
        left_boundary (int): 1-indexed position of first content pixel horizontally (None if not detected)
        right_boundary (int): 1-indexed position of last content pixel horizontally (None if not detected)
        top_boundary (int): 1-indexed position of first content pixel vertically (None if not detected)
        bottom_boundary (int): 1-indexed position of last content pixel vertically (None if not detected)
        enable_right (bool): If False, automatically applies the same margin width from left side to right side
                             If True, requires manual right margin click for right boundary
        enable_vertical (bool): If False, vertical margin detection disabled
                               If True, single click on content area detects both top and bottom boundaries

    Detection behavior:
    - Horizontal: Click on margin areas (left or right) to search toward content
    - Vertical: Click on content area to search both upward and downward simultaneously

    Internal processing uses 0-indexed coordinates, but all user-facing values
    (display and boundary storage) use 1-indexed positions.
    """
    def __init__(self, image_path, enable_right=False, enable_vertical=False):
        self.image_path = image_path
        self.enable_right = enable_right
        self.enable_vertical = enable_vertical
        self.image = None
        self.gray = None
        self.left_boundary = None
        self.right_boundary = None
        self.top_boundary = None
        self.bottom_boundary = None
        self.preview_window_name = "Margin Removed Preview"
        self.current_click = None  # Store current click position

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

    def mouse_callback_left(self, event, x, y, flags, param):
        """Mouse callback for left margin detection"""
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        self.current_click = (x, y)

    def mouse_callback_right(self, event, x, y, flags, param):
        """Mouse callback for right margin detection"""
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        self.current_click = (x, y)

    def mouse_callback_vertical(self, event, x, y, flags, param):
        """Mouse callback for vertical margin detection"""
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        self.current_click = (x, y)

    def detect_left_margin(self):
        """Detect left margin with dedicated window"""
        window_name = "Click image to detect left margin"
        cv2.namedWindow(window_name)
        cv2.setMouseCallback(window_name, self.mouse_callback_left)
        cv2.imshow(window_name, self.image)

        print("\n=== Detecting Left Margin ===")
        print("Click on the left margin area (white/background region)")
        print("The script will search to the right for the content boundary")

        self.current_click = None
        while self.current_click is None:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                sys.exit(0)

        x, y = self.current_click
        print(f"Click position: ({x + 1}, {y + 1})")

        boundary = self.find_boundary_right(x, y)
        if boundary:
            self.left_boundary = boundary
            print(f"Left boundary detected: x = {boundary} (first pixel of content, 1-indexed)")
        else:
            print("Left boundary not found")

        # Auto-detect right margin if enable_right is False
        if not self.enable_right:
            height, width = self.gray.shape
            half_width = width // 2
            distance_from_center = half_width - x
            right_x = half_width + distance_from_center
            right_x = min(right_x, width - 1)
            print(f"Automatically searching from mirrored position x = {right_x + 1} (1-indexed) at y = {y + 1}")
            boundary = self.find_boundary_left(right_x, y)
            if boundary:
                self.right_boundary = boundary
                print(f"Right boundary detected: x = {boundary} (last pixel of content, 1-indexed)")
            else:
                print("Right boundary not found")

        cv2.destroyWindow(window_name)

    def detect_right_margin(self):
        """Detect right margin with dedicated window"""
        window_name = "Click image to detect right margin"
        cv2.namedWindow(window_name)
        cv2.setMouseCallback(window_name, self.mouse_callback_right)
        cv2.imshow(window_name, self.image)

        print("\n=== Detecting Right Margin ===")
        print("Click on the right margin area (white/background region)")
        print("The script will search to the left for the content boundary")

        self.current_click = None
        while self.current_click is None:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                sys.exit(0)

        x, y = self.current_click
        print(f"Click position: ({x + 1}, {y + 1})")

        boundary = self.find_boundary_left(x, y)
        if boundary:
            self.right_boundary = boundary
            print(f"Right boundary detected: x = {boundary} (last pixel of content, 1-indexed)")
        else:
            print("Right boundary not found")

        cv2.destroyWindow(window_name)

    def detect_vertical_margin(self):
        """
        Detect vertical margins (top and bottom) with dedicated window

        This method detects both top and bottom boundaries from a single click on the content area.
        The user clicks on a non-margin (content) region, and the script:
        1. Searches upward to find where content begins (top boundary)
        2. Searches downward to find where content ends (bottom boundary)

        Click position brightness is used as reference (content brightness).
        Boundaries are detected where brightness changes from content to margin.

        Returns both boundaries as 1-indexed positions representing the first and last
        rows of content pixels.
        """
        window_name = "Click image to detect vertical margin"
        cv2.namedWindow(window_name)
        cv2.setMouseCallback(window_name, self.mouse_callback_vertical)
        cv2.imshow(window_name, self.image)

        print("\n=== Detecting Vertical Margins ===")
        print("Click on the content area (non-margin region)")
        print("The script will search both upward and downward for boundaries")

        self.current_click = None
        while self.current_click is None:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                sys.exit(0)

        x, y = self.current_click
        print(f"Click position: ({x + 1}, {y + 1})")

        # Search upward for top boundary (first content pixel)
        boundary = self.find_boundary_up_for_top(x, y)
        if boundary:
            self.top_boundary = boundary
            print(f"Top boundary detected: y = {boundary} (first pixel of content, 1-indexed)")
        else:
            print("Top boundary not found")

        # Search downward for bottom boundary (last content pixel)
        boundary = self.find_boundary_down_for_bottom(x, y)
        if boundary:
            self.bottom_boundary = boundary
            print(f"Bottom boundary detected: y = {boundary} (last pixel of content, 1-indexed)")
        else:
            print("Bottom boundary not found")

        cv2.destroyWindow(window_name)

    def find_boundary_up_for_top(self, x, y):
        """
        Search upward from click position to find first content pixel (top boundary)

        Starting from the click position (which should be in content area), searches upward
        until brightness changes (indicating transition from content to margin).

        Args:
            x, y: Click position (0-indexed) in content area

        Returns:
            int: 1-indexed y-coordinate of first content pixel (top boundary)
                 Returns 1 if no margin found above (content starts at top)

        Example:
            Image with rows 0-99 white (margin), rows 100-511 black (content)
            Click at row 200 (black content) -> searches up -> finds change at row 99
            Returns 101 (1-indexed position of row 100, first content pixel)
        """
        # Use the brightness value at click position as reference
        base_value = self.gray[y, x]

        # Search upward
        for i in range(y - 1, -1, -1):
            current_value = self.gray[i, x]
            # When brightness changes, the next pixel down is the first content pixel
            if current_value != base_value:
                return i + 2  # i+1 is 1-indexed pixel where brightness changed, i+2 is first content pixel

        # If no change found, top boundary is the first pixel
        return 1

    def find_boundary_down_for_bottom(self, x, y):
        """
        Search downward from click position to find last content pixel (bottom boundary)

        Starting from the click position (which should be in content area), searches downward
        until brightness changes (indicating transition from content to margin).

        Args:
            x, y: Click position (0-indexed) in content area

        Returns:
            int: 1-indexed y-coordinate of last content pixel (bottom boundary)
                 Returns image height if no margin found below (content extends to bottom)

        Example:
            Image with rows 0-411 black (content), rows 412-511 white (margin)
            Click at row 200 (black content) -> searches down -> finds change at row 412
            Returns 412 (1-indexed position of row 411 + 1, but we want row 411, so returns i)
            Note: Due to 0/1-indexed conversion, returns i which equals 412 in 1-indexed
        """
        height, width = self.gray.shape

        # Use the brightness value at click position as reference
        base_value = self.gray[y, x]

        # Search downward
        for i in range(y + 1, height):
            current_value = self.gray[i, x]
            # When brightness changes, the previous pixel is the last content pixel
            if current_value != base_value:
                return i  # i is 0-indexed, but we want the previous pixel in 1-indexed, which is i

        # If no change found, bottom boundary is the last pixel
        return height

    def show_preview(self):
        """
        Display preview with margins removed

        Crops the image based on detected boundaries and displays the result.

        Cropping logic (horizontal):
        - If right_boundary is set:
          * With enable_right=False (default): Overrides right boundary
            with left margin width from left side
          * With enable_right=True: Uses detected right boundary directly
        - If only left_boundary is set:
          * With enable_right=False (default): Applies left margin width to right side
          * Otherwise: No cropping on right side
        - Otherwise: No cropping on respective side

        Cropping logic (vertical):
        - If enable_vertical=True: Uses detected top_boundary and bottom_boundary
        - Otherwise: No cropping on vertical direction

        Boundary to slice conversion:
        - left_boundary (1-indexed) -> left = left_boundary - 1 (0-indexed slice start)
        - right_boundary (1-indexed) -> right = right_boundary (slice end, exclusive)
        - top_boundary (1-indexed) -> top = top_boundary - 1 (0-indexed slice start)
        - bottom_boundary (1-indexed) -> bottom = bottom_boundary (slice end, exclusive)

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
            # When enable_right is False, override right boundary with left margin width
            if not self.enable_right and self.left_boundary:
                left_margin = self.left_boundary - 1
                right = width - left_margin
                print(f"Applying left margin width ({left_margin}px) to right side")
            else:
                # right_boundary is 1-indexed last pixel, so use it directly for slice end
                right = self.right_boundary
        elif self.left_boundary and not self.enable_right:
            # When --enable-right is false, remove same width from right as left
            left_margin = self.left_boundary - 1
            right = width - left_margin
            print(f"Applying left margin width ({left_margin}px) to right side")
        else:
            right = width

        # Check if left boundary is to the right of right boundary
        if left >= right:
            print("Error: Invalid horizontal boundary range")
            return

        # Determine vertical crop range (convert to 0-indexed)
        # top_boundary is the first content pixel (1-indexed), convert to 0-indexed for slice start
        top = (self.top_boundary - 1) if self.top_boundary else 0
        # bottom_boundary is the last content pixel (1-indexed), convert to slice end (exclusive)
        bottom = self.bottom_boundary if self.bottom_boundary else height

        # Check if top boundary is below bottom boundary
        if top >= bottom:
            print("Error: Invalid vertical boundary range")
            return

        # Crop image (vertical then horizontal)
        cropped = self.image[top:bottom, left:right].copy()

        print(f"\nDisplaying preview with margins removed...")
        print(f"Original size: {width}x{height}, Cropped size: {cropped.shape[1]}x{cropped.shape[0]}")
        print(f"Horizontal - Left boundary (first pixel): {self.left_boundary or 'None'}, Right boundary (last pixel): {self.right_boundary or right}")
        print(f"Vertical - Top boundary (first pixel): {self.top_boundary or 'None'}, Bottom boundary (last pixel): {self.bottom_boundary or bottom}")
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

        print("\n" + "="*50)
        print("Margin Detection Tool")
        print("="*50)
        print("Press 'q' at any time to exit\n")

        # Detect left margin (always)
        self.detect_left_margin()

        # Detect right margin if enabled
        if self.enable_right:
            self.detect_right_margin()

        # Detect vertical margins if enabled
        if self.enable_vertical:
            self.detect_vertical_margin()

        # Show preview
        if self.left_boundary or self.right_boundary or self.top_boundary or self.bottom_boundary:
            self.show_preview()
        else:
            print("\nNo boundaries detected")
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
        "--enable-right", "-r",
        action="store_true",
        help="Enable right half click processing"
    )
    parser.add_argument(
        "--enable-vertical", "-v",
        action="store_true",
        help="Enable vertical margin detection (top/bottom)"
    )

    args = parser.parse_args()

    detector = MarginDetector(args.image, args.enable_right, args.enable_vertical)
    detector.run()


if __name__ == "__main__":
    main()
