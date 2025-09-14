# SmartPaste - 智能剪贴板工具

**macOS终端智能图片粘贴工具** - 自动识别本地/SSH环境，智能处理图片粘贴。

## 🎯 功能特点

- **智能环境检测** - 自动识别本地终端和SSH连接
- **即时路径粘贴** - 无需等待传输，立即粘贴文件路径  
- **后台传输** - 异步上传文件，不阻塞终端操作
- **多服务器支持** - 自动识别不同SSH连接，智能切换服务器
- **重复传输优化** - 检测服务器文件存在，避免重复上传
- **多终端兼容** - 支持Terminal.app、iTerm2等主流终端

## 📋 系统要求

- **操作系统**: macOS 10.14+
- **Python**: 3.7+
- **终端应用**: Terminal.app, iTerm2, 或其他兼容终端
- **SSH配置**: 已配置SSH密钥认证

## 🚀 快速安装

### 自动安装（推荐）

```bash
# 1. 下载项目
git clone git@github.com:joytianya/smart_paste.git
cd smart_paste

# 2. 运行安装脚本
./install.sh
```

### 手动安装

```bash
# 1. 创建安装目录
mkdir -p ~/.smartpaste

# 2. 复制文件
cp -r * ~/.smartpaste/

# 3. 创建虚拟环境
cd ~/.smartpaste
python3 -m venv venv
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 创建启动器
cat > ~/.smartpaste/smartpaste << 'EOF'
#!/bin/bash
INSTALL_DIR="$HOME/.smartpaste"
source "$INSTALL_DIR/venv/bin/activate"
cd "$INSTALL_DIR"
exec python3 smart_paste.py "$@"
EOF

chmod +x ~/.smartpaste/smartpaste

# 6. 添加到PATH（可选）
echo 'export PATH="$HOME/.smartpaste:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

## ⚙️ 权限配置

SmartPaste需要**辅助功能权限**才能监听键盘事件：

### 授权步骤：
1. **系统偏好设置** > **安全性与隐私** > **隐私**
2. 选择 **辅助功能**
3. 点击 **+** 添加以下应用：
   - **Terminal.app** (如果使用Terminal)
   - **iTerm.app** (如果使用iTerm2) 
   - **Python** (可能位于 `/usr/bin/python3` 或 `/opt/homebrew/bin/python3`)

### SSH密钥配置：
```bash
# 生成SSH密钥（如果没有）
ssh-keygen -t ed25519 -C "your-email@example.com"

# 添加到SSH Agent
ssh-add ~/.ssh/id_ed25519

# 复制公钥到服务器
ssh-copy-id user@your-server.com
```

## 🎮 使用方法

### 启动SmartPaste
```bash
# 方法1: 使用启动器
~/.smartpaste/smartpaste

# 方法2: 直接运行Python
~/.smartpaste/venv/bin/python3 ~/.smartpaste/smart_paste.py

# 带调试信息启动
~/.smartpaste/smartpaste --debug
```

### 基本使用流程

1. **启动SmartPaste** - 在终端运行启动命令
2. **复制图片** - 在任何应用中复制图片到剪贴板
3. **智能粘贴** - 在终端中按 `Command + V`

### 工作模式

#### 🏠 本地模式
```bash
# 在本地终端
$ # 复制图片后按 Command+V
$ /tmp/smart_paste/clipboard_image_20241214_130147_b4b94f23.png
```

#### 🌐 SSH模式  
```bash
# SSH连接到服务器
$ ssh user@server.com

# 复制图片后按 Command+V（立即粘贴路径）
user@server:~$ /tmp/clipboard_image_20241214_130147_b4b94f23.png
# 文件在后台自动上传到服务器
```

## 🔧 高级功能

### 多服务器支持
```bash
# 服务器A
$ ssh user@server-a.com
user@server-a:~$ # Command+V → /tmp/image.png (上传到server-a)

