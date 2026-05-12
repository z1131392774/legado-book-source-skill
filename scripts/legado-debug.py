#!/usr/bin/env python3
"""
Legado 书源调试脚本 (纯 stdlib，YAML 支持需 pip install pyyaml)

用法:
  # 调试搜索 (支持 .json / .yaml / .yml)
  python3 legado-debug.py --host 192.168.1.100 --port 1122 --source ./my_source.yaml --key "系统"

  # 调试发现页
  python3 legado-debug.py --host 192.168.1.100 --source ./my_source.json --key "月票榜::https://www.qidian.com/rank/yuepiao?page={{page}}"

  # 调试详情页
  python3 legado-debug.py --host 192.168.1.100 --source ./my_source.json --key "https://m.qidian.com/book/1015609210"

  # 调试目录页
  python3 legado-debug.py --host 192.168.1.100 --source ./my_source.json --key "++https://www.zhaishuyuan.com/read/30394"

  # 调试正文页
  python3 legado-debug.py --host 192.168.1.100 --source ./my_source.json --key "--https://www.zhaishuyuan.com/chapter/30394/20940996"

  # RSS 源调试
  python3 legado-debug.py --host 192.168.1.100 --source ./rss_source.json --key "科技" --rss

  # 仅保存书源（不调试）
  python3 legado-debug.py --host 192.168.1.100 --source ./my_source.yaml --save-only

  # 指定调试 key（从书源 ruleSearch.checkKeyWord 自动提取，也可手动指定）
"""

import argparse
import base64
import hashlib
import json
import os
import socket
import ssl
import struct
import sys
import urllib.request
import urllib.error
from urllib.parse import urlparse

# YAML 支持 (可选依赖)
try:
    import yaml

    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

# ─── WebSocket 客户端 (纯 stdlib) ───────────────────────────────────────────

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def ws_connect(
    host: str, port: int, path: str, use_ssl: bool = False, proxy: str | None = None
):
    """建立 WebSocket 连接，返回 socket

    proxy: HTTP 代理地址，如 "http://127.0.0.1:7898"
    """
    if proxy:
        # 通过 HTTP CONNECT 隧道连接
        parsed = urlparse(proxy)
        proxy_host = parsed.hostname
        proxy_port = parsed.port or 80
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(60)
        sock.connect((proxy_host, proxy_port))
        # 发送 CONNECT 请求建立隧道
        connect_req = f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n"
        sock.sendall(connect_req.encode())
        # 读取代理响应
        resp = b""
        while b"\r\n\r\n" not in resp:
            chunk = sock.recv(4096)
            if not chunk:
                raise ConnectionError(f"代理连接失败: 无响应")
            resp += chunk
        status_line = resp.split(b"\r\n")[0].decode()
        if "200" not in status_line:
            raise ConnectionError(f"代理隧道建立失败: {status_line}")
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(60)
        sock.connect((host, port))

    if use_ssl:
        ctx = ssl.create_default_context()
        sock = ctx.wrap_socket(sock, server_hostname=host)

    key = base64.b64encode(os.urandom(16)).decode()
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"\r\n"
    )
    sock.sendall(req.encode())

    # 读取握手响应
    resp = b""
    while b"\r\n\r\n" not in resp:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("WebSocket 握手失败: 连接关闭")
        resp += chunk

    status_line = resp.split(b"\r\n")[0].decode()
    if "101" not in status_line:
        raise ConnectionError(f"WebSocket 握手失败: {status_line}")

    return sock


def ws_send(sock, message: str):
    """发送 WebSocket 文本帧"""
    payload = message.encode("utf-8")
    mask_key = os.urandom(4)
    masked = bytearray(b ^ mask_key[i % 4] for i, b in enumerate(payload))

    frame = bytearray()
    frame.append(0x81)  # FIN + text opcode

    length = len(payload)
    if length < 126:
        frame.append(0x80 | length)  # MASK bit + length
    elif length < 65536:
        frame.append(0x80 | 126)
        frame += struct.pack(">H", length)
    else:
        frame.append(0x80 | 127)
        frame += struct.pack(">Q", length)

    frame += mask_key
    frame += masked
    sock.sendall(frame)


