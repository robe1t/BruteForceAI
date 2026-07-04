# -*- coding: utf-8 -*-
"""
Captcha detection module
"""
from typing import Dict, Optional

from playwright.async_api import Page


class CaptchaDetector:
    """
    验证码检测器

    Detects captcha presence and type on web pages.
    """

    # Known captcha selectors
    CAPTCHA_SELECTORS = {
        'image': [
            'img[src*="captcha"]',
            'img[id*="captcha"]',
            'img[class*="captcha"]',
            '#captcha_img',
            '.captcha-img',
            'img[alt*="验证码"]',
            'img[alt*="captcha"]',
        ],
        'recaptcha': [
            '.g-recaptcha',
            '#g-recaptcha',
            'iframe[src*="recaptcha"]',
            'div[data-sitekey]',
        ],
        'hcaptcha': [
            '.h-captcha',
            '#h-captcha',
            'iframe[src*="hcaptcha"]',
        ],
        'slider': [
            '.slider-captcha',
            '.slide-verify',
            '[class*="slider"]',
            '.drag-verify',
        ],
        'click': [
            '.click-captcha',
            '.geetest',
            '[class*="click-verify"]',
        ],
    }

    async def detect(self, page: Page) -> Dict:
        """
        Detect captcha on page

        Args:
            page: Playwright page

        Returns:
            Captcha info dict
        """
        result = {
            'has_captcha': False,
            'type': None,
            'selector': None,
            'input_selector': None
        }

        for captcha_type, selectors in self.CAPTCHA_SELECTORS.items():
            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        result['has_captcha'] = True
                        result['type'] = captcha_type
                        result['selector'] = selector

                        # Try to find input for image captcha
                        if captcha_type == 'image':
                            result['input_selector'] = await self._find_captcha_input(page)

                        return result
                except Exception:
                    continue

        return result

    async def _find_captcha_input(self, page: Page) -> Optional[str]:
        """
        Find captcha input field

        Args:
            page: Playwright page

        Returns:
            Input selector or None
        """
        input_selectors = [
            'input[name*="captcha"]',
            'input[id*="captcha"]',
            'input[placeholder*="验证码"]',
            'input[placeholder*="captcha"]',
            '#captcha',
            '.captcha-input',
        ]

        for selector in input_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    return selector
            except Exception:
                continue

        return None

    def _detect_image_captcha(self, page: Page) -> Dict:
        """Detect image captcha (sync version for compatibility)"""
        return {
            'type': 'image',
            'supported': True
        }

    def _detect_slider_captcha(self, page: Page) -> Dict:
        """Detect slider captcha (sync version for compatibility)"""
        return {
            'type': 'slider',
            'supported': False  # Not implemented yet
        }