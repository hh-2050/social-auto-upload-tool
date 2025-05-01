from datetime import timedelta

from datetime import datetime
from pathlib import Path

from conf import BASE_DIR


def get_absolute_path(relative_path: str, base_dir: str = None) -> str:
    # Convert the relative path to an absolute path
    absolute_path = Path(BASE_DIR) / base_dir / relative_path
    return str(absolute_path)


def get_title_and_hashtags(filename):
    """
    获取短标题和标题+话题内容
    Args:
        filename: 视频文件名
    Returns:
        短标题, 标题和话题内容
    """
    txt_filename = filename.replace(".mp4", ".txt")
    with open(txt_filename, "r", encoding="utf-8") as f:
        content = f.read()
    lines = [line.strip() for line in content.strip().split("\n") if line.strip()]
    if not lines:
        return '', ''
    short_title = lines[0]
    title_and_tags = "\n".join(lines[1:]) if len(lines) > 1 else ''
    return short_title, title_and_tags


def generate_schedule_time_next_day(total_videos, videos_per_day, daily_times=None, timestamps=False, start_days=0):
    """
    Generate a schedule for video uploads, starting from a specified day at fixed times.
    
    Args:
        total_videos (int): Total number of videos to schedule
        videos_per_day (int): Number of videos to publish per day
        daily_times (list): List of hours when videos should be published (default: [6, 9, 12, 15, 18, 21])
        timestamps (bool): Whether to return timestamps instead of datetime objects
        start_days (int): Number of days to offset from tomorrow (0 means tomorrow, 1 means day after tomorrow, etc.)
    
    Returns:
        list: List of datetime objects or timestamps for scheduled uploads
    """
    from datetime import time, datetime, timedelta

    if videos_per_day <= 0:
        raise ValueError("videos_per_day should be a positive integer")

    if daily_times is None:
        daily_times = [6, 9, 12, 15, 18, 21]  # Default publish times
    
    if videos_per_day > len(daily_times):
        raise ValueError("videos_per_day should not exceed the length of daily_times")

    # Sort daily times to ensure chronological order
    daily_times.sort()
    
    # Calculate start date (tomorrow + offset days)
    start_date = datetime.now().date() + timedelta(days=1 + start_days)
    
    # Calculate how many days we need based on total videos and videos per day
    total_days = (total_videos + videos_per_day - 1) // videos_per_day
    
    schedule = []
    current_date = start_date
    videos_scheduled = 0
    
    # Generate schedule for each day until we have enough slots for all videos
    for day in range(total_days):
        # For each day, take only the first videos_per_day time slots
        day_times = daily_times[:videos_per_day]
        for hour in day_times:
            if videos_scheduled < total_videos:
                schedule_time = datetime.combine(current_date, time(hour=hour))
                schedule.append(schedule_time)
                videos_scheduled += 1
        current_date += timedelta(days=1)

    if timestamps:
        schedule = [int(dt.timestamp()) for dt in schedule]
    
    return schedule
