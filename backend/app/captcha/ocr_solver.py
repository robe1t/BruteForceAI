# -*- coding: utf-8 -*-
"""
OCR solver for image captchas using ddddocr with Vision OCR fallback
"""
# Fix for Pillow 10+ compatibility with ddddocr
# ANTIALIAS was removed in Pillow 10, replaced by LANCZOS
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

import ddddocr
import tempfile
import os
import json
from pathlib import Path
from typing import Optional

from playwright.async_api import Page


def load_ocr_config() -> dict:
    """Load OCR configuration from config file"""
    config_path = Path(__file__).parent.parent.parent / 'config' / 'ocr_config.json'
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[OCR] Failed to load config: {e}")
    return {}


class OCRSolver:
    """
    图片验证码 OCR 解决器

    Uses ddddocr library for image captcha recognition.
    Falls back to Vision OCR (DeepSeek-OCR) for better accuracy.
    """

    def __init__(self, vision_api_key: str = None):
        """
        Initialize OCR solver

        Args:
            vision_api_key: Optional API key for Vision OCR fallback (overrides config)
        """
        self.ocr = ddddocr.DdddOcr()
        self.vision_ocr = None
        self.vision_enabled = False

        # Load config if no API key provided
        if not vision_api_key:
            config = load_ocr_config()
            vision_config = config.get('vision_ocr', {})
            if vision_config.get('enabled') and vision_config.get('api_key'):
                vision_api_key = vision_config.get('api_key')

        # Initialize Vision OCR if API key available
        if vision_api_key:
            try:
                from app.captcha.vision_ocr import VisionOCRClient
                config = load_ocr_config()
                vision_config = config.get('vision_ocr', {})
                self.vision_ocr = VisionOCRClient(
                    api_key=vision_api_key,
                    base_url=vision_config.get('api_url'),
                    model=vision_config.get('model')
                )
                self.vision_enabled = True
                print("[OCR] Vision OCR enabled")
            except Exception as e:
                print(f"[OCR] Failed to initialize Vision OCR: {e}")

    async def solve(self, image_bytes: bytes, use_vision: bool = True) -> str:
        """
        Recognize text from image captcha

        Args:
            image_bytes: Image binary data
            use_vision: Whether to use Vision OCR as fallback

        Returns:
            Recognized text
        """
        result = ""

        # Try ddddocr first
        try:
            result = self.ocr.classification(image_bytes)
            if result and len(result) >= 4:  # Valid captcha usually has 4+ chars
                print(f"[OCR] ddddocr result: {result}")
                return result
        except Exception as e:
            print(f"[OCR] ddddocr failed: {e}")

        # Fall back to Vision OCR
        if use_vision and self.vision_enabled and self.vision_ocr and (not result or len(result) < 4):
            try:
                # Save to temp file
                temp_path = tempfile.mktemp(suffix='.png')
                with open(temp_path, 'wb') as f:
                    f.write(image_bytes)

                vision_result = self.vision_ocr.recognize_text(temp_path)

                # Cleanup
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

                if vision_result:
                    print(f"[OCR] Vision OCR result: {vision_result}")
                    return vision_result

            except Exception as e:
                print(f"[OCR] Vision OCR failed: {e}")

        return result

    async def solve_from_element(self, page: Page, selector: str, use_vision: bool = True) -> str:
        """
        Get image from page element and recognize

        Args:
            page: Playwright page
            selector: Image element selector
            use_vision: Whether to use Vision OCR as fallback

        Returns:
            Recognized text
        """
        try:
            element = await page.query_selector(selector)
            if not element:
                return ""

            # Take screenshot of element
            screenshot = await element.screenshot()

            # OCR recognize
            return await self.solve(screenshot, use_vision)

        except Exception as e:
            print(f"Failed to solve captcha from element: {e}")
            return ""

    async def solve_from_url(self, page: Page, image_url: str, use_vision: bool = True) -> str:
        """
        Download and recognize image from URL

        Args:
            page: Playwright page (for cookies/context)
            image_url: Image URL
            use_vision: Whether to use Vision OCR as fallback

        Returns:
            Recognized text
        """
        try:
            # Use page's request context to maintain session
            response = await page.request.get(image_url)
            image_bytes = await response.body()

            return await self.solve(image_bytes, use_vision)

        except Exception as e:
            print(f"Failed to solve captcha from URL: {e}")
            return ""

    async def solve_from_base64(self, base64_data: str, use_vision: bool = True) -> str:
        """
        Recognize from base64 encoded image

        Args:
            base64_data: Base64 encoded image data (with or without data:image prefix)
            use_vision: Whether to use Vision OCR as fallback

        Returns:
            Recognized text
        """
        import base64

        try:
            # Remove data:image prefix if present
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]

            image_bytes = base64.b64decode(base64_data)
            return await self.solve(image_bytes, use_vision)

        except Exception as e:
            print(f"Failed to solve captcha from base64: {e}")
            return ""