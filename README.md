# Legado Book Source Skill

用于创建、编辑和调试 Legado 阅读器的书源规则。

## 特点

- **TDD 驱动**：通过「定义预期 → 编写规则 → 调试验证」的循环确保每个标签页正确
- **严格验证**：未通过调试的规则不会被接受
- **按需加载**：根据场景按需加载对应文档参考

## 使用前提

- 已安装 Legado 阅读器
- 手机与电脑在同一网络
- 安装调试脚本依赖：`pip install pyyaml requests`

## 快速开始

1. 复制模板创建书源文件
2. 按 TDD 循环填写搜索/发现 → 详情 → 目录 → 正文
3. 每个标签页完成后运行调试脚本验证

## token 不够用？

试试 [legado-source-generator](https://github.com/z1131392774/legado-source-generator) —— 可视化点选生成规则，无需手动编写选择器。

## License

MIT