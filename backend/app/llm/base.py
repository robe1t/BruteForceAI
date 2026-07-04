# -*- coding: utf-8 -*-
"""
LLM client base class
"""
import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class LLMResponse:
    """统一的 LLM 响应格式"""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    success: bool
    error: Optional[str] = None


class LLMClient(ABC):
    """LLM 客户端抽象基类"""

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> LLMResponse:
        """
        Send chat request to LLM

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: System prompt (optional)
            max_tokens: Maximum tokens in response
            temperature: Temperature for response generation

        Returns:
            LLMResponse instance
        """
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to LLM provider

        Returns:
            Dict with 'success', 'model', 'error' keys
        """
        pass

    def analyze_html(self, html: str, prompt: str = None) -> LLMResponse:
        """
        Analyze HTML content with LLM

        Args:
            html: HTML content to analyze
            prompt: Custom prompt (optional)

        Returns:
            LLMResponse instance
        """
        if prompt is None:
            prompt = '''你是一个 Web 安全专家，请分析以下登录页面 HTML，提取关键信息。

请以 JSON 格式返回以下字段：
1. username_selector: 用户名输入框的 CSS 选择器
2. password_selector: 密码输入框的 CSS 选择器
3. submit_selector: 提交按钮的 CSS 选择器
4. has_captcha: 是否有验证码 (true/false)
5. captcha_type: 验证码类型

验证码类型枚举：
- none: 无验证码
- image: 图片验证码
- slider: 滑块验证码
- click: 点击验证码
- recaptcha: Google reCAPTCHA
- hcaptcha: hCaptcha

请直接返回 JSON，不要包含其他内容。'''

        return self.chat(
            messages=[{'role': 'user', 'content': f'{prompt}\n\nHTML 内容：\n{html}'}],
            max_tokens=2048,
            temperature=0.3
        )

    def analyze_image(self, image_path: str, prompt: str = None) -> LLMResponse:
        """
        Analyze image with vision-capable LLM

        Args:
            image_path: Path to image file
            prompt: Analysis prompt

        Returns:
            LLMResponse instance
        """
        # Default implementation - subclasses can override for vision API
        return LLMResponse(
            content="",
            model="",
            input_tokens=0,
            output_tokens=0,
            success=False,
            error="Vision analysis not supported by this LLM client"
        )

    def detect_captcha_from_image(self, image_path: str) -> LLMResponse:
        """
        Detect and analyze captcha from screenshot

        Args:
            image_path: Path to screenshot

        Returns:
            LLMResponse with captcha analysis
        """
        prompt = '''请分析这张登录页面截图，检测是否存在验证码。

请以 JSON 格式返回以下信息：
{
    "has_captcha": true/false,
    "captcha_type": "none/image/slider/click/recaptcha/hcaptcha",
    "captcha_description": "验证码描述（如果有）",
    "captcha_position": {"x": 数字, "y": 数字, "width": 数字, "height": 数字} 或 null,
    "form_inputs": [
        {
            "type": "username/password/captcha_input",
            "position": {"x": 数字, "y": 数字, "width": 数字, "height": 数字}
        }
    ]
}

验证码类型说明：
- image: 图片验证码，需要识别图片中的字符
- slider: 滑块验证码，需要拖动滑块
- click: 点击验证码，需要按顺序点击图片/文字
- recaptcha: Google reCAPTCHA
- hcaptcha: hCaptcha

请仔细检查页面中是否有验证码图片、滑块、或任何验证元素。'''

        return self.analyze_image(image_path, prompt)

    def confirm_login_success(self, page_content: str) -> LLMResponse:
        """
        Confirm if login was successful

        Args:
            page_content: Page content after login attempt

        Returns:
            LLMResponse with 'true' or 'false' in content
        """
        prompt = '''请判断以下页面内容是否表示登录成功。

如果是登录成功页面（如：包含"欢迎"、"登录成功"、"退出"等关键词，或显示用户信息），返回 true。
如果是登录失败页面（如：包含"错误"、"失败"、"用户名或密码错误"等关键词），返回 false。

请只返回 true 或 false，不要返回其他内容。'''

        return self.chat(
            messages=[{'role': 'user', 'content': f'{prompt}\n\n页面内容：\n{page_content[:3000]}'}],
            max_tokens=100,
            temperature=0.1
        )