def ws_recv(sock) -> str | None:
    """接收一条 WebSocket 消息，返回文本或 None(连接关闭)"""
    header = _recv_exact(sock, 2)
    if header is None:
        return None

    opcode = header[0] & 0x0F
    masked = (header[1] & 0x80) != 0
    length = header[1] & 0x7F

    if length == 126:
        data = _recv_exact(sock, 2)
        if data is None:
            return None
        length = struct.unpack(">H", data)[0]
    elif length == 127:
        data = _recv_exact(sock, 8)
        if data is None:
            return None
        length = struct.unpack(">Q", data)[0]

    if masked:
        mask_key = _recv_exact(sock, 4)
        if mask_key is None:
            return None
        payload = _recv_exact(sock, length)
        if payload is None:
            return None
        payload = bytearray(b ^ mask_key[i % 4] for i, b in enumerate(payload))
    else:
        payload = _recv_exact(sock, length)
        if payload is None:
            return None

    # opcode 0x8 = close, 0x9 = ping, 0xA = pong
    if opcode == 0x8:
        return None
    if opcode == 0x9:
        # pong reply
        frame = bytearray()
        frame.append(0x8A)
        frame.append(len(payload))
        frame += payload
        sock.sendall(frame)
        return ""  # ping, skip
    if opcode == 0xA:
        return ""  # pong, skip

    return bytes(payload).decode("utf-8", errors="replace")


def _recv_exact(sock, n: int) -> bytearray | None:
    """精确接收 n 字节"""
    if n == 0:
        return bytearray()
    buf = bytearray()
    while len(buf) < n:
        try:
            chunk = sock.recv(n - len(buf))
        except socket.timeout:
            return None
        if not chunk:
            return None
        buf += chunk
    return buf


# ─── HTTP 操作 ────────────────────────────────────────────────────────────────


def _make_opener(proxy: str | None = None):
    """创建 urllib opener，可选代理"""
    if proxy:
        proxy_handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
        return urllib.request.build_opener(proxy_handler)
    return urllib.request.build_opener()


