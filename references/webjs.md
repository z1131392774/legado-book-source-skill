# webJs 参考

> `webJs` 是在 **WebView** 中执行的 JavaScript，与通过 `@js:` `<js>` `{{}}` 调用的 Rhino JS 是两套独立环境。

## 与 Rhino JS 的区别

| | webJs（WebView） | Rhino JS（书源规则） |
|---|---|---|
| **执行环境** | Android WebView（完整浏览器引擎） | Mozilla Rhino（纯 JS 引擎） |
| **访问 DOM** | ✅ `document.querySelector` `$('#id')` | ❌ 无 `window`/`document`/`$` |
| **调用网站函数** | ✅ `getDecode(); doDecrypt();` | ❌ 无函数引用 |
| **使用页面变量** | ✅ `window.x` `globalConfig` | ❌ |
| **await/Promise** | ✅ 通过重试机制支持 | ✅ Rhino 也支持 |
| **调用 Java bridge** | ✅ `ajaxAwait()` `webViewAwait()` | ✅ `java.ajax()` `java.webView()` |
| **jQuery/React/Vue** | ✅ 直接使用页面已加载的 | ❌ |

## 启用 webJs 的三种方式

### 方式一：URL 选项（推荐）

在书源 URL 后附加 JSON 选项：

```
https://example.com/chapter/123,{"webView":true,"webJs":"document.querySelector('.content').innerHTML"}
```

### 方式二：ContentRule.webJs 字段

**前提**：章节 URL 必须设 `webView:true`，否则 webJs 不会在 WebView 中执行。

```json
"ruleContent": {
    "content": "div.content",
    "webJs": "document.querySelector('div.content').innerHTML"
}
```

### 方式三：`@webjs:` 模式

**无需** URL 设 `webView:true`，`@webjs:` 会自行创建后台 WebView 执行。

```
getDecode()@webjs:document.querySelector('.content').innerHTML
```

`getDecode()` 在 Rhino 环境执行，`@webjs:` 之后在 WebView 环境执行。

> 通过 `@webjs:` 或 `contentRule.webJs` 调用时，超时固定为 10 秒；回退到 `BackstageWebView` 时默认 60 秒。

### URL 选项补充字段

| 字段 | 说明 |
|------|------|
| `webView` | 启用 WebView 加载（方式一和二必需） |
| `webJs` | WebView 加载完成后执行的 JS |
| `bodyJs` | 得到响应结果后执行的 JS，对结果二次处理 |
| `webViewDelayTime` | WebView 等待页面加载完毕的延迟时间（毫秒） |

## webJs 写法

### 1. JS 表达式（返回值即为结果）

```javascript
document.documentElement.outerHTML
```

结果就是页面完整 HTML。

### 2. 调用网站函数

```javascript
getDecode();$('#content').html()
```

`getDecode()` 是网站定义的解密函数，最终表达式的值作为结果返回。

### 3. 完整 JS 逻辑

```javascript
(function(){
    let content = document.querySelector('#article');
    let title = document.querySelector('h1').innerText;
    return title + '\n' + content.innerHTML;
})()
```

### 4. 异步操作（scroll/await）

```javascript
(async function(){
    for(let i=0;i<3;i++){
        window.scrollTo(0, document.body.scrollHeight);
        await new Promise(r => setTimeout(r, 1500));
    }
    return document.querySelector('#content').innerHTML;
})()
```

> **原理**：`evaluateJavascript` 不会等待 Promise resolve。async 代码执行时立即返回 `null`，系统通过**重试机制**反复执行 JS（每次间隔递增），直到返回非空值。

### 5. 懒加载轮询模式

`webJs` 返回 `null` 时系统会重试，返回字符串时结束。可用此特性等待动态内容就绪：

