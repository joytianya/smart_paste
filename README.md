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