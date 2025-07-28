# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from playwright.async_api import Playwright, async_playwright, Page # 在这里添加 Page
import os
import asyncio
import random

from conf import LOCAL_CHROME_PATH
from utils.base_social_media import set_init_script
from utils.files_times import get_absolute_path
from utils.log import tencent_logger


def format_str_for_short_title(origin_title: str) -> str:
    # 定义允许的特殊字符 (根据用户描述更新)
    # 书名号《》, 引号", 冒号：, 加号+, 问号?, 百分号%, 摄氏度°
    allowed_special_chars = '《》":+?%°' # 更新：添加冒号，修正引号表示

    # 重写过滤逻辑以提高清晰度并处理两种逗号
    filtered_chars = []
    for char in origin_title:
        if char.isalnum() or char in allowed_special_chars:
            filtered_chars.append(char)
        elif char == ',' or char == '，': # 处理英文和中文逗号
            filtered_chars.append(' ')
        # 其他所有不符合条件的字符（包括不允许的符号和Emoji）会被自动忽略

    formatted_string = ''.join(filtered_chars)

    # 视频号短标题要求至少6个字，不足补空格，超出截断
    if len(formatted_string) > 16:
        formatted_string = formatted_string[:16]
    # 在截断后检查长度是否小于6
    if len(formatted_string) < 6:
        formatted_string += ' ' * (6 - len(formatted_string)) # 补空格

    # 返回处理后的字符串，平台通常会自动处理首尾空格，这里不再strip
    return formatted_string


async def cookie_auth(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://channels.weixin.qq.com/platform/post/create")
        try:
            await page.wait_for_selector('div.title-name:has-text("微信小店")', timeout=5000)  # 等待5秒
            tencent_logger.error("[+] 等待5秒 cookie 失效")
            return False
        except:
            tencent_logger.success("[+] cookie 有效")
            return True


async def get_tencent_cookie(account_file):
    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': False,  # Set headless option here
        }
        # Make sure to run headed.
        # Use default Chromium browser
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        # Pause the page, and start recording manually.
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://channels.weixin.qq.com")
        await page.pause()
        # 点击调试器的继续，保存cookie
        await context.storage_state(path=account_file)


async def weixin_setup(account_file, handle=False):
    account_file = get_absolute_path(account_file, "tencent_uploader")
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            # Todo alert message
            return False
        tencent_logger.info('[+] cookie文件不存在或已失效，即将自动打开浏览器，请扫码登录，登陆后会自动生成cookie文件')
        await get_tencent_cookie(account_file)
    return True


