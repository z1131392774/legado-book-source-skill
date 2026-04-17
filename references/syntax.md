# 规则语法详解

Legado 默认使用 Jsoup 语法。

## 选择器

| 语法 | 用途 |
|------|------|
| `tag@attr` | 获取元素属性（`h3@text`、`img@src`、`a@href`） |
| `.class` | class 选择器 |
| `#id` | id 选择器 |
| `tag.class` | tag + class 组合 |
| `tag > .child` | 直接子元素 |
| `tag:nth-child(n)` | 第 n 个子元素 |

## JavaScript 规则

### 前置规则

可以在 `<js>` 前写其他规则，JS 中的 `result` 就是上一步的结果：

```javascript
pre@html<js>(function(result){
    // result 是 pre@html 解析后的 HTML 内容
    var doc = org.jsoup.Jsoup.parse(result);
    java.log("doc:" + doc);  // 使用 java.log 打印日志
    
    // 处理逻辑
    doc.select("font").remove();
    
    return String(doc.html());
})(result)</js>
```

### 关键特性

- `<js>` 可在任意位置使用，还能作为其他规则的分隔符，如 `tag.li<js></js>//a`
- Legado 的 JavaScript 环境使用 Rhino 引擎
- Legado 重写了 Rhino 环境中的 `java` 变量（指向 Legado 自定义的工具对象）。如需访问原生 Java 标准库，请使用 `Packages.java.*`

## Java 对象类型转换

Legado 的 JavaScript 规则运行环境与浏览器不同。`result` 参数返回 **Java 对象**（Element/Document），不是 JS 字符串。直接调用 `.replace()`、`.match()` 等方法会触发方法选择歧义。

**关键原则：任何字符串操作前强制转换为 String**

```javascript
// ❌ 错误 - Java 方法歧义
var text = element.text();
text.replace(...)

// ✅ 正确 - 先转换
var text = String(element.text());
text.replace(...)
```

**正则匹配返回 Java 数组：**

```javascript
var match = "作者:张三".match(/作者[:：](\S+)/);
return match ? match[1] : "";  // 用 [1] 取捕获组
```

## Jsoup 解析

```javascript
var doc = org.jsoup.Jsoup.parse(String(result));  // 解析 HTML
var element = doc.select("selector").first();   // 选择元素
var text = String(element.text());                // 获取文本
```