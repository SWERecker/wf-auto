from main import *
import cv2
import os

if __name__ == "__main__":
    pos = full_pos
    file = "common_full.bmp"
    # device = Device("localhost:13604")
    # device.init(fast=True)
    # scr = device.screenshot()
    scr = cv2.imread("develop/full.bmp")[..., ::-1]
    pic = cv2.cvtColor(get_area_from_image(pos, scr), cv2.COLOR_BGR2RGB)
    cv2.imwrite(os.path.join(ref_folder, file), pic)
