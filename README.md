# 世界弹射物语 自动铃铛

## 已实现

- 全自动进铃铛/准备/判断结束返回/判断房间已满
- 使用Bark推送至手机查看状态
- 遇到未标记的Boss自动截图存储
- 打完自动截图结果存储至`results`文件夹中

## 已知bug

- 暂无

## Demo

![Demo1](demo_img/IMG_2882.png)

![Demo2](demo_img/IMG_2881.jpg)

~~已经刷吐了~~

终于解脱了

----

## 模拟器测试环境

- BlueStacks 5.4.100.1026 Nougat (支援 Hyper-V) 版本 
- - 直向 720*1280 像素密度 240DPI(中等) / 160DPI | 图形渲染器：DirectX | 安卓调试桥：开
- MuMu模拟器 2.6.7
- - 极速+（默认配置），自定义分辨率720*1280, 160DPI 测试OK

### 游戏
世界弹射物语 官服

----

## 依赖

`opencv-python image_similarity_measures PIL numpy`

同时需要配置好adb

## Boss配置

```
{
	"name": "boss_fire_super", <- results文件名
	"friendly_name": "废墟魔像 超级", <- 推送、日志记录
	"ref_img": "boss_fire_super.bmp", <- reference文件夹下需要存在此文件
	"target": 1 <- 0/1 是否要刷
}
```

## 使用

```
python bell.py fast ip=localhost port=5555
```
参数

| 参数 | 默认值 | 说明 | 是否可选 |
| ---- | ---- | ---- | ---- |
| fast | |非第一次启动可以加快速度 | True |
| ip | localhost|模拟器的ADB IP | True |
| port | 5555 | 模拟器ADB端口 | True |

## 致谢

- 参考了https://github.com/littleplane321/WorldFlipper-OCR-AUTO
