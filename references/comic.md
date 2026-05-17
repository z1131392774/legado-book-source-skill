# 漫画书源制作指南

漫画书源与小说书源的核心区别：正文返回图片列表而非文本。以下是完整制作方法论，总结自大量实战书源。

---

## 零、漫画书源 vs 小说书源速览

| 维度 | 小说 (type=0) | 漫画 (type=2) |
|------|--------------|--------------|
| bookSourceType | 0 | **2** |
| 正文内容 | 纯文本 | `<img src="...">` 列表 |
| imageStyle | 通常空 | **FULL**（全宽显示） |
| book.type (目录) | 8 (安卓) / 0 (iOS) | **64** (安卓) / 2 (iOS) |
| 封面 | 直接 URL | 可能需要 request header |
| 正文分页 | 极少 | 常见（nextContentUrl） |
| 图片解密 | 极少 | 常见（imageDecode/coverDecodeJs） |
| 内容加密 | 较少 | AES/Bitmap/JS 解密常见 |

---

## 一、正文提取（ruleContent）— 四大模式

### 模式A：简单 CSS 选择器（直接可用，无需 JS）

**适用**：图片在页面 HTML 中直接可见，无加密/懒加载/动态渲染。

```yaml
ruleContent:
  content: "#cp_img@html"          # 图片容器
  imageStyle: FULL
```

或：

```yaml
ruleContent:
  content: ".lazy@html"            # 懒加载图片列表
  imageStyle: FULL
```

或获取所有 img 标签：

```yaml
ruleContent:
  content: "class.comiclist@tag.div@class.comicpage@tag.div@tag.img@html"
  imageStyle: FULL
```

**常见选择器**：
- `#cp_img@html` — 漫画图片容器
- `.lazy@html` / `.lazy-read@html` — 懒加载图片
- `class.comic-contain@div@img@html` — 漫画内容区
- `body@html` + 配合 replaceRegex 净化

### 模式B：CSS 选择器 + JS 净化/去重

**适用**：选择器能拿到原始数据，但需要去重、排序、修正 URL。

```yaml
ruleContent:
  content: |
    class.comiclist@tag.div@class.comicpage@tag.div@tag.img@html
    @js:
    function removeDuplicateImgTags(str) {
        var imgTags = str.split(/\n|\r/).filter(Boolean);
        var uniqueImgTags = Array.from(new Set(imgTags));
        return uniqueImgTags.join('\n');
    }
    removeDuplicateImgTags(result);
  imageStyle: FULL
```

**常见 JS 处理**：
```javascript
// 去重
Array.from(new Set(result.split('\n'))).join('\n')

// 修正协议
result.replace(/http:/g, 'https:')

// 添加 Referer 头（图片防盗链）
result.split('\n').map(x => '<img src="' + x + '">').join('\n')
```

### 模式C：JSON API（API 返回图片URL数组）

**适用**：网站使用 API 接口返回图片地址列表。

```javascript
// 例1: 直接取 JSON 中的 URL 数组
content: |
  $..url
  <js>
  result.split('\n').map(x => '<img src="' + x + '">').join('\n');
  </js>
```

```javascript
// 例2: 嵌套 JSON
content: |
  $.data.current_chapter.chapter_img_list
  @js:
  var headers = JSON.stringify({"headers":{"Referer": baseUrl}});
  result.split("\n").map(x => '<img src="' + x + ',' + headers + '">').join("\n");
```

```javascript
// 例3: 批量生成图片URL（已知命名规则）
content: |
  <js>
  var host = 'https://mhpic.example.com/comic/';
  var original = result.match(/dr_original:"([^"]+)"/)[1];
  var end = result.match(/end_var:(\d+)/)[1];
  var html = '';
  for (var i = 1; i <= end; i++) {
      html += '<img src="' + host + original + i + '.jpg">\n';
  }
  html;
  </js>
```

### 模式D：加密解密（AES / Base64 / JS混淆）

**适用**：图片数据被加密，需要从页面 JS 中提取密钥并解密。

#### D1: AES + Base64 混合解密

```javascript
// 从 JSON 字段解密
content: |
  <js>
  result = String(java.getString('$.data')).replace(/arsadata/, '');
  var decrypted = java.aesBase64DecodeToString(
      result,
      "4548ded8c9e02690",       // 密钥
      "AES/CBC/PKCS5Padding",    // 模式
      "1992360ee9bc4f8f"         // IV
  );
  var imgUrls = decrypted.match(/\[(.*)\]/)[1].split(',').map(x => '<img src=' + x + '>').join('\n');
  imgUrls;
  </js>
```

#### D2: JS 混淆（eval unpack）