```javascript
(() => {
  const selector = '.read-content';
  const rejectPattern = /加载中|loading|请稍候/i;
  const scrollToBottom = true;

  if (scrollToBottom && !window.__legado_scrolled) {
    window.scrollTo(0, document.body.scrollHeight);
    window.__legado_scrolled = true;
    return null;
  }

  const el = document.querySelector(selector);
  if (!el) return null;

  if (rejectPattern && rejectPattern.test(el.outerHTML)) return null;

  return document.documentElement.outerHTML;
})();
```

## Bridge API（异步，返回 Promise）

由 `WebJsExtensions` 注入，均在 webJs 环境中可用：

| 函数 | 说明 |
|------|------|
| `run(jsCode)` | 回调到 Rhino 执行 JS |
| `ajaxAwait(url, timeout)` | 异步网络请求 |
| `connectAwait(url, header, timeout)` | 建立连接 |
| `getAwait(url, header, timeout)` | GET 请求 |
| `headAwait(url, header, timeout)` | HEAD 请求 |
| `postAwait(url, body, header, timeout)` | POST 请求 |
| `webViewAwait(html, url, js, cacheFirst)` | 递归启动新的 WebView |
| `webViewGetSourceAwait(html, url, js, regex, cacheFirst, delay)` | 获取资源 URL |
| `decryptStrAwait(transformation, key, iv, data)` | 解密 |
| `encryptBase64Await(transformation, key, iv, data)` | 加密（Base64 输出） |
| `encryptHexAwait(transformation, key, iv, data)` | 加密（Hex 输出） |
| `createSignHexAwait(algorithm, publicKey, privateKey, data)` | 签名（Hex 输出） |
| `downloadFileAwait(url)` | 下载文件 |
| `readTxtFileAwait(path)` | 读取文本文件 |
| `importScriptAwait(url)` | 导入外部 JS 脚本 |
| `getStringAwait(rule, content)` | 用解析规则提取文本 |

Bridge API 的 Promise 通过独立回调通道 resolve，配合重试机制实现异步等待。

## 同步方法（非 bridge，不返回 Promise）

webJs 环境中可直接调用（来自 `Java.callJs`）：

| 方法 | 签名 |
|------|------|
| `getString(rule, content, isUrl)` | 用解析规则提取文本 |
| `getStringList(rule, content, isUrl)` | 用解析规则提取文本列表 |
| `ajax(url, callTimeout)` | 同步网络请求 |
| `connect(url, header, callTimeout)` | 同步连接 |
| `get(url, header, timeout)` | 同步 GET 请求 |
| `post(url, body, header, timeout)` | 同步 POST 请求 |
| `log(msg)` | 输出日志 |
| `toast(msg)` / `longToast(msg)` | 弹出 Toast |

## 使用场景

| 场景 | 示例 |
|------|------|
| **网站内容加密/混淆** | `webJs: "getDecode();$('#content').html()"` |
| **需等待 JS 渲染** | URL 配 `webView:true, webViewDelayTime:3000` |
| **动态加载的内容** | webJs 中 scroll + await 等待加载 |
| **SPA 需调 API 补全** | webJs 中调用页面暴露的 `fetch`/`axios` |
| **绕过无限滚动** | scroll 循环 + 最终提取 |

## 注意事项

- webJs 默认超时：通过 `@webjs:` 或 `contentRule.webJs` 调用时 **10 秒**；回退到 `BackstageWebView` 时默认 **60 秒**
- 返回空或 `null` 时重试最多 30 次（间隔：200ms → 400ms → 600ms → 800ms → 1000ms，之后恒定 1000ms）。重试时 JS 重新执行，不适用于有副作用的操作
- WebView 图片加载默认关闭（`blockNetworkImage = true`），不要依赖图片触发 lazy-load
- 网站可能检查 `event.isTrusted`，程序化触发的点击/滚动会被忽略
- `console.log` 仅在通过 `@webjs:` 或 `contentRule.webJs` 调用时输出到调试面板；通过 URL 选项的路径无此输出
- webJs 不影响的字段如 ruleContent.webJs 的 `sourceRegex` 等仍然在 Rhino 环境执行
