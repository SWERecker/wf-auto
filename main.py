import json
import os
import random
import subprocess
import time
import sys
from urllib.parse import urljoin
from image_similarity_measures.quality_metrics import fsim

import cv2
import requests
from PIL import Image
import numpy as np

"""
----模拟器测试环境----
BlueStacks 5.4.100.1026 N64
Nougat 64 位元 (支援 Hyper-V) 版本

----模拟器设置----
显示  直向，720*1280，像素密度 240DPI(中等)
图形  图形引擎模式：效能
     图形渲染器：DirectX
     界面渲染器：Auto
进阶  安卓调试桥：开

* 其他模拟器未测试

----游戏----
世界弹射物语 官服
"""

bell_pos = [(18, 6), (75, 63)]  # 铃铛位置
awake_pos = [(300, 600), (400, 650)]  # 保持唤醒位置
full_pos = [(198, 762), (509, 863)]  # 房间已满员判断位置
full_continue_pos = [(225, 800), (500, 850)]    # 房间已满员继续按钮

main_pos = [(0, 1179), (108, 1279)]  # 主界面标识
main_btn_pos = [(131, 1195), (230, 1268)]  # 主城按钮
boss_pos = [(48, 296), (207, 420)]  # 怪物图像位置
accept_pos = [(385, 1043), (655, 1100)]  # 接受按钮位置
decline_pos = [(64, 1043), (333, 1100)]  # 拒绝按钮位置

prepare_pos = [(239, 905), (272, 938)]  # 准备按钮位置
continue_btn_pos = [(250, 1175), (455, 1225)]  # 继续按钮位置
continue_pos = [(285, 1185), (322, 1219)]  # 继续点击的位置

ref_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "reference")
results_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "results")

operation_delay = 0.7
threshold = 0.66
boss_threshold = 0.66
fast_connect = False
ip = "localhost"
port = "5555"

if len(sys.argv) > 1:
    for arg in sys.argv:
        if arg == "fast":
            fast_connect = True
        if arg.startswith("port"):
            port = arg.split('=')[1]
        if arg.startswith("ip"):
            ip = arg.split('=')[1]


def get_ref_image(file_name: str):
    return cv2.imread(os.path.join(ref_folder, file_name))[..., ::-1]


