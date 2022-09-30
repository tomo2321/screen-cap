import os
import time

import pyautogui as pag


MAX_PAGE_NUM = 10000
pag.PAUSE = 1.5


def main(
    save_dir,
    total_page_num: int = MAX_PAGE_NUM,
    next_page_direction: str = 'right',
    verbose: bool =True,
) -> None:

    if verbose:
        print(f"total page num: {total_page_num}")
        print(f"save dir: {save_dir}")

    time.sleep(10)

    os.makedirs(save_dir, exist_ok=True)
    for i in range(total_page_num):
        save_filepath = f"{save_dir}/{i:04d}.png"
        if verbose:
            print(f"save: {save_filepath}")
        pag.screenshot(save_filepath)
        pag.hotkey(next_page_direction)


if __name__ == '__main__':

    save_dir = 'figs/title'
    total_page_num = 123

    main(save_dir, total_page_num)