# 切换到服务器B  
$ ssh admin@server-b.com
admin@server-b:~$ # Command+V → /tmp/image.png (上传到server-b)
```

### 重复上传优化
- 自动检测服务器端文件是否已存在
- 跳过重复传输，节省带宽和时间
- 支持同一图片多次粘贴不同路径

### 配置文件
编辑 `~/.smartpaste/config.json`:
```json
{
  "enabled": true,
  "debug_mode": false,
  "local_temp_dir": "/tmp/smart_paste",
  "remote_temp_dir": "/tmp", 
  "max_file_size_mb": 100,
  "ssh_timeout_seconds": 10,
  "scp_retry_count": 3,
  "auto_create_remote_dirs": true,
  "cleanup_interval_hours": 24
}
```

## 🛠️ 管理命令

```bash
# 查看状态
ps aux | grep smart_paste

# 停止SmartPaste  
pkill -f smart_paste
# 或在SmartPaste终端按 Ctrl+C

# 重启
pkill -f smart_paste && ~/.smartpaste/smartpaste

# 查看日志
tail -f ~/.smartpaste/smart_paste.log

# 清理临时文件
rm -rf /tmp/smart_paste/*
```

## 🐛 故障排除

### 权限问题
```bash
# 检查辅助功能权限
~/.smartpaste/smartpaste
# 如果提示权限问题，按照上述权限配置步骤操作
```

### SSH连接问题
```bash
# 测试SSH连接
ssh user@your-server.com

# 检查SSH Agent
ssh-add -l

# 重新添加密钥
ssh-add ~/.ssh/id_ed25519
```

### 诊断工具
```bash
# SSH检测测试
source ~/.smartpaste/venv/bin/activate && python3 test_upload.py

# 完整功能测试  
source ~/.smartpaste/venv/bin/activate && python3 test_full_functionality.py

# 进程树调试
source ~/.smartpaste/venv/bin/activate && python3 debug_process_tree.py
```

### 常见问题

**Q: Command+V没有反应？**
- 检查辅助功能权限是否已授予
- 确认SmartPaste正在运行 (`ps aux | grep smart_paste`)
- 确认在支持的终端应用中使用

**Q: SSH上传失败？**  
- 检查SSH密钥配置 (`ssh-add -l`)
- 测试手动SSH连接 (`ssh user@server`)
- 查看详细错误信息 (`~/.smartpaste/smartpaste --debug`)

**Q: 启动脚本卡住？**
- 使用Python直接运行: `~/.smartpaste/venv/bin/python3 ~/.smartpaste/smart_paste.py`
- 检查虚拟环境是否正确创建

## 🔍 技术架构

### SSH连接识别机制
1. **进程树分析** - 从当前shell向上遍历找到SSH进程
2. **命令解析** - 解析SSH命令行参数提取连接信息  
3. **全局检测** - 扫描系统所有SSH进程作为备用方法
4. **服务器标识** - 生成 `user@host:port` 唯一标识符

### 智能传输优化
- **即时响应** - 立即粘贴预期路径，后台异步传输
- **连接复用** - 智能复用SSH连接，避免重复建连  
- **文件检测** - 检查远程文件存在性，跳过重复传输
- **多线程** - 后台传输不阻塞主界面操作

## 📁 项目结构
```
smart_paste/
├── README.md                 # 项目说明文档
├── USAGE.md                  # 使用指南  
├── install.sh                # 自动安装脚本
├── requirements.txt          # Python依赖包
├── smart_paste.py           # 主程序入口
├── clipboard_monitor.py     # 剪贴板监听模块
├── terminal_detector.py     # 终端/SSH检测模块  
├── file_transfer.py         # 文件传输模块
├── keyboard_handler.py      # 键盘事件处理模块
├── config_manager.py        # 配置管理模块
└── tests/                   # 测试脚本目录
    ├── test_upload.py       # 传输功能测试
    ├── test_full_functionality.py  # 完整功能测试
    └── debug_process_tree.py # 进程调试工具
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境搭建
```bash
git clone git@github.com:joytianya/smart_paste.git
cd smart_paste
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 运行测试
```bash
# 功能测试
python3 test_full_functionality.py

# SSH传输测试
python3 test_upload.py
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [paramiko](https://github.com/paramiko/paramiko) - SSH客户端库
- [pynput](https://github.com/moses-palmer/pynput) - 键盘监听库  
- [psutil](https://github.com/giampaolo/psutil) - 进程管理库
- [pyobjc](https://github.com/ronaldoussoren/pyobjc) - macOS系统集成

---

**SmartPaste** - 让终端图片分享变得简单高效！ 🚀

SmartPaste 是一个强大的 macOS 工具，能够智能识别剪贴板中的图片并自动处理：
- 🖼️ **本地模式**：将图片保存到本地 `/tmp` 目录并粘贴路径
- 🌐 **远程模式**：自动检测 SSH 连接，通过 SCP 上传图片到远程服务器并粘贴远程路径
- 📝 **文本兼容**：完全兼容正常的文本粘贴功能
- ⚡ **快捷操作**：只需 `Command + V`，一键完成所有操作

## 功能特性

- ✅ 支持所有主流终端应用（Terminal.app, iTerm2, Hyper 等）
- ✅ 自动检测 SSH 连接状态和服务器信息
- ✅ 支持多种 SSH 认证方式（密钥、密码、SSH Agent）
- ✅ 智能文件管理和临时文件清理
- ✅ 完全兼容现有的粘贴工作流
- ✅ 详细的配置选项和日志记录
- ✅ 权限安全设计

## 系统要求

- macOS 10.15+ (推荐 macOS 12+)
- Python 3.8+
- 终端应用需要授予辅助功能权限

## 安装指南

### 1. 克隆项目

```bash
git clone <repository-url>
cd smart_paste
```

### 2. 安装 Python 依赖

```bash
# 推荐使用虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 授予辅助功能权限

**重要步骤**：SmartPaste 需要辅助功能权限才能监听全局快捷键。

1. 打开 **系统偏好设置** > **安全性与隐私** > **隐私**
2. 选择左侧的 **辅助功能**
3. 点击 🔒 解锁（需要管理员密码）
4. 点击 **+** 按钮添加以下应用：
   - **Terminal.app** （如果使用 Terminal）
   - **iTerm.app** （如果使用 iTerm2）
   - **Python** 或 **Your Terminal App**

### 4. 配置 SSH（可选）

确保你的 SSH 配置正常工作：

```bash
# 测试 SSH 连接
ssh your-server

# 确保 SSH 密钥认证工作正常
ssh-add -l
```

## 使用方法

### 启动 SmartPaste

```bash
# 基本启动
python3 smart_paste.py

# 调试模式启动
python3 smart_paste.py --debug

# 指定配置目录
python3 smart_paste.py --config-dir ~/.my-smartpaste
```

### 基本使用流程

1. **启动程序**：运行 `python3 smart_paste.py`
2. **复制图片**：在任何应用中复制图片到剪贴板
3. **切换到终端**：打开 Terminal.app 或 iTerm2
4. **智能粘贴**：按 `Command + V`

### 使用场景

#### 场景 1：本地使用
```bash
# 在本地终端中
$ pwd
/Users/username/projects

# 复制图片后按 Cmd+V，自动粘贴：
$ /tmp/clipboard_image_20231214_143022_a1b2c3d4.png
```

#### 场景 2：SSH 远程使用
```bash
# SSH 连接到远程服务器
$ ssh user@remote-server

# 复制图片后按 Cmd+V，自动上传并粘贴：
user@remote-server:~$ /tmp/clipboard_image_20231214_143022_a1b2c3d4.png
```

#### 场景 3：文本粘贴（完全兼容）
```bash
# 复制文本后按 Cmd+V，正常粘贴：
$ echo "Hello World"
```

## 配置选项

SmartPaste 的配置文件位于 `~/.smartpaste/config.json`：

```json
{
  "enabled": true,
  "debug_mode": false,
  "local_temp_dir": "/tmp",
  "remote_temp_dir": "/tmp",
  "max_file_size_mb": 100,
  "cleanup_interval_hours": 24,
  "terminal_apps": [
    "Terminal",
    "iTerm2", 
    "iTerm",
    "Hyper",
    "Alacritty",
    "Wezterm"
  ],
  "paste_cooldown_ms": 500,
  "ssh_timeout_seconds": 10,
  "scp_retry_count": 3,
  "auto_create_remote_dirs": true,
  "clipboard_check_interval_ms": 500,
  "keyboard_listener_enabled": true,
  "compress_images": false,
  "max_image_width": 2048,
  "max_image_height": 2048
}
```

### 主要配置说明

- `local_temp_dir`: 本地临时文件存储目录
- `remote_temp_dir`: 远程服务器临时文件存储目录  
- `max_file_size_mb`: 最大文件大小限制（MB）
- `terminal_apps`: 支持的终端应用名称列表
- `ssh_timeout_seconds`: SSH 连接超时时间
- `scp_retry_count`: SCP 上传重试次数

## 命令行选项

```bash
# 显示帮助
python3 smart_paste.py --help

# 查看版本
python3 smart_paste.py --version  

# 显示状态
python3 smart_paste.py --status

# 调试模式
python3 smart_paste.py --debug

# 指定配置目录
python3 smart_paste.py --config-dir ~/.my-config
```

## 故障排除

### 常见问题

#### 1. "Accessibility permissions not granted" 错误

**原因**：未授予辅助功能权限

**解决方法**：
1. 打开系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能
2. 添加你的终端应用和 Python
3. 重启 SmartPaste

#### 2. SSH 连接失败

**原因**：SSH 配置或认证问题

**解决方法**：
```bash
# 检查 SSH 配置
cat ~/.ssh/config

# 测试 SSH 连接
ssh -v your-server

# 检查 SSH Agent
ssh-add -l

# 添加密钥到 SSH Agent
ssh-add ~/.ssh/id_rsa
```

#### 3. 图片上传失败

**原因**：网络问题、权限问题或文件过大

**解决方法**：
- 检查网络连接
- 确认远程目录权限：`mkdir -p /tmp && chmod 755 /tmp`
- 检查文件大小是否超过限制
- 查看日志：`~/.smartpaste/logs/smartpaste_main.log`

#### 4. 键盘监听不工作

**原因**：权限问题或应用冲突

**解决方法**：
```bash
# 检查权限
python3 keyboard_handler.py

# 重启 SmartPaste
# 检查是否有其他键盘监听程序冲突
```

### 调试技巧

#### 启用调试模式
```bash
python3 smart_paste.py --debug
```

#### 查看日志
```bash
# 主日志
tail -f ~/.smartpaste/logs/smartpaste_main.log

# 查看所有日志文件
ls ~/.smartpaste/logs/
```

#### 测试各个模块
```bash
# 测试剪贴板监听
python3 clipboard_monitor.py

# 测试终端检测  
python3 terminal_detector.py

# 测试文件传输
python3 file_transfer.py

# 测试键盘处理
python3 keyboard_handler.py
```

## 项目结构

```
smart_paste/
├── README.md                 # 说明文档
├── requirements.txt          # Python 依赖
├── smart_paste.py           # 主程序
├── clipboard_monitor.py     # 剪贴板监听器
├── terminal_detector.py     # 终端状态检测器
├── file_transfer.py         # 文件传输模块
├── keyboard_handler.py      # 键盘处理器
└── config_manager.py        # 配置管理器
```

## 高级用法

### 自定义终端应用支持

如果你使用的终端应用不在默认支持列表中，可以在配置文件中添加：

```json
{
  "terminal_apps": [
    "Terminal",
    "iTerm2",
    "YourCustomTerminal"
  ]
}
```

### 自定义 SSH 配置

SmartPaste 会自动读取 `~/.ssh/config` 中的配置：

```bash
# ~/.ssh/config
Host myserver
    HostName example.com
    User myuser
    Port 2222
    IdentityFile ~/.ssh/my_key
```

### 服务化运行

创建 Launch Agent 实现开机自启：

```bash
# 创建 plist 文件
cat > ~/Library/LaunchAgents/com.smartpaste.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.smartpaste</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/smart_paste.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF

# 加载服务
launchctl load ~/Library/LaunchAgents/com.smartpaste.plist
```

## 安全考虑

- SmartPaste 只监听 Command+V 快捷键，不记录其他键盘输入
- 传输的文件存储在临时目录，会定期清理
- SSH 连接使用系统现有的认证配置
- 不会保存或传输敏感信息

## 许可证

MIT License - 详见 LICENSE 文件

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.0.0
- 🎉 初始版本发布
- ✅ 支持本地和远程图片粘贴
- ✅ 自动 SSH 检测和文件传输
- ✅ 完整的配置系统
- ✅ 多终端应用支持

## 技术支持

如果遇到问题：

1. 查看本文档的故障排除部分
2. 检查 `~/.smartpaste/logs/` 中的日志文件  
3. 在 GitHub Issues 中搜索相似问题
4. 提交新的 Issue 并包含详细信息

---

**享受智能粘贴的便利吧！** 🚀