class TencentVideo(object):
    def __init__(self, short_title, title_and_tags, file_path, publish_date: datetime, account_file, category=None, original_declaration=True, cover_position='top', thumbnail_path=None):
        self.short_title = short_title  # 短标题
        self.title_and_tags = title_and_tags  # 标题和话题内容
        self.file_path = file_path
        self.publish_date = publish_date
        self.account_file = account_file
        self.category = category
        self.local_executable_path = LOCAL_CHROME_PATH
        self.original_declaration = original_declaration  # 添加原创声明配置
        self.cover_position = cover_position  # 封面选取位置：'top'/'middle'/'bottom'
        self.thumbnail_path = thumbnail_path  # 新增：外部传入的封面路径

    async def set_schedule_time_tencent(self, page, publish_date):
        label_element = page.locator("label").filter(has_text="定时").nth(1)
        await label_element.click()

        await page.click('input[placeholder="请选择发表时间"]')

        str_month = str(publish_date.month) if publish_date.month > 9 else "0" + str(publish_date.month)
        current_month = str_month + "月"
        # 获取当前的月份
        page_month = await page.inner_text('span.weui-desktop-picker__panel__label:has-text("月")')

        # 检查当前月份是否与目标月份相同
        if page_month != current_month:
            await page.click('button.weui-desktop-btn__icon__right')

        # 获取页面元素
        elements = await page.query_selector_all('table.weui-desktop-picker__table a')

        # 遍历元素并点击匹配的元素
        for element in elements:
            if 'weui-desktop-picker__disabled' in await element.evaluate('el => el.className'):
                continue
            text = await element.inner_text()
            if text.strip() == str(publish_date.day):
                await element.click()
                break

        # 选择时间（鼠标点选小时和分钟）
        await page.click('input[placeholder="请选择时间"]')
        await page.wait_for_selector('ol.weui-desktop-picker__time__hour', timeout=3000)
        # 点击目标小时
        hour_str = f"{publish_date.hour:02d}"
        hour_ol = page.locator('ol.weui-desktop-picker__time__hour')
        hour_count = await hour_ol.locator('li').count()
        for i in range(hour_count):
            li = hour_ol.locator('li').nth(i)
            if await li.inner_text() == hour_str:
                await li.click()
                break
        # 点击目标分钟
        minute_str = f"{publish_date.minute:02d}"
        minute_ol = page.locator('ol.weui-desktop-picker__time__minute')
        minute_count = await minute_ol.locator('li').count()
        for i in range(minute_count):
            li = minute_ol.locator('li').nth(i)
            if await li.inner_text() == minute_str:
                await li.click()
                break
        # 点击空白处，令选择生效
        await page.click("body")

    async def handle_upload_error(self, page):
        tencent_logger.info("视频出错了，重新上传中")
        await page.locator('div.media-status-content div.tag-inner:has-text("删除")').click()
        await page.get_by_role('button', name="删除", exact=True).click()
        file_input = page.locator('input[type="file"]')
        await file_input.set_input_files(self.file_path)

    async def adjust_cover_position(self, page: Page):
        """调整封面选取框位置"""
        if self.cover_position == 'middle':
            tencent_logger.info("封面位置设置为中间，无需调整")
            return

        try:
            await page.wait_for_selector('div.crop-wrapper.vertical', timeout=8000)
            crop_area = page.locator('div.crop-wrapper.vertical')
            box = await crop_area.bounding_box()
            if not box:
                tencent_logger.warning("未获取到crop-wrapper.vertical的bounding box，跳过拖动")
                return

            await page.screenshot(path="crop_wrapper_vertical.png", clip=box)
            tencent_logger.info("已截图crop-wrapper.vertical区域")
            
            start_x = box["x"] + box["width"] / 2
            max_attempts = 15  # 增加最大尝试次数
            attempt = 0
            
            while attempt < max_attempts:
                box = await crop_area.bounding_box()
                if not box:
                    tencent_logger.warning("拖动时未获取到crop-wrapper.vertical的bounding box，跳过")
                    break
                
                current_y = box["y"] + box["height"] / 2
                target_y = box["y"] + 5 if self.cover_position == 'top' else box["y"] + box["height"] - 5
                
                # 检查是否已经到达目标位置
                if abs(current_y - target_y) <= 5:
                    tencent_logger.info(f"选取框已到达目标位置({current_y:.1f})，共拖动{attempt}次")
                    break
                
                # 随机步长（每次拖动60~100像素）
                step = random.randint(60, 100)
                if self.cover_position == 'top':
                    next_y = max(current_y - step, target_y)
                else:  # bottom
                    next_y = min(current_y + step, target_y)
                
                await page.mouse.move(start_x, current_y)
                await page.mouse.down()
                await page.mouse.move(start_x, next_y, steps=5)
                await page.mouse.up()
                tencent_logger.info(f"第{attempt+1}次拖动：{current_y:.1f} -> {next_y:.1f}")
                
                # 随机等待（每次拖动后等待0.8~1.5秒）
                wait_ms = random.randint(800, 1500)
                await page.wait_for_timeout(wait_ms)
                attempt += 1
            else:
                tencent_logger.warning("多次拖动后仍未到达目标位置，可能平台有阻尼或页面异常")
                
        except Exception as e:
            tencent_logger.warning(f"调整封面位置失败: {e}")

    async def upload_cover(self, page: Page, cover_path: str):
        try:
            # 1. 等待并点击"更换封面"按钮
            btn_selector = 'div.finder-tag-wrap.btn .tag-inner:text("更换封面")'
            for _ in range(60):
                btn = await page.query_selector(btn_selector)
                if btn:
                    btn_class = await btn.evaluate('el => el.parentElement.className')
                    if 'disabled' not in btn_class and 'is-disabled' not in btn_class:
                        break
                await asyncio.sleep(1)
            else:
                tencent_logger.error("更换封面按钮长时间不可用，放弃上传封面")
                return
            await btn.click()
            await page.wait_for_selector('div.cover-control-wrap', timeout=10000)

            # 2. 如果有封面图，先上传
            uploaded_cover = False
            if cover_path:
                try:
                    # 等待并上传封面图
                    file_input = page.locator('input[type="file"][accept*="image"]')
                    await file_input.set_input_files(cover_path)
                    # 等待图片加载完成
                    await page.wait_for_timeout(2000)
                    uploaded_cover = True
                except Exception as e:
                    tencent_logger.warning(f"上传封面图片失败: {e}")

            # 3. 只有未上传图片时才执行拖拽逻辑
            if not uploaded_cover:
                await self.adjust_cover_position(page)

            # 4. 点击确认按钮
            confirm_selector = 'button:has-text("确认")'
            try:
                await page.wait_for_selector(confirm_selector, timeout=8000)
                confirm_buttons = await page.query_selector_all(confirm_selector)
                for btn in confirm_buttons:
                    if await btn.is_visible():
                        await btn.click()
                        tencent_logger.info("已点击最终 '确认' 按钮")
                        await page.screenshot(path="after_final_confirm.png")
                        break
            except Exception as e:
                tencent_logger.warning(f"查找或点击最终 '确认' 按钮失败: {e}")

            await asyncio.sleep(2)  # 等待页面反应
        except Exception as e:
            tencent_logger.error(f"处理封面失败: {e}")
            await page.screenshot(path="cover_upload_error.png")

    async def set_no_location(self, page):
        try:
            # 1. 点击"位置"区域，弹出下拉框
            await page.click('div.label:has-text("位置") + div .position-display-wrap')
            await page.wait_for_timeout(500)  # 等待下拉框弹出
            # 2. 点击"不显示位置"选项
            await page.wait_for_selector('div.common-option-list-wrap', timeout=2000)
            await page.click('div.option-item .name:text("不显示位置")')
            tencent_logger.info("已设置为不显示位置")
        except Exception as e:
            tencent_logger.error(f"设置不显示位置失败: {e}")

    async def upload_cover_image(self, page):
        """查找并上传封面图片"""
        # 优先使用外部传入的thumbnail_path
        if self.thumbnail_path and os.path.exists(self.thumbnail_path):
            tencent_logger.info(f"  [-] 使用外部传入的封面图: {self.thumbnail_path}")
            await self.upload_cover(page, self.thumbnail_path)
            return
        # 否则自动查找同名封面
        base_name = os.path.splitext(os.path.basename(self.file_path))[0]
        exts = [".png", ".jpeg", ".jpg", ".webp"]
        cover_path = None
        video_dir = os.path.dirname(self.file_path)
        for ext in exts:
            candidate = os.path.join(video_dir, f"{base_name}{ext}")
            if os.path.exists(candidate):
                cover_path = candidate
                break
        if cover_path:
            tencent_logger.info(f"  [-] 找到封面图，准备上传: {cover_path}")
            await self.upload_cover(page, cover_path)
        else:
            tencent_logger.info(f"  [-] 未找到与视频同名的封面图片: {base_name}.[png/jpeg/jpg/webp]，依然进入封面裁剪界面。")
            await self.upload_cover(page, None)

    async def upload(self, playwright: Playwright) -> None:
        # 使用 Chromium (这里使用系统内浏览器，用chromium 会造成h264错误
        # Use Chrome for better H.264 support
        try:
            browser = await playwright.chromium.launch(
                headless=False,
                channel="chrome"  # Use Chrome which includes H.264 support
            )
        except Exception as e:
            tencent_logger.warning(f"Failed to launch Chrome, falling back to Chromium: {str(e)}")
            # Fall back to Chromium if Chrome is not available
            browser = await playwright.chromium.launch(headless=False)
        # 创建一个浏览器上下文，使用指定的 cookie 文件
        context = await browser.new_context(storage_state=f"{self.account_file}")
        context = await set_init_script(context)

        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://channels.weixin.qq.com/platform/post/create")
        tencent_logger.info(f'[+]正在上传-------{self.title_and_tags}.mp4')
        # 等待页面跳转到指定的 URL，没进入，则自动等待到超时
        await page.wait_for_url("https://channels.weixin.qq.com/platform/post/create")
        # await page.wait_for_selector('input[type="file"]', timeout=10000)
        file_input = page.locator('input[type="file"]')
        await file_input.set_input_files(self.file_path)
        # 检查上传状态，失败自动重试
        await self.detect_upload_status(page)
        # 填充标题和话题
        await self.add_title_tags(page)
        # 添加商品
        # await self.add_product(page)
        # 合集功能
        await self.add_collection(page)
        # 原创选择
        if self.original_declaration:
            print("开始执行原创声明流程...")
            await self.add_original(page)
            print("原创声明流程执行完成")
        else:
            print("已跳过原创声明流程（根据配置）")
        
        # 设置不显示位置
        await self.set_no_location(page)
        # 默认定时发布：无论publish_date是否为0都定时，若为0则设为次日9点
        if not self.publish_date or self.publish_date == 0:
            now = datetime.now()
            self.publish_date = now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
        await self.set_schedule_time_tencent(page, self.publish_date)
        # 添加短标题
        await self.add_short_title(page)
        # 上传同名封面图片（放到最后，确保视频解析完成后再操作）
        await self.upload_cover_image(page) # 现在这个调用是有效的
        # 点击发表
        await self.click_publish(page)

        await context.storage_state(path=f"{self.account_file}")  # 保存cookie
        tencent_logger.success('  [-]cookie更新完毕！')
        await asyncio.sleep(2)  # 这里延迟是为了方便眼睛直观的观看
        # 关闭浏览器上下文和浏览器实例
        await context.close()
        await browser.close()

    async def add_title_tags(self, page):
        await page.locator("div.input-editor").click()
        await page.keyboard.type(self.title_and_tags)
        tencent_logger.info("已填写标题和话题")

    async def add_short_title(self, page):
        short_title_element = page.get_by_text("短标题", exact=True).locator("..") \
            .locator("xpath=following-sibling::div").locator('span input[type="text"]')
        if await short_title_element.count():
            await short_title_element.fill(self.short_title)

    async def click_publish(self, page):
        while True:
            try:
                publish_buttion = page.locator('div.form-btns button:has-text("发表")')
                if await publish_buttion.count():
                    await publish_buttion.click()
                await page.wait_for_url("https://channels.weixin.qq.com/platform/post/list", timeout=1500)
                tencent_logger.success("  [-]视频发布成功")
                break
            except Exception as e:
                current_url = page.url
                if "https://channels.weixin.qq.com/platform/post/list" in current_url:
                    tencent_logger.success("  [-]视频发布成功")
                    break
                else:
                    tencent_logger.exception(f"  [-] Exception: {e}")
                    tencent_logger.info("  [-] 视频正在发布中...")
                    await asyncio.sleep(0.5)

    async def detect_upload_status(self, page):
        retry_count = 0
        max_retries = 3
        while True:
            try:
                # 匹配删除按钮，代表视频上传完毕
                if "weui-desktop-btn_disabled" not in await page.get_by_role("button", name="发表").get_attribute('class'):
                    tencent_logger.info("  [-]视频上传完毕")
                    break
                else:
                    tencent_logger.info("  [-] 正在上传视频中...")
                    await asyncio.sleep(2)
                    # 出错了视频出错
                    if await page.locator('div.status-msg.error').count() and await page.locator('div.media-status-content div.tag-inner:has-text("删除")').count():
                        retry_count += 1
                        if retry_count > max_retries:
                            tencent_logger.error(f"  [-] 上传失败已达最大重试次数（{max_retries}次），终止流程。")
                            raise Exception("视频上传失败，重试次数过多，已终止。")
                        tencent_logger.error(f"  [-] 发现上传出错了...准备重试（第{retry_count}次）")
                        await self.handle_upload_error(page)
            except Exception as e:
                tencent_logger.info(f"  [-] 正在上传视频中...（异常：{e}）")
                await asyncio.sleep(2)

    async def add_collection(self, page):
        # 默认不添加合集，直接跳过
        return

    async def add_original(self, page: Page):
        """声明原创"""
        try:
            tencent_logger.info("开始原创声明流程...")
            # 等待第一个复选框可见
            original_checkbox = page.locator('.declare-original-checkbox .ant-checkbox-input')
            await original_checkbox.wait_for(state="visible", timeout=10000)
            tencent_logger.info("原创声明复选框可见，尝试点击...")
            await original_checkbox.click(timeout=5000)
            tencent_logger.info("已勾选原创声明复选框")
            
            dialog = page.locator('.weui-desktop-dialog:has-text("原创权益")').first
            await dialog.wait_for(state="visible", timeout=10000)
            tencent_logger.info("原创权益弹窗已出现")
            
            agreement_checkbox = dialog.locator('.original-proto-wrapper .ant-checkbox-input')
            await agreement_checkbox.wait_for(state="visible", timeout=10000)
            tencent_logger.info("原创声明协议复选框可见，尝试点击...")
            await agreement_checkbox.click(timeout=5000)
            tencent_logger.info("已同意原创声明协议")
            
            confirm_button = dialog.locator('.weui-desktop-dialog__ft .weui-desktop-btn_primary:has-text("声明原创")')
            # 修改点：等待按钮可见，而不是"enabled"
            await confirm_button.wait_for(state="visible", timeout=10000) 
            tencent_logger.info("声明原创按钮可见，尝试点击...") # 更新日志信息
            # .click() 会自动等待按钮可被点击 (包括 enabled)
            await confirm_button.click(timeout=5000)
            
            await dialog.wait_for(state="hidden", timeout=10000)
            
            tencent_logger.success("原创声明流程完成")
        except Exception as e:
            tencent_logger.error(f"原创声明过程出错: {e}")
            # raise e # 根据需要决定是否抛出异常

    async def main(self):
        async with async_playwright() as playwright:
            await self.upload(playwright)
