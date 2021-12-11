from wf_auto.pos import *
from wf_auto.device import Device
from wf_auto.util import *
import cv2

if __name__ == "__main__":
    pos = main_pos
    file = "common_main"
    device = Device("localhost:8889", fast=True)
    scr = device.screenshot()
    # scr = cv2.imread("develop/de.bmp")[..., ::-1]
    pic = cv2.cvtColor(get_area_from_image(pos, scr), cv2.COLOR_BGR2RGB)
    cv2.imwrite(f"reference/{file}.bmp", pic)
