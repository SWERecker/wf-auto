from wf_auto.pos import *
from wf_auto.device import Device
from wf_auto.util import *
import cv2

if __name__ == "__main__":
    pos = in_room_pos
    file = "common_in_room"
    # device = Device("localhost:8889", fast=True)
    # scr = device.screenshot()
    scr = cv2.imread("develop/9.bmp")
    # pic = cv2.cvtColor(get_area_from_image(pos, scr), cv2.COLOR_BGR2RGB)
    pic = get_area_from_image(pos, scr)
    cv2.imwrite(f"reference/{file}.bmp", pic)
