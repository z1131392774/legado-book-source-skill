# 登录与回调

## 登录 UI

不使用内置 webView 登录网站时，需要使用 `登录URL` 规则实现登录逻辑，可使用 `登录检查JS` 检查登录结果。

> 版本 20221113 重要更改：按钮支持调用 `登录URL` 规则里面的函数，必须实现 `login` 函数
> 版本 20260131：文本输入类型支持 `action` 键，在用户完成输入后执行 js 函数，用来判断用户输入内容并进行提示

文本类输入需用户主动打勾保存，或调用 `java.upLoginData` 更新。

### 按钮类型

所有按钮类型：`"text"`、`"password"`、`"button"`、`"toggle"`、`"select"`

### 规则填写示范

```json
[
    {
        "name": "telephone",
        "type": "text",
        "default": "123"
    },
    {
        "name": "password",
        "type": "password",
        "action": "checkPassword()"
    },
    {
        "name": "注册",
        "type": "button",
        "action": "http://www.yooike.com/xiaoshuo/#/register?title=%E6%B3%A8%E5%86%8C"
    },
    {
        "name": "获取验证码",
        "type": "button",
        "action": "getVerificationCode()",
        "style": {
            "layout_flexGrow": 0,
            "layout_flexShrink": 1,
            "layout_alignSelf": "auto",
            "layout_flexBasisPercent": -1,
            "layout_wrapBefore": false
        }
    },
    {
        "name": "评论开关",
        "type": "toggle",
        "chars": ["❎", "☑️"],
        "default": "☑️"
    },
    {
        "name": "显示书名",
        "viewName": "book?.name||'未获取到书名'",
        "type": "button"
    },
    {
        "name": "选择排序",
        "viewName": "'排序按钮别名'",
        "type": "select",
        "chars": ["月票", "人气"],
        "default": "人气",
        "style": {
            "layout_flexGrow": 0,
            "layout_flexBasisPercent": -1,
            "layout_justifySelf": "flex_end"
        }
    }
]
```

## 登录 URL

可填写登录链接或者实现登录 UI 的登录逻辑的 JavaScript。

变量 `isLongClick` 为 `true` 时表示为按钮长按点击。

### 示范填写

```javascript
// 必须实现的 login 函数
function login() {
    java.log("模拟登录请求");
    java.log(source.getLoginInfoMap());
}

// 登录 UI 按钮调用的函数
function getVerificationCode() {
    java.log("登录UI按钮：获取到手机号码" + result.get("telephone"))
}
```

### 获取登录信息

登录按钮函数获取登录信息：
```js
result.get("telephone")
```

login 函数获取登录信息：
```js
source.getLoginInfo()
source.getLoginInfoMap().get("telephone")
```

### source 登录相关方法

可在 js 内通过 `source.` 调用：

```js
login()                                              // 登录
getHeaderMap(hasLoginHeader: Boolean = false)         // 获取请求头 Map
getLoginHeader(): String?                             // 获取登录头字符串
getLoginHeaderMap(): Map<String, String>?             // 获取登录头 Map
putLoginHeader(header: String)                        // 保存登录头
removeLoginHeader()                                   // 清除登录头
setVariable(variable: String?)                        // 设置变量
getVariable(): String?                                // 获取变量
```

### AnalyzeUrl 相关函数

js 中通过 `java.` 调用：

```js
initUrl() // 重新解析 url，可以用于登录检测 js 登录后重新解析 url 重新访问
getHeaderMap().putAll(source.getHeaderMap(true)) // 重新设置登录头
getStrResponse(jsStr: String? = null, sourceRegex: String? = null) // 返回访问结果，文本类型
getResponse(): Response // 返回访问结果，调用登录后再调用这方法可以重新访问
```

## 登录检查（非 CF 场景）

`loginCheckJs` 位于书源基础选项卡，可用于检查登录结果（与过验证盾的用法区分）。

登录 UI 中描述了如何使用 `loginCheckJs` 检查登录结果。

> 关于 `loginCheckJs` 用于过 Cloudflare 等验证盾的用法，请参阅 `references/troubleshoot.md`。

## 回调操作

先启用事件监听按钮（`eventListener: true`），然后软件触发事件时会执行回调规则的 js 代码。

- 字符串变量 `result` 的值为事件对应内容
- 字符串变量 `event` 的值对应事件名称

### 事件列表

**可消费事件（返回 true 会阻止默认操作）：**

```js
"clickBookName"        // 点击详情页书名
"longClickBookName"    // 长按详情页书名
"clickAuthor"          // 点击详情页作者
"longClickAuthor"      // 长按详情页作者
"clickCustomButton"    // 点击书源自定义按钮
"longClickCustomButton" // 长按书源自定义按钮（只存在小说的正文界面）
"clickShareBook"       // 点击详情页分享按钮
"clickClearCache"      // 点击详情页清理缓存按钮
"clickCopyBookUrl"     // 点击详情页拷贝书籍 URL 按钮
"clickCopyTocUrl"      // 点击详情页拷贝目录 URL 按钮
"clickCopyPlayUrl"     // 音频、视频界面点击拷贝播放 URL 按钮
"clickBookLabel"       // 点击详情页标签
"longClickBookLabel"   // 长按详情页标签
```

**不可消费事件（回调结果无法阻止默认操作）：**

```js
"addBookShelf"         // 添加到书架
"delBookShelf"         // 移除书架
"saveRead"             // 保存阅读进度
"startRead"            // 开始阅读
"endRead"              // 结束阅读
"startShelfRefresh"    // 开始书架刷新
"endShelfRefresh"      // 结束书架刷新
```
