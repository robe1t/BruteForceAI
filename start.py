# -*- coding: utf-8 -*-
"""
一键启动脚本 - 同时启动前后端服务
Windows下使用 taskkill /T /F 杀进程树，确保 Ctrl+C 能彻底关闭所有子进程
"""
import os
import re
import sys
import time
import signal
import subprocess
import webbrowser
import threading
from pathlib import Path

# 设置控制台编码
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")

# 项目根目录
ROOT_DIR = Path(__file__).parent.absolute()
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

# 服务配置
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 5000
FRONTEND_PORT = 3000

# 全局进程变量
processes = []
stop_event = threading.Event()
_shutting_down = False  # 防止重复关闭


def kill_process_tree(pid):
    """杀死进程及其所有子进程（Windows用taskkill，其他平台用os.killpg）"""
    try:
        if sys.platform == "win32":
            # /T = 终止子进程树, /F = 强制终止
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
    except Exception:
        pass


def shutdown():
    """关闭所有服务进程"""
    global _shutting_down
    if _shutting_down:
        return
    _shutting_down = True

    print("\n\n正在停止所有服务...")
    stop_event.set()

    for p in processes:
        if p.poll() is None:  # 进程仍在运行
            print(f"  停止进程 PID={p.pid} ...")
            kill_process_tree(p.pid)

    # 等待进程实际退出
    for p in processes:
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print(f"  进程 PID={p.pid} 未响应，强制终止")
            kill_process_tree(p.pid)

    print("所有服务已停止")


def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    shutdown()
    sys.exit(0)


def read_output(process, prefix):
    """持续读取进程输出并打印到控制台"""
    while not stop_event.is_set():
        try:
            line = process.stdout.readline()
            if not line:
                if process.poll() is not None:
                    break
                continue

            # 清理 ANSI 转义序列和特殊字符
            clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line)
            clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', clean)
            clean = clean.strip()

            if clean:
                # 过滤前端无用的Sass/Deprecation警告
                if prefix == "[前端]" and any(kw in clean for kw in [
                    'DEPRECATION WARNING', 'legacy-js-api', 'sass-lang.com/d/',
                    'Sass @import rules', 'automated migrator', '│', '╷', '╵',
                    'root stylesheet'
                ]):
                    continue
                print(f"{prefix} {clean}")
        except Exception as e:
            if not stop_event.is_set():
                print(f"{prefix} [读取错误] {e}")
            break


def main():
    """主函数"""
    # 注册信号处理（Windows不支持SIGTERM，只注册SIGINT即Ctrl+C）
    signal.signal(signal.SIGINT, signal_handler)
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 60)
    print("   BruteForceAI - 智能爆破安全审计系统")
    print("=" * 60)
    print()

    print("[*] 正在启动服务...\n")

    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    env['PYTHONUNBUFFERED'] = '1'  # 禁用缓冲

    # Windows下创建新进程组，方便后续整体终止
    popen_kwargs = {}
    if sys.platform == "win32":
        popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP

    # 启动后端服务
    backend = subprocess.Popen(
        [sys.executable, "-u", "run.py", "--host", BACKEND_HOST, "--port", str(BACKEND_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        env=env,
        cwd=str(BACKEND_DIR),
        bufsize=1,
        **popen_kwargs
    )
    processes.append(backend)

    # 启动后端日志读取线程
    threading.Thread(
        target=read_output,
        args=(backend, "[后端]"),
        daemon=True
    ).start()

    print(f"[后端] PID={backend.pid}  http://localhost:{BACKEND_PORT}")

    # 等待后端启动
    time.sleep(2)

    # 启动前端服务
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        env=env,
        cwd=str(FRONTEND_DIR),
        bufsize=1,
        **popen_kwargs
    )
    processes.append(frontend)

    # 启动前端日志读取线程
    threading.Thread(
        target=read_output,
        args=(frontend, "[前端]"),
        daemon=True
    ).start()

    print(f"[前端] PID={frontend.pid}  http://localhost:{FRONTEND_PORT}")

    # 等待前端启动
    time.sleep(3)

    print()
    print("=" * 60)
    print("   服务启动完成！")
    print("=" * 60)
    print(f"   后端 API:  http://localhost:{BACKEND_PORT}")
    print(f"   前端界面:  http://localhost:{FRONTEND_PORT}")
    print("=" * 60)
    print()
    print("   按 Ctrl+C 停止所有服务")
    print("   日志将实时显示在下方...")
    print("=" * 60)
    print()



    # 主线程等待
    try:
        while not stop_event.is_set():
            # 检查进程状态
            if backend.poll() is not None:
                print("[后端] 进程已退出")
                break
            if frontend.poll() is not None:
                print("[前端] 进程已退出")
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass

    shutdown()


if __name__ == "__main__":
    main()