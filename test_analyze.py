# -*- coding: utf-8 -*-
"""
LLM页面分析测试工具（命令行版）
从数据库读取LLM提供商配置，对目标URL执行页面分析，展示启发式规则和LLM重试反馈的完整过程

用法:
  python test_analyze.py <URL>
  python test_analyze.py https://example.com/login
  python test_analyze.py https://example.com/login --show-browser
"""
import sys
import os
import asyncio
import argparse
from pathlib import Path

# 将backend加入模块搜索路径
ROOT_DIR = Path(__file__).parent.absolute()
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))


def create_minimal_app():
    """创建最小Flask应用（仅用于数据库上下文，不启动Web服务）"""
    from app import create_app
    app = create_app('development')
    return app


def get_provider_config(app):
    """在Flask上下文中读取活跃的LLM提供商配置"""
    with app.app_context():
        from app.database.models import Provider
        provider = Provider.get_active()

    if not provider:
        print("  [!] 数据库中无活跃的LLM提供商，请先在Web界面配置")
        return None

    return {
        'name': provider.name,
        'api_type': provider.api_type,
        'api_key': provider.api_key,
        'base_url': provider.base_url,
        'default_model': provider.default_model,
    }


def print_header():
    print()
    print("=" * 60)
    print("  BruteForceAI - LLM 页面分析测试")
    print("  展示启发式规则 + LLM重试反馈机制")
    print("=" * 60)
    print()


def print_result(result):
    """格式化打印分析结果"""
    print()
    print("-" * 50)

    if not result:
        print("  ✗ 分析失败：未能识别任何选择器")
        return

    method = result.get('_method', 'unknown')
    method_label = '启发式规则（零Token消耗）' if method == 'heuristic' else 'LLM智能分析'

    print(f"  识别方式:     {method_label}")
    print(f"  用户名选择器: {result.get('username_selector', '-')}")
    print(f"  密码选择器:   {result.get('password_selector', '-')}")
    print(f"  提交按钮:     {result.get('submit_selector', '-')}")

    has_captcha = result.get('has_captcha', False)
    if has_captcha:
        print(f"  验证码:       {result.get('captcha_type', '未知类型')}")
        if result.get('captcha_selector'):
            print(f"  验证码选择器: {result.get('captcha_selector')}")
    else:
        print(f"  验证码:       无")

    if result.get('has_checkbox'):
        print(f"  隐私勾选框:   {result.get('checkbox_selector', '-')}")

    if result.get('failed_dom_length'):
        print(f"  失败DOM长度:  {result.get('failed_dom_length')}")

    print("-" * 50)
    print("  ✓ 分析完成")


async def run_analysis(url, show_browser=False):
    """执行页面分析的核心异步函数"""

    # 切换工作目录到backend
    os.chdir(str(BACKEND_DIR))

    # 0. 创建Flask应用（用于数据库上下文）
    app = create_minimal_app()

    # 1. 读取LLM提供商配置
    print("[1/4] 读取LLM提供商配置...")
    provider = get_provider_config(app)

    llm_client = None
    if provider:
        print(f"  提供商: {provider['name']}")
        print(f"  模型:   {provider['default_model']}")
        print(f"  类型:   {provider['api_type']}")

        from app.llm import create_llm_client
        llm_client = create_llm_client(provider)
    else:
        print("  [!] 无LLM配置，将仅使用启发式规则")

    # 2. 初始化浏览器
    print()
    print(f"[2/4] 启动浏览器（{'有头' if show_browser else '无头'}模式）...")
    from app.core.browser_pool import BrowserPool
    browser_pool = BrowserPool()
    if show_browser:
        browser_pool.set_headless(False)

    # 3. 创建分析器并执行（需要Flask上下文因为内部会写数据库）
    print()
    print(f"[3/4] 开始分析页面: {url}")
    print("  （以下为分析器实时输出）")
    print("-" * 50)

    from app.core.page_analyzer import PageAnalyzer

    def log_callback(task_id, message, level='info'):
        level_icon = {'info': '·', 'warning': '⚠', 'error': '✗'}
        print(f"  {level_icon.get(level, '·')} {message}")

    analyzer = PageAnalyzer(
        llm_client=llm_client,
        browser_pool=browser_pool,
        log_callback=log_callback
    )

    import uuid
    task_id = f"cli_test_{uuid.uuid4().hex[:8]}"

    try:
        with app.app_context():
            result = await analyzer.analyze(url, task_id)
    except Exception as e:
        print(f"  ✗ 分析出错: {e}")
        result = None
    finally:
        # 4. 清理
        print()
        print("[4/4] 清理浏览器资源...")
        await browser_pool.cleanup()

    return result


def main():
    parser = argparse.ArgumentParser(
        description='BruteForceAI - LLM页面分析测试工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python test_analyze.py https://example.com/login
  python test_analyze.py https://example.com/login --show-browser
        """
    )
    parser.add_argument('url', help='要分析的登录页面URL')
    parser.add_argument('--show-browser', action='store_true', help='显示浏览器窗口（默认无头模式）')

    args = parser.parse_args()

    url = args.url
    if not url.startswith(('http://', 'https://')):
        print(f"错误: URL 必须以 http:// 或 https:// 开头")
        sys.exit(1)

    print_header()
    print(f"  目标URL: {url}")
    print()

    result = asyncio.run(run_analysis(url, show_browser=args.show_browser))

    print_result(result)
    print()


if __name__ == "__main__":
    main()
