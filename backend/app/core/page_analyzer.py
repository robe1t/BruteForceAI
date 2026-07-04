# -*- coding: utf-8 -*-
"""
Page analyzer for login form analysis
"""
import asyncio
import json
import re
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse
from datetime import datetime

from playwright.async_api import Page

from app.core.browser_pool import BrowserPool
from app.database.models import PageAnalysis


class PageAnalyzer:
    """
    页面分析器

    Analyzes login pages to identify:
    - Username selector
    - Password selector
    - Submit button selector
    - Captcha presence and type
    - Error page characteristics (via test/test probe)
    """

    def __init__(self, llm_client, browser_pool: BrowserPool, log_callback=None):
        """
        Initialize page analyzer

        Args:
            llm_client: LLM client for AI analysis
            browser_pool: Browser pool instance
            log_callback: Optional callback for logging (task_id, message, level)
        """
        self.llm_client = llm_client
        self.browser_pool = browser_pool
        self.log_callback = log_callback

    def _log(self, task_id: str, message: str, level: str = 'info'):
        """Output log to both console and callback"""
        print(f"[{task_id}] {message}")
        if self.log_callback:
            self.log_callback(task_id, message, level)

    async def analyze(self, url: str, task_id: str) -> Optional[Dict]:
        """
        分析登录页面 - 优化流程（节省token）

        流程:
        1. 访问页面，截图
        2. 启发式规则找选择器（优先，不消耗token）
        3. 规则失败才调用AI分析
        4. 检测验证码
        5. 错误探测(test/test)，记录DOM长度
        6. 存入数据库

        Args:
            url: Target URL
            task_id: Task ID

        Returns:
            Analysis result dict or None if failed
        """
        domain = urlparse(url).netloc
        page = None

        try:
            # Step 1: 创建页面并访问
            self._log(task_id, f"正在访问页面: {url}")
            self._log(task_id, f"Browser pool state: browser={self.browser_pool.browser is not None}, playwright={self.browser_pool.playwright is not None}", "debug")
            page = await self.browser_pool.create_page(domain)
            self._log(task_id, "Page created successfully")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            self._log(task_id, "Page loaded successfully")

            # Step 2: 截图保存
            screenshot_path = await self._take_screenshot(page, task_id)
            self._log(task_id, "截图已保存")

            # Step 3: 启发式规则查找选择器（优先，不消耗token）
            self._log(task_id, "尝试启发式规则查找选择器...")
            selectors = await self._find_selectors_heuristically(page)

            # Step 4: 如果启发式规则失败，调用AI分析
            ai_used = False
            if not selectors:
                self._log(task_id, "启发式规则未找到选择器，调用AI分析...")
                html = await page.content()
                selectors = await self._analyze_with_llm(html)
                ai_used = True
            else:
                self._log(task_id, "启发式规则成功找到选择器（节省token）")

            if not selectors:
                self._log(task_id, "无法识别页面选择器", "error")
                return None

            # Step 5: 验证选择器
            valid = await self._validate_selectors(page, selectors)
            if not valid:
                self._log(task_id, "选择器验证失败，重新尝试启发式规则...", "warning")
                selectors = await self._find_selectors_heuristically(page)
                if not selectors:
                    self._log(task_id, "无法找到有效选择器", "error")
                    return None

            self._log(task_id, f"选择器已定位: 用户名={selectors.get('username_selector')}, 密码={selectors.get('password_selector')}, 提交={selectors.get('submit_selector')}")

            # Step 6: 检测验证码
            captcha_info = await self._detect_captcha(page)
            selectors.update(captcha_info)
            captcha_msg = f"验证码检测: {'存在' if captcha_info['has_captcha'] else '无'}"
            if captcha_info['has_captcha']:
                captcha_msg += f", 类型={captcha_info.get('captcha_type')}"
            self._log(task_id, captcha_msg)

            # Step 7: 错误探测(test/test) - 获取错误DOM长度
            self._log(task_id, "执行错误探测(test/test)...")
            error_info = await self._error_probe(page, url, selectors, task_id)
            selectors.update(error_info)
            self._log(task_id, f"错误DOM长度: {selectors.get('failed_dom_length')}")

            # Step 8: 保存截图路径
            selectors['screenshot_path'] = screenshot_path

            # Step 9: 存入数据库
            PageAnalysis.create(
                task_id=task_id,
                url=url,
                **selectors
            )

            self._log(task_id, "页面分析完成")
            return selectors

        except Exception as e:
            error_msg = str(e)
            self._log(task_id, f"页面分析失败: {error_msg}", "error")
            import traceback
            traceback.print_exc()

            # Provide more specific error message
            if 'net::ERR' in error_msg or 'timeout' in error_msg.lower():
                raise Exception(f"无法访问目标URL: {error_msg}")
            else:
                raise Exception(f"页面分析失败: {error_msg}")

        finally:
            if page:
                await self.browser_pool.release_page(page)

    async def _take_screenshot(self, page: Page, task_id: str) -> str:
        """
        Take screenshot and save

        Args:
            page: Playwright page
            task_id: Task ID

        Returns:
            Screenshot path
        """
        from flask import current_app

        try:
            screenshot_dir = Path(current_app.config.get('SCREENSHOT_FOLDER', 'data/screenshots'))
        except RuntimeError:
            screenshot_dir = Path('data/screenshots')

        screenshot_dir.mkdir(parents=True, exist_ok=True)

        screenshot_path = screenshot_dir / f"{task_id}.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)

        return str(screenshot_path)

    async def _analyze_with_llm(self, html: str) -> Optional[Dict]:
        """
        Use LLM to analyze HTML

        Args:
            html: HTML content

        Returns:
            Selectors dict or None
        """
        if not self.llm_client:
            print("[PageAnalyzer] No LLM client available, skipping LLM analysis")
            return None

        try:
            # Extract relevant parts of HTML to reduce token usage
            # Focus on form elements, inputs, and buttons
            import re

            # Try to extract just the form content
            form_match = re.search(r'<form[^>]*>[\s\S]*?</form>', html, re.IGNORECASE)
            if form_match:
                html_snippet = form_match.group()
            else:
                # Extract all input and button elements
                inputs = re.findall(r'<input[^>]*>', html, re.IGNORECASE)
                buttons = re.findall(r'<button[^>]*>[\s\S]*?</button>', html, re.IGNORECASE)
                forms = re.findall(r'<form[^>]*>', html, re.IGNORECASE)
                html_snippet = '\n'.join(forms + inputs + buttons)

            # Truncate if still too long (reduce to 15000 chars for faster processing)
            if len(html_snippet) > 15000:
                html_snippet = html_snippet[:15000]

            print(f"[PageAnalyzer] HTML snippet length: {len(html_snippet)} chars")
            print("[PageAnalyzer] Calling LLM analyze_html...")

            response = self.llm_client.analyze_html(html_snippet)

            if not response.success:
                print(f"[PageAnalyzer] LLM analysis failed: {response.error}")
                return None

            print(f"[PageAnalyzer] LLM response: {response.content[:500]}...")

            # Parse JSON response
            content = response.content.strip()

            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group()
                selectors = json.loads(json_str)
                print(f"[PageAnalyzer] Parsed selectors: {selectors}")
                return selectors

            print("[PageAnalyzer] No JSON found in LLM response")
            return None

        except json.JSONDecodeError as e:
            print(f"[PageAnalyzer] Failed to parse LLM response: {e}")
            return None
        except Exception as e:
            print(f"[PageAnalyzer] Error in LLM analysis: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _validate_selectors(self, page: Page, selectors: Dict) -> bool:
        """
        Validate that selectors exist on page

        Args:
            page: Playwright page
            selectors: Selectors dict

        Returns:
            True if all selectors are valid
        """
        required = ['username_selector', 'password_selector', 'submit_selector']

        for key in required:
            selector = selectors.get(key)
            if not selector:
                return False

            try:
                element = await page.query_selector(selector)
                if not element:
                    return False
            except Exception:
                return False

        return True

    async def _find_selectors_heuristically(self, page: Page) -> Optional[Dict]:
        """
        Find selectors using heuristics when LLM fails

        Args:
            page: Playwright page

        Returns:
            Selectors dict or None
        """
        selectors = {}

        # Extended username selectors
        username_selectors = [
            # Standard names
            'input[name="username"]',
            'input[name="user"]',
            'input[name="login"]',
            'input[name="account"]',
            'input[name="accountname"]',
            'input[name="uname"]',
            'input[name="userid"]',
            'input[name="uid"]',
            # Type=text with user-related names
            'input[type="text"][name*="user"]',
            'input[type="text"][name*="login"]',
            'input[type="text"][name*="account"]',
            # IDs
            'input[id*="user"]',
            'input[id*="login"]',
            'input[id*="account"]',
            '#username',
            '#user',
            '#login',
            '#account',
            '#userid',
            '#uid',
            # Email inputs (often used as username)
            'input[type="email"]',
            'input[name="email"]',
            'input[id*="email"]',
            # Placeholder-based
            'input[placeholder*="用户名"]',
            'input[placeholder*="账号"]',
            'input[placeholder*="username"]',
            'input[placeholder*="email"]',
            'input[placeholder*="邮箱"]',
            # Class-based
            'input[class*="username"]',
            'input[class*="user-name"]',
            'input[class*="login"]',
            # Generic text input in form
            'form input[type="text"]:first-of-type',
            'form input:not([type="password"]):not([type="hidden"]):not([type="submit"]):first-of-type',
        ]

        for selector in username_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    is_visible = await element.is_visible()
                    if is_visible:
                        selectors['username_selector'] = selector
                        break
            except Exception:
                continue

        # Extended password selectors
        password_selectors = [
            'input[name="password"]',
            'input[name="pass"]',
            'input[name="pwd"]',
            'input[name="passwd"]',
            'input[name="userpass"]',
            'input[type="password"]',
            'input[id*="pass"]',
            'input[id*="pwd"]',
            '#password',
            '#pass',
            '#pwd',
            'input[placeholder*="密码"]',
            'input[placeholder*="password"]',
            'input[class*="password"]',
            'input[class*="pass"]',
        ]

        for selector in password_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    is_visible = await element.is_visible()
                    if is_visible:
                        selectors['password_selector'] = selector
                        break
            except Exception:
                continue

        # Extended submit button selectors - prioritize specific selectors
        submit_selectors = [
            # Type=submit (highest priority)
            'button[type="submit"]',
            'input[type="submit"]',
            # IDs
            '#submit',
            '#login-btn',
            '#submit-btn',
            '#loginBtn',
            '#submitBtn',
            # Classes
            '.submit-btn',
            '.login-btn',
            '.btn-login',
            '.btn-submit',
        ]

        submit_selector = None
        for selector in submit_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    is_visible = await element.is_visible()
                    if is_visible:
                        # Verify this is a valid login button
                        if await self._is_valid_login_button(page, element):
                            submit_selector = selector
                            break
            except Exception:
                continue

        # If not found, search by text but exclude invalid buttons
        if not submit_selector:
            submit_selector = await self._find_submit_by_text(page)

        if submit_selector:
            selectors['submit_selector'] = submit_selector

        # If we have all three, return immediately
        if len(selectors) >= 3:
            return selectors

        # Fallback: Try to find any text input and password input
        if 'username_selector' not in selectors:
            try:
                # Find all text/email inputs
                text_inputs = await page.query_selector_all('input[type="text"], input[type="email"], input:not([type])')
                for inp in text_inputs:
                    try:
                        is_visible = await inp.is_visible()
                        if is_visible:
                            inp_type = await inp.get_attribute('type')
                            inp_name = await inp.get_attribute('name') or ''
                            inp_id = await inp.get_attribute('id') or ''
                            # Skip if it looks like a password or hidden field
                            if inp_type not in ['password', 'hidden', 'submit', 'button']:
                                # Skip captcha inputs
                                if 'captcha' not in inp_name.lower() and 'captcha' not in inp_id.lower():
                                    selectors['username_selector'] = f'input[name="{inp_name}"]' if inp_name else f'#{inp_id}' if inp_id else 'input[type="text"]'
                                    break
                    except Exception:
                        continue
            except Exception:
                pass

        if 'password_selector' not in selectors:
            try:
                pwd_input = await page.query_selector('input[type="password"]')
                if pwd_input:
                    is_visible = await pwd_input.is_visible()
                    if is_visible:
                        selectors['password_selector'] = 'input[type="password"]'
            except Exception:
                pass

        if 'submit_selector' not in selectors:
            try:
                # Try to find any button in the form
                buttons = await page.query_selector_all('button, input[type="submit"], input[type="button"]')
                for btn in buttons:
                    try:
                        is_visible = await btn.is_visible()
                        if is_visible:
                            selectors['submit_selector'] = 'button'  # Generic fallback
                            break
                    except Exception:
                        continue
            except Exception:
                pass

        # Return if we have at least username and password
        if 'username_selector' in selectors and 'password_selector' in selectors:
            # Ensure we have a submit selector
            if 'submit_selector' not in selectors:
                selectors['submit_selector'] = 'button'  # Generic fallback
            return selectors

        return None

    async def _repair_selectors(self, page: Page, selectors: Dict) -> Optional[Dict]:
        """
        尝试修复无效的选择器

        Args:
            page: Playwright page
            selectors: 原始选择器

        Returns:
            修复后的选择器或None
        """
        repaired = selectors.copy()

        # 检查并修复用户名选择器
        if not await self._is_selector_valid(page, selectors.get('username_selector')):
            for sel in ['input[type="text"]', 'input:not([type="password"])', 'input']:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        repaired['username_selector'] = sel
                        break
                except Exception:
                    continue

        # 检查并修复密码选择器
        if not await self._is_selector_valid(page, selectors.get('password_selector')):
            try:
                el = await page.query_selector('input[type="password"]')
                if el and await el.is_visible():
                    repaired['password_selector'] = 'input[type="password"]'
            except Exception:
                pass

        # 检查并修复提交按钮选择器
        if not await self._is_selector_valid(page, selectors.get('submit_selector')):
            for sel in ['button', 'input[type="submit"]', '[role="button"]']:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        repaired['submit_selector'] = sel
                        break
                except Exception:
                    continue

        # 验证修复后的选择器
        if await self._validate_selectors(page, repaired):
            return repaired

        return None

    async def _is_selector_valid(self, page: Page, selector: str) -> bool:
        """检查选择器是否有效"""
        if not selector:
            return False
        try:
            el = await page.query_selector(selector)
            return el is not None and await el.is_visible()
        except Exception:
            return False

    async def _is_valid_login_button(self, page: Page, button) -> bool:
        """
        Check if a button is a valid login submit button (not QR code, etc.)

        Args:
            page: Playwright page
            button: Button element

        Returns:
            True if it's a valid login button
        """
        try:
            # Get button text
            text = await button.inner_text()
            text_lower = text.lower()

            # Keywords that indicate this is NOT a login submit button
            exclude_keywords = [
                '二维码', '扫码', 'qr', 'qrcode',
                '微信', 'qq', 'weixin', 'weibo',
                '注册', 'register', 'signup', 'sign up',
                '忘记', 'forgot', 'reset',
                '短信', 'sms', '手机', 'phone',
                '验证码', 'captcha',
                '其他', 'other', '更多', 'more'
            ]

            for kw in exclude_keywords:
                if kw in text_lower:
                    print(f"[PageAnalyzer] Excluding button with text: {text} (contains: {kw})")
                    return False

            # Check if button is inside a form (preferred)
            in_form = await button.evaluate('el => el.closest("form") !== null')
            if in_form:
                return True

            # Check if button is near password input
            try:
                # Look for password input in the same container
                parent = await button.evaluate_handle('el => el.parentElement')
                password_nearby = await parent.query_selector('input[type="password"]')
                if password_nearby:
                    return True
            except Exception:
                pass

            return True

        except Exception as e:
            print(f"[PageAnalyzer] Error validating login button: {e}")
            return True  # Default to True if check fails

    async def _find_submit_by_text(self, page: Page) -> Optional[str]:
        """
        Find submit button by text content, excluding invalid buttons

        Args:
            page: Playwright page

        Returns:
            Selector for the submit button or None
        """
        # Valid login button texts (prioritized)
        valid_texts = [
            ('登录', 'button:has-text("登录")'),
            ('登 录', 'button:has-text("登 录")'),
            ('登陆', 'button:has-text("登陆")'),
            ('Login', 'button:has-text("Login")'),
            ('Log in', 'button:has-text("Log in")'),
            ('Sign in', 'button:has-text("Sign in")'),
            ('提交', 'button:has-text("提交")'),
            ('确认', 'button:has-text("确认")'),
            ('立即登录', 'button:has-text("立即登录")'),
        ]

        for text, selector in valid_texts:
            try:
                # Find all buttons with this text
                elements = await page.query_selector_all(f'button:has-text("{text}"), a:has-text("{text}")')

                for element in elements:
                    is_visible = await element.is_visible()
                    if is_visible:
                        # Check if this is a valid login button
                        if await self._is_valid_login_button(page, element):
                            # Get element's tag and attributes for a more specific selector
                            tag = await element.evaluate('el => el.tagName.toLowerCase()')
                            btn_text = await element.inner_text()

                            # Try to get a unique selector
                            btn_id = await element.get_attribute('id')
                            btn_class = await element.get_attribute('class')

                            if btn_id:
                                return f'#{btn_id}'
                            elif btn_class:
                                # Use first class
                                first_class = btn_class.split()[0] if btn_class.split() else ''
                                if first_class:
                                    return f'{tag}.{first_class}'

                            return selector

            except Exception:
                continue

        # Fallback: find button in form
        try:
            form_buttons = await page.query_selector_all('form button, form input[type="submit"], form input[type="button"]')
            for btn in form_buttons:
                is_visible = await btn.is_visible()
                if is_visible:
                    if await self._is_valid_login_button(page, btn):
                        btn_type = await btn.get_attribute('type')
                        btn_id = await btn.get_attribute('id')

                        if btn_id:
                            return f'#{btn_id}'
                        elif btn_type == 'submit':
                            return 'button[type="submit"]'
                        else:
                            return 'form button'
        except Exception:
            pass

        return None

    async def _detect_captcha(self, page: Page) -> Dict:
        """
        Detect captcha on page

        Args:
            page: Playwright page

        Returns:
            Captcha info dict
        """
        captcha_info = {
            'has_captcha': False,
            'captcha_type': None,
            'captcha_selector': None,
            'captcha_input_selector': None
        }

        # First, check for captcha input field (most reliable indicator)
        captcha_input_selectors = [
            'input[name*="captcha"]',
            'input[id*="captcha"]',
            'input[placeholder*="验证码"]',
            'input[placeholder*="captcha"]',
            'input[class*="captcha"]',
            '#captcha',
            '.captcha-input',
            'input[maxlength="4"]',  # Many captchas are 4 chars
            'input[maxlength="5"]',
            'input[maxlength="6"]',
        ]

        captcha_input = None
        for input_sel in captcha_input_selectors:
            try:
                input_el = await page.query_selector(input_sel)
                if input_el:
                    is_visible = await input_el.is_visible()
                    if is_visible:
                        captcha_input = input_el
                        captcha_info['captcha_input_selector'] = input_sel
                        break
            except Exception:
                continue

        # If we found a captcha input, there's likely a captcha
        if captcha_input:
            captcha_info['has_captcha'] = True

        # Check for image captcha
        image_captcha_selectors = [
            # Standard captcha indicators
            'img[src*="captcha"]',
            'img[id*="captcha"]',
            'img[class*="captcha"]',
            '#captcha_img',
            '.captcha-img',
            'img[alt*="验证码"]',
            'img[alt*="captcha"]',
            # Base64 images (often used for captchas)
            'img[src^="data:image"]',
            # Canvas captcha
            'canvas[class*="captcha"]',
            'canvas[id*="captcha"]',
        ]

        for selector in image_captcha_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    is_visible = await element.is_visible()
                    if is_visible:
                        # Check image size (captchas are typically small)
                        box = await element.bounding_box()
                        if box:
                            width = box['width']
                            height = box['height']
                            # Typical captcha dimensions: 50-200px width, 20-80px height
                            if 40 <= width <= 250 and 20 <= height <= 100:
                                captcha_info['has_captcha'] = True
                                captcha_info['captcha_type'] = 'image'
                                captcha_info['captcha_selector'] = selector
                                return captcha_info
            except Exception:
                continue

        # If captcha input found but no image detected, still mark as having captcha
        if captcha_info['has_captcha']:
            captcha_info['captcha_type'] = 'image'
            # Try to find the image near the input
            if captcha_input:
                try:
                    # Look for any img in the same container
                    parent = await captcha_input.evaluate_handle('el => el.parentElement')
                    img = await parent.query_selector('img')
                    if img:
                        captcha_info['captcha_selector'] = 'img'
                except Exception:
                    pass
            return captcha_info

        # Check for reCAPTCHA
        recaptcha_selectors = [
            '.g-recaptcha',
            '#g-recaptcha',
            'iframe[src*="recaptcha"]',
        ]

        for selector in recaptcha_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    captcha_info['has_captcha'] = True
                    captcha_info['captcha_type'] = 'recaptcha'
                    return captcha_info
            except Exception:
                continue

        # Check for hCaptcha
        hcaptcha_selectors = [
            '.h-captcha',
            '#h-captcha',
            'iframe[src*="hcaptcha"]',
        ]

        for selector in hcaptcha_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    captcha_info['has_captcha'] = True
                    captcha_info['captcha_type'] = 'hcaptcha'
                    return captcha_info
            except Exception:
                continue

        # Check for slider captcha
        slider_selectors = [
            '.slider-captcha',
            '.slide-verify',
            '[class*="slider"]',
            '.slider-btn',
            '.slider-button',
        ]

        for selector in slider_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    captcha_info['has_captcha'] = True
                    captcha_info['captcha_type'] = 'slider'
                    captcha_info['captcha_selector'] = selector
                    return captcha_info
            except Exception:
                continue

        return captcha_info

    async def _error_probe(self, page: Page, url: str, selectors: Dict, task_id: str = None) -> Dict:
        """
        Perform error probe with test/test credentials

        错误探测的核心目的:
        1. 验证选择器正确性
        2. 确认验证码处理流程
        3. 记录错误页面DOM长度（后续爆破判断基准）

        Args:
            page: Playwright page
            url: Target URL
            selectors: Page selectors
            task_id: Task ID for logging

        Returns:
            Error info dict with failed_dom_length
        """
        error_info = {
            'failed_dom_length': None,
            'success_keywords': None,
            'failure_keywords': None
        }

        try:
            # Navigate to login page
            await page.goto(url, wait_until='networkidle', timeout=30000)

            # Fill test credentials
            username_sel = selectors.get('username_selector')
            password_sel = selectors.get('password_selector')
            submit_sel = selectors.get('submit_selector')

            if not all([username_sel, password_sel, submit_sel]):
                self._log(task_id, "缺少必要的选择器", "error")
                return error_info

            # Fill username
            self._log(task_id, "填入测试用户名: test")
            await page.fill(username_sel, 'test')

            # Fill password
            self._log(task_id, "填入测试密码: test")
            await page.fill(password_sel, 'test')

            # Handle captcha if present
            captcha_solved = False
            captcha_type = selectors.get('captcha_type')

            if selectors.get('has_captcha'):
                if captcha_type == 'image':
                    self._log(task_id, "检测到图片验证码，尝试OCR识别...")
                    captcha_text = await self._solve_image_captcha(page, selectors)
                    captcha_solved = bool(captcha_text)
                    self._log(task_id, f"验证码识别结果: {captcha_text if captcha_text else '失败'}")
                elif captcha_type == 'slider':
                    self._log(task_id, "检测到滑块验证码，尝试模拟拖动...")
                    captcha_solved = await self._solve_slider_captcha(page, selectors, task_id)
                    self._log(task_id, f"滑块验证码处理结果: {'成功' if captcha_solved else '失败'}")
                elif captcha_type in ['recaptcha', 'hcaptcha']:
                    self._log(task_id, f"检测到{captcha_type}验证码，需要人工处理", "warning")
                    # 对于复杂的验证码，获取当前DOM作为基准
                    html = await page.content()
                    error_info['failed_dom_length'] = len(html)
                    error_info['captcha_unsupported'] = True
                    return error_info

            # Submit form
            self._log(task_id, "提交登录表单...")
            try:
                await page.click(submit_sel, timeout=5000)
            except Exception as e:
                self._log(task_id, f"点击提交按钮失败: {e}", "warning")
                # 如果滑块验证码阻止了点击，获取当前DOM
                html = await page.content()
                error_info['failed_dom_length'] = len(html)
                return error_info

            # Wait for response with shorter timeout for error probe
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
            except Exception:
                # If page doesn't settle, still try to get DOM
                self._log(task_id, "页面未完全加载，获取当前DOM", "warning")

            # Get DOM length
            html = await page.content()
            error_info['failed_dom_length'] = len(html)

            # Get page text for keywords
            page_text = await page.inner_text('body')

            # Detect failure keywords
            failure_keywords = ['错误', '失败', 'incorrect', 'invalid', 'failed', 'wrong', '不正确', '不存在']
            found_keywords = []
            for keyword in failure_keywords:
                if keyword.lower() in page_text.lower():
                    found_keywords.append(keyword)

            if found_keywords:
                error_info['failure_keywords'] = ','.join(found_keywords)
                self._log(task_id, f"检测到失败关键词: {found_keywords}")

            self._log(task_id, f"错误探测完成，DOM长度: {error_info['failed_dom_length']}")

        except Exception as e:
            self._log(task_id, f"错误探测失败: {e}", "warning")

        return error_info

    async def _solve_image_captcha(self, page: Page, selectors: Dict) -> str:
        """
        Solve image captcha using OCR

        Args:
            page: Playwright page
            selectors: Selectors dict

        Returns:
            Captcha text or empty string
        """
        from app.captcha.ocr_solver import OCRSolver

        captcha_sel = selectors.get('captcha_selector')
        input_sel = selectors.get('captcha_input_selector')

        if not captcha_sel or not input_sel:
            return ''

        try:
            ocr = OCRSolver()
            captcha_text = await ocr.solve_from_element(page, captcha_sel)

            if captcha_text:
                await page.fill(input_sel, captcha_text)
                return captcha_text

        except Exception as e:
            print(f"Captcha solving failed: {e}")

        return ''

    async def _solve_slider_captcha(self, page: Page, selectors: Dict, task_id: str = None) -> bool:
        """
        Solve slider captcha by simulating drag

        滑块验证码处理策略:
        1. 查找滑块元素
        2. 检测滑块轨道宽度
        3. 模拟鼠标拖动滑块到目标位置
        4. 等待验证结果

        Args:
            page: Playwright page
            selectors: Selectors dict
            task_id: Task ID for logging

        Returns:
            True if slider was solved successfully
        """
        try:
            self._log(task_id, "正在查找滑块元素...")

            # Extended slider button selectors
            slider_btn_selectors = [
                '.slider-btn',
                '.slider-button',
                '.slide-verify-slider-mask-item',
                '[class*="slider"] button',
                '[class*="slider-btn"]',
                '.drag-btn',
                '.handler',
                '.slider-handle',
                '.slide-block',
                '.slider-track-btn',
                '.nc_iconfont.btn_slide',
                '.slidetounlock',
                '.slideunlock-slider',
                '#nc_1__scale_span',
                '.btn_slide',
            ]

            slider_element = None
            found_selector = None

            for sel in slider_btn_selectors:
                try:
                    element = await page.query_selector(sel)
                    if element:
                        is_visible = await element.is_visible()
                        if is_visible:
                            slider_element = element
                            found_selector = sel
                            self._log(task_id, f"找到滑块元素: {sel}")
                            break
                except Exception:
                    continue

            if not slider_element:
                # Try to find by checking all elements with slider-related classes
                self._log(task_id, "尝试查找所有滑块相关元素...")
                try:
                    elements = await page.query_selector_all('[class*="slider"], [class*="slide"], [class*="drag"]')
                    for el in elements:
                        tag = await el.evaluate('el => el.tagName.toLowerCase()')
                        is_visible = await el.is_visible()
                        if is_visible and tag in ['div', 'span', 'button', 'a']:
                            slider_element = el
                            self._log(task_id, f"找到滑块元素: {tag}")
                            break
                except Exception:
                    pass

            if not slider_element:
                # Try draggable elements
                slider_element = await page.query_selector('[draggable="true"]')
                if slider_element:
                    self._log(task_id, "找到可拖动元素")

            if slider_element:
                # Get slider bounding box
                box = await slider_element.bounding_box()
                if not box:
                    self._log(task_id, "无法获取滑块位置", "warning")
                    return False

                self._log(task_id, f"滑块位置: x={box['x']:.0f}, y={box['y']:.0f}, w={box['width']:.0f}, h={box['height']:.0f}")

                # Try to find slider track/container to determine drag distance
                track_width = 280  # Default drag distance
                track_selectors = [
                    '.slider-track',
                    '.slide-verify-slider',
                    '[class*="slider-track"]',
                    '[class*="slider-container"]',
                    '.slider',
                ]

                for track_sel in track_selectors:
                    try:
                        track = await page.query_selector(track_sel)
                        if track:
                            track_box = await track.bounding_box()
                            if track_box:
                                track_width = int(track_box['width'] - box['width'])
                                self._log(task_id, f"检测到轨道宽度: {track_width}px")
                                break
                    except Exception:
                        continue

                # Calculate start position
                start_x = box['x'] + box['width'] / 2
                start_y = box['y'] + box['height'] / 2

                self._log(task_id, f"开始拖动滑块，距离: {track_width}px")

                # Simulate mouse movement and drag
                await page.mouse.move(start_x, start_y)
                await asyncio.sleep(0.1)
                await page.mouse.down()
                await asyncio.sleep(0.1)

                # Drag with human-like movement
                import random

                # Move in steps to simulate human-like dragging
                steps = random.randint(15, 25)
                for i in range(steps):
                    # Add some acceleration curve (slow start, fast middle, slow end)
                    progress = i / steps
                    eased_progress = progress * progress * (3 - 2 * progress)  # Smooth step

                    step_x = start_x + (track_width * eased_progress)
                    step_y = start_y + random.uniform(-3, 3)  # Small vertical variation
                    await page.mouse.move(step_x, step_y)
                    await asyncio.sleep(random.uniform(0.01, 0.05))

                # Final position
                final_x = start_x + track_width - 10  # Leave a small margin
                await page.mouse.move(final_x, start_y)
                await asyncio.sleep(0.1)
                await page.mouse.up()

                self._log(task_id, "滑块拖动完成，等待验证...")

                # Wait for verification
                await asyncio.sleep(1.5)

                # Check if slider is still visible (if not, verification passed)
                try:
                    is_visible = await slider_element.is_visible()
                    if not is_visible:
                        self._log(task_id, "滑块验证成功！")
                        return True

                    # Check if there's a success indicator
                    page_content = await page.content()
                    success_indicators = ['验证成功', 'success', 'verify-success', 'slider-success']
                    for indicator in success_indicators:
                        if indicator.lower() in page_content.lower():
                            self._log(task_id, f"检测到成功标识: {indicator}")
                            return True

                    self._log(task_id, "滑块仍可见，验证可能失败")
                    return False

                except Exception as e:
                    self._log(task_id, f"检查滑块状态失败: {e}")
                    return False

            self._log(task_id, "未找到滑块元素", "warning")
            return False

        except Exception as e:
            self._log(task_id, f"滑块验证码处理异常: {e}", "error")
            import traceback
            traceback.print_exc()
            return False