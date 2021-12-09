import json
import os
import random
import time

import cv2
from PIL import Image
from image_similarity_measures.quality_metrics import fsim


def log(content):
    with open("record.txt", 'a', encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y%m%d_%H%M%S', time.localtime())} | {content}\n")


def get_boss(_boss: Image, _ref: list, boss_threshold: float) -> dict:
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


def random_pos(area) -> [int, int]:
    """
    在某范围内随机一个触摸点

    :param area: [(x1, y1), (x2, y2)]
    :return: [x, y]
    """
    return random.randint(area[0][0], area[1][0]), random.randint(area[0][1], area[1][1])


def get_ref_image(ref_folder: str, file_name: str):
    return cv2.imread(os.path.join(ref_folder, file_name))[..., ::-1]


def get_area_from_image(area, image):
    return image[area[0][1]:area[1][1], area[0][0]:area[1][0]]


def get_config(config_name="config.json"):
    with open(config_name, 'r', encoding='utf-8') as cfg:
        return json.load(cfg)
