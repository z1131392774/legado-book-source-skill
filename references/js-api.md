# JS API 参考

> 阅读使用 [Rhino v1.8.1](https://github.com/mozilla/rhino) 作为 JavaScript 引擎以便于[调用 Java 类和方法](https://m.jb51.net/article/92138.htm)，查看 [ECMAScript 兼容性表格](https://mozilla.github.io/rhino/compat/engines.html)

> [Rhino 运行时](https://github.com/mozilla/rhino/blob/master/rhino/src/main/java/org/mozilla/javascript/ScriptRuntime.java)懒加载导入的 Java 类和方法

| 构造函数 | 函数 | 对象 | 调用类 | 简要说明 |
|------|-----|------|----|------|
| JavaImporter | importClass importPackage | | [ImporterTopLevel](https://github.com/mozilla/rhino/blob/master/rhino/src/main/java/org/mozilla/javascript/ImporterTopLevel.java) | 导入 Java 类到 JavaScript |
| | getClass | Packages java javax ... | [NativeJavaTopPackage](https://github.com/mozilla/rhino/blob/master/rhino/src/main/java/org/mozilla/javascript/NativeJavaTopPackage.java) | 默认导入 JavaScript 中的 Java 类 |
| JavaAdapter | | | [JavaAdapter](https://github.com/mozilla/rhino/blob/master/rhino/src/main/java//org/mozilla/javascript/JavaAdapter.java) | 继承 Java 类 |

> 注意 `java` 变量指向已经被阅读修改，如果想要调用 `java.*` 下的包，请使用 `Packages.java.*`

> 在书源规则中使用 `@js` `<js>` `{{}}` 可使用 JavaScript 调用阅读部分内置的类和方法

> 注意为了安全，阅读会屏蔽部分 java 类调用，见 [RhinoClassShutter](https://github.com/gedoor/legado/blob/master/modules/rhino/src/main/java/com/script/rhino/RhinoClassShutter.kt)

> 不同的书源规则中支持的调用的 Java 类和方法可能有所不同

> 注意使用 `const` 声明的变量不支持块级作用域，在循环里使用会出现值不变的问题，请改用 `var` 声明

## 内置变量

| 变量名 | 调用类 |
|------|-----|
| java | 当前类 |
| baseUrl | 当前 url, String |
| result | 上一步的结果 |
| book | [书籍类](https://github.com/gedoor/legado/blob/master/app/src/main/java/io/legado/app/data/entities/Book.kt) |
| rssArticle | [Article 类](https://github.com/gedoor/legado/blob/master/app/src/main/java/io/legado/app/data/entities/RssArticle.kt) |
| chapter | [章节类](https://github.com/gedoor/legado/blob/master/app/src/main/java/io/legado/app/data/entities/BookChapter.kt) |
| source | [基础书源类](https://github.com/gedoor/legado/blob/master/app/src/main/java/io/legado/app/data/entities/BaseSource.kt) |
| cookie | [cookie 操作类](https://github.com/gedoor/legado/blob/master/app/src/main/java/io/legado/app/help/http/CookieStore.kt) |
| cache | [缓存操作类](https://github.com/gedoor/legado/blob/master/app/src/main/java/io/legado/app/help/CacheManager.kt) |
| title | 章节当前标题 String |
| src | 请求返回的源码 |
| nextChapterUrl | 下一章节 url |
| isFromBookInfo | 是否为详情页刷新 |

## java 对象方法

函数带有默认值的函数会自动重载，可以不填。

### RssJsExtensions 独有函数

> 在订阅源 `shouldOverrideUrlLoading` 规则中使用
> 被下方 `SourceLoginJsExtensions` 类包含，也能使用这些函数
> 订阅添加跳转 url 拦截, js, 返回 true 拦截, js 变量 url, 可以通过 js 打开 url
> url 跳转拦截规则不能执行耗时操作

**调用阅读搜索：**
```js
/**
 * @param key 搜索关键词
 * @param searchScope 搜索作用域，为空时调用所有书源搜索
 */
// searchScope 作用域，形式为 `源名称::源地址`、或者 `,` 符号隔开的源分组名称
// 在书源调用时可写为 java.searchBook(key, source)，仅本书源进行搜索
java.searchBook(key: String, searchScope: String? = null)
```

**添加书架：**
```js
java.addBook(bookUrl: String)
```

**打开源界面：**
```js
/**
 * @param name "sort"打开订阅源分类界面、"rss"打开订阅源正文界面、"explore"打开书源发现界面、"search"打开书籍搜索界面、"login"打开源登录界面
 * @param url "sort"时为分类链接、"rss"时为正文链接、"explore"时为发现链接，"search"/"login"时该参数无意义
 *        特别说明，"sort"时 url 可以传序列化后的键值对用来打开多个分类界面
 * @param title 对应界面的标题，"search"时为搜索关键词，"login"时该参数无意义
 * @param origin 打开指定源界面的源地址
 */
java.open(name: String, url: String? = null, title: String? = null, origin: String? = null)
```

**展示图片：**
```js
java.showPhoto(src: String)
```

### SourceLoginJsExtensions 独有函数

> 只在 `登录界面按钮` 被触发、`界面按钮的回调` 事件、`发现按钮` 函数、`图片链接 click 键`、`购买规则` 中有效

```js
// 用内置浏览器打开本地 html
java.showBrowser(url: String, html: String, preloadJs: String? = null, config: String? = null)

// 复制文本到剪贴板
java.copyText(text: String)

// 实时更新登录界面用户信息，upLoginData(null) 会全部重置为默认值
java.upLoginData(data: Map<String, String?>?)

// 刷新登录界面
java.reLoginView(deltaUp: Boolean = false)

// 刷新书籍详情页
java.refreshBookInfo()

// 刷新书籍目录页
java.refreshBookToc()

// 刷新书籍正文内容
java.refreshContent()

// 清除 TTS 源的缓存，仅限 TTS 源的登录界面
java.clearTtsCache()

// 刷新发现，仅限发现按钮
java.refreshExplore()
```

[showBrowser 函数介绍](https://github.com/Luoyacheng/legado/wiki/java.showBrowser%E5%87%BD%E6%95%B0%E4%BB%8B%E7%BB%8D)

### AnalyzeUrl 部分函数

> js 中通过 java.调用，只在 `登录检查 JS` 规则中有效

```js
initUrl() // 重新解析 url，可以用于登录检测 js 登录后重新解析 url 重新访问
getHeaderMap().putAll(source.getHeaderMap(true)) // 重新设置登录头
getStrResponse(jsStr: String? = null, sourceRegex: String? = null) // 返回访问结果，文本类型
getResponse(): Response // 返回访问结果，网络朗读引擎采用此方法
```

### AnalyzeRule 部分函数

**获取文本/文本列表：**
```js
// mContent 待解析源代码，默认为当前页面
// isUrl 链接标识，默认为 false
java.getString(ruleStr: String?, mContent: Any? = null, isUrl: Boolean = false)
java.getStringList(ruleStr: String?, mContent: Any? = null, isUrl: Boolean = false)
```

**设置解析内容：**
```js
java.setContent(content: Any?, baseUrl: String? = null)
```

**获取 Element/Element 列表：**
> 如果要改变解析源代码，请先使用 `java.setContent`
```js
java.getElement(ruleStr: String)
java.getElements(ruleStr: String)
```

**重新搜索书籍/重新获取目录 url：**
> 只能在刷新目录之前使用，有些书源书籍地址和目录 url 会变
```js
java.reGetBook()
java.refreshTocUrl()
```

**变量存取：**
```js
java.get(key)
java.put(key, value)
```

### JS 扩展类 部分函数

**链接解析：**
```js
java.toURL(url: String, baseUrl: String? = null): JsURL
```

**获取 SystemWebView User-Agent：**
```js
java.getWebViewUA(): String
```

**网络请求：**
```js
// 普通请求
java.ajax(urlStr, callTimeout: Int? = null): String

// 并发访问网络，skipRateLimit 为 true 时不受源并发率限制
java.ajaxAll(urlList: Array<String>, skipRateLimit: Boolean = false): Array<StrResponse>

// ajaxTestAll 会忽略网络访问错误，错误类型由 callTime() 获取
// 错误码值：-1 超过设定时间, -2 超时, -3 域名错误, -4 连接被拒绝, -5 连接被重置, -6 SSL证书错误, -7 其它错误
// 无错误时 callTime() 为响应时间
java.ajaxTestAll(urlList: Array<String>, timeout: Int, skipRateLimit: Boolean = false): Array<StrResponse>

// 连接请求，返回 StrResponse 对象具有方法：body() code() message() headers() raw() toString() callTime()
java.connect(urlStr, header = null, callTimeout: Int? = null): StrResponse

// POST / GET / HEAD 请求
java.post(url: String, body: String, headerMap: Map<String, String>, timeout: Int? = null): Connection.Response
java.get(url: String, headerMap: Map<String, String>, timeout: Int? = null): Connection.Response
java.head(url: String, headerMap: Map<String, String>, timeout: Int? = null): Connection.Response

// 使用 webView 访问网络
java.webView(html: String?, url: String?, js: String?, cacheFirst: Boolean = false): String?

// 使用 webView 获取跳转 url
java.webViewGetOverrideUrl(html: String?, url: String?, js: String?, overrideUrlRegex: String, cacheFirst: Boolean = false, delayTime: Long = 0): String?

// 使用内置浏览器打开链接，可用于获取验证码、手动验证网站防爬
java.startBrowser(url: String, title: String, html: String? = null)

// 使用内置浏览器打开链接并等待网页结果
java.startBrowserAwait(url: String, title: String, refetchAfterSuccess: Boolean = false, html: String? = null): StrResponse
```

**调试：**
```js
java.log(msg)
java.logType(var)
```

**获取用户输入的验证码：**
```js
java.getVerificationCode(imageUrl)
```

**弹窗提示：**
```js
java.longToast(msg: Any?)
java.toast(msg: Any?)
```

**获取用户阅读配置：**
```js
java.getReadBookConfig(): String
java.getReadBookConfigMap(): Map<String, Any>
```

**获取用户主题配置：**
```js
java.getThemeConfig(): String
java.getThemeConfigMap(): Map<String, Any?>
```

**获取用户主题模式：**
```js
// @return 0 跟随系统，1 亮色主题，2 暗色主题，3 墨水屏
fun getThemeMode(): String
```

**从网络/本地读取 JavaScript 文件：**
```js
java.importScript(url)
// 相对路径支持 android/data/{package}/cache
java.importScript(relativePath)
java.importScript(absolutePath)
```

**缓存网络文件：**
```js
// 获取
java.cacheFile(url)
java.cacheFile(url, saveTime)
// 执行内容
eval(String(java.cacheFile(url)))
// 使缓存失效
cache.delete(java.md5Encode16(url))
```

**获取网络压缩文件里面指定路径的数据（可替换 Zip Rar 7Z）：**
```js
java.getStringContent(url: String, path: String): String
java.getStringContent(url: String, path: String, charsetName: String): String
java.getByteArrayContent(url: String, path: String): ByteArray?
```

**URI 编码：**
```js
java.encodeURI(str: String, enc: String = "UTF-8")
```

**Base64：**
> flags 参数可省略，默认 Base64.NO_WRAP，查看 [flags 参数说明](https://blog.csdn.net/zcmain/article/details/97051870)
```js
java.base64Decode(str: String)
java.base64Decode(str: String, charset: String)
java.base64DecodeToByteArray(str: String, flags: Int)
java.base64Encode(str: String, flags: Int)
```

**ByteArray：**
```js
// Str 转 Bytes
java.strToBytes(str: String)
java.strToBytes(str: String, charset: String)
// Bytes 转 Str
java.bytesToStr(bytes: ByteArray)
java.bytesToStr(bytes: ByteArray, charset: String)
```

**Hex：**
```js
// HexString 解码为字节数组
java.hexDecodeToByteArray(hex: String)
// hexString 解码为 utf8String
java.hexDecodeToString(hex: String)
// utf8 编码为 hexString
java.hexEncodeToString(utf8: String)
```

**标识 id：**
```js
java.randomUUID()
java.androidId()
```

**繁简转换：**
```js
java.t2s(text: String): String  // 转简体
java.s2t(text: String): String  // 转繁体
```

**时间格式化：**
```js
java.timeFormatUTC(time: Long, format: String, sh: Int): String?
java.timeFormat(time: Long): String
```

**HTML 格式化：**
```js
java.htmlFormat(str: String): String
```

**文件操作：**
> 所有对于文件的读写删操作都是相对路径，只能操作阅读缓存 `android/data/{package}/cache/` 内的文件
```js
// 文件下载，url 用于生成文件名，返回文件路径
downloadFile(url: String): String
// 文件解压，zipPath 为压缩文件路径，返回解压路径
unArchiveFile(zipPath: String): String
unzipFile(zipPath: String): String
unrarFile(zipPath: String): String
un7zFile(zipPath: String): String
// 文件夹内所有文件读取
getTxtInFolder(unzipPath: String): String
// 读取文本文件
readTxtFile(path: String): String
// 删除文件
deleteFile(path: String)
```

### JS 加解密类

> 提供在 JavaScript 环境中快捷调用 crypto 算法的函数，由 [hutool-crypto](https://www.hutool.cn/docs/#/crypto/%E6%A6%82%E8%BF%B0) 实现
> 由于兼容性问题，hutool-crypto 当前版本为 5.8.22
> 注意：如果输入的参数不是 Utf8String，可先调用 `java.hexDecodeToByteArray` / `java.base64DecodeToByteArray` 转成 ByteArray

**对称加密：**
```js
// 创建 Cipher (key, iv 支持 ByteArray|Utf8String)
java.createSymmetricCrypto(transformation, key, iv)

// 解密加密 (data 支持 ByteArray|Base64String|HexString|InputStream)
cipher.decrypt(data)        // 解密为 ByteArray
cipher.decryptStr(data)     // 解密为 String
cipher.encrypt(data)        // 加密为 ByteArray
cipher.encryptBase64(data)  // 加密为 Base64 字符
cipher.encryptHex(data)     // 加密为 HEX 字符
```

**非对称加密：**
```js
// 创建 Cipher (key 支持 ByteArray|Utf8String)
java.createAsymmetricCrypto(transformation)
  .setPublicKey(key)
  .setPrivateKey(key)

// 解密加密 (data 支持 ByteArray|Base64String|HexString|InputStream)
cipher.decrypt(data, usePublicKey: Boolean? = true)
cipher.decryptStr(data, usePublicKey: Boolean? = true)
cipher.encrypt(data, usePublicKey: Boolean? = true)
cipher.encryptBase64(data, usePublicKey: Boolean? = true)
cipher.encryptHex(data, usePublicKey: Boolean? = true)
```

**签名：**
```js
// 创建 Sign (key 支持 ByteArray|Utf8String)
java.createSign(algorithm)
  .setPublicKey(key)
  .setPrivateKey(key)

// 签名 (data 支持 ByteArray|InputStream|String)
sign.sign(data)      // 签名输出 ByteArray
sign.signHex(data)   // 签名输出 HexString
```

**摘要：**
```js
java.digestHex(data: String, algorithm: String): String?
java.digestBase64Str(data: String, algorithm: String): String?
```

**MD5：**
```js
java.md5Encode(str: String)
java.md5Encode16(str: String)
```

**HMac：**
```js
java.HMacHex(data: String, algorithm: String, key: String): String
java.HMacBase64(data: String, algorithm: String, key: String): String
```

**跳转外部链接/应用：**
```js
// 跳转外部链接，传入 http 链接或者 scheme 跳转到浏览器或其他应用
// 指定 mimeType，可以跳转指定类型应用，例如（video/*）
java.openUrl(url: String, mimeType: String = null)
```

**视频播放器函数：**
```js
/**
 * @param url 视频播放链接
 * @param title 视频的标题
 * @param isFloat 是否悬浮窗打开
 */
java.openVideoPlayer(url: String, title: String, isFloat: Boolean = false)
```

## book 对象

### 属性

> 使用方法：在 js 中或 `{{}}` 中使用 book.属性的方式即可获取。如在正文内容后加上 `##{{book.name+"正文卷"+title}}` 可以净化 书名+正文卷+章节名称（如 我是大明星正文卷第二章我爸是豪门总裁）这一类的字符。

```js
bookUrl              // 详情页 Url（本地书源存储完整文件路径）
tocUrl               // 目录页 Url（toc=table of Contents）
origin               // 书源 URL（默认 BookType.local）
originName           // 书源名称 or 本地书籍文件名
name                 // 书籍名称（书源获取）
author               // 作者名称（书源获取）
kind                 // 分类信息（书源获取）
customTag            // 分类信息（用户修改）
coverUrl             // 封面 Url（书源获取）
customCoverUrl       // 封面 Url（用户修改）
intro                // 简介内容（书源获取）
customIntro          // 简介内容（用户修改）
charset              // 自定义字符集名称（仅适用于本地书籍）
type                 // 0:text 1:audio
group                // 自定义分组索引号
latestChapterTitle   // 最新章节标题
latestChapterTime    // 最新章节标题更新时间
lastCheckTime        // 最近一次更新书籍信息的时间
lastCheckCount       // 最近一次发现新章节的数量
totalChapterNum      // 书籍目录总数
durChapterTitle      // 当前章节名称
durChapterIndex      // 当前章节索引
durChapterPos        // 当前阅读的进度（首行字符的索引位置）
durChapterTime       // 最近一次阅读书籍的时间（打开正文的时间）
canUpdate            // 刷新书架时更新书籍信息
order                // 手动排序
originOrder          // 书源排序
variable             // 自定义书籍变量信息（用于书源规则检索书籍信息）
```

### 函数

**自定义书籍变量存取：**
```js
book.putVariable(key: String, variable: String?)
book.getVariable(key: String): String?
```

## chapter 对象

### 属性

> 使用方法：在 js 中或 `{{}}` 中使用 chapter.属性的方式即可获取。如在正文内容后加上 `##{{chapter.title+chapter.index}}` 可以净化 章节标题+序号（如 第二章 天仙下凡2）这一类的字符。

```js
url          // 章节地址
title        // 章节标题
baseUrl      // 用来拼接相对 url
bookUrl      // 书籍地址
index        // 章节序号
resourceUrl  // 音频真实 URL
tag          //
start        // 章节起始位置
end          // 章节终止位置
variable     // 变量
```

### 函数

**自定义章节变量存取：**
```js
chapter.putVariable(key: String, variable: String?)
chapter.getVariable(key: String): String?
// 在函数回调或登录界面等地方调用，chapter 自身不会进行保存，需要调用 chapter.update()
```

**章节信息存储：**
```js
chapter.putLyric(value: String?)   // 存储音频章节歌词
chapter.putImgUrl(value: String?)  // 存储章节图标链接，比如标题上的段评图标链接
```

## source 对象

**获取书源 url：**
```js
source.getKey()
```

**书源变量存取：**
```js
source.putVariable(variable: String?)
source.getVariable()
```

**自定义书源变量存取：**
```js
source.put(key: String, variable: String?)
source.get(key: String): String?
```

**登录头操作：**
```js
source.getLoginHeader()                   // 获取登录头
source.getLoginHeaderMap().get(key: String) // 获取登录头某一键值
source.putLoginHeader(header: String)     // 保存登录头
source.removeLoginHeader()                // 清除登录头
```

**用户登录信息操作：**
> 使用 `登录UI` 规则，并成功登录，阅读自动加密保存登录UI规则中除 type 为 button 的信息
```js
source.getLoginInfo()                     // login 函数获取登录信息
source.getLoginInfoMap().get(key: String) // login 函数获取登录信息键值
source.removeLoginInfo()                  // 清除登录信息
source.putLoginInfo()                     // login 函数存放登录信息（在登录界面时请调用 java.upLoginData）
```

**书源缓存刷新：**
```js
source.refreshExplore()  // 刷新发现
source.refreshJSLib()    // 刷新 jslib
```

## cookie 对象

```js
cookie.getCookie(url: String)           // 获取全部 cookie
cookie.getKey(url: String, key: String)  // 获取 cookie 某一键值
cookie.setCookie(url: String, cookie: String)     // 设置 cookie
cookie.replaceCookie(url: String, cookie: String)  // 替换 cookie
cookie.removeCookie(url: String)         // 删除 cookie
cookie.setWebCookie(url: String, cookie: String)  // 设置内置浏览器 cookie
```

## cache 对象

> saveTime 单位：秒，可省略
> 保存至数据库和缓存文件（50M），保存的内容较大时请使用 `getFile` / `putFile`

```js
cache.put(key: String, value: String, saveTime: Int = 0)  // 保存，saveTime 为 0 时无过期时间
cache.get(key: String, onlyDisk: Boolean = false): String? // 读取数据库，onlyDisk 为 true 时只从磁盘读取
cache.delete(key: String)                   // 删除
cache.putFile(key: String, value: String, saveTime: Int)  // 缓存文件内容
cache.getFile(key: String): String?          // 读取文件内容
cache.putMemory(key: String, value: Any)     // 保存到内存
cache.getFromMemory(key: String): Any?       // 读取内存
cache.deleteMemory(key: String)              // 删除内存
```

## URL 选项参考

URL 末尾以 `,{JSON}` 追加行内选项，格式如 `https://example.com/page,{"webView":true}`。

| 选项 | 类型 | 说明 |
|------|------|------|
| `webView` | bool | `true` 时使用 WebView 加载页面 |
| `webJs` | string | WebView 加载完成后执行的 JS |
| `webViewDelayTime` | number | 页面加载后等待延迟（毫秒） |
| `method` | string | 请求方法：`POST` / `GET` / `HEAD` |
| `charset` | string | 编码，如 `utf-8`、`gbk` |
| `retry` | number | 重试次数 |
| `header` | object | 自定义请求头，如 `{"User-Agent":"..."}` |
| `headers` | array | 同上，数组格式 |
| `body` | string | POST 请求体 |
| `js` | string | 访问前执行 JS，结果替换 URL |
| `bodyJs` | string | 获取响应后执行 JS，结果替换 body |
| `dnsIp` | string | 自定义 DNS 解析 IP |
| `type` | string | 资源类型标识 |
| `serverID` | number | 服务器 ID |

**js 参数示例**（访问前处理 URL）：

```
https://www.baidu.com,{"js":"java.headerMap.put('xxx', 'yyy')"}
https://www.baidu.com,{"js":"java.url=java.url+'yyyy'"}
```

**bodyJs 参数示例**（响应后处理）：

```
https://www.baidu.com,{"bodyJs":"if(result)'这里的文本作为访问返回的响应体body'else result"}
```

**dnsIp 参数示例**（强制指定 IP）：

```
https://dns.google,{"dnsIp":"8.8.8.8"}
```
