# 规则语法详解

> Legado 默认使用 Jsoup 语法。基础选择器表见 `template.yaml`，本文档覆盖 @ 分隔符、数组写法、JS 规则基础。

- 字段名以 `Js` 结尾时，代表此字段接受 js 代码，无需使用 `<js>` 标签包裹。

## @ 分隔符语法（**核心规则**）

`@` 为规则分隔符，每段规则可分为 3 段：`类型@名称@位置`。

| 段 | 说明 |
|----|------|
| 第一段 - 类型 | `class`, `id`, `tag`, `text`, `children` 等。`children` 获取所有子标签，不需要第二段和第三段。`text` 可根据文本内容获取元素 |
| 第二段 - 名称 | 如 class 名、tag 名、text 内容的一部分 |
| 第三段 - 位置 | class/tag/id 会匹配多个，需指定位置。正序从 0 开始，负数为倒序（-1=倒数第1个）。不加位置则获取所有匹配项。`!` 表示排除，格式 `!0:1:3` 排除第1、2、4个 |

最后一段为获取内容：`text`, `textNodes`, `ownText`, `href`, `src`, `html`, `all` 等。

正则替换：末尾加 `##正则##替换内容`，替换内容为空时第二个 `##` 可省略。

多规则组合：`||` 表示或（任一匹配即可），`&&` 表示与（都要匹配）。

示例：

```
class.odd.0@tag.a.0@text
tag.dd.0@tag.h1@text##全文阅读
class.odd.0@tag.a.0@text||tag.dd.0@tag.h1@text##全文阅读
```

## 数组/区间写法

| 写法 | 说明 |
|------|------|
| `[index]` | 取指定索引，如 `[0]`, `[-1]` |
| `[!index,...]` | 排除指定索引，如 `[!0:2]` |
| `[start:end]` | 区间，start 为 0 或 end 为 -1 时可省略，如 `[:3]`, `[-2:]` |
| `[start:end:step]` | 带步长的区间，如 `[::2]`（每隔1个取1个） |

索引、区间两端、步长均支持负数。

`head@.1@text` ≡ `head@[1]@text` ≡ `head@children[1]@text`

## 列表倒置

规则最前面加负号 `-` 可使列表倒置，适用于目录倒序的网站。例：`-tag.dd` 获取所有 dd 标签并倒置顺序。区间反向：`tag.div[-1:0]` 也可实现反向。

## JS 规则注意

- `result` 是 Java 对象，字符串操作前必须 `String(result)` 转换
- 解析 HTML：`var doc = org.jsoup.Jsoup.parse(result);`
- 选择元素：`var element = doc.select("selector").first();`
- 获取文本：`var text = String(element.text());`
- 打印日志：`java.log("msg")`
- Legado 重写了 `java` 变量，原生 Java 用 `Packages.java.*`
- 前置规则: `<js>` 前可写其他规则，JS 中 `result` 为前置规则的结果
  - 例: `pre@html<js>处理逻辑</js>` 其中 result 为 `pre@html` 解析后的 HTML 内容

## 规则类型标志

`{{......}}` 内使用规则必须有明显的规则标志，没有规则标志当作 js 执行。

| 标志 | 说明 |
|------|------|
| `@@` | 默认规则，直接写时可以省略 `@@` |
| `@XPath:` | XPath 规则，直接写时以 `//` 开头可省略 `@XPath` |
| `@Json:` | JSON 规则，直接写时以 `$.` 开头可省略 `@Json` |
| `:` | 正则规则，不可省略，只可用在书籍列表和目录列表 |
| `<js>...</js>` | JS 包裹标签，可在任意位置插入 JS 代码，也可作规则分隔符。例: `tag.li<js></js>//a` 或 `pre@html<js>处理逻辑</js>` |

## URL 变量

| 变量 | 说明 |
|------|------|
| `{{page}}` | Legado 内置分页变量，从 1 开始，搜索/发现 URL **必须包含** |
| `{{key}}` | Legado 内置搜索关键词变量，搜索 URL **必须包含**，发现页带输入框时使用 |
| `{{xxx}}` | 自定义变量，需通过 JS 定义，如 `source.put('bookId', '123')` |

搜索 URL 例：`https://example.com/search?q={{key}}&page={{page}}`

发现 URL 例：`https://example.com/top?page={{page}}`

## URL 选项（常用）

URL 末尾以 `,{JSON}` 追加，格式如 `https://example.com/page,{"webView":true}`。完整列表见 `references/js-api.md`。

| 选项 | 说明 |
|------|------|
| `webView: true/false` | 是否使用 WebView 渲染页面（JS 动态渲染的网站必开） |
| `method: POST/GET/HEAD` | 请求方法，默认 GET |
| `charset: string` | 编码，如 utf-8、gbk |
| `header: {key:val}` | 自定义请求头 |
| `body: string` | POST 请求体 |
