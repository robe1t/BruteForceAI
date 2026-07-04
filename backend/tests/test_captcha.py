# -*- coding: utf-8 -*-
"""
Captcha module tests
"""
import pytest


class TestOCRSolver:
    """OCR solver tests"""

    def test_ocr_solver_init(self):
        """Test OCR solver initialization"""
        from app.captcha.ocr_solver import OCRSolver

        solver = OCRSolver()

        assert solver.ocr is not None

    @pytest.mark.asyncio
    async def test_solve_empty_image(self):
        """Test solving empty image"""
        from app.captcha.ocr_solver import OCRSolver

        solver = OCRSolver()

        # Empty bytes should return empty string
        result = await solver.solve(b'')
        assert isinstance(result, str)


class TestCaptchaDetector:
    """Captcha detector tests"""

    def test_captcha_selectors(self):
        """Test captcha selectors exist"""
        from app.captcha.detector import CaptchaDetector

        detector = CaptchaDetector()

        assert 'image' in detector.CAPTCHA_SELECTORS
        assert 'recaptcha' in detector.CAPTCHA_SELECTORS
        assert 'hcaptcha' in detector.CAPTCHA_SELECTORS
        assert 'slider' in detector.CAPTCHA_SELECTORS