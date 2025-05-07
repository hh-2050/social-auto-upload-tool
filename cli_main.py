import argparse
import asyncio
from datetime import datetime
from os.path import exists
from pathlib import Path

from conf import BASE_DIR
from uploader.douyin_uploader.main import douyin_setup, DouYinVideo
from uploader.ks_uploader.main import ks_setup, KSVideo
from uploader.tencent_uploader.main import weixin_setup, TencentVideo
from uploader.tk_uploader.main_chrome import tiktok_setup, TiktokVideo
from utils.base_social_media import get_supported_social_media, get_cli_action, SOCIAL_MEDIA_DOUYIN, \
    SOCIAL_MEDIA_TENCENT, SOCIAL_MEDIA_TIKTOK, SOCIAL_MEDIA_KUAISHOU
from utils.constant import TencentZoneTypes
from utils.files_times import get_title_and_hashtags


def parse_schedule(schedule_raw):
    if schedule_raw:
        schedule = datetime.strptime(schedule_raw, '%Y-%m-%d %H:%M')
    else:
        schedule = None
    return schedule


async def main():
    # 主解析器
    parser = argparse.ArgumentParser(description="Upload video to multiple social-media.")
    parser.add_argument("platform", metavar='platform', choices=get_supported_social_media(), help="Choose social-media platform: douyin tencent tiktok kuaishou")

    parser.add_argument("account_name", type=str, help="Account name for the platform: xiaoA")
    subparsers = parser.add_subparsers(dest="action", metavar='action', help="Choose action", required=True)

    actions = get_cli_action()
    for action in actions:
        action_parser = subparsers.add_parser(action, help=f'{action} operation')
        if action == 'login':
            # Login 不需要额外参数
            continue
        elif action == 'upload':
            action_parser.add_argument("video_file", help="Path to the Video file")
            action_parser.add_argument("-pt", "--publish_type", type=int, choices=[0, 1],
                                       help="0 for immediate, 1 for scheduled", default=0)
            action_parser.add_argument('-t', '--schedule', help='Schedule UTC time in %Y-%m-%d %H:%M format')

    # 解析命令行参数
    args = parser.parse_args()
    
    # 检查视频文件和目录
    if args.action == 'upload':
        video_file_path = Path(args.video_file)
        
        # 检查视频文件是否存在
        if not video_file_path.exists():
            print(f"错误：视频文件不存在 - {video_file_path}")
            print("\n" + "="*50)
            print("【提示】未找到指定的视频文件！")
            print(f"请确保视频文件(.mp4格式)存在于指定路径")
            print("每个视频文件需要有对应的同名.txt文件，包含标题和标签")
            print("例如: video1.mp4 对应 video1.txt")
            print("="*50 + "\n")
            return
            
        # 检查对应的txt文件是否存在
        txt_file = video_file_path.with_suffix('.txt')
        if not txt_file.exists():
            print(f"警告：未找到对应的文本文件 - {txt_file}")
            print("视频标题和标签可能无法正确设置")
            
        # 参数校验
        if args.publish_type == 1 and not args.schedule:
            parser.error("定时发布必须指定发布时间 (--schedule)。")

    account_file = Path(BASE_DIR / "cookies" / f"{args.platform}_{args.account_name}.json")
    account_file.parent.mkdir(exist_ok=True)

    # 根据 action 处理不同的逻辑
    if args.action == 'login':
        print(f"Logging in with account {args.account_name} on platform {args.platform}")
        if args.platform == SOCIAL_MEDIA_DOUYIN:
            await douyin_setup(str(account_file), handle=True)
        elif args.platform == SOCIAL_MEDIA_TIKTOK:
            await tiktok_setup(str(account_file), handle=True)
        elif args.platform == SOCIAL_MEDIA_TENCENT:
            await weixin_setup(str(account_file), handle=True)
        elif args.platform == SOCIAL_MEDIA_KUAISHOU:
            await ks_setup(str(account_file), handle=True)
    elif args.action == 'upload':
        title, tags = get_title_and_hashtags(args.video_file)
        video_file = args.video_file

        if args.publish_type == 0:
            print("Uploading immediately...")
            publish_date = 0
        else:
            print("Scheduling videos...")
            publish_date = parse_schedule(args.schedule)

        if args.platform == SOCIAL_MEDIA_DOUYIN:
            await douyin_setup(account_file, handle=False)
            app = DouYinVideo(title, video_file, tags, publish_date, account_file)
        elif args.platform == SOCIAL_MEDIA_TIKTOK:
            await tiktok_setup(account_file, handle=True)
            app = TiktokVideo(title, video_file, tags, publish_date, account_file)
        elif args.platform == SOCIAL_MEDIA_TENCENT:
            await weixin_setup(account_file, handle=True)
            category = TencentZoneTypes.LIFESTYLE.value
            app = TencentVideo(title, video_file, tags, publish_date, account_file, category, original_declaration)
        elif args.platform == SOCIAL_MEDIA_KUAISHOU:
            await ks_setup(account_file, handle=True)
            app = KSVideo(title, video_file, tags, publish_date, account_file)
        else:
            print("Wrong platform, please check your input")
            exit()

        await app.main()


if __name__ == "__main__":
    asyncio.run(main())
