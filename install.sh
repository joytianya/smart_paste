#!/bin/bash

# SmartPaste 安装脚本
# 自动安装SmartPaste到系统

set -e

echo "🚀 SmartPaste 安装向导"
echo "========================="

# 检查macOS系统
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ 错误: SmartPaste只支持macOS系统"
    exit 1
fi

# 检查Python版本
python_version=$(python3 --version 2>/dev/null | awk '{print $2}' || echo "0.0.0")
required_version="3.7.0"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,7) else 1)" 2>/dev/null; then
    echo "❌ 错误: 需要Python 3.7或更高版本"
    echo "   当前版本: $python_version"
    echo "   请安装Python 3.7+: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python版本检查通过: $python_version"

# 设置安装目录
INSTALL_DIR="$HOME/.smartpaste"
BACKUP_DIR="$HOME/.smartpaste.backup.$(date +%Y%m%d_%H%M%S)"

# 备份现有安装
if [ -d "$INSTALL_DIR" ]; then
    echo "📦 发现现有安装，创建备份..."
    mv "$INSTALL_DIR" "$BACKUP_DIR"
    echo "   备份位置: $BACKUP_DIR"
fi

echo "📂 创建安装目录: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

echo "📋 复制项目文件..."
# 复制所有Python文件和配置
cp *.py "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"

# 复制或创建默认配置
if [ -f "config.json" ]; then
    cp config.json "$INSTALL_DIR/"
else
    cat > "$INSTALL_DIR/config.json" << 'EOF'
{
  "enabled": true,
  "debug_mode": false,
  "local_temp_dir": "/tmp/smart_paste",
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
EOF
fi

echo "🔨 创建Python虚拟环境..."
cd "$INSTALL_DIR"
python3 -m venv venv

echo "📦 激活虚拟环境并安装依赖..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "🔧 创建启动脚本..."
cat > smartpaste << 'EOF'
#!/bin/bash
# SmartPaste Launcher Script

INSTALL_DIR="$HOME/.smartpaste"

# 检查安装目录
if [ ! -d "$INSTALL_DIR" ]; then
    echo "❌ SmartPaste not installed in $INSTALL_DIR"
    exit 1
fi

# 激活虚拟环境
if [ ! -f "$INSTALL_DIR/venv/bin/activate" ]; then
    echo "❌ Virtual environment not found"
    exit 1
fi

source "$INSTALL_DIR/venv/bin/activate"
cd "$INSTALL_DIR"

# 检查Python脚本存在
if [ ! -f "smart_paste.py" ]; then
    echo "❌ smart_paste.py not found in $INSTALL_DIR"
    exit 1
fi

# 启动SmartPaste
exec python3 smart_paste.py "$@"
EOF

chmod +x smartpaste

echo "📁 创建本地临时目录..."
mkdir -p /tmp/smart_paste

echo ""
echo "🎉 SmartPaste 安装成功！"
echo "========================="
echo ""
echo "📍 安装位置: $INSTALL_DIR"
echo "🚀 启动命令: ~/.smartpaste/smartpaste"
echo ""
echo "⚠️  重要提醒："
echo "1. 需要授予辅助功能权限："
echo "   系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能"
echo "   添加: Terminal.app, iTerm.app, Python"
echo ""
echo "2. 确保SSH密钥已配置："
echo "   ssh-keygen -t ed25519"
echo "   ssh-add ~/.ssh/id_ed25519"
echo "   ssh-copy-id user@server"
echo ""
echo "📖 使用方法："
echo "   1. 启动: ~/.smartpaste/smartpaste"
echo "   2. 复制图片到剪贴板"
echo "   3. 在终端中按 Command+V"
echo ""

# 询问是否添加到PATH
read -p "🔗 是否添加到PATH以便全局使用? (y/N): " add_to_path

if [[ $add_to_path =~ ^[Yy]$ ]]; then
    # 检查shell类型
    if [[ "$SHELL" == *"zsh"* ]]; then
        shell_rc="$HOME/.zshrc"
    elif [[ "$SHELL" == *"bash"* ]]; then
        shell_rc="$HOME/.bashrc"
    else
        shell_rc="$HOME/.profile"
    fi
    
    if ! grep -q "smartpaste" "$shell_rc" 2>/dev/null; then
        echo "" >> "$shell_rc"
        echo "# SmartPaste" >> "$shell_rc"
        echo 'export PATH="$HOME/.smartpaste:$PATH"' >> "$shell_rc"
        echo "✅ 已添加到 $shell_rc"
        echo "   重启终端或运行: source $shell_rc"
        echo "   然后可以直接使用: smartpaste"
    else
        echo "ℹ️  PATH已存在SmartPaste配置"
    fi
fi

echo ""
echo "🎯 立即体验："
echo "   ~/.smartpaste/smartpaste"
echo ""
echo "📚 更多帮助: https://github.com/joytianya/smart_paste"