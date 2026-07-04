# -*- coding: utf-8 -*-
"""
Vision OCR solver for captcha recognition using DeepSeek-OCR API
"""
import os
import base64
import requests
from typing import Optional

from PIL import Image


class VisionOCRClient:
    """
    视觉OCR客户端 - 使用DeepSeek-OCR模型识别验证码

    使用SiliconFlow API调用deepseek-ai/DeepSeek-OCR模型
    """

    DEFAULT_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
    DEFAULT_MODEL = "deepseek-ai/DeepSeek-OCR"

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        """
        Initialize Vision OCR client

        Args:
            api_key: SiliconFlow API key (can also be set via SILICONFLOW_API_KEY env var)
            base_url: API base URL
            model: Model name
        """
        self.api_key = api_key or os.environ.get('SILICONFLOW_API_KEY')
        self.base_url = base_url or self.DEFAULT_API_URL
        self.model = model or self.DEFAULT_MODEL

    def _get_proxies(self) -> dict:
        """Get proxy settings from environment"""
        proxies = {}
        http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
        https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')

        if http_proxy:
            proxies['http'] = http_proxy
        if https_proxy:
            proxies['https'] = https_proxy

        return proxies if proxies else None

    def recognize_text(self, image_path: str) -> str:
        """
        Recognize text from image

        Args:
            image_path: Path to image file

        Returns:
            Recognized text
        """
        if not self.api_key:
            print("[VisionOCR] No API key configured")
            return ""

        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Encode to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            # Determine image type
            image_ext = image_path.lower().split('.')[-1]
            mime_type = {
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'gif': 'image/gif',
                'webp': 'image/webp'
            }.get(image_ext, 'image/png')

            # Build request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": "请识别图片中的验证码文字，只返回验证码文字，不要返回其他内容。"
                            }
                        ]
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.1
            }

            # Send request
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60,
                proxies=self._get_proxies()
            )
            response.raise_for_status()
            data = response.json()

            # Extract result
            choices = data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content", "")
                # Clean up result - remove spaces and common noise
                result = content.strip().replace(" ", "").replace("\n", "")
                print(f"[VisionOCR] Recognized: {result}")
                return result

            return ""

        except requests.exceptions.Timeout:
            print("[VisionOCR] Request timeout")
            return ""
        except requests.exceptions.RequestException as e:
            print(f"[VisionOCR] Request failed: {e}")
            return ""
        except FileNotFoundError:
            print(f"[VisionOCR] Image file not found: {image_path}")
            return ""
        except Exception as e:
            print(f"[VisionOCR] Error: {e}")
            return ""

    def recognize_from_element(self, page, selector: str, temp_path: str = None) -> str:
        """
        Recognize text from page element (sync version - use recognize_from_element_async for async pages)

        Args:
            page: Playwright page (sync)
            selector: Element selector
            temp_path: Temporary path for screenshot (optional)

        Returns:
            Recognized text
        """
        import tempfile

        try:
            element = page.query_selector(selector)
            if not element:
                return ""

            # Take screenshot of element
            if temp_path is None:
                temp_path = tempfile.mktemp(suffix='.png')

            element.screenshot(path=temp_path)

            # Recognize
            result = self.recognize_text(temp_path)

            # Cleanup
            try:
                os.remove(temp_path)
            except Exception:
                pass

            return result

        except Exception as e:
            print(f"[VisionOCR] Element recognition failed: {e}")
            return ""

    async def recognize_from_element_async(self, page, selector: str) -> str:
        """
        Async version: Recognize text from page element

        Args:
            page: Playwright page (async)
            selector: Element selector

        Returns:
            Recognized text
        """
        import tempfile

        try:
            element = await page.query_selector(selector)
            if not element:
                return ""

            # Take screenshot of element
            temp_path = tempfile.mktemp(suffix='.png')
            await element.screenshot(path=temp_path)

            # Recognize
            result = self.recognize_text(temp_path)

            # Cleanup
            try:
                os.remove(temp_path)
            except Exception:
                pass

            return result

        except Exception as e:
            print(f"[VisionOCR] Async element recognition failed: {e}")
            return ""

    def recognize_from_base64(self, image_base64: str, mime_type: str = "image/png") -> str:
        """
        Recognize text from base64 encoded image

        Args:
            image_base64: Base64 encoded image data
            mime_type: Image MIME type

        Returns:
            Recognized text
        """
        if not self.api_key:
            print("[VisionOCR] No API key configured")
            return ""

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": "请识别图片中的验证码文字，只返回验证码文字，不要返回其他内容。"
                            }
                        ]
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.1
            }

            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60,
                proxies=self._get_proxies()
            )
            response.raise_for_status()
            data = response.json()

            choices = data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content", "")
                result = content.strip().replace(" ", "").replace("\n", "")
                return result

            return ""

        except Exception as e:
            print(f"[VisionOCR] Base64 recognition failed: {e}")
            return ""