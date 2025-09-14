#!/usr/bin/env python3
"""
SmartPaste 演示脚本
展示各个模块的功能
"""

import os
import time
import tempfile
from pathlib import Path

def create_demo_image():
    """创建演示用图片"""
    # 创建一个简单的测试图片文件
    demo_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x19tEXtSoftware\x00Adobe ImageReadyq\xc9e<\x00\x00\x00\x0eIDATx\xdab\x00\x02\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
    
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    temp_file.write(demo_content)
    temp_file.close()
    
    return temp_file.name

def demo_clipboard_monitor():
    """演示剪贴板监听功能"""
    print("\n=== 剪贴板监听演示 ===")
    
    try:
        from clipboard_monitor import ClipboardMonitor
        
        def on_change(content, is_image):
            if is_image:
                print(f"📸 检测到图片: {content}")
            else:
                print(f"📝 检测到文本: {content[:30]}...")
        
        monitor = ClipboardMonitor(callback=on_change)
        
        print("✅ 剪贴板监听器初始化成功")
        
        # 获取当前剪贴板内容
        content, is_image = monitor.get_clipboard_content()
        if content:
            if is_image:
                print(f"📸 当前剪贴板内容: 图片 ({content})")
            else:
                print(f"📝 当前剪贴板内容: {content[:50]}...")
        else:
            print("📋 剪贴板为空")
            
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
    except Exception as e:
        print(f"❌ 演示失败: {e}")

def demo_terminal_detector():
    """演示终端检测功能"""
    print("\n=== 终端状态检测演示 ===")
    
    try:
        from terminal_detector import TerminalDetector
        
        detector = TerminalDetector()
        print("✅ 终端检测器初始化成功")
        
        # 获取当前连接信息
        conn_info = detector.get_current_connection_info()
        
        print(f"🖥️  当前终端状态:")
        print(f"   类型: {'SSH远程连接' if conn_info['is_ssh'] else '本地终端'}")
        print(f"   用户: {conn_info['username']}")
        print(f"   主机: {conn_info['hostname']}")
        if conn_info['port']:
            print(f"   端口: {conn_info['port']}")
        print(f"   PID: {conn_info['pid']}")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
    except Exception as e:
        print(f"❌ 演示失败: {e}")

def demo_file_transfer():
    """演示文件传输功能"""
    print("\n=== 文件传输演示 ===")
    
    try:
        from file_transfer import FileTransfer
        
        transfer = FileTransfer()
        print("✅ 文件传输器初始化成功")
        
        # 创建测试文件
        demo_image = create_demo_image()
        print(f"📁 创建演示文件: {demo_image}")
        
        # 生成远程路径
        remote_path = transfer.generate_remote_path(demo_image)
        print(f"🌐 远程路径: {remote_path}")
        
        print("ℹ️  文件传输功能需要实际的SSH连接才能完整演示")
        
        # 清理测试文件
        os.unlink(demo_image)
        print("🧹 清理演示文件")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
    except Exception as e:
        print(f"❌ 演示失败: {e}")

def demo_keyboard_handler():
    """演示键盘处理功能"""
    print("\n=== 键盘处理演示 ===")
    
    try:
        from keyboard_handler import KeyboardHandler
        
        def on_paste():
            print("⌨️  智能粘贴事件触发！")
        
        handler = KeyboardHandler(paste_callback=on_paste)
        print("✅ 键盘处理器初始化成功")
        
        # 检查权限
        if handler.check_permissions():
            print("✅ 辅助功能权限已授权")
        else:
            print("⚠️  需要授权辅助功能权限")
            print("   系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能")
        
        # 获取当前应用
        current_app = handler._get_current_app()
        if current_app:
            is_terminal = any(terminal in current_app for terminal in handler.terminal_apps)
            print(f"🎯 当前应用: {current_app} {'(终端)' if is_terminal else '(非终端)'}")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
    except Exception as e:
        print(f"❌ 演示失败: {e}")

def demo_config_manager():
    """演示配置管理功能"""
    print("\n=== 配置管理演示 ===")
    
    try:
        from config_manager import ConfigManager
        
        # 创建临时配置目录
        temp_dir = tempfile.mkdtemp(prefix='smartpaste_demo_')
        
        manager = ConfigManager(temp_dir)
        print("✅ 配置管理器初始化成功")
        
        config = manager.get_config()
        print(f"⚙️  默认配置:")
        print(f"   启用状态: {config.enabled}")
        print(f"   本地临时目录: {config.local_temp_dir}")
        print(f"   远程临时目录: {config.remote_temp_dir}")
        print(f"   最大文件大小: {config.max_file_size_mb}MB")
        print(f"   支持终端: {', '.join(config.terminal_apps[:3])}...")
        
        # 验证配置
        errors = manager.validate_config()
        if errors:
            print("❌ 配置验证错误:")
            for key, error in errors.items():
                print(f"   {key}: {error}")
        else:
            print("✅ 配置验证通过")
        
        # 清理临时目录
        import shutil
        shutil.rmtree(temp_dir)
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
    except Exception as e:
        print(f"❌ 演示失败: {e}")

def main():
    """主演示函数"""
    print("SmartPaste 功能演示")
    print("=" * 40)
    
    # 检查 Python 版本
    import sys
    print(f"🐍 Python 版本: {sys.version}")
    
    # 运行各个模块演示
    demo_clipboard_monitor()
    demo_terminal_detector()
    demo_file_transfer()
    demo_keyboard_handler()
    demo_config_manager()
    
    print("\n" + "=" * 40)
    print("📋 SmartPaste 功能演示完成")
    print("\n💡 使用说明:")
    print("   1. 运行 'python3 smart_paste.py' 启动程序")
    print("   2. 复制图片到剪贴板")
    print("   3. 在终端中按 Cmd+V 进行智能粘贴")
    print("\n🔧 如需完整功能，请先授权辅助功能权限")

if __name__ == "__main__":
    main()