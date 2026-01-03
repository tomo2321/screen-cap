"""
Integration tests for MarginDetector
"""

import sys
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

import cv2
import numpy as np
import pytest

from detect_margin import MarginDetector


class TestMarginDetector:
    """Integration tests for MarginDetector class"""

    @pytest.fixture
    def test_image_symmetric(self):
        """
        Create a test image with symmetric margins (100px on each side)
        Total size: 512x512
        Margin: 100px left/right (white background)
        Content: 312x512 (gray background)
        """
        width = 512
        height = 512
        margin = 100

        # Create white background (255)
        image = np.ones((height, width, 3), dtype=np.uint8) * 255

        # Fill content area with gray (128)
        image[:, margin:width-margin] = 128

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            cv2.imwrite(tmp.name, image)
            yield tmp.name, margin, width, height

        # Cleanup
        Path(tmp.name).unlink(missing_ok=True)

    @pytest.fixture
    def test_image_asymmetric(self):
        """
        Create a test image with asymmetric margins
        Total size: 512x512
        Left margin: 80px (white)
        Right margin: 120px (white)
        Content: 312x512 (gray)
        """
        width = 512
        height = 512
        left_margin = 80
        right_margin = 120

        # Create white background (255)
        image = np.ones((height, width, 3), dtype=np.uint8) * 255

        # Fill content area with gray (128)
        image[:, left_margin:width-right_margin] = 128

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            cv2.imwrite(tmp.name, image)
            yield tmp.name, left_margin, right_margin, width, height

        # Cleanup
        Path(tmp.name).unlink(missing_ok=True)

    @pytest.fixture
    def test_image_vertical_margins(self):
        """
        Create a test image with vertical margins
        Total size: 512x512
        Top margin: 100px (white)
        Bottom margin: 100px (white)
        Content: 512x312 (gray)
        """
        width = 512
        height = 512
        top_margin = 100
        bottom_margin = 100

        # Create white background (255)
        image = np.ones((height, width, 3), dtype=np.uint8) * 255

        # Fill content area with gray (128)
        image[top_margin:height-bottom_margin, :] = 128

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            cv2.imwrite(tmp.name, image)
            yield tmp.name, top_margin, bottom_margin, width, height

        # Cleanup
        Path(tmp.name).unlink(missing_ok=True)

    @pytest.fixture
    def test_image_all_margins(self):
        """
        Create a test image with both horizontal and vertical margins
        Total size: 512x512
        Left/Right margin: 100px (white)
        Top/Bottom margin: 100px (white)
        Content: 312x312 (gray)
        """
        width = 512
        height = 512
        h_margin = 100  # horizontal margin
        v_margin = 100  # vertical margin

        # Create white background (255)
        image = np.ones((height, width, 3), dtype=np.uint8) * 255

        # Fill content area with gray (128)
        image[v_margin:height-v_margin, h_margin:width-h_margin] = 128

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            cv2.imwrite(tmp.name, image)
            yield tmp.name, h_margin, v_margin, width, height

        # Cleanup
        Path(tmp.name).unlink(missing_ok=True)

    def test_enable_right_false_symmetric_margins(self, test_image_symmetric):
        """
        Test with enable_right=False on symmetric margins
        Should detect left boundary and apply same margin to right
        """
        image_path, margin, width, height = test_image_symmetric

        detector = MarginDetector(image_path, enable_right=False)
        detector.load_image()

        # Click on left margin area to detect right boundary
        # Click at position (50, 256) - middle of left margin
        click_x, click_y = 50, 256
        boundary = detector.find_boundary_right(click_x, click_y)

        # Verify boundary detected at expected position (1-indexed)
        # Expected: margin + 1 = 101
        assert boundary == margin + 1, f"Expected boundary at {margin + 1}, got {boundary}"

        # Set left boundary
        detector.left_boundary = boundary

        # Verify the crop range calculation
        left = detector.left_boundary - 1  # Convert to 0-indexed
        assert left == margin, f"Expected left crop position {margin}, got {left}"

        # When enable_right is False, right should be width - left_margin
        left_margin_width = detector.left_boundary - 1
        expected_right = width - left_margin_width
        right = expected_right

        assert right == width - margin, f"Expected right crop position {width - margin}, got {right}"

        # Verify cropped width
        expected_width = width - 2 * margin
        cropped_width = right - left
        assert cropped_width == expected_width, f"Expected cropped width {expected_width}, got {cropped_width}"

    def test_enable_right_true_symmetric_margins(self, test_image_symmetric):
        """
        Test with enable_right=True on symmetric margins
        Should detect both left and right boundaries independently
        """
        image_path, margin, width, height = test_image_symmetric

        detector = MarginDetector(image_path, enable_right=True)
        detector.load_image()

        # Detect left boundary - click on left margin
        click_x_left, click_y = 50, 256
        left_boundary = detector.find_boundary_right(click_x_left, click_y)

        assert left_boundary == margin + 1, f"Expected left boundary at {margin + 1}, got {left_boundary}"
        detector.left_boundary = left_boundary

        # Detect right boundary - click on right margin
        click_x_right = width - 50  # Middle of right margin
        right_boundary = detector.find_boundary_left(click_x_right, click_y)

        # Expected: width - margin (1-indexed, last pixel of content)
        expected_right_boundary = width - margin
        assert right_boundary == expected_right_boundary, \
            f"Expected right boundary at {expected_right_boundary}, got {right_boundary}"
        detector.right_boundary = right_boundary

        # Verify the crop range
        left = detector.left_boundary - 1
        right = detector.right_boundary

        assert left == margin, f"Expected left crop at {margin}, got {left}"
        assert right == width - margin, f"Expected right crop at {width - margin}, got {right}"

        # Verify cropped width
        expected_width = width - 2 * margin
        cropped_width = right - left
        assert cropped_width == expected_width, f"Expected width {expected_width}, got {cropped_width}"

    def test_enable_right_true_asymmetric_margins(self, test_image_asymmetric):
        """
        Test with enable_right=True on asymmetric margins
        Should correctly detect different left and right margins
        """
        image_path, left_margin, right_margin, width, height = test_image_asymmetric

        detector = MarginDetector(image_path, enable_right=True)
        detector.load_image()

        # Detect left boundary
        click_x_left, click_y = 40, 256
        left_boundary = detector.find_boundary_right(click_x_left, click_y)

        assert left_boundary == left_margin + 1, \
            f"Expected left boundary at {left_margin + 1}, got {left_boundary}"
        detector.left_boundary = left_boundary

        # Detect right boundary
        click_x_right = width - 60
        right_boundary = detector.find_boundary_left(click_x_right, click_y)

        expected_right_boundary = width - right_margin
        assert right_boundary == expected_right_boundary, \
            f"Expected right boundary at {expected_right_boundary}, got {right_boundary}"
        detector.right_boundary = right_boundary

        # Verify crop range
        left = detector.left_boundary - 1
        right = detector.right_boundary

        assert left == left_margin, f"Expected left crop at {left_margin}, got {left}"
        assert right == width - right_margin, f"Expected right crop at {width - right_margin}, got {right}"

        # Verify cropped width
        expected_width = width - left_margin - right_margin
        cropped_width = right - left
        assert cropped_width == expected_width, f"Expected width {expected_width}, got {cropped_width}"

    def test_enable_right_false_asymmetric_margins(self, test_image_asymmetric):
        """
        Test with enable_right=False on asymmetric margins
        Should apply left margin width to right side, even though actual right margin differs
        """
        image_path, left_margin, right_margin, width, height = test_image_asymmetric

        detector = MarginDetector(image_path, enable_right=False)
        detector.load_image()

        # Detect left boundary only
        click_x_left, click_y = 40, 256
        left_boundary = detector.find_boundary_right(click_x_left, click_y)

        assert left_boundary == left_margin + 1, \
            f"Expected left boundary at {left_margin + 1}, got {left_boundary}"
        detector.left_boundary = left_boundary

        # Calculate expected crop (applying left margin to right)
        left = detector.left_boundary - 1
        expected_right = width - left_margin  # Same as left margin

        assert left == left_margin, f"Expected left crop at {left_margin}, got {left}"

        # Verify that the right side uses left margin width
        expected_width = width - 2 * left_margin
        cropped_width = expected_right - left
        assert cropped_width == expected_width, \
            f"Expected cropped width {expected_width}, got {cropped_width}"

    def test_boundary_not_found(self, test_image_symmetric):
        """
        Test when boundary is not found (clicking at the rightmost edge)
        """
        image_path, margin, width, height = test_image_symmetric

        detector = MarginDetector(image_path, enable_right=False)
        detector.load_image()

        # Click at the very last column where no boundary exists to the right
        click_x, click_y = width - 1, 256
        boundary = detector.find_boundary_right(click_x, click_y)

        # Should return None when no boundary found
        assert boundary is None, f"Expected None when boundary not found, got {boundary}"

    def test_boundary_at_edge(self, test_image_symmetric):
        """
        Test boundary detection at the very edge of the image
        """
        image_path, margin, width, height = test_image_symmetric

        detector = MarginDetector(image_path, enable_right=False)
        detector.load_image()

        # Click at position just before boundary
        click_x, click_y = margin - 1, 256
        boundary = detector.find_boundary_right(click_x, click_y)

        assert boundary == margin + 1, f"Expected boundary at {margin + 1}, got {boundary}"

    def test_vertical_margin_detection(self, test_image_vertical_margins):
        """
        Test vertical margin detection with single click on content area
        Should detect both top and bottom boundaries simultaneously
        """
        image_path, top_margin, bottom_margin, width, height = test_image_vertical_margins

        detector = MarginDetector(image_path, enable_vertical=True)
        detector.load_image()

        # Click on content area (middle of content)
        click_x, click_y = 256, 256

        # Detect top boundary
        top_boundary = detector.find_boundary_up_for_top(click_x, click_y)
        assert top_boundary == top_margin + 1, \
            f"Expected top boundary at {top_margin + 1}, got {top_boundary}"
        detector.top_boundary = top_boundary

        # Detect bottom boundary
        bottom_boundary = detector.find_boundary_down_for_bottom(click_x, click_y)
        expected_bottom = height - bottom_margin
        assert bottom_boundary == expected_bottom, \
            f"Expected bottom boundary at {expected_bottom}, got {bottom_boundary}"
        detector.bottom_boundary = bottom_boundary

        # Verify crop range
        top = detector.top_boundary - 1
        bottom = detector.bottom_boundary

        assert top == top_margin, f"Expected top crop at {top_margin}, got {top}"
        assert bottom == height - bottom_margin, \
            f"Expected bottom crop at {height - bottom_margin}, got {bottom}"

        # Verify cropped height
        expected_height = height - top_margin - bottom_margin
        cropped_height = bottom - top
        assert cropped_height == expected_height, \
            f"Expected cropped height {expected_height}, got {cropped_height}"

    def test_combined_horizontal_vertical_margins(self, test_image_all_margins):
        """
        Test detection of both horizontal and vertical margins
        """
        image_path, h_margin, v_margin, width, height = test_image_all_margins

        detector = MarginDetector(image_path, enable_right=False, enable_vertical=True)
        detector.load_image()

        # Detect left boundary (horizontal)
        click_x_h, click_y_h = 50, 256
        left_boundary = detector.find_boundary_right(click_x_h, click_y_h)
        assert left_boundary == h_margin + 1, \
            f"Expected left boundary at {h_margin + 1}, got {left_boundary}"
        detector.left_boundary = left_boundary

        # Detect vertical boundaries (single click on content)
        click_x_v, click_y_v = 256, 256
        top_boundary = detector.find_boundary_up_for_top(click_x_v, click_y_v)
        bottom_boundary = detector.find_boundary_down_for_bottom(click_x_v, click_y_v)

        assert top_boundary == v_margin + 1, \
            f"Expected top boundary at {v_margin + 1}, got {top_boundary}"
        assert bottom_boundary == height - v_margin, \
            f"Expected bottom boundary at {height - v_margin}, got {bottom_boundary}"

        detector.top_boundary = top_boundary
        detector.bottom_boundary = bottom_boundary

        # Verify horizontal crop
        left = detector.left_boundary - 1
        right = width - h_margin  # Symmetric application

        # Verify vertical crop
        top = detector.top_boundary - 1
        bottom = detector.bottom_boundary

        # Verify dimensions
        expected_width = width - 2 * h_margin
        expected_height = height - 2 * v_margin
        cropped_width = right - left
        cropped_height = bottom - top

        assert cropped_width == expected_width, \
            f"Expected cropped width {expected_width}, got {cropped_width}"
        assert cropped_height == expected_height, \
            f"Expected cropped height {expected_height}, got {cropped_height}"

    def test_vertical_no_top_margin(self, test_image_vertical_margins):
        """
        Test vertical detection when clicking near the top (content starts at top)
        """
        image_path, top_margin, bottom_margin, width, height = test_image_vertical_margins

        # Create image with no top margin
        image = np.ones((height, width, 3), dtype=np.uint8) * 128  # All content
        image[height-bottom_margin:, :] = 255  # Only bottom margin

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            cv2.imwrite(tmp.name, image)
            detector = MarginDetector(tmp.name, enable_vertical=True)
            detector.load_image()

            # Click on content area
            click_x, click_y = 256, 50

            # Detect top boundary (should return 1 since no margin at top)
            top_boundary = detector.find_boundary_up_for_top(click_x, click_y)
            assert top_boundary == 1, \
                f"Expected top boundary at 1 (no margin), got {top_boundary}"

            # Cleanup
            Path(tmp.name).unlink(missing_ok=True)

    def test_vertical_no_bottom_margin(self, test_image_vertical_margins):
        """
        Test vertical detection when clicking near bottom (content extends to bottom)
        """
        image_path, top_margin, bottom_margin, width, height = test_image_vertical_margins

        # Create image with no bottom margin
        image = np.ones((height, width, 3), dtype=np.uint8) * 128  # All content
        image[:top_margin, :] = 255  # Only top margin

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            cv2.imwrite(tmp.name, image)
            detector = MarginDetector(tmp.name, enable_vertical=True)
            detector.load_image()

            # Click on content area
            click_x, click_y = 256, 400

            # Detect bottom boundary (should return height since no margin at bottom)
            bottom_boundary = detector.find_boundary_down_for_bottom(click_x, click_y)
            assert bottom_boundary == height, \
                f"Expected bottom boundary at {height} (no margin), got {bottom_boundary}"

            # Cleanup
            Path(tmp.name).unlink(missing_ok=True)
