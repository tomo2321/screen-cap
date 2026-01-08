"""
Capture screenshots of pages in an application (e.g., PDF viewer) and save them as image files.
"""

import argparse
import os
import time
from datetime import datetime

import pyautogui as pag

MAX_PAGE_NUM = 10000
pag.PAUSE = 1.5


def capture(
    save_dir,
    total_page_num: int = MAX_PAGE_NUM,
    next_page_direction: str = "right",
) -> None:
    """
    Capture screenshots continuously

    Args:
        save_dir: Save directory
        total_page_num: Number of pages to capture
        next_page_direction: Key to advance to next page (default: "right")
    """
    print(f"total page num: {total_page_num}")
    print(f"save dir: {save_dir}")

    time.sleep(10)

    os.makedirs(save_dir, exist_ok=True)
    for i in range(total_page_num):
        save_filepath = f"{save_dir}/{i:04d}.png"
        print(f"save: {save_filepath}")

        screenshot = pag.screenshot()
        screenshot.save(save_filepath)

        pag.hotkey(next_page_direction)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture screenshots of pages in an application"
    )

    parser.add_argument(
        "--save-dir",
        type=str,
        default=f"figs/{datetime.today().strftime('%Y-%m-%d_%H:%M:%S')}",
        help="Directory to save screenshots (default: figs/YYYY-MM-DD_HH:MM:SS)",
    )
    parser.add_argument(
        "--total-page-num",
        type=int,
        default=MAX_PAGE_NUM,
        help=f"Number of pages to capture (default: {MAX_PAGE_NUM})",
    )
    parser.add_argument(
        "--next-page-direction",
        type=str,
        default="right",
        choices=["right", "left"],
        help="Key to advance to next page (default: right)",
    )

    args = parser.parse_args()

    capture(
        save_dir=args.save_dir,
        total_page_num=args.total_page_num,
        next_page_direction=args.next_page_direction,
    )


if __name__ == "__main__":
    main()
