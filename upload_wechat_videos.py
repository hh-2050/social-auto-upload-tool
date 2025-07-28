import os
import re
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import shutil

from conf import BASE_DIR
from uploader.tencent_uploader.main import weixin_setup, TencentVideo
from utils.files_times import get_title_and_hashtags
from playwright.async_api import async_playwright

class WeChatVideoUploader:
    def __init__(self, account_file: str):
        self.account_file = account_file
        self.videos_dir = Path(BASE_DIR) / "videos"
        
        # 从 config.json 加载设置
        self.config = self._load_config()
        self.original_declaration = self.config.get('original_declaration', False)
        self.default_publish_hour = 7  # 默认上午7点发布
        
    def _load_config(self) -> dict:
        """从 config.json 加载配置"""
        config_path = Path(BASE_DIR) / "config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
        
    def extract_date_from_folder(self, folder_name: str) -> Optional[datetime]:
        """从文件夹名中提取日期"""
        # 匹配前6位数字作为日期 (YYMMDD)
        match = re.match(r'^(\d{6})', folder_name)
        if not match:
            return None
            
        date_str = match.group(1)
        try:
            # 将YYMMDD转换为datetime对象 (假设20xx年)
            year = 2000 + int(date_str[:2])
            month = int(date_str[2:4])
            day = int(date_str[4:6])
            return datetime(year, month, day)
        except (ValueError, IndexError):
            return None
    
    def get_video_info(self, folder_path: Path) -> Optional[Dict]:
        """获取视频文件夹中的视频、标题和封面信息"""
        video_files = list(folder_path.glob("*.mp4"))
        if not video_files:
            print(f"警告: 在 {folder_path} 中未找到视频文件")
            return None
            
        # 获取第一个视频文件
        video_file = video_files[0]
        
        # 查找文本文件 (标题和描述)
        txt_files = list(folder_path.glob("*.txt"))
        if txt_files:
            with open(txt_files[0], 'r', encoding='utf-8') as f:
                title = f.readline().strip()
                description = f.read().strip()
        else:
            title = video_file.stem
            description = ""
            
        # 查找封面图片
        cover_files = list(folder_path.glob("*.jpg")) + list(folder_path.glob("*.jpeg")) + list(folder_path.glob("*.png"))
        cover_path = str(cover_files[0]) if cover_files else None
        
        return {
            'video_path': str(video_file),
            'title': title,
            'description': description,
            'cover_path': cover_path
        }
    
    def get_sorted_video_folders(self) -> List[Tuple[datetime, Path]]:
        """获取按日期排序的视频文件夹（适配单层结构）"""
        dated_folders = []
        for folder in self.videos_dir.iterdir():
            if not folder.is_dir():
                continue
            date = self.extract_date_from_folder(folder.name)
            if date and date >= datetime(2025, 8, 1):
                dated_folders.append((date, folder))
        dated_folders.sort(key=lambda x: x[0])
        return dated_folders
    
    async def upload_video(self, video_info: Dict, publish_date: datetime, playwright):
        """上传单个视频"""
        print(f"\n准备上传视频: {video_info['title']}")
        print(f"计划发布时间: {publish_date.strftime('%Y-%m-%d %H:%M')}")
        
        # 设置分类 (这里使用生活类，可以根据需要修改)
        category = 15  # 15 是生活类，可以根据需要修改
        
        # 创建视频对象并上传
        app = TencentVideo(
            short_title=video_info['title'],
            title_and_tags=video_info['description'],
            file_path=video_info['video_path'],
            publish_date=publish_date,
            account_file=self.account_file,
            category=category,
            original_declaration=self.original_declaration,
            thumbnail_path=video_info.get('cover_path')
        )
        
        try:
            await app.upload(playwright)
            print(f"✅ 视频上传成功: {video_info['title']}")
            return True
        except Exception as e:
            print(f"❌ 视频上传失败: {video_info['title']} - {str(e)}")
            return False
    
    async def upload_all_videos(self):
        """上传所有视频"""
        print("开始扫描视频文件夹...")
        dated_folders = self.get_sorted_video_folders()
        
        if not dated_folders:
            print("未找到有效的视频文件夹！")
            return
            
        print(f"\n找到 {len(dated_folders)} 个视频待上传，按日期排序:")
        for date, folder in dated_folders:
            print(f"- {date.strftime('%Y-%m-%d')}: {folder.name}")
            
        confirm = input("\n确认开始上传？(y/n): ")
        if confirm.lower() != 'y':
            print("上传已取消")
            return
            
        # 登录微信视频号
        print("\n正在登录微信视频号...")
        if not await weixin_setup(self.account_file, handle=True):
            print("登录失败，请检查账号配置")
            return
        
        # 上传每个视频
        success_count = 0
        max_retries = 3
        async with async_playwright() as playwright:
            for date, folder in dated_folders:
                video_info = self.get_video_info(folder)
                if not video_info:
                    print(f"跳过无效文件夹: {folder}")
                    continue
                
                # 设置发布时间为当天的上午7点
                publish_time = datetime.combine(date.date(), datetime.min.time()) + timedelta(hours=self.default_publish_hour)
                for attempt in range(1, max_retries + 1):
                    success = await self.upload_video(video_info, publish_time, playwright)
                    if success:
                        success_count += 1
                        # 上传成功后移动到 published 目录
                        published_dir = Path(BASE_DIR) / "published"
                        published_dir.mkdir(exist_ok=True)
                        target_folder = published_dir / folder.name
                        shutil.move(str(folder), str(target_folder))
                        print(f"已移动到: {target_folder}")
                        break
                    else:
                        print(f"重试第 {attempt} 次失败: {video_info['title']}")
                        if attempt < max_retries:
                            await asyncio.sleep(5)
                        else:
                            print(f"❌ 最终失败，跳过: {video_info['title']}")
                # 添加延迟，避免请求过于频繁（只在所有重试后）
                await asyncio.sleep(5)
        
        print(f"\n上传完成！成功上传 {success_count}/{len(dated_folders)} 个视频")


async def main():
    # 账号配置文件路径
    account_file = str(BASE_DIR / "cookies" / "tencent_uploader" / "account.json")
    
    # 确保账号文件存在
    if not os.path.exists(account_file):
        print(f"错误: 账号文件不存在: {account_file}")
        print("请先运行 examples/get_tencent_cookie.py 获取cookie")
        return
    
    # 创建并运行上传器
    try:
        uploader = WeChatVideoUploader(account_file)
        await uploader.upload_all_videos()
    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
