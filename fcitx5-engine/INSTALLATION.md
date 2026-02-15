# Fcitx5 输入法引擎 - 快速安装指南

## 一键安装

```bash
cd ~/dev/input-method/
chmod +x fcitx5-engine/scripts/install.sh
./fcitx5-engine/scripts/install.sh
```

## 后续步骤

1. **注销或重启系统**（应用环境变量）

2. **启动Fcitx5**：
   ```bash
   fcitx5 -d
   ```

3. **启动中文引擎**：
   ```bash
   ~/.local/share/fcitx5-chinese/start.sh
   ```

4. **配置输入法**：
   ```bash
   fcitx5-config-qt
   ```
   - 点击"添加输入法"
   - 选择"拼音"
   - 点击"确定"

5. **切换输入法**：`Ctrl + Space`

## 验证安装

打开任意文本编辑器，按 `Ctrl + Space` 切换到拼音输入法，输入拼音测试。

## 常见问题

### 引擎无法启动
```bash
tail -f /tmp/fcitx5-chinese-smart-engine.log
```

### 候选词不显示
```bash
fcitx5-remote -r
```

### 环境变量问题
注销或重启系统

---

详细文档请参考：[README.md](README.md)
