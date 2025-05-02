# social-auto-upload
social-auto-upload 该项目旨在自动化发布视频到各个社交媒体平台

## 💡Feature
- 中国主流社交媒体平台：

  - [x] 百家号

- 部分国外社交媒体：

## 更新说明
本次提交主要包含以下更新：

1. **发布时间配置**:
   - 实现发布时间完全由 `config.json` 中的 `publish_date` 和 `publish_times` 控制。
   - 移除了旧的默认从次日开始发布的逻辑。
   - 新增 `utils.files_times.generate_schedule_times` 函数处理配置读取和时间生成。
   - 更新 `examples/upload_video_to_tencent.py` 以使用新的时间生成函数。

2. **腾讯视频号短标题处理**:
   - 更新 `uploader.tencent_uploader.main.format_str_for_short_title` 函数，使其更严格地遵守视频号短标题规则：
     - 校验允许的特殊字符（书名号、引号、冒号、加号、问号、百分号、摄氏度）。
     - 将中英文逗号替换为空格。
     - 移除其他不支持的字符。
   - **注意**: 当前未实现自动截断至16字或基于语义的总结，仅处理字符校验和替换。

3. **封面上传逻辑**:
   - 修复并完善了 `uploader.tencent_uploader.main` 中的封面上传逻辑 (`upload_cover_image`, `upload_cover`)。
   - 兼容处理标准尺寸（无裁剪）和非标准尺寸（有裁剪）的封面上传流程。

4. **代码结构优化**:
   - 解耦 `utils.files_times.get_title_and_hashtags` 与特定上传器。
   - `get_title_and_hashtags` 现在只返回原始文本，标题格式化（如短标题）的责任移至调用方（例如 `examples/upload_video_to_tencent.py`）。

5. **文件处理**:
   - 确认 `examples/upload_video_to_tencent.py` 在上传成功后，会将视频文件、对应的 `.txt` 文件以及封面图片（兼容 `.png`, `.jpg`, `.jpeg`, `.webp` 格式）移动到 `published` 目录。

6. **标题与内容读取**:
   - `utils.files_times.get_title_and_hashtags` 使用 `.txt` 文件第一行作为短标题，第二行及之后所有行作为标题和话题内容。
   - 对于标题和话题内容，`.strip()` 会移除整体内容开头和结尾的空白/换行符，但会保留内容内部的换行符（包括由空行产生的）。

# 💾Installation