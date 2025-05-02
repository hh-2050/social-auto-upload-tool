import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
import asyncio
import re
import shutil
import json
from datetime import datetime

from conf import BASE_DIR
# --- 修改开始 ---
# 确保从 tencent_uploader 导入格式化函数
from uploader.tencent_uploader.main import weixin_setup, TencentVideo, format_str_for_short_title
# --- 修改结束 ---
from utils.constant import TencentZoneTypes
# 导入修改后的 get_title_and_hashtags 和 generate_schedule_times
from utils.files_times import generate_schedule_times, get_title_and_hashtags

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

    # --- 修改开始 ---
    # 读取 config.json 并生成发布时间
    config_path = Path(BASE_DIR) / "config.json"
    publish_datetimes = []
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # 主要逻辑：使用 config.json 中的 publish_date 和 publish_times
        if "publish_date" in config and "publish_times" in config:
            publish_date_str = config["publish_date"]
            daily_times = config["publish_times"]
            # 调用新的函数生成时间列表
            publish_datetimes = generate_schedule_times(publish_date_str, daily_times, file_num)
        else:
            print("错误：config.json 文件缺少 'publish_date' 或 'publish_times'。无法安排发布时间。")
            # 可以选择退出或使用默认值
            # 使用默认值（例如，从今天开始，每天早上 9 点发布）
            print("将使用默认设置：从今天开始，每天早上 9 点发布。")
            publish_datetimes = generate_schedule_times(datetime.now().strftime("%Y-%m-%d"), [9], file_num)

    else:
        print(f"错误：未找到 config.json 文件于 {config_path}。无法安排发布时间。")
        # 可以选择退出或使用默认值
        print("将使用默认设置：从今天开始，每天早上 9 点发布。")
        publish_datetimes = generate_schedule_times(datetime.now().strftime("%Y-%m-%d"), [9], file_num)

    # 确保生成的时间列表长度与文件数量匹配
    if len(publish_datetimes) < file_num:
         print(f"警告：生成的时间点数量 ({len(publish_datetimes)}) 少于视频数量 ({file_num})。可能由于配置错误导致。")
         # 可以补充时间点，例如使用最后一个有效时间点
         if publish_datetimes:
             publish_datetimes.extend([publish_datetimes[-1]] * (file_num - len(publish_datetimes)))
         else: # 如果完全没有生成时间点
             print("错误：无法生成任何有效的发布时间。请检查 config.json。")
             sys.exit(1) # 退出脚本

    # --- 修改结束 ---

    cookie_setup = asyncio.run(weixin_setup(account_file, handle=True))
    category = TencentZoneTypes.LIFESTYLE.value  # 标记原创需要否则不需要传
    published_dir = Path(BASE_DIR) / "published"
    published_dir.mkdir(exist_ok=True)
    for index, file in enumerate(files):
        # --- 修改开始 ---
        # 1. 调用 get_title_and_hashtags 获取原始标题
        raw_short_title, title_and_tags = get_title_and_hashtags(str(file))
        # 2. 在这里调用特定平台的格式化函数
        short_title = format_str_for_short_title(raw_short_title)
        # --- 修改结束 ---

        print(f"视频文件名：{file}")
        print(f"格式化后短标题：{short_title}") # 打印格式化后的
        print(f"标题和话题内容：{title_and_tags}")
        current_publish_time = publish_datetimes[index]
        print(f"实际发布时间：{current_publish_time}")

        app = TencentVideo(
            short_title=short_title, # 传递格式化后的短标题
            title_and_tags=title_and_tags,
            file_path=str(file),
            publish_date=current_publish_time,
            account_file=str(account_file),
            category=category
        )
        try:
            asyncio.run(app.main(), debug=False)
            # 上传成功后移动视频、封面图和txt
            shutil.move(str(file), str(published_dir / file.name))
            
            # 支持多种图片格式
            for img_ext in ['.png', '.jpg', '.jpeg', '.webp']:
                cover = file.with_suffix(img_ext)
                if cover.exists():
                    shutil.move(str(cover), str(published_dir / cover.name))
                    break
            
            txt = file.with_suffix('.txt')
            if txt.exists():
                shutil.move(str(txt), str(published_dir / txt.name))
            print(f"已移动到published文件夹: {file.name}")
        except Exception as e:
            print(f"上传失败未移动: {file.name}, 错误: {e}")
