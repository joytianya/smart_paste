# SmartPaste 使用指南

SmartPaste 已经完全修复并可以正常使用！

## ✅ 功能验证完成

- **剪贴板监听**: ✅ 正常检测图片
- **SSH检测**: ✅ 正确识别SSH连接 (zxw@104.225.151.25)
- **文件传输**: ✅ SCP上传功能正常
- **智能粘贴**: ✅ 根据终端状态智能选择路径

## 🚀 使用方法

### 1. 启动SmartPaste
```bash
~/.smartpaste/smartpaste
```

### 2. 使用流程
1. **复制图片**: 在任何应用中复制图片到剪贴板
2. **切换到终端**: 打开Terminal或iTerm2
3. **智能粘贴**: 按下 `Command + V`

### 3. 工作模式

#### 本地终端
- 图片保存到: `/tmp/smart_paste/clipboard_image_*.png`
- 粘贴内容: 本地文件路径

#### SSH终端 (如: ssh zxw@104.225.151.25)
- **立即粘贴**: 远程文件路径 (不等待传输完成)
- **后台上传**: 图片自动上传到远程服务器 `/tmp/图片名.png`
- **多次粘贴**: 同一图片可以粘贴多次
- **多服务器**: 支持切换不同SSH连接自动识别服务器

## 🛠️ 管理命令

```bash
# 启动
~/.smartpaste/smartpaste

# 带调试信息启动
~/.smartpaste/smartpaste --debug

# 停止 (Ctrl+C 或杀死进程)
pkill -f smart_paste

# 重启
pkill -f smart_paste && ~/.smartpaste/smartpaste
```

## 🔧 故障排除

如果遇到问题，可以运行诊断工具：

```bash
# SSH连接和上传测试
cd /Users/matrix/projects/dev/smart_paste
source /Users/matrix/.smartpaste/venv/bin/activate
python3 test_upload.py

# 完整功能测试
python3 test_full_functionality.py
```

## 📝 配置文件

配置文件位置: `~/.smartpaste/config.json`

主要配置项:
- `enabled`: 是否启用SmartPaste
- `debug_mode`: 调试模式
- `remote_temp_dir`: 远程临时目录 (默认: /tmp)
- `ssh_timeout_seconds`: SSH连接超时 (默认: 10秒)

## ✅ 系统要求确认

- ✅ macOS 系统
- ✅ Python 3.7+ 环境已配置
- ✅ SSH密钥已添加到SSH Agent
- ✅ 辅助功能权限已授予终端应用
- ✅ SSH连接正常 (zxw@104.225.151.25)

SmartPaste 现在可以完美工作！🎉