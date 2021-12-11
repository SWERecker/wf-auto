from urllib.parse import urljoin
import requests


class Push:
    def __init__(self, base):
        self.base = base
        self.title = "世界弹射物语护肝助手"
        self.group = "世界弹射物语护肝助手"
        self.icon = "https://ossstatic.leiting.com/static/game/images/wf_ico.ico"
        self.fail = False
        if self.base == "":
            print("Bark推送服务地址未配置！")
            self.fail = True

    def push(self, content):
        if self.fail:
            return
        content = content
        requests.get(urljoin(self.base, f"{self.title}/{content.replace('+', '%2B')}/"),
                     params={"group": self.group, "icon": self.icon})
