# Legado 参考路由

每一轮创建、修改、继续调试书源时先读本文件。不要依赖上一轮上下文中的参考文档。

## 必读流程

1. 重新阅读 `SKILL.md`
2. 阅读本文件
3. 根据当前阶段、失败现象、规则类型读取下方对应文件
4. 只改一个阶段或一个字段
5. 运行 `scripts/legado-debug.py` 验证
6. 在回复或调试记录中写明本轮读取的参考文件

## 按阶段读取

| 当前阶段 | 必读文件 |
|----------|----------|
| 初始化/基础字段 | `references/basics.md`, `references/template.yaml` |
| 正文 | `references/basics.md`, `scripts/README.md` |
| 目录 | `references/basics.md`, `scripts/README.md` |
| 详情 | `references/basics.md`, `scripts/README.md` |
| 搜索 | `references/basics.md`, `scripts/README.md` |
| 发现 | `references/discovery.md`, `scripts/README.md` |
| 漫画正文/图片 | `references/comic.md`, `references/basics.md` |
| 订阅源/RSS | `references/basics.md`, `references/js-api.md` |

## 按失败现象读取

| 现象 | 读取文件 |
|------|----------|
| 选择器无结果、字段为空、提取错字段 | `references/basics.md` |
| 搜索无结果、乱码、URL 参数异常 | `references/basics.md`, `references/troubleshoot.md` |
| 页面浏览器有内容但脚本拿不到 | `references/troubleshoot.md`, `references/webjs.md` |
| 403、验证盾、跳转、反爬、需要 UA/请求头/cookie | `references/troubleshoot.md`, `references/js-api.md` |
| JS 报错、String.replace 歧义、java.* 用法不确定 | `references/basics.md`, `references/js-api.md` |
| WebView/webJs/动态渲染/调用网页 JS | `references/webjs.md`, `references/troubleshoot.md` |
| 登录、按钮、回调、用户输入、变量持久化 | `references/login.md`, `references/patterns.md` |
| 发现页 JSON、分类、按钮布局 | `references/discovery.md` |
| 漫画图片不显示、403、防盗链、imageDecode、懒加载图片 | `references/comic.md`, `references/troubleshoot.md` |
| 多线路、多类型、跨页面状态 | `references/patterns.md`, `references/js-api.md` |
| 调试脚本连接失败、参数不确定、阶段不确定 | `scripts/README.md` |

## 搜索命令

在不确定具体规则时，先搜索参考文档：

```bash
rg -n "关键词" references scripts/README.md
```

常用关键词：

```text
webView
webJs
header
charset
cookie
loginCheckJs
java.ajax
java.connect
source.getVariable
imageDecode
Referer
replaceRegex
```

## 输出要求

每轮调试输出必须包含：

- 本轮阶段：正文/目录/详情/搜索/发现
- 重新读取的参考文件
- 本轮预期值
- 修改的字段
- 调试命令和结果摘要
- 下一步只处理哪个字段或阶段
