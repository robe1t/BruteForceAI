# -*- coding: utf-8 -*-
"""
Captcha module initialization
"""
from app.captcha.detector import CaptchaDetector
from app.captcha.ocr_solver import OCRSolver

__all__ = ['CaptchaDetector', 'OCRSolver']