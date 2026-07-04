# -*- coding: utf-8 -*-
"""
Anthropic Messages API client
"""
import os
import requests
from typing import Optional, List, Dict, Any

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


class AnthropicClient(LLMClient):
    """Anthropic Messages API 原生格式客户端"""

    DEFAULT_BASE_URL = "https://api.anthropic.com"
    API_VERSION = "2023-06-01"

    MODELS = [
        "claude-opus-4-6"
    ]

    def __init__(
        self,
        api_key: str,
        base_url: str = None,
        model: str = "claude-sonnet-4-6"
    ):
        """
        Initialize Anthropic client

        Args:
            api_key: Anthropic API key
            base_url: Base URL (optional)
            model: Model name
        """
        super().__init__()
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip('/')
        self.model = model

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> LLMResponse:
        """
        Send Anthropic Messages API request

        Note: Anthropic's system is a separate field, not in messages

        Args:
            messages: List of message dicts
            system: System prompt (separate field in Anthropic API)
            max_tokens: Max tokens in response
            temperature: Temperature for generation

        Returns:
            LLMResponse instance
        """
        # Build URL - handle both cases: base_url ending with /v1 or not
        if self.base_url.endswith('/v1'):
            url = f"{self.base_url}/messages"
        else:
            url = f"{self.base_url}/v1/messages"

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION,
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature
        }

        if system:
            payload["system"] = system

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

            # Extract content from response blocks
            content = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    content += block.get("text", "")

            # Extract usage
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                model=data.get("model", self.model),
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
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
        """Test connection to Anthropic API"""
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