```javascript
// 页面内嵌的 eval(function(p,a,c,k,e,d)...) 混淆代码
content: |
  <js>
  var evalStr = result.match(/(eval.*\)\))/)[1];  // 提取 eval 代码
  var match = evalStr.match(
      /eval\(function\(p,a,c,k,e,d\)\{.*?\}\('(.*?)',(\d+),(\d+),'(.*?)'\.split\('\|'\)/
  );
  var unpacked = unpack(match[1], parseInt(match[2]), parseInt(match[3]), match[4].split('|'));
  eval(unpacked);  // 得到 picTree 或 newImgs 数组
  var imgTags = picTree.map(item => '<img src="' + item + '">').join('\n');
  imgTags;
  </js>
```

**需要在 jsLib 中定义 unpack 函数**。

#### D3: 自定义 JS 混淆（var _0x...)

```javascript
// 页面使用自定义混淆器，需要从 page script 中提取并 eval
content: |
  <js>
  eval(result.match(/eval(.*?)\{\}\)\)/)[0]);  // 执行页面混淆代码
  var image_list = [];
  newImgs.map(item => {
      image_list.push('<img src="' + item + '">')
  });
  image_list.join("\n");
  </js>
```

### 模式E：图片解密（imageDecode — 逐图处理）

**适用**：图片本身被加密（如打乱顺序），需对每个图片 ByteArray 进行解密重组。

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
        var num = 10;  // 块数（根据网站算法计算）
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

---

## 二、目录（ruleToc）— 必备配置

### book.type 必须设置

```javascript
chapterList: |
  <js>
  // ... 目录解析逻辑 ...
  if (device_type == "安卓") {
      book.type = 64;     // 漫画（Android）
  } else {
      book.type = 2;      // 漫画（iOS）
  }
  // ... 继续解析 ...
  </js>
```

完整 book.type 对照：
| 类型 | Android | iOS |
|------|---------|-----|
| 小说 | 8 | 0 |
| 听书 | 32 | 1 |
| **漫画** | **64** | **2** |
| 短剧 | 8 | 3 |

### 目录倒序

很多漫画站目录是倒序的（最新在前），用 `-` 前缀反转：

```yaml
ruleToc:
  chapterList: "-.detail-list-select@li"         # 减号 = 反转
```

或区间反转：

```yaml
ruleToc:
  chapterList: ".chapter-list@li[-1:0]"          # 从最后到第一个
```

### VIP 章节标记

```yaml
ruleToc:
  isVip: "img@class##detail-list-lock"          # 检测锁图标
  # 或
  isVip: "@js: result.select('img').hasClass('detail-list-lock')"
```

### 章节 URL 拼接参数

```yaml
ruleToc:
  chapterUrl: |
    href
    @js:
    result += '/?shunt=' + SH[Get('shunt')]    # 拼接分流参数
```

---

## 三、详情页（ruleBookInfo）— 漫画特有问题

### init 中处理 JS 渲染

```javascript
init: |
  <js>
  if (result.includes('no-js')) {
      cookie.removeCookie(baseUrl);
      result = java.startBrowserAwait(baseUrl, "验证").body();
  }
  result
  </js>
```

### 多类型来源合并在详情展示

```javascript
intro: |
  &nbsp;&nbsp;🎴当前来源：{{$.source}}
  🎯最新章节：{{$.last_chapter_title}}
  ⏳更新时间：{{$.last_chapter_update_time}}
  📚书籍简介：
  {{$.abstract}}
```

### 封面防盗链

```javascript
coverUrl: |
  @js:
  var headers = JSON.stringify({"headers":{"Referer": baseUrl}});
  result + ',' + headers;     // 追加请求选项
```

```yaml
# 或使用 coverDecodeJs 解密加密封面
coverDecodeJs: "java.createSymmetricCrypto('AES/CBC/PKCS5Padding', key, iv).decrypt(result)"
```

---

## 四、搜索（ruleSearch）— URL 参数

### 搜索 URL 示例

```yaml
searchUrl: "/search?keyword={{key}}&page={{page}}"
# 或
searchUrl: "{{Get('urls')[Get('ci')]}}/search?q={{key}}&page={{page}}"
```

### JSON API 搜索（POST）

```yaml
searchUrl: |
  /search/selfdefine,{
    "method": "POST",
    "body": "keyword={{key}}&page={{page}}"
  }
```

### 搜索列表中的分类信息

漫画搜索结果中 kind 字段常包含多种信息，用 `&&` 组合：

```yaml
ruleSearch:
  kind: "{{$.status}},{{$.score}},{{$.tags}},{{$.last_chapter_update_time}}"
```

---

## 五、发现页（ruleExplore / exploreUrl）— 漫画分类

### 静态发现 URL

```yaml
exploreUrl: |
  全部::/category/list/1
  连载::/booklist?tag=全部&end=0&page={{page}}
  完结::/booklist?tag=全部&end=1&page={{page}}
```

### 动态 JS 生成发现菜单

