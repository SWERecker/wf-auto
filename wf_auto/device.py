import os
import subprocess
import time

import cv2
import numpy as np

from .util import get_area_from_image, log
from .pos import boss_pos


class Device:
    def __init__(self, device_ip, fast=False):
        self.ip = device_ip
        self.friendly_name = ""
        self.inited = False
        if fast:
            print("ADB Fast load Enabled.")
            print(self.shell(f'connect {self.ip}'))
        else:
            print(self.shell('kill-server'))
            print(self.shell(f'connect {self.ip}'))
            self.friendly_name = self.shell("shell getprop ro.product.model")
            print("Device:", self.friendly_name)
        self.sdk = int(self.shell("shell getprop ro.build.version.sdk").replace('\n', ""))

    def shell(self, cmd):
        """
        执行shell command.

        :param cmd: 要执行的命令
        :return: 执行的返回值
        """
        # print("Executing " + f"adb -s {self.ip} {cmd}")
        res = subprocess.Popen(f"adb -s {self.ip} {cmd}", shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf8')
        result = res.stdout.read()
        res.wait()
        res.stdout.close()
        if res.poll() == 0:
            return result.replace('\r\n', '\n')
        else:
            return 'Operation Error'

    def screenshot(self):
        """
        截图

        :return: 截图
        """
        res = subprocess.Popen(f'adb -s {self.ip} shell screencap -p', shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = res.stdout.read()
        res.wait()
        res.stdout.close()
        if res.poll() == 0:
            if self.sdk > 23:
                return cv2.imdecode(np.frombuffer(result.replace(b'\r\n', b'\n'), np.uint8), 1)
            else:
                return cv2.imdecode(np.frombuffer(result.replace(b'\r\r\n', b'\n'), np.uint8), 1)
        else:
            raise Exception("无法正常截图，检查模拟器工作情况")

    def touch(self, _pos):
        """
        模拟触摸.

        :param _pos: [x, y]
        :return: None
        """
        # print("Touching", pos)
        res = subprocess.Popen(f'adb -s {self.ip} shell input tap {_pos[0]} {_pos[1]}', shell=True,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res.wait()
        res.stdout.close()

    def button(self, btn_name=""):
        btns = {
            "KEYCODE_HOME": 3,
            "KEYCODE_BACK": 4
        }
        self.shell(f"shell input keyevent {btns[btn_name]}")

    def get_unknown_boss(self):
        """
        如果遇到未知的怪物，自动截图存储至reference文件夹下备用.

        :return: None
        """
        print("未知怪物，存储备用")
        scr = self.screenshot()
        pic = get_area_from_image(boss_pos, scr)
        timestamp = int(time.time())
        log(f"记录未知怪物 boss_unknown_{timestamp}.bmp")
        cv2.imwrite(f"reference/boss_unknown_{timestamp}.bmp", pic)
