# -*- coding: utf-8 -*-
"""
OpenAI compatible API client
Supports OpenAI, Groq, Ollama, and other OpenAI-compatible endpoints
"""
import os
import base64
import requests
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

from app.llm.base import LLMClient, LLMResponse


def get_proxies() -> Dict[str, str]:
    """Get proxy settings from environment"""
    proxies = {}
    http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')

    if http_proxy:
        proxies['http'] = http_proxy
    if https_proxy:
        proxies['https'] = https_proxy

    return proxies if proxies else None


def format_error(error: Exception) -> str:
    """Format error message for user-friendly display"""
    error_str = str(error)

    # Connection aborted
    if 'Connection aborted' in error_str or 'ConnectionAbortedError' in error_str:
        return '网络连接被中断，请检查：1) 网络是否正常 2) 是否需要配置代理 3) 防火墙是否阻止了连接'

    # Connection timeout
    if 'timeout' in error_str.lower():
        return '连接超时，请检查网络或 API 地址是否正确'

    # SSL errors
    if 'ssl' in error_str.lower() or 'certificate' in error_str.lower():
        return 'SSL证书验证失败，请检查 API 地址是否正确'

    # DNS errors
    if 'dns' in error_str.lower() or 'getaddrinfo' in error_str.lower() or 'name or service not known' in error_str.lower():
        return 'DNS解析失败，请检查 API 地址是否正确'

    # Connection refused
    if 'connection refused' in error_str.lower():
        return '连接被拒绝，请检查 API 地址和端口是否正确'

    # API errors with response
    if hasattr(error, 'response') and error.response is not None:
        try:
            error_data = error.response.json()
            if 'error' in error_data:
                err_obj = error_data['error']
                if isinstance(err_obj, dict):
                    return err_obj.get('message', str(err_obj))
                return str(err_obj)
        except Exception:
            pass

        status = error.response.status_code
        if status == 401:
            return 'API Key 无效或已过期'
        elif status == 403:
            return '访问被拒绝，请检查 API Key 权限'
        elif status == 404:
            return 'API 端点不存在，请检查 API 地址'
        elif status == 429:
            return '请求过于频繁，请稍后重试'
        elif status >= 500:
            return f'服务器错误 ({status})，请稍后重试'

    return error_str


class OpenAICompatibleClient(LLMClient):
    """OpenAI 兼容格式 API 客户端"""

    DEFAULT_BASE_URL = "https://api.openai.com"
    DEFAULT_MODEL = "gpt-3.5-turbo"

    def __init__(
        self,
        api_key: str,
        base_url: str = None,
        model: str = None
    ):
        """
        Initialize OpenAI compatible client

        Args:
            api_key: API key
            base_url: Base URL for API (optional)
            model: Default model name
        """
        super().__init__()
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip('/')
        self.model = model or self.DEFAULT_MODEL

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> LLMResponse:
        """
        Send OpenAI compatible chat request

        Args:
            messages: List of message dicts
            system: System prompt
            max_tokens: Max tokens in response
            temperature: Temperature for generation

        Returns:
            LLMResponse instance
        """
        # Build URL - handle both cases: base_url ending with /v1 or not
        if self.base_url.endswith('/v1'):
            url = f"{self.base_url}/chat/completions"
        else:
            url = f"{self.base_url}/v1/chat/completions"

        # Prepare messages
        chat_messages = []
        if system:
            chat_messages.append({'role': 'system', 'content': system})
        chat_messages.extend(messages)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": chat_messages,
            "temperature": temperature
        }

        try:
            # Get proxy settings
            proxies = get_proxies()

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=120,
                proxies=proxies
            )
            response.raise_for_status()
            data = response.json()

            # Extract content
            content = ""
            choices = data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content", "")

            # Extract usage
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                model=data.get("model", self.model),
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                success=True
            )

        except requests.exceptions.Timeout:
            return LLMResponse(
                content="",
                model=self.model,
                input_tokens=0,
                output_tokens=0,
                success=False,
                error="连接超时，请检查网络或 API 地址"
            )
        except requests.exceptions.RequestException as e:
            return LLMResponse(
                content="",
                model=self.model,
                input_tokens=0,
                output_tokens=0,
                success=False,
                error=format_error(e)
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.model,
                input_tokens=0,
                output_tokens=0,
                success=False,
                error=f"未知错误: {str(e)}"
            )

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to API"""
        response = self.chat(
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10
        )
        return {
            "success": response.success,
            "connected": response.success,
            "model": self.model,
            "error": response.error,
            "message": response.error if not response.success else "连接成功"
        }

    def analyze_image(self, image_path: str, prompt: str = None) -> LLMResponse:
        """
        Analyze image with vision-capable model

        Args:
            image_path: Path to image file
            prompt: Analysis prompt

        Returns:
            LLMResponse instance
        """
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

            # Build URL
            if self.base_url.endswith('/v1'):
                url = f"{self.base_url}/chat/completions"
            else:
                url = f"{self.base_url}/v1/chat/completions"

            # Build message with image
            user_message = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt or "请分析这张图片。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_base64}"
                        }
                    }
                ]
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "max_tokens": 2048,
                "messages": [user_message],
                "temperature": 0.3
            }

            # Get proxy settings
            proxies = get_proxies()

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=120,
                proxies=proxies
            )
            response.raise_for_status()
            data = response.json()

            # Extract content
            content = ""
            choices = data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content", "")

            # Extract usage
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                model=data.get("model", self.model),
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                success=True
            )

        except requests.exceptions.Timeout:
            return LLMResponse(
                content="",
                model=self.model,
                input_tokens=0,
                output_tokens=0,
                success=False,
                error="连接超时，请检查网络或 API 地址"
            )
        except requests.exceptions.RequestException as e:
            return LLMResponse(
                content="",
                model=self.model,
                input_tokens=0,
                output_tokens=0,
                success=False,
                error=format_error(e)
            )
        except FileNotFoundError:
            return LLMResponse(
                content="",
                model=self.model,
                input_tokens=0,
                output_tokens=0,
                success=False,
                error=f"图片文件不存在: {image_path}"
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.model,
                input_tokens=0,
                output_tokens=0,
                success=False,
                error=f"图片分析失败: {str(e)}"
            )