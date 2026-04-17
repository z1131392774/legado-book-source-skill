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