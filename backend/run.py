# -*- coding: utf-8 -*-
"""
Backend application runner
"""
import argparse
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, socketio


def main():
    parser = argparse.ArgumentParser(
        description='智能爆破安全审计系统 - 后端服务',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='服务监听地址 (default: 0.0.0.0)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='服务监听端口 (default: 5000)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='开启调试模式'
    )

    parser.add_argument(
        '--config',
        default='default',
        choices=['default', 'development', 'production', 'testing'],
        help='配置环境 (default: default)'
    )

    args = parser.parse_args()

    # Create app
    app = create_app(config_name=args.config)

    print(f"""
╔════════════════════════════════════════════════════════════════╗
║         智能爆破安全审计系统 - 后端服务                          ║
╠════════════════════════════════════════════════════════════════╣
║  服务地址: http://{args.host}:{args.port}                          ║
║  调试模式: {'开启' if args.debug else '关闭'}                                    ║
║  配置环境: {args.config}                                        ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # Run with SocketIO (using threading mode for Python 3.13 compatibility)
    socketio.run(
        app,
        host=args.host,
        port=args.port,
        debug=args.debug
    )


if __name__ == '__main__':
    main()