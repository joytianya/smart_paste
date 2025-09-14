#!/usr/bin/env python3
"""
键盘处理器模块
监听全局Command+V快捷键并处理智能粘贴
"""

import os
import time
import subprocess
import threading
from typing import Optional, Callable, Set
from enum import Enum

try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False
    print("Warning: pynput not available, install with: pip install pynput")

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

class PasteMode(Enum):
    """粘贴模式枚举"""
    NORMAL = "normal"  # 正常文本粘贴
    IMAGE_LOCAL = "image_local"  # 本地图片路径
    IMAGE_REMOTE = "image_remote"  # 远程图片路径
    DISABLED = "disabled"  # 禁用智能粘贴

class KeyboardHandler:
    """键盘处理器类"""
    
    def __init__(self, paste_callback: Optional[Callable] = None):
        """
        初始化键盘处理器
        
        Args:
            paste_callback: 粘贴回调函数，参数为(content, is_image, is_ssh)
        """
        self.paste_callback = paste_callback
        self.listener = None
        self.running = False
        
        # 按键状态跟踪
        self.pressed_keys: Set = set()
        self.cmd_pressed = False
        self.intercepted = False
        
        # 配置
        self.terminal_apps = {'Terminal', 'iTerm2', 'iTerm', 'Hyper', 'Alacritty', 'Wezterm', 'stable', 'Warp'}
        self.enabled = True
        
        # 防重复触发
        self.last_paste_time = 0
        self.paste_cooldown = 0.5  # 500ms 冷却时间
        
    def start_listening(self):
        """开始监听键盘事件"""
        if not HAS_PYNPUT:
            print("Error: pynput not available")
            return False
            
        if self.running:
            return True
            
        try:
            self.running = True
            self.listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            
            self.listener.start()
            print("Keyboard listener started (requires Accessibility permissions)")
            print("Press Cmd+V in terminal applications to test smart paste")
            return True
            
        except Exception as e:
            print(f"Error starting keyboard listener: {e}")
            print("Make sure to grant Accessibility permissions in System Preferences")
            return False
            
    def stop_listening(self):
        """停止监听键盘事件"""
        self.running = False
        if self.listener:
            self.listener.stop()
            self.listener = None
        print("Keyboard listener stopped")
        
    def _on_key_press(self, key):
        """按键按下事件处理"""
        try:
            self.pressed_keys.add(key)
            
            # 检测Command键
            if key == Key.cmd or key == Key.cmd_r:
                self.cmd_pressed = True
                
            # 检测Cmd+V组合
            elif key == KeyCode.from_char('v') and self.cmd_pressed:
                if self.enabled and self._should_intercept():
                    current_time = time.time()
                    
                    # 防重复触发
                    if current_time - self.last_paste_time > self.paste_cooldown:
                        self.last_paste_time = current_time
                        self._handle_paste_event()
                        return False  # 阻止事件继续传播
                        
        except Exception as e:
            print(f"Error in key press handler: {e}")
            
    def _on_key_release(self, key):
        """按键释放事件处理"""
        try:
            if key in self.pressed_keys:
                self.pressed_keys.remove(key)
                
            # 重置Command键状态
            if key == Key.cmd or key == Key.cmd_r:
                self.cmd_pressed = False
                
        except Exception as e:
            print(f"Error in key release handler: {e}")
            
    def _should_intercept(self) -> bool:
        """判断是否应该拦截粘贴事件"""
        try:
            # 检查当前活跃应用
            current_app = self._get_current_app()
            if not current_app:
                return False
                
            # 只在终端应用中拦截
            is_terminal = any(terminal in current_app for terminal in self.terminal_apps)
            if not is_terminal:
                return False
                
            print(f"Intercepting paste in {current_app}")
            return True
            
        except Exception as e:
            print(f"Error checking intercept condition: {e}")
            return False
            
    def _get_current_app(self) -> Optional[str]:
        """获取当前活跃应用名称"""
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
                return result.stdout.strip()
                
        except Exception as e:
            print(f"Error getting current app: {e}")
            
        return None
        
    def _handle_paste_event(self):
        """处理粘贴事件"""
        try:
            if self.paste_callback:
                # 在单独线程中执行回调，避免阻塞键盘监听
                threading.Thread(
                    target=self.paste_callback,
                    daemon=True
                ).start()
            else:
                print("Paste event detected, but no callback configured")
                
        except Exception as e:
            print(f"Error handling paste event: {e}")
            
    def simulate_paste(self, content: str):
        """模拟粘贴文本到当前应用"""
        try:
            if HAS_PYPERCLIP:
                # 保存当前剪贴板内容
                original_content = pyperclip.paste()
                
                # 设置新内容到剪贴板
                pyperclip.copy(content)
                
                # 执行原始粘贴操作
                self._execute_native_paste()
                
                # 恢复原始剪贴板内容（延迟恢复，给粘贴操作时间）
                def restore_clipboard():
                    time.sleep(0.2)
                    try:
                        pyperclip.copy(original_content)
                    except:
                        pass
                        
                threading.Thread(target=restore_clipboard, daemon=True).start()
                
            else:
                print(f"Simulated paste: {content[:50]}...")
                
        except Exception as e:
            print(f"Error simulating paste: {e}")
            
    def _execute_native_paste(self):
        """执行原生粘贴操作"""
        try:
            # 方法1: 通过AppleScript发送Cmd+V
            script = '''
                tell application "System Events"
                    keystroke "v" using command down
                end tell
            '''
            
            subprocess.run(['osascript', '-e', script], timeout=2)
            
        except Exception as e:
            print(f"Error executing native paste: {e}")
            
    def type_text(self, text: str):
        """直接输入文本到当前应用"""
        try:
            # 转义特殊字符
            escaped_text = text.replace('\\', '\\\\').replace('"', '\\"')
            
            script = f'''
                tell application "System Events"
                    keystroke "{escaped_text}"
                end tell
            '''
            
            subprocess.run(['osascript', '-e', script], timeout=5)
            
        except Exception as e:
            print(f"Error typing text: {e}")
            
    def send_text_to_terminal(self, text: str):
        """发送文本到终端（尝试直接输入）"""
        try:
            current_app = self._get_current_app()
            
            if 'iTerm2' in current_app or 'iTerm' in current_app:
                # iTerm2 特殊处理
                escaped_text = text.replace('\\', '\\\\').replace('"', '\\"')
                script = f'''
                    tell application "iTerm2"
                        tell current session of current tab of current window
                            write text "{escaped_text}"
                        end tell
                    end tell
                '''
            elif 'Terminal' in current_app:
                # Terminal.app 特殊处理
                escaped_text = text.replace('\\', '\\\\').replace('"', '\\"')
                script = f'''
                    tell application "Terminal"
                        do script "{escaped_text}" in selected tab of front window
                    end tell
                '''
            else:
                # 其他终端应用，使用通用方法
                self.type_text(text)
                return
                
            subprocess.run(['osascript', '-e', script], timeout=5)
            
        except Exception as e:
            print(f"Error sending text to terminal: {e}")
            # 回退到通用方法
            self.type_text(text)
            
    def enable(self):
        """启用智能粘贴"""
        self.enabled = True
        print("Smart paste enabled")
        
    def disable(self):
        """禁用智能粘贴"""
        self.enabled = False
        print("Smart paste disabled")
        
    def toggle(self):
        """切换智能粘贴状态"""
        if self.enabled:
            self.disable()
        else:
            self.enable()
            
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self.running and self.listener and self.listener.running
        
    def check_permissions(self) -> bool:
        """检查辅助功能权限"""
        try:
            # 尝试创建一个临时监听器来测试权限
            test_listener = keyboard.Listener(on_press=lambda key: None)
            test_listener.start()
            time.sleep(0.1)
            test_listener.stop()
            return True
        except Exception:
            return False


