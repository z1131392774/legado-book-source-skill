# 高级技巧

## fallback 机制

当搜索规则未填写时，Legado 会使用发现规则作为 fallback（反之亦然），前提是两者的列表解析规则能产出相同结构的数据。

注意：搜索地址和发现地址不会互相 fallback。

## loginCheckJs 过验证盾

`loginCheckJs` 位于书源**基础**选项卡。Legado 在每次请求网站后都会执行此 JS 代码，`result` 为响应对象（包含 `url`、`code`、`body` 等属性）。JS 需返回修改后的响应对象。

### 原理

检测响应中是否包含验证特征，如有则启动浏览器等待用户完成验证，验证通过后继续。

### 典型用法（过 Cloudflare 盾）

```javascript
var resultUrl = result.url();
var resultCode = result.code();
var resultBoDy = result.body();
if (/_cf_|ge_ua|verify.php/gi.test(resultBoDy) && resultCode >= 403) {
  if (key) {
    url = baseUrl + java.ruleUrl;
  }
  cookie.removeCookie(baseUrl);
  result = java.startBrowserAwait(resultUrl, "验证", false);
  if (key) {
    url =
      org.jsoup.Jsoup.parse(result.body())
        .select('meta[property="og:url"]')
        .attr("content") || url;
  }
}
result;
```

### 关键步骤

1. 检测响应体中的验证特征（如 `_cf_`、`ge_ua`、`verify.php`）+ 状态码 ≥ 403
2. 清除旧 cookie：`cookie.removeCookie(baseUrl)`
3. 调用 `java.startBrowserAwait(url, title, isPost)` 启动浏览器等待用户操作
4. 验证通过后从新响应中提取正确的 URL
5. **末尾必须返回 `result`**（修改后的响应对象）

### 调试注意

调用 `java.startBrowserAwait` 后，手机上会弹出浏览器窗口显示 Cloudflare 验证页面。用户需要手动点击完成验证（勾选"我不是机器人"等），代码会等待用户操作完成后才继续执行。调试时要提醒用户留意手机上弹出的验证窗口。

## URL 选项：使用 WebView 渲染

在 URL 规则中可以通过行内 JSON 传递选项，强制使用 WebView 加载页面（而非默认的 OkHttp 请求）。

### 基本写法

```
https://example.com/page,{"webView":true}
```

### 完整选项

URL 选项以 JSON 对象形式写在 URL 末尾（用逗号分隔），支持以下字段：

| 选项 | 类型 | 说明 |
|------|------|------|
| `webView` | bool | `true` 时使用 WebView 加载页面 |
| `webJs` | string | 页面加载完成后在 WebView 中执行的 JS |
| `webViewDelayTime` | number | 页面加载后等待的延迟时间（毫秒） |
| `method` | string | 请求方法：`POST` / `GET` / `HEAD` |
| `charset` | string | 编码，如 `utf-8`、`gbk` |
| `retry` | number | 重试次数 |
| `header` | object | 自定义请求头，如 `{"User-Agent":"...", "Cookie":"..."}` |
| `headers` | array | 同上，数组格式 |
| `body` | string | POST 请求体 |
| `js` | string | 访问前执行的 JS，结果替换 URL |
| `bodyJs` | string | 获取响应后执行的 JS，结果替换 body |
| `type` | string | 资源类型标识 |
| `dnsIp` | string | 自定义 DNS 解析 IP |
| `serverID` | number | 服务器 ID |

### 组合使用

```
https://example.com/page,{"webView":true, "webJs":"...", "webViewDelayTime":2000}
```

### 执行流程

```
URL + 选项解析
  → useWebView = true?
     ├─ 是 → BackstageWebView 加载页面
     │       → onPageFinished + delayTime
     │       → 执行 webJs（如有）
     │       → 返回渲染后的 HTML
     └─ 否 → OkHttp 直接请求
```

### 适用场景

- 页面内容由 JS 动态渲染（SPA 站点）
- 需要加载图片才能触发后继请求的页面
- 使用 `webJs` 配合等待懒加载内容

## webjs 等待页面就绪

正文规则中的 `webJs` 字段用于处理**懒加载页面**。与普通请求不同，webjs 会在 WebView 中反复执行，直到返回非 `null` 值才结束。

### 原理

```
webjs 返回 null → 等待后重新执行 → 再次检查 → 直到返回非 null
```

- 返回 `null` → 继续轮询等待
- 返回字符串 → 作为页面 HTML 内容，结束轮询

### 典型用法（等待懒加载内容）

```javascript
(() => {
  // ========== 用户配置区 ==========
  const selector = '.read-content';
  const scrollToBottom = true;

  // 检测目标：'html' 检查 outerHTML，'text' 检查 innerText
  const checkTarget = 'html';

  // 对检测目标做正则匹配（均作用于 checkTarget 的结果）
  const expectPattern = null;                       // 必须匹配才视为就绪
  const rejectPattern = /加载中|loading|请稍候/i;    // 匹配则未就绪，设 null 关闭

  // 自定义就绪检测，存在时独占判断，正则不生效
  const readyCheck = null;

  // 是否压缩空白符（仅 checkTarget = 'text' 时生效）
  const normalizeWhitespace = true;
  // ==============================

  if (scrollToBottom && !window.__legado_scrolled) {
    window.scrollTo(0, document.body.scrollHeight);
    window.__legado_scrolled = true;
    return null;
  }

  const el = document.querySelector(selector);
  if (!el) return null;

  // readyCheck 独占：存在时忽略正则
  if (typeof readyCheck === 'function') {
    return readyCheck(el) ? document.documentElement.outerHTML : null;
  }

  let content = checkTarget === 'html'
    ? el.outerHTML
    : (el.innerText || el.textContent || '');
  if (checkTarget === 'text' && normalizeWhitespace) {
    content = content.replace(/\s+/g, ' ').trim();
  }

  if (rejectPattern && rejectPattern.test(content)) return null;
  if (expectPattern && !expectPattern.test(content)) return null;

  return document.documentElement.outerHTML;
})();
```

### 配置项说明

| 配置项 | 作用 |
|--------|------|
| `selector` | 内容元素的 CSS 选择器 |
| `scrollToBottom` | 首次执行时滚动到底部，触发懒加载 |
| `checkTarget` | `'html'` 检查 outerHTML，`'text'` 检查 innerText |
| `expectPattern` | 必须匹配才视为就绪（null 关闭） |
| `rejectPattern` | 匹配则未就绪，继续等待 |
| `readyCheck` | 自定义就绪函数，存在时独占判断 |
| `normalizeWhitespace` | 压缩空白符（仅 text 模式生效） |

### 执行流程

1. **首次执行**：滚动到底部（触发懒加载），返回 `null`
2. **后续执行**：检查目标元素内容是否就绪
   - 未就绪（匹配 `rejectPattern`）→ 返回 `null`
   - 已就绪 → 返回 `document.documentElement.outerHTML`

### 适用场景

- 需要 JS 渲染的 SPA 页面
- 懒加载内容（滚动后才加载）
- 有"加载中"提示的页面
- 需要等待动态内容就绪的场景

### 调试注意

webjs 会在 WebView 中反复执行，注意避免无限循环。确保 `rejectPattern` 能正确识别未就绪状态，`expectPattern` 或 `readyCheck` 能正确识别就绪状态。