def save_book_source(
    host: str, port: int, source_json: dict, proxy: str | None = None
) -> dict:
    """保存书源到 Legado App，返回 API 响应"""
    url = f"http://{host}:{port}/saveBookSource"
    data = json.dumps(source_json, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    opener = _make_opener(proxy)
    try:
        with opener.open(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return {"isSuccess": False, "errorMsg": f"连接失败: {e.reason}"}
    except Exception as e:
        return {"isSuccess": False, "errorMsg": f"请求异常: {e}"}


def save_rss_source(
    host: str, port: int, source_json: dict, proxy: str | None = None
) -> dict:
    """保存订阅源到 Legado App，返回 API 响应"""
    url = f"http://{host}:{port}/saveRssSource"
    data = json.dumps(source_json, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    opener = _make_opener(proxy)
    try:
        with opener.open(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return {"isSuccess": False, "errorMsg": f"连接失败: {e.reason}"}
    except Exception as e:
        return {"isSuccess": False, "errorMsg": f"请求异常: {e}"}


# ─── 调试 ─────────────────────────────────────────────────────────────────────


def debug_source(
    host: str,
    http_port: int,
    ws_port: int,
    source_json: dict,
    key: str,
    is_rss: bool = False,
    proxy: str | None = None,
) -> list[str]:
    """
    调试书源/订阅源，返回调试消息列表。

    流程:
    1. POST 保存书源到 App
    2. WebSocket 连接调试端点
    3. 发送 {tag, key}
    4. 收集所有调试输出直到连接关闭
    """
    # 1. 保存书源
    if is_rss:
        source_url = source_json.get("sourceUrl", "")
        result = save_rss_source(host, http_port, source_json, proxy)
    else:
        source_url = source_json.get("bookSourceUrl", "")
        result = save_book_source(host, http_port, source_json, proxy)

    if not result.get("isSuccess"):
        raise RuntimeError(f"保存书源失败: {result.get('errorMsg', '未知错误')}")

    # 2. WebSocket 调试
    ws_path = "/rssSourceDebug" if is_rss else "/bookSourceDebug"
    sock = ws_connect(host, ws_port, ws_path, proxy=proxy)

    # 3. 发送调试请求
    if is_rss:
        msg = json.dumps({"tag": source_url, "key": key})
    else:
        msg = json.dumps({"tag": source_url, "key": key})
    ws_send(sock, msg)

    # 4. 收集调试输出
    messages = []
    try:
        while True:
            text = ws_recv(sock)
            if text is None:
                break
            if text:  # 跳过空消息 (ping/pong)
                messages.append(text)
    except (socket.timeout, ConnectionError):
        pass
    finally:
        try:
            sock.close()
        except Exception:
            pass

    return messages


# ─── 主入口 ───────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Legado 书源调试脚本 (纯 stdlib)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Legado Web 服务地址 (默认 127.0.0.1)"
    )
    parser.add_argument(
        "--http-port", type=int, default=0, help="HTTP 端口 (默认 ws-port-1)"
    )
    parser.add_argument(
        "--ws-port", type=int, default=0, help="WebSocket 端口 (默认 http-port+1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=1122,
        help="Legado HTTP 端口 (默认 1122，自动推算 WS 端口)",
    )
    parser.add_argument(
        "--source", required=True, help="书源文件路径 (支持 .json / .yaml / .yml)"
    )
    parser.add_argument(
        "--key", default="", help="调试关键字 (默认从书源 ruleSearch.checkKeyWord 提取)"
    )
    parser.add_argument("--rss", action="store_true", help="调试订阅源 (默认调试书源)")
    parser.add_argument("--save-only", action="store_true", help="仅保存书源，不调试")
    parser.add_argument(
        "--proxy", default="", help="HTTP 代理地址，如 http://127.0.0.1:7898"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="静默模式，只输出调试结果"
    )

    args = parser.parse_args()

    # 端口推算
    http_port = args.http_port or args.port
    ws_port = args.ws_port or (http_port + 1)

    # 读取书源文件 (自动识别 JSON / YAML)
    source_path = os.path.expanduser(args.source)
    if not os.path.isfile(source_path):
        print(f"错误: 文件不存在: {source_path}", file=sys.stderr)
        sys.exit(1)

    _, ext = os.path.splitext(source_path)
    ext = ext.lower()

    with open(source_path, "r", encoding="utf-8") as f:
        if ext in (".yaml", ".yml"):
            if not _YAML_AVAILABLE:
                print(
                    "错误: YAML 文件需要 PyYAML 库，请运行: pip install pyyaml",
                    file=sys.stderr,
                )
                sys.exit(1)
            try:
                source_json = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"错误: YAML 解析失败: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            try:
                source_json = json.load(f)
            except json.JSONDecodeError as e:
                print(f"错误: JSON 解析失败: {e}", file=sys.stderr)
                sys.exit(1)

    # 处理 JSON 数组 (取第一个)
    if isinstance(source_json, list):
        if len(source_json) == 0:
            print("错误: JSON 数组为空", file=sys.stderr)
            sys.exit(1)
        if not args.quiet:
            print(f"注意: JSON 数组包含 {len(source_json)} 个源，使用第一个")
        source_json = source_json[0]

    # 仅保存模式
    if args.save_only:
        if args.rss:
            result = save_rss_source(
                args.host, http_port, source_json, args.proxy or None
            )
        else:
            result = save_book_source(
                args.host, http_port, source_json, args.proxy or None
            )
        if result.get("isSuccess"):
            name = source_json.get("sourceName" if args.rss else "bookSourceName", "")
            print(f"✓ 书源「{name}」保存成功")
        else:
            print(f"✗ 保存失败: {result.get('errorMsg', '未知错误')}", file=sys.stderr)
            sys.exit(1)
        return

    # 确定调试 key
    key = args.key
    if not key:
        if args.rss:
            key = source_json.get("ruleSearch", {}).get("checkKeyWord", "")
        else:
            key = source_json.get("ruleSearch", {}).get("checkKeyWord", "")
        if not key:
            key = "我的"
            if not args.quiet:
                print(f"未指定 --key，使用默认关键字: {key}")

    if not args.quiet:
        source_url = source_json.get("sourceUrl" if args.rss else "bookSourceUrl", "")
        source_name = source_json.get(
            "sourceName" if args.rss else "bookSourceName", ""
        )
        print(f"调试: {source_name} ({source_url})")
        print(f"关键字: {key}")
        print(f"连接: http://{args.host}:{http_port} / ws://{args.host}:{ws_port}")
        print("─" * 50)

    # 执行调试
    try:
        messages = debug_source(
            args.host,
            http_port,
            ws_port,
            source_json,
            key,
            args.rss,
            args.proxy or None,
        )
    except Exception as e:
        print(f"✗ 调试失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 输出结果
    success = False
    for msg in messages:
        print(msg)
        if "解析完成" in msg or "调试完成" in msg:
            success = True
        if "错误" in msg.lower() or "失败" in msg.lower():
            # 不立即判定失败，可能中间有错误但最终成功
            pass

    # 判断最终状态: 最后一条消息包含 state 信息
    # state=-1 或 state=1000 在 WebSocket 中对应连接关闭
    # 如果最后一条消息包含 "解析完成" 则成功
    if messages and any("解析完成" in m for m in messages[-3:]):
        success = True

    if not args.quiet:
        print("─" * 50)
        if success:
            print("✓ 调试完成")
        else:
            print("✗ 调试未成功完成")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