class Device:
    def __init__(self, device_ip):
        self.ip = device_ip
        self.friendly_name = ""

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

    def init(self, fast=False):
        """
        初始化adb，连接设备.

        :param fast: 快速连接，省去kill-server
        :return:
        """
        if not fast:
            print(self.shell('kill-server'))
            print(self.shell(f'connect {self.ip}'))
            self.friendly_name = self.shell("shell getprop ro.product.model")
            print("Device:", self.friendly_name)
        else:
            print("ADB Fast load Enabled.")
        print(self.shell(f'connect {self.ip}'))

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
            return cv2.imdecode(np.frombuffer(result.replace(b'\r\n', b'\n'), np.uint8), 1)
        else:
            raise Exception("无法正常截图，检查模拟器工作情况")
            # return None

    def touch(self, pos):
        """
        模拟触摸.

        :param pos: [x, y]
        :return: None
        """
        # print("Touching", pos)
        res = subprocess.Popen(f'adb -s {self.ip} shell input tap {pos[0]} {pos[1]}', shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res.wait()
        res.stdout.close()

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
        cv2.imwrite(os.path.join(ref_folder, f"boss_unknown_{timestamp}.bmp"), pic)


# def hist_similar(img1, img2):
#     """
#     直方图相似度计算
#
#     :param img1: 图像1
#     :param img2: 图像2
#     :return:
#     """
#     # r_size = (128, 128)
#     # gi1 = img1.resize(r_size).convert('RGB')
#     # gi2 = img2.resize(r_size).convert('RGB')
#     # assert len(gi1.histogram()) == len(gi2.histogram())
#     # hist = sum(
#     #     1 - (0 if l == r else float(abs(l - r)) / max(l, r))
#     #     for l, r in zip(gi1.histogram(), gi2.histogram())) / len(gi1.histogram())
#     # return hist
#     s = fsim(img1, img2)
#     print(f"fsim = {s}")
#     return s


def random_pos(area) -> [int, int]:
    """
    在某范围内随机一个触摸点

    :param area: [(x1, y1), (x2, y2)]
    :return: [x, y]
    """
    return random.randint(area[0][0], area[1][0]), random.randint(area[0][1], area[1][1])


def get_area_from_image(area, image):
    return image[area[0][1]:area[1][1], area[0][0]:area[1][0]]


def get_boss(_boss: Image, _ref: list) -> dict:
    for mon in _ref:
        _simi = fsim(_boss, mon["ref_img"])
        # print(f"Simi with {mon['friendly_name']} = {_simi}")
        if _simi > boss_threshold:
            return {
                "name": mon["name"],
                "friendly_name": mon["friendly_name"],
                "target": True if mon["target"] == 1 else False
            }
    return {
        "name": "unknown",
        "friendly_name": "未知怪物",
        "target": False
    }


# def cv2pil(src):
#     # return Image.fromarray(cv2.cvtColor(src, cv2.COLOR_BGR2RGB))
#     return src


def log(content):
    with open("record.txt", 'a', encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y%m%d_%H%M%S', time.localtime())} | {content}\n")


class Push:
    def __init__(self, base):
        self.base = base
        self.title = "世界弹射物语护肝助手"
        self.group = "世界弹射物语护肝助手"
        self.icon = "https://ossstatic.leiting.com/static/game/images/wf_ico.ico"

    def push(self, content):
        if self.base == "":
            print("Bark推送服务地址未配置！")
            return 
        requests.get(urljoin(self.base, f"{self.title}/{content}/"), params={"group": self.group, "icon": self.icon})


if __name__ == "__main__":
    with open("config.json", 'r', encoding='utf-8') as cfg:
        config = json.load(cfg)
    device = Device(f"{ip}:{port}")
    device.init(fast=fast_connect)
    boss_ref = []
    common_ref = {}
    idle_count = 0

    bark = Push(config["push"])
    for index in range(len(config["boss"])):
        ref_img_path = config["boss"][index]["ref_img"]
        config["boss"][index]["ref_img"] = get_ref_image(ref_img_path)
        boss_ref.append(config["boss"][index])

    for item in config["common"]:
        common_ref[item] = get_ref_image(config["common"][item])

    print("开始等待铃铛.", end="", flush=True)
    while True:
        room_full = False
        screenshot = device.screenshot()
        bell = get_area_from_image(bell_pos, screenshot)

        simi = fsim(bell, common_ref["bell"])
        # print("铃铛相似度：", simi)
        print(".", end="", flush=True)
        if simi > threshold:
            idle_count = 0
            print("\n识别到铃铛，点击")
            device.touch(random_pos(bell_pos))
            time.sleep(1)
            screenshot = device.screenshot()
            boss_info = get_boss(get_area_from_image(boss_pos, screenshot), boss_ref)
            print("怪物名称：", boss_info["friendly_name"])
            log(f"铃铛：{boss_info['friendly_name']}")
            if boss_info["name"] == "unknown":
                device.get_unknown_boss()
            if boss_info["target"]:
                print("是要刷的怪物，接受")
                device.touch(random_pos(accept_pos))
                time.sleep(1.5)
                screenshot = device.screenshot()
                room_full_simi = fsim(common_ref["full"],
                                      get_area_from_image(full_pos, screenshot))
                if room_full_simi > threshold:
                    print("房间已满，返回继续等待")
                    bark.push("进入房间失败：已满/正在开始")
                    device.touch(random_pos(full_continue_pos))
                    cv2.imwrite(
                        os.path.join(results_folder,
                                     f"{time.strftime('%Y%m%d_%H%M%S', time.localtime())}_{boss_info['name']}.jpg")
                        , screenshot
                    )
                    continue
                time.sleep(1)
                print("点击准备")
                device.touch(random_pos(prepare_pos))
                while True:
                    time.sleep(operation_delay)
                    screenshot = device.screenshot()
                    prepared_simi = fsim(common_ref["prepared"],
                                         get_area_from_image(prepare_pos, screenshot))
                    unprepared_simi = fsim(common_ref["unprepared"],
                                           get_area_from_image(prepare_pos, screenshot))
                    if prepared_simi > threshold:
                        print("已准备!")
                        break
                    elif unprepared_simi > threshold:
                        print("尚未准备...")
                        continue
                    else:
                        print("未找到准备标志，可能已经开始")
                        break
                print("正在等待结束.", end="", flush=True)
                while True:
                    screenshot = device.screenshot()
                    continue_simi = fsim(common_ref["continue"],
                                         get_area_from_image(continue_btn_pos, screenshot))
                    finish = True if continue_simi > threshold else False
                    main_simi = fsim(common_ref["main"],
                                     get_area_from_image(main_pos, screenshot))
                    finish_abnormal = True if main_simi > threshold else False
                    if finish:
                        print(f"\n{boss_info['friendly_name']} 已正常结束")
                        log(f"{boss_info['friendly_name']} 正常结束")
                        screenshot = device.screenshot()
                        cv2.imwrite(
                            os.path.join(results_folder,
                                         f"{time.strftime('%Y%m%d_%H%M%S', time.localtime())}.jpg"), screenshot)
                        bark.push(f"{boss_info['friendly_name']} 正常结束")
                        device.touch(random_pos(continue_pos))
                        break
                    else:
                        print(".", end="", flush=True)
                    if finish_abnormal:
                        print(f"{boss_info['friendly_name']} \n非正常结束")
                        log(f"{boss_info['friendly_name']} 未正常结束")
                        bark.push(f"{boss_info['friendly_name']} 未正常结束")
                        break
                    time.sleep(2)
                print("正在回到主界面.", end="", flush=True)
                while True:
                    screenshot = device.screenshot()
                    main_simi = fsim(common_ref["main"],
                                     get_area_from_image(main_pos, screenshot))
                    back_to_main = True if main_simi > threshold else False
                    if back_to_main:
                        device.touch(random_pos(main_btn_pos))
                        print("\n已回到主界面，继续等待铃铛", end="", flush=True)
                        break
                    else:
                        print(".", end="", flush=True)
                        device.touch(random_pos(continue_pos))
                    time.sleep(4)
            else:
                print("不是要刷的怪物，继续等待.", end="", flush=True)
                device.touch(random_pos(decline_pos))

        if idle_count == 80:
            print("Keep Awake")
            device.touch(random_pos(awake_pos))
            idle_count = 0
        time.sleep(operation_delay)
