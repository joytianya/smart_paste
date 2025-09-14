#!/usr/bin/env python3
"""
剪贴板监听器模块
监听macOS剪贴板变化，检测图片类型并保存到临时文件
"""

import os
import time
import tempfile
import hashlib
from datetime import datetime
from typing import Optional, Tuple
import threading
from pathlib import Path

try:
    from AppKit import NSPasteboard, NSPasteboardTypeString, NSPasteboardTypePNG, NSPasteboardTypeTIFF
    from Cocoa import NSData
    HAS_APPKIT = True
except ImportError:
    HAS_APPKIT = False
    print("Warning: AppKit not available, falling back to alternative methods")

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

class ClipboardMonitor:
    """剪贴板监听器类"""
    
    def __init__(self, callback=None):
        """
        初始化剪贴板监听器
        
        Args:
            callback: 回调函数，当检测到图片变化时调用，参数为(image_path, is_image)
        """
        self.callback = callback
        self.running = False
        self.thread = None
        self.last_change_count = 0
        self.last_text_content = ""
        self.temp_dir = Path("/tmp/smart_paste")
        self.temp_dir.mkdir(exist_ok=True)
        
        if HAS_APPKIT:
            self.pasteboard = NSPasteboard.generalPasteboard()
            self.last_change_count = self.pasteboard.changeCount()
        
    def start_monitoring(self):
        """开始监听剪贴板"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print("Clipboard monitoring started")
        
    def stop_monitoring(self):
        """停止监听剪贴板"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        print("Clipboard monitoring stopped")
        
    def _monitor_loop(self):
        """监听循环"""
        while self.running:
            try:
                if HAS_APPKIT:
                    self._check_clipboard_nsboard()
                else:
                    self._check_clipboard_fallback()
                time.sleep(0.5)  # 检查间隔
            except Exception as e:
                print(f"Clipboard monitoring error: {e}")
                time.sleep(1.0)
                
    def _check_clipboard_nsboard(self):
        """使用NSPasteboard检查剪贴板变化"""
        current_change_count = self.pasteboard.changeCount()
        
        if current_change_count != self.last_change_count:
            self.last_change_count = current_change_count
            
            # 检查是否有图片
            if self.pasteboard.availableTypeFromArray_([NSPasteboardTypePNG, NSPasteboardTypeTIFF]):
                image_path = self._save_image_from_pasteboard()
                if image_path and self.callback:
                    self.callback(image_path, True)
            # 检查是否有文本
            elif self.pasteboard.availableTypeFromArray_([NSPasteboardTypeString]):
                text = self.pasteboard.stringForType_(NSPasteboardTypeString)
                if text and text != self.last_text_content:
                    self.last_text_content = text
                    if self.callback:
                        self.callback(text, False)
                        
    def _check_clipboard_fallback(self):
        """备用方法检查剪贴板（仅文本）"""
        if not HAS_PYPERCLIP:
            return
            
        try:
            current_text = pyperclip.paste()
            if current_text != self.last_text_content:
                self.last_text_content = current_text
                if self.callback:
                    self.callback(current_text, False)
        except Exception as e:
            print(f"Fallback clipboard check error: {e}")
            
    def _save_image_from_pasteboard(self) -> Optional[str]:
        """从剪贴板保存图片到临时文件"""
        try:
            # 优先尝试PNG格式
            image_data = self.pasteboard.dataForType_(NSPasteboardTypePNG)
            file_ext = "png"
            
            # 如果没有PNG，尝试TIFF
            if not image_data:
                image_data = self.pasteboard.dataForType_(NSPasteboardTypeTIFF)
                file_ext = "tiff"
                
            if not image_data:
                return None
                
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            data_hash = hashlib.md5(image_data.bytes()).hexdigest()[:8]
            filename = f"clipboard_image_{timestamp}_{data_hash}.{file_ext}"
            file_path = self.temp_dir / filename
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(image_data.bytes())
                
            print(f"Image saved to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            print(f"Error saving image: {e}")
            return None
            
    def get_clipboard_content(self) -> Tuple[str, bool]:
        """
        获取当前剪贴板内容
        
        Returns:
            Tuple[str, bool]: (内容/路径, 是否为图片)
        """
        if HAS_APPKIT:
            # 检查图片
            if self.pasteboard.availableTypeFromArray_([NSPasteboardTypePNG, NSPasteboardTypeTIFF]):
                image_path = self._save_image_from_pasteboard()
                if image_path:
                    return image_path, True
                    
            # 检查文本
            if self.pasteboard.availableTypeFromArray_([NSPasteboardTypeString]):
                text = self.pasteboard.stringForType_(NSPasteboardTypeString)
                if text:
                    return text, False
                    
        elif HAS_PYPERCLIP:
            try:
                text = pyperclip.paste()
                return text, False
            except:
                pass
                
        return "", False
        
    def cleanup_old_files(self, max_age_hours=24):
        """清理旧的临时文件"""
        try:
            current_time = time.time()
            for file_path in self.temp_dir.glob("clipboard_image_*"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_hours * 3600:
                        file_path.unlink()
                        print(f"Cleaned up old file: {file_path}")
        except Exception as e:
            print(f"Error cleaning up files: {e}")


def test_clipboard_monitor():
    """测试剪贴板监听器"""
    def on_clipboard_change(content, is_image):
        if is_image:
            print(f"New image detected: {content}")
        else:
            print(f"New text detected: {content[:50]}...")
            
    monitor = ClipboardMonitor(callback=on_clipboard_change)
    
    print("Starting clipboard monitoring test...")
    print("Copy some text or images to test. Press Ctrl+C to stop.")
    
    monitor.start_monitoring()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping monitoring...")
        monitor.stop_monitoring()


if __name__ == "__main__":
    test_clipboard_monitor()