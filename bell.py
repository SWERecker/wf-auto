import os
import sys
import time
import warnings
from time import sleep

import cv2
from image_similarity_measures.quality_metrics import fsim

from wf_auto import *
from wf_auto.util import Debug

warnings.filterwarnings('ignore')

ref_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "reference")
results_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "results")

operation_delay = 0.7
threshold = 0.64
boss_threshold = 0.64
fast_connect = False
ip = "localhost"
port = "7555"
record = {}

if len(sys.argv) > 1:
    for arg in sys.argv:
        if arg == "fast":
            fast_connect = True
        if arg.startswith("port"):
            port = arg.split('=')[1]
        if arg.startswith("ip"):
            ip = arg.split('=')[1]


def battle_record(boss_name):
    if boss_name in record:
        record[boss_name] += 1
    else:
        record[boss_name] = 1


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

    Debug.print("开始等待铃铛.", inline=True)
    try:
        while True:
            screenshot = device.screenshot()
            boss_info = {"name": "unknown", "friendly_name": "未知怪物", "target": 0}
            bell = util.get_area_from_image(pos.bell_pos, screenshot)
            simi = fsim(bell, common_ref["bell"])
            # Debug.print("铃铛相似度：", simi)
            Debug.print(".", prefix=False, inline=True)
            if simi > threshold:
                idle_count = 0
                Debug.print("识别到铃铛，点击", new_line=True)
                device.touch(pos.bell_pos)
                sleep(1)
                bell_info = device.screenshot()
                boss_accept = False
                if skip_filter_boss:
                    Debug.print("跳过筛选Boss，接受")
                    boss_accept = True
                else:
                    boss_info = util.get_boss(
                        util.get_area_from_image(pos.boss_pos, bell_info), boss_ref, boss_threshold)
                    if boss_info["name"] == "unknown":
                        Debug.print(f"怪物名称：{boss_info['friendly_name']}")
                        Debug.log(f"怪物名称：{boss_info['friendly_name']}")
                        Debug.print("未知Boss，保存备用")
                        device.get_unknown_boss(bell_info)
                    boss_accept = boss_info["target"]
                if boss_accept:
                    Debug.print("点击接受")
                    device.touch(pos.accept_pos)
                    sleep(1)
                    Debug.print("正在等待进入房间.", inline=True, new_line=True)
                    room_entered = False
                    while True:
                        screenshot = device.screenshot()
                        room_full_simi = fsim(common_ref["full"],
                                              util.get_area_from_image(pos.full_pos, screenshot))
                        if room_full_simi > threshold:
                            Debug.print("房间已满或正在开始，返回继续等待", new_line=True)
                            bark.push("进入房间失败：已满或正在开始")
                            device.touch(pos.full_continue_pos)
                            break
                        in_room_simi = fsim(common_ref["in_room"],
                                            util.get_area_from_image(pos.in_room_pos, screenshot))
                        if in_room_simi < threshold:
                            Debug.print(".", prefix=False, inline=True)
                            continue
                        else:
                            Debug.print("已进入房间！", new_line=True)
                            room_entered = True
                            break
                    if not room_entered:
                        Debug.print("未成功进入房间")
                        continue

                    Debug.print("点击准备.")
                    while True:
                        device.touch(pos.prepare_pos)
                        sleep(operation_delay)
                        screenshot = device.screenshot()
                        prepared_simi = fsim(common_ref["prepared"],
                                             util.get_area_from_image(pos.prepare_pos, screenshot))
                        if prepared_simi > threshold:
                            Debug.print("已准备!")
                            break
                        unprepared_simi = fsim(common_ref["unprepared"],
                                               util.get_area_from_image(pos.prepare_pos, screenshot))
                        if unprepared_simi > threshold + 0.05:
                            Debug.print("尚未准备...")
                            continue
                        else:
                            Debug.print("未找到准备标志，可能已经开始")
                            break
                    if skip_filter_boss:
                        Debug.print("尝试识别Boss信息.")
                        boss_info = util.get_boss(
                            util.get_area_from_image(pos.boss_pos, bell_info), boss_ref, boss_threshold)
                        Debug.print(f"怪物名称：{boss_info['friendly_name']}")
                        Debug.log(f"怪物名称：{boss_info['friendly_name']}")
                        if boss_info["name"] == "unknown":
                            Debug.print("未知Boss，保存备用")
                            device.get_unknown_boss(bell_info)

                    Debug.print("正在等待结束.", prefix=True, inline=True)
                    while True:
                        screenshot = device.screenshot()
                        continue_simi = fsim(common_ref["continue"],
                                             util.get_area_from_image(pos.continue_btn_pos, screenshot))
                        finish = True if continue_simi > threshold else False
                        if finish:
                            Debug.print(f"{boss_info['friendly_name']} 已正常结束", new_line=True)
                            Debug.log(f"{boss_info['friendly_name']} 已正常结束")
                            file_name = f"{time.strftime('%Y%m%d_%H%M%S', time.localtime())}_{boss_info['name']}.jpg"
                            cv2.imwrite(os.path.join(results_folder, file_name), screenshot)
                            bark.push(f"{boss_info['friendly_name']} 正常结束")
                            battle_record(boss_info["name"])
                            device.touch(pos.continue_pos)
                            break
                        else:
                            Debug.print(".", prefix=False, inline=True)
                        main_simi = fsim(common_ref["main"],
                                         util.get_area_from_image(pos.main_pos, screenshot))
                        finish_abnormal = True if main_simi > threshold else False
                        if finish_abnormal:
                            msg = f"{boss_info['friendly_name']} 非正常结束"
                            Debug.print(msg, new_line=True)
                            Debug.log(msg)
                            bark.push(msg)
                            break
                        dismiss_simi = fsim(common_ref["full"],
                                            util.get_area_from_image(pos.full_pos, screenshot))
                        room_dismiss = True if dismiss_simi > threshold else False
                        if room_dismiss:
                            msg = f"{boss_info['friendly_name']} 房间已解散"
                            Debug.print(msg, new_line=True)
                            Debug.log(msg)
                            bark.push(msg)
                            device.touch(pos.full_continue_pos)
                            sleep(2)
                            break
                        sleep(3)
                    Debug.print("正在回到主界面.", inline=True, new_line=True)
                    attempt_count = 0
                    while True:
                        screenshot = device.screenshot()
                        main_simi = fsim(common_ref["main"],
                                         util.get_area_from_image(pos.main_pos, screenshot))
                        back_to_main = True if main_simi > threshold else False
                        if back_to_main:
                            device.touch(pos.main_btn_pos)
                            Debug.print("已回到主界面，继续等待铃铛", inline=True, new_line=True)
                            break
                        else:
                            Debug.print(".", prefix=False, inline=True)
                            device.touch(pos.continue_pos)
                        attempt_count += 1
                        if attempt_count > 8:
                            Debug.print("似乎返回主界面失败，尝试使用返回键", new_line=True)
                            device.button("KEYCODE_BACK")
                            attempt_count = 0
                        sleep(2)
                else:
                    Debug.print("不是要刷的怪物，继续等待.", inline=True, new_line=True)
                    device.touch(pos.decline_pos)

            if idle_count == 100:
                Debug.print("点击保持唤醒.", new_line=True, inline=True)
                device.touch(pos.awake_pos)
                idle_count = 0
            idle_count += 1
            sleep(operation_delay)
    except KeyboardInterrupt:
        if record:
            total = 0
            recs = []
            for boss, count in record.items():
                total += count
                recs.append(f"{util.get_boss_friendly_name(boss_ref, boss)}{count}只")
            msg = f"共成功战斗{total}场\n{'；'.join(recs)}"
            bark.push(msg)
        else:
            bark.push("本次未成功进入战斗")
        Debug.print("Control-C", new_line=True, prefix=False)
        exit(0)
