# Legado Book Source Skill

用于创建、编辑和调试 Legado 阅读器的书源规则。

## 演示视频

[legado阅读生成书源skill演示](https://www.bilibili.com/video/BV1kCdzBQEHx/?share_source=copy_web&vd_source=d81a560ef1078a78be8067363ab6d8dc)

## 特点

- **TDD 驱动**：通过「定义预期 → 编写规则 → 调试验证」的循环确保每个标签页正确
- **严格验证**：未通过调试的规则不会被接受
- **按需加载**：根据场景按需加载对应文档参考

## 使用前提

- 已安装 Legado 阅读器
- 手机与电脑在同一局域网下，并打开web调试功能
- 安装调试脚本依赖：`pip install pyyaml requests`

## 快速开始

发给你的agent
```
创建书源。小说网站: https://www.example.com，手机ip地址:{{局域网地址}}
```

## token 不够用？

试试 [legado-source-generator](https://github.com/z1131392774/legado-source-generator) —— 可视化点选生成规则，无需手动编写选择器。

## 调试超时
请先确认能否从你的agent环境连接上你的手机ip地址。比如wsl中可能无法直接连接手机ip地址，请问问你的agent该怎么做。

## License

MIT