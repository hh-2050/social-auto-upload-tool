# social-auto-upload
social-auto-upload 该项目旨在自动化发布视频到各个社交媒体平台

## 💡Feature
- 中国主流社交媒体平台：
  - [x] 腾讯视频号
  - [ ] 待添加

- 部分国外社交媒体：
  - [ ] 待添加

- 功能特性：
  - [x] 原创声明配置（可在 config.json 中通过 original_declaration 设置）
  - [x] 定时发布功能
  - [x] 批量上传处理
  - [x] 空视频目录检测与提示

## 🚀 待办事项
1. **封面处理优化**:
   - [ ] 优化封面截取逻辑
   - [ ] 添加智能裁剪功能
   - [ ] 处理不同尺寸比例的封面图片

2. **视频发布顺序**:
   - [x] 修复 Videos 目录中视频发布顺序的问题
   - [ ] 实现更灵活的排序规则
   - [ ] 添加自定义排序功能

3. **前端可视化界面**:
   - [ ] 设计并实现基于 React 的前端界面
   - [ ] 开发视频上传和管理功能
   - [ ] 实现发布时间可视化配置
   - [ ] 添加发布状态实时监控
   - [ ] 开发平台选择和账号管理功能
   - [ ] 实现数据持久化存储
   - [ ] 添加用户认证和权限管理
   - [ ] 优化用户交互体验

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

7. **原创声明开关功能实现**:
   - 完成了原创声明功能的可配置项设置
   - 在 config.json 中添加了 original_declaration 开关（布尔值）
   - 优化了原创声明的错误处理逻辑
   - 添加了原创声明状态的日志记录
   - 在 cli_main.py 中实现了对配置的读取和应用

8. **原创声明流程优化**:
   - 优化了腾讯视频号原创声明流程
   - 使用更精确的选择器定位元素
   - 增加了等待时间确保页面状态稳定
   - 添加了错误处理和日志输出
   - 在每个操作之间增加了适当的等待时间
   - 自动勾选"声明原创"复选框
   - 自动处理"原创权益"弹窗
   - 自动同意原创声明使用条款
   - 自动点击确认按钮完成声明

9. **空视频目录处理**:
   - 添加了对空视频目录的检测机制
   - 当视频目录为空时，会显示友好的提示信息
   - 提示用户将视频文件放入正确的目录
   - 说明视频文件命名和对应文本文件的要求
   - 自动创建不存在的视频目录

10. **腾讯视频号原创声明流程稳定性修复**:
    - **问题1：定位"原创权益"弹窗严格模式冲突**
        - **原因**: `page.locator('.weui-desktop-dialog:has-text("原创权益")')` 匹配到多个元素。
        - **解决**: 使用 `.first` 明确选择第一个匹配项，即 `page.locator('.weui-desktop-dialog:has-text("原创权益")').first`，并确保后续弹窗内元素定位基于此。
    - **问题2：等待"声明原创"按钮状态参数错误**
        - **原因**: `await confirm_button.wait_for(state="enabled", ...)` 中 `state="enabled"` 无效。
        - **解决**: 改为 `await confirm_button.wait_for(state="visible", ...)`，因为 `.click()` 方法会自动等待元素可用。同时优化了确认按钮的选择器为 `dialog.locator('.weui-desktop-dialog__ft .weui-desktop-btn_primary:has-text("声明原创")')`。
    - **效果**: 修复上述问题后，原创声明流程恢复正常，并解决了因此导致的后续页面操作（如设置不显示位置）超时的问题。

---

## 常见问题与解决方案

### 腾讯视频号批量上传卡在封面上传弹窗/无法自动上传封面图片

**现象：**
- 自动化上传时，页面卡在"编辑视频封面"弹窗，未自动上传本地封面图片，也未自动点击"确认"按钮。
- 日志报错：`上传封面图片失败: Cannot set input files to detached element`
- 有时"发表"按钮也无法点击，提示被浮层遮挡。

**原因分析：**
- 腾讯视频号前端在弹窗出现后，会重建或移除 input[type="file"] 元素，导致 Playwright 之前获取的 input 节点失效（detached）。
- 赋值 input 时节点已被移除，或页面未及时渲染，导致上传失败。

**解决方法：**
- 上传图片时，务必用 `locator('div.single-cover-uploader-wrap input[type="file"]')` 并加 `.set_input_files(...)`，Playwright 会自动等待 input 节点 attached，极大减少"detached element"问题。
- 上传图片后适当等待页面渲染，再自动点击"确认"按钮。
- 相关代码片段：

```python
input_locator = page.locator('div.single-cover-uploader-wrap input[type="file"]')
await input_locator.wait_for(state="attached", timeout=5000)
await input_locator.set_input_files(cover_path)
```

- 这样可以大幅提升封面上传的稳定性，自动化流程会顺利上传封面、点击确认并完成后续操作。

---
