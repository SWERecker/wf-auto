import os
from time import sleep
import time
import sys

from image_similarity_measures.quality_metrics import fsim
import cv2

from wf_auto import *


ref_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "reference")
results_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "results")

operation_delay = 0.7
threshold = 0.64
boss_threshold = 0.64
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

if __name__ == "__main__":
    config = util.get_config()
    device = device.Device(f"{ip}:{port}", fast=fast_connect)
    bark = bark.Push(config["push"])

    boss_ref = []
    common_ref = {}
    for index in range(len(config["boss"])):
        ref_img = config["boss"][index]["ref_img"]
        config["boss"][index]["ref_img"] = util.get_ref_image(ref_folder, ref_img)
        boss_ref.append(config["boss"][index])
    for item in config["common"]:
        common_ref[item] = util.get_ref_image(ref_folder, config["common"][item])

    idle_count = 0
    skip_filter_boss = True if config["filter_boss"] == 0 else False

    print("开始等待铃铛.", end="", flush=True)
    try:
        while True:
            screenshot = device.screenshot()

            bell = util.get_area_from_image(pos.bell_pos, screenshot)
            simi = fsim(bell, common_ref["bell"])
            # print("铃铛相似度：", simi)
            print(".", end="", flush=True)
            if simi > threshold:
                idle_count = 0
                print("\n识别到铃铛，点击")
                device.touch(util.random_pos(pos.bell_pos))
                sleep(1)
                screenshot = device.screenshot()
                boss_info = util.get_boss(util.get_area_from_image(pos.boss_pos, screenshot), boss_ref, boss_threshold)
                print("怪物名称：", boss_info["friendly_name"])
                util.log(f"铃铛：{boss_info['friendly_name']}")
                if boss_info["name"] == "unknown":
                    device.get_unknown_boss()
                if boss_info["target"] or skip_filter_boss:
                    print("是要刷的怪物，接受")
                    device.touch(util.random_pos(pos.accept_pos))
                    sleep(1.5)
                    screenshot = device.screenshot()
                    room_full_simi = fsim(common_ref["full"],
                                          util.get_area_from_image(pos.full_pos, screenshot))
                    if room_full_simi > threshold:
                        print("房间已满，返回继续等待")
                        bark.push("进入房间失败：已满或正在开始")
                        device.touch(util.random_pos(pos.full_continue_pos))
                        continue
                    sleep(1)
                    print("点击准备")
                    while True:
                        device.touch(util.random_pos(pos.prepare_pos))
                        sleep(operation_delay)
                        screenshot = device.screenshot()
                        prepared_simi = fsim(common_ref["prepared"],
                                             util.get_area_from_image(pos.prepare_pos, screenshot))
                        unprepared_simi = fsim(common_ref["unprepared"],
                                               util.get_area_from_image(pos.prepare_pos, screenshot))
                        if prepared_simi > threshold:
                            print("已准备!")
                            break
                        elif unprepared_simi > threshold:
                            print("尚未准备...")
                            continue
                        else:
                            print("未找到准备标志，可能已经开始")
                            break
                    print("\n正在等待结束.", end="", flush=True)
                    while True:
                        screenshot = device.screenshot()
                        continue_simi = fsim(common_ref["continue"],
                                             util.get_area_from_image(pos.continue_btn_pos, screenshot))
                        finish = True if continue_simi > threshold else False
                        main_simi = fsim(common_ref["main"],
                                         util.get_area_from_image(pos.main_pos, screenshot))
                        finish_abnormal = True if main_simi > threshold else False
                        dismiss_simi = fsim(common_ref["full"],
                                            util.get_area_from_image(pos.full_pos, screenshot))
                        room_dismiss = True if dismiss_simi > threshold else False
                        if finish:
                            print(f"\n{boss_info['friendly_name']} 已正常结束")
                            util.log(f"{boss_info['friendly_name']} 已正常结束")
                            file_name = f"{time.strftime('%Y%m%d_%H%M%S', time.localtime())}_{boss_info['name']}.jpg"
                            cv2.imwrite(os.path.join(results_folder, file_name), screenshot)
                            bark.push(f"{boss_info['friendly_name']} 正常结束")
                            device.touch(util.random_pos(pos.continue_pos))
                            break
                        else:
                            print(".", end="", flush=True)
                        if finish_abnormal:
                            msg = f"{boss_info['friendly_name']} 非正常结束"
                            print(msg)
                            util.log(msg)
                            bark.push(msg)
                            break
                        if room_dismiss:
                            msg = f"{boss_info['friendly_name']} 房间已解散"
                            print(msg)
                            util.log(msg)
                            bark.push(msg)
                        sleep(3)
                    print("\n正在回到主界面.", end="", flush=True)
                    attempt_count = 0
                    while True:
                        screenshot = device.screenshot()
                        main_simi = fsim(common_ref["main"],
                                         util.get_area_from_image(pos.main_pos, screenshot))
                        back_to_main = True if main_simi > threshold else False
                        if back_to_main:
                            device.touch(util.random_pos(pos.main_btn_pos))
                            print("\n已回到主界面，继续等待铃铛", end="", flush=True)
                            break
                        else:
                            print(".", end="", flush=True)
                            device.touch(util.random_pos(pos.continue_pos))
                        attempt_count += 1
                        if attempt_count > 5:
                            print("似乎返回主界面失败，尝试使用返回键")
                            device.button("KEYCODE_BACK")
                            attempt_count = 0
                        sleep(4)
                else:
                    print("\n不是要刷的怪物，继续等待.", end="", flush=True)
                    device.touch(util.random_pos(pos.decline_pos))

            if idle_count == 70:
                print("\n点击保持唤醒.")
                device.touch(util.random_pos(pos.awake_pos))
                idle_count = 0
            idle_count += 1
            sleep(operation_delay)
    except KeyboardInterrupt:
        print()
        exit(0)
