# 获取不到内容？排查指南

> 当规则写了但获取不到内容时，按以下顺序从简到繁排查。先读完第 0 节，再往下走。

## 0. 排查之前：先确认你看得见什么

“选择器不对”经常是误判：真实的原始响应可能根本没看到，或者看到的是上一次的结果。先确认下面几件事，再决定改哪里。

### 0.1 原始响应在哪看

App 的「书源调试」页，右上角菜单里有四项：

- **搜索源码**
- **书籍源码**
- **目录源码**
- **正文源码**

点开是当次请求的原始内容，纯文本显示，不渲染 HTML。要找选择器、看页面结构，就在这里看。

调试脚本（WebSocket）拿不到这四份原文：调试服务把搜索、详情、目录、正文四种原始 body 按状态号 10/20/30/40 发送，这四个状态在推送前就被过滤了。所以脚本里只有流程日志、`列表大小`、章节列表，没有页面本身。

规则里的 `java.log(msg)` 会进调试流，也会写进 App 日志，排查时优先用它。

### 0.2 失败文案会被当成正文存下来

正文规则返回的**任何非空字符串**都会被写进章节缓存，只有空串才会触发“内容为空”。

```js
// 错：这句错误会被存成正文，之后一直显示它
return "未找到正文：div.postmessage 未匹配";
```

修好规则也没用，缓存里存的还是那句话。两条规矩：

- 失败时 `return ""`，或者直接抛异常。抛异常不落盘，阅读页显示“获取正文失败 + 原因”。
- 已经被污染的章节，先清缓存再重试：阅读页刷新正文会删掉当前章缓存再重新拉取，也可以长按章节清除缓存。

### 0.3 改了书源却不生效

阅读页在打开这本书时载入书源对象，之后只有一条路会换掉它：从这本书里进入书源编辑页，保存后返回。

下面这些改法都不会让阅读页换对象，刷新正文、刷新目录仍然用旧规则，看起来像“缓存清不掉”：

- 用 Web API 改书源
- 在书源管理页面改完，直接切回阅读页
- 在另一台设备上改

处理：退出阅读页重进，或者从这本书的书源编辑页保存返回。

### 0.4 用探针规则数数量

需要“数量”而不是原文时，临时把规则换成探针，返回几个数字：

```js
<js>
(function (result) {
  var doc = org.jsoup.Jsoup.parse(String(result));
  return "len=" + String(result).length
    + " | title=" + doc.title()
    + " | div=" + doc.select("div.postmessage").size()
    + " | th=" + doc.select("th[id^=postmessage_]").size();
})(result)
</js>
```

另外，JS 规则必须带 `<js>` 或 `@js:` 前缀，漏了会被当成文本选择器，返回空且不报错——探针“返回空”时先查这一条。

改探针前备份书源 JSON，跑完立刻还原。**还原用改之前的快照**，不要拿旧快照还原，否则会把刚做的修改一起回滚。

排查顺序因此是：先看原始响应（0.1）→ 再用探针数数量（0.4）→ 最后才动选择器。跳过前两步，改选择器就是猜。

## 1. 更换 User-Agent（第一步）

遇到反爬时，**先换 UA**，这是最简单的反爬手段。在书源 `header` 字段中填写 `User-Agent`。

最稳妥的方式是用户在手机上获取自己的浏览器 UA，例如使用 https://tool.ip138.com/useragent/ 网站查看 UA。注意部分网站针对手机 UA 和 PC UA 会分别做适配，网页结构可能变化。

如果还不够，再试 `webView:true` 或 `loginCheckJs`。

## 2. 使用 WebView 渲染页面

当页面上有内容但 OkHttp 请求返回空 HTML（SPA 站点、JS 动态渲染、需执行脚本后才出现内容），最简单的修复：在 URL 后加 `,{"webView":true}` 用 WebView 加载。

```
https://example.com/page,{"webView":true}
```

组合使用示例（同时开启 WebView + 编码 + 延迟）：

```
https://example.com/page,{"webView":true, "webJs":"...", "webViewDelayTime":2000}
```

**注意：** `webView` 设为 `true` 时才会执行 `webJs`。若缺省或为 `false`，即使传了 `webJs` 也不会启用 WebView。

