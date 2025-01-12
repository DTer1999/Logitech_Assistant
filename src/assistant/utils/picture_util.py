import os

import cv2


class PictureUtil:
    @staticmethod
    def savePicture(frame):
        from datetime import datetime
        # 获取当前时间
        now = datetime.now()
        # 获取微秒的前三位
        milliseconds = now.microsecond // 1000
        # 使用 strftime 获取其它时间数据，并拼接微秒的前三位
        timestamp = now.strftime("%Y%m%d_%H%M%S.") + "%03d" % milliseconds
        # 生成唯一的文件名
        # timestamp = time.strftime("%Y%m%d_%H%M%S")
        save_dir = 'E:/pubg/Logitech_Assistant/temp/pic'
        save_path = os.path.join(save_dir, f"{timestamp}.png")

        # 保存截图
        cv2.imwrite(save_path, frame)
        print(f"截图已保存至: {save_path}")
