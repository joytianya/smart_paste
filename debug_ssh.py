#!/usr/bin/env python3
"""
SmartPaste SSH调试脚本
帮助诊断SSH环境下的粘贴问题
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# 添加SmartPaste模块路径
sys.path.insert(0, str(Path.home() / '.smartpaste'))

from terminal_detector import TerminalDetector
from clipboard_monitor import ClipboardMonitor  
from keyboard_handler import KeyboardHandler

def check_environment():
    """检查当前环境"""
    print("🔍 环境检查")
    print("=" * 40)
    
    # 检查终端应用
    detector = TerminalDetector()
    current_app = None
    
    try:
        script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
            end tell
            return frontApp
        '''
        
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True, timeout=2)
        
        if result.returncode == 0:
            current_app = result.stdout.strip()
            
    except Exception as e:
        print(f"❌ 获取当前应用失败: {e}")
    
    print(f"📱 当前应用: {current_app}")
    
    # 检查是否是终端应用
    terminal_apps = ['Terminal', 'iTerm2', 'iTerm', 'Hyper', 'Alacritty', 'Wezterm']
    is_terminal = current_app in terminal_apps if current_app else False
    print(f"🖥️  是否为终端: {'是' if is_terminal else '否'}")
    
    # 检查SSH连接
    conn_info = detector.get_current_connection_info()
    print(f"🔗 连接类型: {'SSH远程' if conn_info['is_ssh'] else '本地'}")
    if conn_info['is_ssh']:
        print(f"   👤 用户: {conn_info['username']}")
        print(f"   🌐 主机: {conn_info['hostname']}")
        print(f"   🔌 端口: {conn_info['port']}")
    
    print()
    return is_terminal, conn_info

def check_clipboard():
    """检查剪贴板内容"""
    print("📋 剪贴板检查")
    print("=" * 40)
    
    monitor = ClipboardMonitor()
    content, is_image = monitor.get_clipboard_content()
    
    if content:
        if is_image:
            print(f"🖼️  检测到图片: {content}")
            # 检查文件是否存在
            if os.path.exists(content):
                file_size = os.path.getsize(content)
                print(f"   📏 文件大小: {file_size} bytes")
            else:
                print(f"   ❌ 文件不存在")
        else:
            print(f"📝 检测到文本: {content[:50]}...")
    else:
        print("📭 剪贴板为空")
    
    print()
    return content, is_image

def check_permissions():
    """检查权限"""
    print("🔐 权限检查")
    print("=" * 40)
    
    handler = KeyboardHandler()
    has_permissions = handler.check_permissions()
    
    print(f"🔓 辅助功能权限: {'已授权' if has_permissions else '未授权'}")
    
    if not has_permissions:
        print("⚠️  需要授权辅助功能权限:")
        print("   1. 系统偏好设置 > 安全性与隐私 > 隐私")
        print("   2. 选择'辅助功能'")
        print("   3. 添加当前终端应用")
    
    print()
    return has_permissions

def simulate_paste_event():
    """模拟粘贴事件测试"""
    print("🧪 模拟粘贴测试")
    print("=" * 40)
    
    try:
        # 检查环境
        is_terminal, conn_info = check_environment()
        content, is_image = check_clipboard()
        has_permissions = check_permissions()
        
        if not is_terminal:
            print("❌ 当前不在终端应用中")
            return False
        
        if not has_permissions:
            print("❌ 没有辅助功能权限")
            return False
        
        if not content:
            print("❌ 剪贴板为空")
            return False
        
        print("✅ 环境检查通过")
        
        if is_image:
            if conn_info['is_ssh']:
                print(f"🌐 将上传图片到 {conn_info['username']}@{conn_info['hostname']}")
                # 这里应该进行文件上传测试
                print("📤 模拟上传...")
                # 实际的上传逻辑会在这里
                remote_path = f"/tmp/{os.path.basename(content)}"
                print(f"✅ 应该粘贴: {remote_path}")
            else:
                print(f"📁 应该粘贴本地路径: {content}")
        else:
            print(f"📝 应该粘贴文本: {content[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("SmartPaste SSH调试工具")
    print("=" * 50)
    print()
    
    print("请按以下步骤操作:")
    print("1. 确保你在SSH连接的终端中运行此脚本")
    print("2. 复制一张图片到剪贴板")
    print("3. 运行此脚本查看诊断结果")
    print()
    
    input("按回车键开始诊断...")
    print()
    
    # 运行诊断
    success = simulate_paste_event()
    
    print()
    print("🏁 诊断完成")
    print("=" * 40)
    
    if success:
        print("✅ 环境配置正确，SmartPaste应该能正常工作")
        print()
        print("💡 如果Command+V仍然不工作，请检查:")
        print("   1. SmartPaste是否正在运行")
        print("   2. 是否在正确的SSH会话中")
        print("   3. 网络连接是否正常")
    else:
        print("❌ 发现配置问题，请按照上述提示修复")
    
    print()
    print("🔧 手动测试命令:")
    print("   ~/.smartpaste/smartpaste --debug")

if __name__ == "__main__":
    main()