完整 URL 选项（method/charset/header/body/js/bodyJs/dnsIp 等）见 `references/js-api.md`。<!-- url-选项参考 -->

## 3. webJs 等待页面就绪

正文规则中的 `webJs` 字段可以用于处理**懒加载页面**。与普通请求不同，webjs 会在 WebView 中反复执行，直到返回非 `null` 值才结束。

**前置要求：** 使用 `contentRule.webJs` 前，URL 必须带 `,{"webView":true}` 选项，否则 WebView 路径不通，`webJs` 被静默忽略。如果章节 URL 不便于加选项，可将 webjs 写在内联规则中通过 `@@webjs:` 触发。

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

### WebView 内置 JS 方法

- `window.close()` — 关闭浏览器界面
- `screen.orientation.lock()` — 全屏后控制屏幕方向（lock 参数：`"landscape"`、`"landscape-primary"`、`"landscape-secondary"`）
- `window.run("js代码")` — 异步执行阅读函数并返回字符串结果

```javascript
window.run("java.toast('执行成功');'成功'")
.then(r=>alert(r))
.catch(e=>alert("执行出错:"+e));
```

## 4. loginCheckJs 过验证盾

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

## 5. 重定向拦截

对于搜索重定向的源，使用 `java.get()` / `java.post()` 获取重定向后的 URL。

```javascript
// 方法一：使用 java.connect
(()=>{
  if(page==1){
    let url='https://www.yooread.net/e/search/index.php,'+JSON.stringify({
    "method":"POST",
    "body":"show=title&tempid=1&keyboard="+key
    });
    return source.put('surl',String(java.connect(url).raw().request().url()));
  } else {
    return source.get('surl')+'&page='+(page-1)
  }
})()

// 方法二：使用 java.post 获取重定向 header
(()=>{
  let base='https://www.yooread.net/e/search/';
  if(page==1){
    let url=base+'index.php';
    let body='show=title&tempid=1&keyboard='+key;
    return base+source.put('surl',java.post(url,body,{}).header("Location"));
  } else {
    return base+source.get('surl')+'&page='+(page-1);
  }
})()
```

Java 网络请求方法（详见 `references/js-api.md`）：
- `java.get(urlStr: String, headers: Map<String, String>)`
- `java.post(urlStr: String, body: String, headers: Map<String, String>)`
- `java.connect(urlStr, header = null, callTimeout: Int? = null): StrResponse`

## 6. 字体解析（正文乱码）

正文替换规则中使用，根据 f1 字体的字形数据到 f2 中查找字形对应的编码。

```js
<js>
(function(){
  var b64=String(src).match(/ttf;base64,([^\)]+)/);
  if(b64){
    var f1 = java.queryTTF(b64[1]);
    var f2 = java.queryTTF("https://alanskycn.gitee.io/teachme/assets/font/Source Han Sans CN Regular.ttf");
    return java.replaceFont(result, f1, f2, true); // 过滤掉 f1 中不存在的字形
  }
  return result;
})()
</js>
```

## 7. 图片解密

正文或封面图片需要二次解密时使用。`result` 为待解密图片的 `ByteArray`，`src` 为图片链接。封面解密同理，`result` 为 `inputStream`。

```js
// AES 解密
java.createSymmetricCrypto("AES/CBC/PKCS5Padding", key, iv).decrypt(result)

// XOR 解密
function decodeImage(data, key) {
  var input = new Packages.java.io.ByteArrayInputStream(data)
  var out = new Packages.java.io.ByteArrayOutputStream()
  var byte
  while ((byte = input.read()) != -1) {
    out.write(byte ^ key)
  }
  return out.toByteArray()
}
decodeImage(result, key)
```

## 8. 超出文档范围的反爬

上述方法覆盖了 Legado 书源最常见的反爬场景。如果遇到文档未覆盖的反爬手段（请求签名、指纹检测、字体反爬、JS 混淆等），请自行查阅 Legado 源码仓库（需询问用户阅读版本）和小说网页本身来寻找解决方案。Legado 的 `loginCheckJs`、URL 选项、JS 规则等接口足够灵活，很多反爬可以通过 JS 逆向在规则层解决。