```javascript
exploreUrl: |
  <js>
  var sort = [];
  var push = function(title, url, type1, type2) {
      sort.push({
          title: title,
          url: url,
          style: {
              layout_flexGrow: type1,
              layout_flexBasisPercent: type2
          }
      });
  };
  
  var typeNames = ["全部", "恋爱", "纯爱", "古风", ...];
  var types = ["all", "lianai", "chunai", "gufeng", ...];
  
  typeNames.forEach(function(item, index) {
      var url = "https://example.com/api/list?type=" + types[index] + "&page={{page}}";
      push(item, url, 1, 0.25);
  });
  JSON.stringify(sort);
  </js>
```

---

## 六、HTTP 请求 — 漫画常见坑

### 防盗链 Referer

漫画图片通常需要 Referer 头才能加载：

```javascript
// 正文中给每个图片加 Referer
var headers = JSON.stringify({"headers":{"Referer": baseUrl}});
result.split('\n').map(x => '<img src="' + x + ',' + headers + '">').join('\n');
```

或全局 header：

```yaml
header: '{"User-Agent":"...", "Referer":"baseUrl"}'
```

### WebView 验证

部分漫画站需要过 Cloudflare/验证盾：

```javascript
if (result.includes('html.js') || result.includes('_cf_')) {
    cookie.removeCookie(baseUrl);
    result = java.startBrowserAwait(baseUrl, "验证").body();
}
```

可放入 `loginCheckJs` 实现全局检测。

### Cookie 管理

```yaml
enabledCookieJar: true     # 启用 Cookie 自动管理
```

---

## 七、常见 API 签名

部分漫画站需要请求签名验证：

```javascript
// URL MD5 签名
var t = "/api/v2/comic/getcomicdata?comic_id=" + cid + "&...";
var sign = java.md5Encode(t + "erciyuan2020");   // 密钥拼接
var headers = {
    "m-request-id": sign
};
```

---

## 八、完整模板（最小可工作漫画书源）

```yaml
bookSourceName: "示例漫画源"
bookSourceGroup: "漫画"
bookSourceType: 2                           # ← 漫画必须填 2
bookSourceUrl: "https://example.com"

header: '{"User-Agent": "Mozilla/5.0 ..."}'

ruleSearch:
  bookList: ".book-list li"
  name: ".book-list-info-title@text"
  author: ".book-list-info-bottom-item@text"
  coverUrl: "img@data-original"
  bookUrl: "a.0@href"

ruleBookInfo:
  name: "h1@text"
  author: ".detail-main-info-author@text"
  coverUrl: "img@src"
  intro: ".detail-desc@text"
  kind: ".detail-main-info-class@a@text"

ruleToc:
  chapterList: "-#detail-list-select@li@a"
  chapterName: "text"
  chapterUrl: |
    href
    @js:
    book.type = 64;                          # ← 漫画必须设置 book.type
    result;

ruleContent:
  content: "#cp_img@html"
  imageStyle: FULL                           # ← 漫画必须设置 FULL

searchUrl: "/search?keyword={{key}}"
```

---

## 九、调试检查清单

制作漫画书源时，顺序验证：

| # | 检查项 | 命令/方法 |
|---|--------|----------|
| 1 | bookSourceType = 2 | 查看模板 |
| 2 | 搜索返回漫画列表 | `--key "鬼灭之刃"` |
| 3 | 目录有章节、book.type=64 | `"++详情URL"` |
| 4 | 正文有 img 标签 | `"--章节URL"` |
| 5 | imageStyle = FULL | 查看模板 |
| 6 | 图片可加载（无403） | 阅读界面查看 |
| 7 | 封面可显示 | 详情页查看 |
| 8 | 发现页可翻页 | 发现页滑动 |

### 调试脚本用法

```bash
# 搜索
python3 scripts/legado-debug.py --host <手机IP> --source 漫画源.yaml --key "系统"

# 详情
python3 scripts/legado-debug.py --host <手机IP> --source 漫画源.yaml --key "https://example.com/book/123"

# 目录（++前缀）
python3 scripts/legado-debug.py --host <手机IP> --source 漫画源.yaml --key "++https://example.com/book/123"

# 正文（--前缀）
python3 scripts/legado-debug.py --host <手机IP> --source 漫画源.yaml --key "--https://example.com/chapter/456"
```

---

## 十、常见错误和解决

| 错误 | 原因 | 解决 |
|------|------|------|
| 正文无内容 | imageStyle 未设 FULL | 加 `imageStyle: FULL` |
| 图片 403 | 无 Referer | header 加 Referer 或 JS 拼接 |
| 目录顺序反了 | 网站倒序 | `-` 前缀反转 |
| 阅读模式是文本 | book.type 未设置 | 目录中设 `book.type = 64` |
| 图片不显示 | 懒加载 data-src | 用 `@data-original` 或 replaceRegex 替换 |
| 搜索返回空 | 编码问题 | searchUrl 加 `,{"charset":"utf-8"}` 或 `"gbk"` |
| 解析报错 | Java 对象歧义 | 字符串操作前 `String(result)` |
| Cloudflare 拦截 | 验证盾 | `loginCheckJs` + `startBrowserAwait` |
| 图片块错乱 | 加密重组 | 使用 `imageDecode` |
