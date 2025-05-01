import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
import asyncio
import re
import shutil
import json
from datetime import datetime

from conf import BASE_DIR
from uploader.tencent_uploader.main import weixin_setup, TencentVideo
from utils.constant import TencentZoneTypes
from utils.files_times import generate_schedule_time_next_day, get_title_and_hashtags

def natural_key(s):
    # 提取字符串中的数字用于自然排序
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

if __name__ == '__main__':
    filepath = Path(BASE_DIR) / "videos"
    account_file = Path(BASE_DIR / "cookies" / "tencent_uploader" / "account.json")
    # 获取视频目录
    folder_path = Path(filepath)
    # 获取文件夹中的所有文件，并按自然顺序排序
    files = sorted(folder_path.glob("*.mp4"), key=lambda x: natural_key(x.name))
    file_num = len(files)
    # 读取 config.json 里的 publish_datetimes 或 publish_times
    config_path = Path(BASE_DIR) / "config.json"
    publish_datetimes = None
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        if "publish_datetimes" in config:
            publish_datetimes = [datetime.strptime(dt, "%Y-%m-%d %H:%M") for dt in config["publish_datetimes"]]
            if len(files) > len(publish_datetimes):
                publish_datetimes += [publish_datetimes[-1]] * (len(files) - len(publish_datetimes))
        else:
            daily_times = config.get("publish_times", [6])
            publish_datetimes = generate_schedule_time_next_day(file_num, len(daily_times), daily_times=daily_times)
    else:
        daily_times = [6]
        publish_datetimes = generate_schedule_time_next_day(file_num, len(daily_times), daily_times=daily_times)
    cookie_setup = asyncio.run(weixin_setup(account_file, handle=True))
    category = TencentZoneTypes.LIFESTYLE.value  # 标记原创需要否则不需要传
    published_dir = Path(BASE_DIR) / "published"
    published_dir.mkdir(exist_ok=True)
    for index, file in enumerate(files):
        short_title, title_and_tags = get_title_and_hashtags(str(file))
        # 打印视频文件名、短标题、标题和话题内容、实际发布时间
        print(f"视频文件名：{file}")
        print(f"短标题：{short_title}")
        print(f"标题和话题内容：{title_and_tags}")
        print(f"实际发布时间：{publish_datetimes[index]}")
        app = TencentVideo(short_title, title_and_tags, file, publish_datetimes[index], account_file, category)
        try:
            asyncio.run(app.main(), debug=False)
            # 上传成功后移动视频、同名封面和txt
            shutil.move(str(file), str(published_dir / file.name))
            cover = file.with_suffix('.png')
            if cover.exists():
                shutil.move(str(cover), str(published_dir / cover.name))
            txt = file.with_suffix('.txt')
            if txt.exists():
                shutil.move(str(txt), str(published_dir / txt.name))
            print(f"已移动到published文件夹: {file.name}")
        except Exception as e:
            print(f"上传失败未移动: {file.name}, 错误: {e}")
