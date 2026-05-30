# 模拟器前置设置

## 1. 连接模拟器

```bash
adb connect 127.0.0.1:<端口>
```

可以在设置中查看模拟器adb端口

验证连接：
```bash
adb devices
```

## 2. 转发 Legado 端口

Legado Web 服务需要转发两个端口：

```bash
adb -s <设备ID> forward tcp:1122 tcp:1122
adb -s <设备ID> forward tcp:1123 tcp:1123
```

- `1122` - HTTP 端口（Web 界面、保存书源）
- `1123` - WebSocket 端口（调试功能）