def test_keyboard_handler():
    """测试键盘处理器"""
    def on_paste():
        print("Smart paste triggered!")
        print("This is where the smart paste logic would execute")
        
    handler = KeyboardHandler(paste_callback=on_paste)
    
    print("=== Keyboard Handler Test ===")
    
    # 检查权限
    if not handler.check_permissions():
        print("❌ Accessibility permissions not granted")
        print("Please grant Accessibility permissions to this terminal application in:")
        print("System Preferences > Security & Privacy > Privacy > Accessibility")
        return
    else:
        print("✅ Accessibility permissions OK")
        
    print("Starting keyboard listener...")
    print("Open a terminal application (Terminal.app or iTerm2)")
    print("Press Cmd+V to test smart paste interception")
    print("Press Ctrl+C to stop")
    
    if handler.start_listening():
        try:
            # 测试应用检测
            while True:
                time.sleep(2)
                current_app = handler._get_current_app()
                if current_app:
                    is_terminal = any(terminal in current_app for terminal in handler.terminal_apps)
                    status = "🎯 TERMINAL" if is_terminal else "📱 OTHER"
                    print(f"\rCurrent app: {current_app} {status}", end='', flush=True)
                    
        except KeyboardInterrupt:
            print("\n\nStopping keyboard handler...")
        finally:
            handler.stop_listening()
    else:
        print("❌ Failed to start keyboard listener")


if __name__ == "__main__":
    test_keyboard_handler()