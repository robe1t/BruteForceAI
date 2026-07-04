# -*- coding: utf-8 -*-
"""
Security evaluator for audit results
"""
from typing import Dict, List
from datetime import datetime

from app.database.models import (
    SecurityFinding, SecurityScore, TestResult, PageAnalysis
)


class Evaluator:
    """
    安全评估器

    Evaluates security based on:
    - Weak password findings
    - Captcha presence and strength
    - Account lockout mechanism
    - Rate limiting
    - Username enumeration
    """

    # Scoring weights
    WEIGHTS = {
        'weak_password': 30,
        'captcha': 20,
        'lockout': 20,
        'rate_limit': 15,
        'enumeration': 15
    }

    def evaluate(
        self,
        task_id: str,
        url: str,
        analysis: Dict,
        attack_result: Dict
    ) -> Dict:
        """
        Evaluate security based on analysis and attack results

        Args:
            task_id: Task ID
            url: Target URL
            analysis: Page analysis result
            attack_result: Attack execution result

        Returns:
            Score dict
        """
        scores = {}

        # 1. Weak password score
        weak_password_score = self._evaluate_weak_password(
            task_id, url, attack_result
        )
        scores['weak_password_score'] = weak_password_score

        # 2. Captcha score
        captcha_score = self._evaluate_captcha(task_id, url, analysis)
        scores['captcha_score'] = captcha_score

        # 3. Lockout score
        lockout_score = self._evaluate_lockout(task_id, url, attack_result)
        scores['lockout_score'] = lockout_score

        # 4. Rate limit score
        rate_limit_score = self._evaluate_rate_limit(task_id, url, attack_result)
        scores['rate_limit_score'] = rate_limit_score

        # 5. Enumeration score
        enumeration_score = self._evaluate_enumeration(task_id, url, analysis)
        scores['enumeration_score'] = enumeration_score

        # Calculate overall score
        overall_score = self._calculate_overall(scores)

        scores['overall_score'] = overall_score

        # Save to database
        SecurityScore.create(
            task_id=task_id,
            url=url,
            overall_score=overall_score,
            weak_password_score=weak_password_score,
            captcha_score=captcha_score,
            lockout_score=lockout_score,
            rate_limit_score=rate_limit_score,
            enumeration_score=enumeration_score
        )

        return scores

    def _evaluate_weak_password(
        self,
        task_id: str,
        url: str,
        attack_result: Dict
    ) -> int:
        """
        Evaluate weak password vulnerability

        Score: 0 (critical - many weak passwords) to 100 (secure - no weak passwords)
        """
        total = attack_result.get('total', 0)
        success_count = attack_result.get('success_count', 0)

        if total == 0:
            return 100

        success_rate = success_count / total

        if success_count == 0:
            score = 100
        elif success_rate <= 0.01:
            score = 80
        elif success_rate <= 0.05:
            score = 50
        elif success_rate <= 0.1:
            score = 30
        else:
            score = 10

        # Create finding if weak passwords found
        if success_count > 0:
            credentials = attack_result.get('credentials_found', [])
            SecurityFinding.create(
                task_id=task_id,
                url=url,
                finding_type='weak_password',
                severity='critical' if success_count > 5 else 'high',
                title='弱口令发现',
                description=f'发现 {success_count} 个有效弱口令凭证',
                recommendation='强制用户使用强密码，实施密码复杂度策略'
            )

        return score

    def _evaluate_captcha(
        self,
        task_id: str,
        url: str,
        analysis: Dict
    ) -> int:
        """
        Evaluate captcha protection

        Score: 0 (no captcha) to 100 (strong captcha)
        """
        has_captcha = analysis.get('has_captcha', False)
        captcha_type = analysis.get('captcha_type', 'none')

        if not has_captcha:
            SecurityFinding.create(
                task_id=task_id,
                url=url,
                finding_type='captcha',
                severity='medium',
                title='缺少验证码保护',
                description='登录页面没有验证码保护，容易遭受暴力破解攻击',
                recommendation='添加验证码保护，建议使用 reCAPTCHA 或 hCaptcha'
            )
            return 30

        # Score based on captcha type
        captcha_scores = {
            'none': 30,
            'image': 60,  # Simple image captcha can be OCR'd
            'slider': 70,
            'click': 70,
            'recaptcha': 90,
            'hcaptcha': 90
        }

        return captcha_scores.get(captcha_type, 50)

    def _evaluate_lockout(
        self,
        task_id: str,
        url: str,
        attack_result: Dict
    ) -> int:
        """
        Evaluate account lockout mechanism

        Score: 0 (no lockout) to 100 (proper lockout)
        """
        total = attack_result.get('total', 0)
        success_count = attack_result.get('success_count', 0)

        # If many attempts succeeded without lockout, no lockout mechanism
        if total > 50 and success_count > 0:
            SecurityFinding.create(
                task_id=task_id,
                url=url,
                finding_type='lockout',
                severity='high',
                title='缺少账户锁定机制',
                description=f'在 {total} 次尝试后仍未触发账户锁定',
                recommendation='实施账户锁定策略：连续失败N次后锁定账户M分钟'
            )
            return 20

        # If attempts were blocked or rate limited, good
        if success_count == 0 and total > 20:
            return 80

        return 50

    def _evaluate_rate_limit(
        self,
        task_id: str,
        url: str,
        attack_result: Dict
    ) -> int:
        """
        Evaluate rate limiting

        Score: 0 (no rate limit) to 100 (strong rate limit)
        """
        total = attack_result.get('total', 0)

        # Without actual timing data, make reasonable assumptions
        if total > 100:
            # Many requests allowed, likely no rate limit
            SecurityFinding.create(
                task_id=task_id,
                url=url,
                finding_type='rate_limit',
                severity='medium',
                title='缺少速率限制',
                description='允许大量快速请求，缺少速率限制',
                recommendation='实施 API 速率限制，如每分钟最多 10 次请求'
            )
            return 30

        if total > 30:
            return 50

        return 70

    def _evaluate_enumeration(
        self,
        task_id: str,
        url: str,
        analysis: Dict
    ) -> int:
        """
        Evaluate username enumeration vulnerability

        Score: 0 (enumerable) to 100 (no enumeration)
        """
        # Check if error messages reveal username validity
        failure_keywords = analysis.get('failure_keywords', '')

        if not failure_keywords:
            return 80

        # Generic error messages are good
        generic_errors = ['invalid', 'incorrect', 'failed']
        specific_errors = ['user not found', '用户不存在', 'username not found']

        failure_lower = failure_keywords.lower()

        for err in specific_errors:
            if err in failure_lower:
                SecurityFinding.create(
                    task_id=task_id,
                    url=url,
                    finding_type='enumeration',
                    severity='medium',
                    title='用户名枚举风险',
                    description='错误消息可能泄露用户名是否存在的信息',
                    recommendation='使用通用错误消息，如"用户名或密码错误"'
                )
                return 40

        return 70

    def _calculate_overall(self, scores: Dict) -> int:
        """
        Calculate overall security score

        Args:
            scores: Individual scores dict

        Returns:
            Overall score (0-100)
        """
        weighted_sum = 0
        weight_total = 0

        for key, weight in self.WEIGHTS.items():
            score_key = f'{key}_score'
            if score_key in scores:
                weighted_sum += scores[score_key] * weight
                weight_total += weight

        if weight_total == 0:
            return 0

        return int(weighted_sum / weight_total)