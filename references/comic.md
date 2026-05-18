# 漫画书源制作指南

> 漫画书源 (bookSourceType=2) 与小说书源的核心区别：正文返回图片列表而非文本。

## 1. 正文规则

### 1.1 模式A：简单 CSS 选择器

图片在 HTML 中直接可见，无加密或懒加载。

```yaml
ruleContent:
  content: "#cp_img@html"
  imageStyle: FULL
```

常见选择器：
- `#cp_img@html` — 漫画图片容器
- `.lazy@html` — 懒加载图片列表
- `class.comic-contain@div@img@html` — 漫画内容区

> `@html` 是 CSS 链的获取内容后缀，完整语法见 `references/basics.md` §@ 分隔符语法。

### 1.2 模式B：CSS + JS 净化/去重

选择器能拿到数据，但需要去重、排序或修正 URL。

```yaml
content: |
  class.comiclist@tag.div@class.comicpage@tag.div@tag.img@html
  @js:
  var uniqueImgTags = Array.from(new Set(result.split('\n').filter(Boolean)));
  uniqueImgTags.join('\n');
```

常见 JS 处理：
```js
// 去重
Array.from(new Set(result.split('\n'))).join('\n')

// 修正协议
result.replace(/http:/g, 'https:')
```

### 1.3 模式C：JSON API

网站使用 API 接口返回图片地址列表（JSONPath 提取）。

```js
content: |
  $..url
  <js>
  result.split('\n').map(x => '<img src="' + x + '">').join('\n');
  </js>
```

批量生成图片 URL（已知命名规则）：
```js
content: |
  <js>
  var host = 'https://mhpic.example.com/comic/';
  var original = result.match(/dr_original:"([^"]+)"/)[1];
  var end = parseInt(result.match(/end_var:(\d+)/)[1]);
  var html = '';
  for (var i = 1; i <= end; i++) {
      html += '<img src="' + host + original + i + '.jpg">\n';
  }
  html;
  </js>
```

### 1.4 模式D：加密解密（AES / Base64 / JS 混淆）

图片数据被加密，需从页面 JS 中提取密钥并解密。

AES 解密：
```js
content: |
  <js>
  result = String(java.getString('$.data')).replace(/arsadata/, '');
  var key = "4548ded8c9e02690";
  var iv = "1992360ee9bc4f8f";
  var decrypted = java.createSymmetricCrypto("AES/CBC/PKCS5Padding", key, iv).decryptStr(result);
  var imgUrls = decrypted.match(/\[(.*)\]/)[1].split(',')
      .map(x => '<img src=' + x + '>').join('\n');
  imgUrls;
  </js>
```

JS 混淆（eval unpack）：
```js
content: |
  <js>
  var evalStr = result.match(/(eval.*\)\))/)[1];
  var match = evalStr.match(
      /eval\(function\(p,a,c,k,e,d\)\{.*?\}\('(.*?)',(\d+),(\d+),'(.*?)'\.split\('\|'\)/
  );
  var unpacked = unpack(match[1], parseInt(match[2]), parseInt(match[3]), match[4].split('|'));
  eval(unpacked);
  var imgTags = picTree.map(item => '<img src="' + item + '">').join('\n');
  imgTags;
  </js>
```

需要在 jsLib 中定义 `unpack` 函数。

### 1.5 模式E：imageDecode（逐图解密）

图片本身被加密（如打乱顺序），用 `imageDecode` 对每个图片的 ByteArray 解密重组。

```yaml
ruleContent:
  content: "$.data[*].attributes.url"
  imageStyle: FULL
  imageDecode: |
    <js>
    var Magua = new JavaImporter();
    Magua.importPackage(Packages.java.io, Packages.android.graphics);
    with (Magua) {
        var img = BitmapFactory.decodeByteArray(result, 0, result.length);
        var height = img.getHeight();
        var width = img.getWidth();
        var num = 10;
        var y = Math.floor(height / num);
        var remainder = height % num;
        var newImg = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
        var canvas = new Canvas(newImg);
        for (var i = 1; i <= num; i++) {
            var h = i === num ? remainder : 0;
            canvas.drawBitmap(
                Bitmap.createBitmap(img, 0, y * (i - 1), width, y + h),
                0, height - y * i - h, null
            );
        }
        var newbit = new ByteArrayOutputStream();
        newImg.compress(Bitmap.CompressFormat.PNG, 100, newbit);
        newbit.toByteArray();
    }
    </js>
```

## 2. 图片懒加载选择器

漫画站常用 `data-src`、`data-original` 等属性存储真实图片 URL，而非 `src`。

```yaml
ruleContent:
  content: "img@data-original@html"
  # 或
  content: "img@data-src@html"
```

如果选择器不支持直接取自定义属性，用 replaceRegex：
```yaml
replaceRegex: "data-src=\"([^\"]+)\"##<img src=\"$1\">"
```

## 3. 图片防盗链（Referer）

漫画图片通常需要 Referer 头才能加载。在正文 JS 中为每个图片拼接请求头：

```js
var headers = JSON.stringify({"headers":{"Referer": baseUrl}});
result.split('\n').map(x => '<img src="' + x + ',' + headers + '">').join('\n');
```

图片链接 header 格式：`<img src="url,{"headers":{"Referer":"..."}}">`。

> 全局 header 配置见 `references/template.yaml` 的 header 字段。

## 4. 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| 正文无内容 | imageStyle 未设 FULL | 加 `imageStyle: FULL` |
| 图片 403 | 无 Referer | 正文 JS 中为图片拼接 Referer header |
| 目录顺序反了 | 网站倒序 | `-` 前缀反转 |
| 阅读模式是文本 | bookSourceType 不是 2 | 设置 `bookSourceType: 2` |
| 图片不显示 | 懒加载 data-src | 用 `@data-original` 或 replaceRegex 替换 |