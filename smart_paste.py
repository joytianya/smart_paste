#!/usr/bin/env python3
"""
SmartPaste主程序
智能图片粘贴工具，支持本地和远程终端
"""

import os
import sys
import time
import signal
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# 导入本地模块
from clipboard_monitor import ClipboardMonitor
from terminal_detector import TerminalDetector
from file_transfer import FileTransfer
from keyboard_handler import KeyboardHandler
from config_manager import ConfigManager

class SmartPaste:
    """SmartPaste主类"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化SmartPaste
        
        Args:
            config_dir: 配置目录路径
        """
        self.config_manager = ConfigManager(config_dir)
        self.config = self.config_manager.get_config()
        
        # 初始化各个模块
        self.clipboard_monitor = ClipboardMonitor()
        self.terminal_detector = TerminalDetector()
        self.file_transfer = FileTransfer()
        self.keyboard_handler = KeyboardHandler(paste_callback=self._handle_smart_paste)
        
        # 状态管理
        self.running = False
        self.startup_time = None
        
        # 统计信息
        self.stats = {
            'pastes_handled': 0,
            'images_uploaded': 0,
            'errors': 0,
            'last_activity': None
        }
        
        # 设置日志
        self._setup_logging()
        
        # 信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _setup_logging(self):
        """设置日志记录"""
        log_file = self.config_manager.get_log_file_path('main')
        
        logging.basicConfig(
            level=logging.DEBUG if self.config.debug_mode else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout) if self.config.debug_mode else logging.NullHandler()
            ]
        )
        
        self.logger = logging.getLogger('SmartPaste')
        self.logger.info("SmartPaste initialized")
        
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
        
    def start(self) -> bool:
        """
        启动SmartPaste
        
        Returns:
            是否启动成功
        """
        if self.running:
            self.logger.warning("SmartPaste is already running")
            return True
            
        self.logger.info("Starting SmartPaste...")
        
        # 验证配置
        config_errors = self.config_manager.validate_config()
        if config_errors:
            self.logger.error("Configuration validation failed:")
            for key, error in config_errors.items():
                self.logger.error(f"  {key}: {error}")
            return False
            
        # 检查权限
        if not self.keyboard_handler.check_permissions():
            self.logger.error("Accessibility permissions not granted")
            print("❌ Accessibility permissions required!")
            print("Please grant Accessibility permissions in:")
            print("System Preferences > Security & Privacy > Privacy > Accessibility")
            return False
            
        try:
            # 启动键盘监听器
            if not self.keyboard_handler.start_listening():
                self.logger.error("Failed to start keyboard handler")
                return False
                
            # 启动剪贴板监听器
            self.clipboard_monitor.start_monitoring()
            
            self.running = True
            self.startup_time = datetime.now()
            
            self.logger.info("SmartPaste started successfully")
            print("🚀 SmartPaste is running!")
            print("Press Cmd+V in terminal applications to use smart paste")
            print("Press Ctrl+C to stop")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting SmartPaste: {e}")
            return False
            
    def stop(self):
        """停止SmartPaste"""
        if not self.running:
            return
            
        self.logger.info("Stopping SmartPaste...")
        
        try:
            # 停止各个模块
            self.keyboard_handler.stop_listening()
            self.clipboard_monitor.stop_monitoring()
            self.file_transfer.close()
            
            # 清理临时文件
            self.cleanup_temp_files()
            
            self.running = False
            
            self.logger.info("SmartPaste stopped")
            print("👋 SmartPaste stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping SmartPaste: {e}")
            
    def _handle_smart_paste(self):
        """处理智能粘贴事件"""
        try:
            self.logger.debug("Smart paste event triggered")
            
            # 获取剪贴板内容
            content, is_image = self.clipboard_monitor.get_clipboard_content()
            
            if not content:
                self.logger.warning("No content in clipboard")
                return
                
            # 更新统计
            self.stats['pastes_handled'] += 1
            self.stats['last_activity'] = datetime.now()
            
            if is_image:
                self._handle_image_paste(content)
            else:
                self._handle_text_paste(content)
                
        except Exception as e:
            self.logger.error(f"Error in smart paste handler: {e}")
            self.stats['errors'] += 1
            
    def _handle_image_paste(self, image_path: str):
        """处理图片粘贴"""
        try:
            self.logger.info(f"Handling image paste: {image_path}")
            
            # 检查文件大小
            file_size = os.path.getsize(image_path)
            max_size = self.config.max_file_size_mb * 1024 * 1024
            
            if file_size > max_size:
                self.logger.warning(f"Image too large: {file_size} bytes (max: {max_size})")
                self.keyboard_handler.send_text_to_terminal(f"# Image too large: {file_size/(1024*1024):.1f}MB")
                return
                
            # 检测终端状态
            conn_info = self.terminal_detector.get_current_connection_info()
            
            if conn_info['is_ssh']:
                # SSH连接，上传到远程服务器
                self._upload_and_paste(image_path, conn_info)
            else:
                # 本地连接，复制到本地临时目录
                self._copy_and_paste_local(image_path)
                
        except Exception as e:
            self.logger.error(f"Error handling image paste: {e}")
            self.keyboard_handler.send_text_to_terminal(f"# Error: {str(e)}")
            
    def _handle_text_paste(self, text: str):
        """处理文本粘贴"""
        try:
            self.logger.debug(f"Handling text paste: {text[:50]}...")
            
            # 对于文本，直接执行正常粘贴
            self.keyboard_handler.simulate_paste(text)
            
        except Exception as e:
            self.logger.error(f"Error handling text paste: {e}")
            
    def _upload_and_paste(self, local_path: str, conn_info: Dict[str, Any]):
        """上传文件并粘贴远程路径"""
        try:
            self.logger.info(f"Uploading to {conn_info['username']}@{conn_info['hostname']}")
            
            # 连接SSH
            if not self.file_transfer.connect_ssh(
                hostname=conn_info['hostname'],
                username=conn_info['username'],
                port=conn_info['port'] or 22
            ):
                self.keyboard_handler.send_text_to_terminal("# SSH connection failed")
                return
                
            # 生成远程路径
            remote_path = self.file_transfer.generate_remote_path(
                local_path, self.config.remote_temp_dir
            )
            
            # 上传文件
            def progress_callback(filename, size, sent):
                if sent == size:  # 上传完成
                    self.logger.info(f"Upload completed: {filename}")
                    
            result = self.file_transfer.upload_file_with_retry(
                local_path, remote_path, 
                max_retries=self.config.scp_retry_count,
                progress_callback=progress_callback
            )
            
            if result.success:
                # 上传成功，粘贴远程路径
                self.keyboard_handler.send_text_to_terminal(result.remote_path)
                self.stats['images_uploaded'] += 1
                self.logger.info(f"Successfully pasted remote path: {result.remote_path}")
            else:
                # 上传失败，显示错误信息
                self.keyboard_handler.send_text_to_terminal(f"# Upload failed: {result.error_message}")
                self.logger.error(f"Upload failed: {result.error_message}")
                
        except Exception as e:
            self.logger.error(f"Error uploading file: {e}")
            self.keyboard_handler.send_text_to_terminal(f"# Error: {str(e)}")
            
    def _copy_and_paste_local(self, image_path: str):
        """复制到本地临时目录并粘贴路径"""
        try:
            self.logger.info("Copying to local temp directory")
            
            # 目标路径
            filename = os.path.basename(image_path)
            local_temp_path = os.path.join(self.config.local_temp_dir, filename)
            
            # 如果源文件已经在目标目录，直接使用
            if os.path.dirname(image_path) == self.config.local_temp_dir:
                local_temp_path = image_path
            else:
                # 复制文件
                import shutil
                shutil.copy2(image_path, local_temp_path)
                self.logger.info(f"File copied to: {local_temp_path}")
                
            # 粘贴路径
            self.keyboard_handler.send_text_to_terminal(local_temp_path)
            self.logger.info(f"Successfully pasted local path: {local_temp_path}")
            
        except Exception as e:
            self.logger.error(f"Error copying file locally: {e}")
            self.keyboard_handler.send_text_to_terminal(f"# Error: {str(e)}")
            
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            self.clipboard_monitor.cleanup_old_files(self.config.cleanup_interval_hours)
            self.logger.info("Temporary files cleaned up")
        except Exception as e:
            self.logger.error(f"Error cleaning up temp files: {e}")
            
    def show_status(self):
        """显示运行状态"""
        print("\n=== SmartPaste Status ===")
        print(f"Running: {'Yes' if self.running else 'No'}")
        
        if self.startup_time:
            uptime = datetime.now() - self.startup_time
            print(f"Uptime: {uptime}")
            
        print(f"Pastes handled: {self.stats['pastes_handled']}")
        print(f"Images uploaded: {self.stats['images_uploaded']}")
        print(f"Errors: {self.stats['errors']}")
        
        if self.stats['last_activity']:
            print(f"Last activity: {self.stats['last_activity']}")
            
        # 显示当前终端状态
        try:
            conn_info = self.terminal_detector.get_current_connection_info()
            print(f"\nCurrent terminal status:")
            if conn_info['is_ssh']:
                print(f"  SSH: {conn_info['username']}@{conn_info['hostname']}:{conn_info['port']}")
            else:
                print(f"  Local: {conn_info['username']}@{conn_info['hostname']}")
        except:
            print("  Status: Unable to detect")
            
        print(f"\nConfiguration:")
        print(f"  Config file: {self.config_manager.config_file}")
        print(f"  Debug mode: {self.config.debug_mode}")
        print(f"  Local temp: {self.config.local_temp_dir}")
        print(f"  Remote temp: {self.config.remote_temp_dir}")
        
    def run_interactive(self):
        """运行交互式界面"""
        if not self.start():
            return False
            
        try:
            while self.running:
                time.sleep(1)
                
                # 定期清理临时文件
                if datetime.now().minute % 30 == 0:
                    threading.Thread(target=self.cleanup_temp_files, daemon=True).start()
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
            
        return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SmartPaste - Intelligent clipboard for terminals')
    parser.add_argument('--config-dir', help='Configuration directory')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--status', action='store_true', help='Show status and exit')
    parser.add_argument('--version', action='version', version='SmartPaste 1.0.0')
    
    args = parser.parse_args()
    
    # 创建SmartPaste实例
    smart_paste = SmartPaste(args.config_dir)
    
    # 应用命令行参数
    if args.debug:
        smart_paste.config.debug_mode = True
        smart_paste._setup_logging()
        
    if args.status:
        smart_paste.show_status()
        return
        
    print("SmartPaste - Intelligent Clipboard for Terminals")
    print("=" * 50)
    
    # 运行主循环
    try:
        smart_paste.run_interactive()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()