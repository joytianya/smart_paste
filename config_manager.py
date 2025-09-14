#!/usr/bin/env python3
"""
配置管理器模块
管理SmartPaste的配置文件和运行时设置
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class SmartPasteConfig:
    """SmartPaste配置类"""
    
    # 基础设置
    enabled: bool = True
    debug_mode: bool = False
    
    # 文件设置
    local_temp_dir: str = "/tmp"
    remote_temp_dir: str = "/tmp"
    max_file_size_mb: int = 100
    cleanup_interval_hours: int = 24
    
    # 终端设置
    terminal_apps: list = None
    paste_cooldown_ms: int = 500
    
    # SSH设置
    ssh_timeout_seconds: int = 10
    scp_retry_count: int = 3
    auto_create_remote_dirs: bool = True
    
    # 监听设置
    clipboard_check_interval_ms: int = 500
    keyboard_listener_enabled: bool = True
    
    # 高级设置
    compress_images: bool = False
    max_image_width: int = 2048
    max_image_height: int = 2048
    
    def __post_init__(self):
        """初始化后处理"""
        if self.terminal_apps is None:
            self.terminal_apps = ['Terminal', 'iTerm2', 'iTerm', 'Hyper', 'Alacritty', 'Wezterm']

class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置目录路径，默认为 ~/.smartpaste
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / '.smartpaste'
            
        self.config_file = self.config_dir / 'config.json'
        self.log_dir = self.config_dir / 'logs'
        
        # 创建配置目录
        self.config_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)
        
        self._config = SmartPasteConfig()
        self._load_config()
        
    def _load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    
                # 更新配置对象
                for key, value in config_data.items():
                    if hasattr(self._config, key):
                        setattr(self._config, key, value)
                        
                print(f"Configuration loaded from {self.config_file}")
                
            except Exception as e:
                print(f"Error loading config file: {e}")
                print("Using default configuration")
        else:
            # 创建默认配置文件
            self.save_config()
            print(f"Created default configuration at {self.config_file}")
            
    def save_config(self):
        """保存配置到文件"""
        try:
            config_data = asdict(self._config)
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
            print(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            print(f"Error saving config file: {e}")
            return False
            
    def get_config(self) -> SmartPasteConfig:
        """获取配置对象"""
        return self._config
        
    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
            else:
                print(f"Warning: Unknown config key '{key}'")
                
    def reset_to_defaults(self):
        """重置为默认配置"""
        self._config = SmartPasteConfig()
        self.save_config()
        print("Configuration reset to defaults")
        
    def validate_config(self) -> Dict[str, str]:
        """
        验证配置有效性
        
        Returns:
            错误信息字典，空字典表示无错误
        """
        errors = {}
        
        # 验证目录路径
        try:
            local_dir = Path(self._config.local_temp_dir)
            if not local_dir.exists():
                local_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors['local_temp_dir'] = f"Invalid local temp directory: {e}"
            
        # 验证数值范围
        if self._config.max_file_size_mb <= 0:
            errors['max_file_size_mb'] = "Max file size must be positive"
            
        if self._config.paste_cooldown_ms < 0:
            errors['paste_cooldown_ms'] = "Paste cooldown cannot be negative"
            
        if self._config.ssh_timeout_seconds <= 0:
            errors['ssh_timeout_seconds'] = "SSH timeout must be positive"
            
        if self._config.scp_retry_count < 0:
            errors['scp_retry_count'] = "Retry count cannot be negative"
            
        # 验证图片设置
        if self._config.max_image_width <= 0 or self._config.max_image_height <= 0:
            errors['image_dimensions'] = "Image dimensions must be positive"
            
        return errors
        
    def get_log_file_path(self, log_type: str = 'main') -> Path:
        """获取日志文件路径"""
        return self.log_dir / f'smartpaste_{log_type}.log'
        
    def export_config(self, file_path: str) -> bool:
        """导出配置到指定文件"""
        try:
            config_data = asdict(self._config)
            
            with open(file_path, 'w') as f:
                json.dump(config_data, f, indent=2)
                
            print(f"Configuration exported to {file_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting config: {e}")
            return False
            
    def import_config(self, file_path: str) -> bool:
        """从指定文件导入配置"""
        try:
            with open(file_path, 'r') as f:
                config_data = json.load(f)
                
            # 备份当前配置
            backup_file = self.config_file.with_suffix('.backup')
            if self.config_file.exists():
                self.config_file.rename(backup_file)
                print(f"Current config backed up to {backup_file}")
                
            # 应用新配置
            for key, value in config_data.items():
                if hasattr(self._config, key):
                    setattr(self._config, key, value)
                    
            # 验证配置
            errors = self.validate_config()
            if errors:
                print("Configuration validation errors:")
                for key, error in errors.items():
                    print(f"  {key}: {error}")
                    
                # 恢复备份
                if backup_file.exists():
                    backup_file.rename(self.config_file)
                    self._load_config()
                    print("Restored previous configuration due to errors")
                return False
                
            # 保存新配置
            self.save_config()
            print(f"Configuration imported from {file_path}")
            return True
            
        except Exception as e:
            print(f"Error importing config: {e}")
            return False
            
    def show_config(self):
        """显示当前配置"""
        print("=== SmartPaste Configuration ===")
        config_data = asdict(self._config)
        
        for key, value in config_data.items():
            if isinstance(value, list):
                print(f"{key}: {', '.join(map(str, value))}")
            else:
                print(f"{key}: {value}")
                
        print(f"\nConfiguration file: {self.config_file}")
        print(f"Log directory: {self.log_dir}")


def test_config_manager():
    """测试配置管理器"""
    print("=== Config Manager Test ===")
    
    # 创建临时配置目录
    test_dir = Path("/tmp/smartpaste_test")
    
    manager = ConfigManager(str(test_dir))
    
    print("\n1. Default configuration:")
    manager.show_config()
    
    print("\n2. Updating configuration...")
    manager.update_config(
        debug_mode=True,
        max_file_size_mb=50,
        paste_cooldown_ms=1000
    )
    
    print("\n3. Updated configuration:")
    manager.show_config()
    
    print("\n4. Validating configuration...")
    errors = manager.validate_config()
    if errors:
        print("Validation errors:")
        for key, error in errors.items():
            print(f"  {key}: {error}")
    else:
        print("✓ Configuration is valid")
        
    print("\n5. Exporting configuration...")
    export_file = test_dir / "exported_config.json"
    if manager.export_config(str(export_file)):
        print(f"✓ Configuration exported to {export_file}")
        
    print("\n6. Resetting to defaults...")
    manager.reset_to_defaults()
    
    print("\n7. Importing configuration...")
    if manager.import_config(str(export_file)):
        print("✓ Configuration imported successfully")
        
    print("\n8. Final configuration:")
    manager.show_config()
    
    # 清理测试文件
    try:
        import shutil
        shutil.rmtree(test_dir)
        print(f"\n✓ Cleaned up test directory: {test_dir}")
    except:
        pass


if __name__ == "__main__":
    test_config_manager()