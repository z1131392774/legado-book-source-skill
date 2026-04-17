# 发现地址规则

## 格式一：简单发现页

`名称::URL`，URL 可用 `&&` 或 `\n` 隔开：

```
月票榜::https://www.qidian.com/rank/yuepiao?page={{page}}
```

## 格式二：JSON 数组（复杂发现页）

多级分类、排行榜、推荐位混合等场景优先使用格式二：

```json
[
  {
    "title": "今日限免",
    "url": "https://app-cdn.jjwxc.net/bookstore/getFullPage?channel=novelfree",
    "style": { "layout_flexGrow": 1 }
  },
  {
    "title": "频道金榜",
    "url": "http://app-cdn.jjwxc.net/bookstore/getFullPage?channelBody=...&versionCode=148",
    "style": {
      "layout_flexGrow": 0, "layout_flexShrink": 1,
      "layout_alignSelf": "auto", "layout_flexBasisPercent": -1,
      "layout_wrapBefore": true
    }
  },
  { "title": "分类", "url": "", "style": { "layout_flexBasisPercent": 1, "layout_flexGrow": 1 } },
  { "title": "幻想未来", "url": "http://app-cdn.jjwxc.net/bookstore/getFullPage?channelBody=..." }
]
```

其中"分类"项用于分隔。

### style 属性

5 个样式属性：`layout_flexGrow`、`layout_flexShrink`、`layout_alignSelf`、`layout_flexBasisPercent`、`layout_wrapBefore`

→ 详见 [Flexbox 布局](https://www.jianshu.com/p/3c471953e36d)

## 翻页

- `page` 为翻页标识，初值为 1
- 计算页码：`{{(page-1)*20}}`
- 第一页无页数：① `{{page - 1 == 0 ? "": page}}`  ② `<,{{page}}>`
- 支持相对 URL

## 发现页按钮类型

除标准发现项外，还可添加交互控件：

```json
[
  { "title": "关键词", "type": "text" },
  { "title": "xxx", "url": "", "style": { "layout_flexGrow": 0 } }
]
```

支持类型：`url`、`text`、`button`、`toggle`、`select`

## infoMap 变量

读写发现页按钮的交互状态：

```javascript
var input = infoMap["关键词"];       // 读取
infoMap["关键词"] = "系统";          // 修改
infoMap.set({"键": "值"});           // 替换
infoMap.save();                      // 保存
```