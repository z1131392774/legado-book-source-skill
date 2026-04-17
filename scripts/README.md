# legado-debug.py 使用教程

Legado 书源调试脚本，纯 Python stdlib，YAML 支持需额外安装 PyYAML。

## 前提条件

- Legado App 已开启 Web 服务（设置 → Web 服务）
- 手机与运行脚本的机器网络可达（直连或代理）
- Python 3.10+
- （可选）PyYAML — 如需直接使用 `.yaml`/`.yml` 书源文件：`pip install pyyaml`

## 脚本位置

```
scripts/legado-debug.py
```

相对于 skill 根目录 (`~/.config/opencode/skills/legado-book-source/`)。

## 基本语法

```bash
python3 scripts/legado-debug.py --host <手机IP> --source <书源文件路径> [选项]
```

`--source` 支持 `.json`、`.yaml`、`.yml` 三种格式，脚本根据扩展名自动选择解析器。

## 参数说明

| 参数             | 默认值      | 说明                                  |
| ---------------- | ----------- | ------------------------------------- |
| `--host`         | `127.0.0.1` | Legado Web 服务地址                   |
| `--port`         | `1122`      | HTTP 端口（WS 端口自动 +1）           |
| `--http-port`    | `0`         | 单独指定 HTTP 端口（覆盖 --port）     |
| `--ws-port`      | `0`         | 单独指定 WebSocket 端口               |
| `--source`       | **必填**    | 书源文件路径 (支持 .json / .yaml / .yml) |
| `--key`          | 自动提取    | 调试关键字（见下方 key 格式）         |
| `--rss`          | 否          | 调试订阅源（默认调试书源）            |
| `--proxy`        | 无          | HTTP 代理，如 `http://127.0.0.1:7898` |
| `--save-only`    | 否          | 仅保存书源到 App，不调试              |
| `--quiet` / `-q` | 否          | 静默模式，只输出调试结果              |

## `--key` 格式（决定调试类型）

| key 格式      | 调试类型  | 示例                                                         |
| ------------- | --------- | ------------------------------------------------------------ |
| 普通文本      | 搜索      | `"系统"`                                                     |
| `分类名::URL` | 发现/探索 | `"月票榜::https://www.qidian.com/rank/yuepiao?page={{page}}"` |
| 完整 URL      | 详情页    | `"https://m.qidian.com/book/1015609210"`                     |
| `++URL`       | 目录页    | `"++https://www.zhaishuyuan.com/read/30394"`                 |
| `--URL`       | 正文页    | `"--https://www.zhaishuyuan.com/chapter/30394/20940996"`     |

不指定 `--key` 时，自动从书源的 `ruleSearch.checkKeyWord` 提取；若为空则默认 `"我的"`。

## 典型用法

**1. 搜索调试（最常用）**
```bash
python3 scripts/legado-debug.py --host 192.168.137.157 --source ./my_source.json
```

**2. 指定搜索关键字**
```bash
python3 scripts/legado-debug.py --host 192.168.137.157 --source ./my_source.json --key "斗破苍穹"
```

**3. 调试发现页**
```bash
python3 scripts/legado-debug.py --host 192.168.137.157 --source ./my_source.json \
  --key "月票榜::https://www.qidian.com/rank/yuepiao?page={{page}}"
```

**4. 调试详情页**
```bash
python3 scripts/legado-debug.py --host 192.168.137.157 --source ./my_source.json \
  --key "https://m.bbiqudu.com/75_75519/"
```

**5. 调试目录页**
```bash
python3 scripts/legado-debug.py --host 192.168.137.157 --source ./my_source.json \
  --key "++https://m.bbiqudu.com/75_75519/1/"
```

**6. 调试正文页**
```bash
python3 scripts/legado-debug.py --host 192.168.137.157 --source ./my_source.json \
  --key "--https://m.bbiqudu.com/75_75519/1.html"
```

**7. 通过代理连接**
```bash
python3 scripts/legado-debug.py --host 192.168.137.157 --source ./my_source.json \
  --proxy http://127.0.0.1:7898
```

**8. 仅保存书源（不调试）**
```bash
python3 scripts/legado-debug.py --host 192.168.137.157 --source ./my_source.json --save-only
```

**9. RSS 源调试**
```bash
python3 scripts/legado-debug.py --host 192.168.137.157 --source ./rss.json --key "科技" --rss
```

## 退出码

| 退出码 | 含义                         |
| ------ | ---------------------------- |
| `0`    | 调试成功（输出含"解析完成"） |
| `1`    | 调试失败或连接错误           |
