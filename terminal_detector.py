#!/usr/bin/env python3
"""
终端状态检测器模块
检测当前活跃终端是否在SSH会话中，并提取连接信息
"""

import os
import re
import subprocess
import psutil
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import json

@dataclass
class SSHConnection:
    """SSH连接信息"""
    username: str
    hostname: str
    port: int = 22
    is_active: bool = True
    pid: int = 0

class TerminalDetector:
    """终端检测器类"""
    
    def __init__(self):
        """初始化终端检测器"""
        self.ssh_config_cache = {}
        self._load_ssh_config()
        
    def _load_ssh_config(self):
        """加载SSH配置文件"""
        ssh_config_paths = [
            os.path.expanduser("~/.ssh/config"),
            "/etc/ssh/ssh_config"
        ]
        
        for config_path in ssh_config_paths:
            if os.path.exists(config_path):
                try:
                    self._parse_ssh_config(config_path)
                except Exception as e:
                    print(f"Warning: Error parsing SSH config {config_path}: {e}")
                    
    def _parse_ssh_config(self, config_path: str):
        """解析SSH配置文件"""
        try:
            with open(config_path, 'r') as f:
                content = f.read()
                
            current_host = None
            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                # Host 定义
                if line.lower().startswith('host '):
                    current_host = line.split()[1]
                    if current_host not in self.ssh_config_cache:
                        self.ssh_config_cache[current_host] = {}
                        
                # 其他配置项
                elif current_host:
                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        key, value = parts
                        self.ssh_config_cache[current_host][key.lower()] = value
                        
        except Exception as e:
            print(f"Error parsing SSH config: {e}")
            
    def get_active_terminal_pid(self) -> Optional[int]:
        """获取活跃终端的PID"""
        try:
            # 方法1: 通过AppleScript获取前台Terminal/iTerm2
            script = '''
                tell application "System Events"
                    set frontApp to name of first application process whose frontmost is true
                end tell
                return frontApp
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                app_name = result.stdout.strip()
                if app_name in ['Terminal', 'iTerm2', 'iTerm']:
                    return self._get_terminal_shell_pid(app_name)
                    
        except Exception as e:
            print(f"Error getting active terminal via AppleScript: {e}")
            
        # 方法2: 通过进程检测当前可能的终端
        return self._get_current_shell_pid()
        
    def _get_terminal_shell_pid(self, app_name: str) -> Optional[int]:
        """获取终端应用的shell PID"""
        try:
            if app_name == 'iTerm2' or app_name == 'iTerm':
                script = '''
                    tell application "iTerm2"
                        tell current session of current tab of current window
                            return tty
                        end tell
                    end tell
                '''
            else:  # Terminal
                script = '''
                    tell application "Terminal"
                        return tty of selected tab of front window
                    end tell
                '''
                
            result = subprocess.run(['osascript', '-e', script],
                                  capture_output=True, text=True, timeout=5)
                                  
            if result.returncode == 0:
                tty = result.stdout.strip()
                return self._get_pid_by_tty(tty)
                
        except Exception as e:
            print(f"Error getting terminal shell PID: {e}")
            
        return None
        
    def _get_pid_by_tty(self, tty: str) -> Optional[int]:
        """通过TTY获取进程PID"""
        try:
            result = subprocess.run(['ps', '-t', tty.replace('/dev/', ''), '-o', 'pid,command'],
                                  capture_output=True, text=True)
            
            lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
            for line in lines:
                parts = line.strip().split(None, 1)
                if len(parts) >= 2:
                    pid = int(parts[0])
                    command = parts[1]
                    # 找到shell进程
                    if any(shell in command for shell in ['bash', 'zsh', 'fish', 'sh']):
                        return pid
                        
        except Exception as e:
            print(f"Error getting PID by TTY: {e}")
            
        return None
        
    def _get_current_shell_pid(self) -> Optional[int]:
        """获取当前可能的shell PID（备用方法）"""
        try:
            # 获取所有终端相关进程
            terminal_procs = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'parent']):
                try:
                    if proc.info['name'] in ['bash', 'zsh', 'fish', 'sh']:
                        parent = psutil.Process(proc.info['parent'])
                        if parent.name() in ['Terminal', 'iTerm2', 'login']:
                            terminal_procs.append(proc.info['pid'])
                except:
                    continue
                    
            # 返回最新的shell进程
            if terminal_procs:
                return max(terminal_procs)
                
        except Exception as e:
            print(f"Error getting current shell PID: {e}")
            
        return None
        
    def detect_ssh_connection(self, shell_pid: Optional[int] = None) -> Optional[SSHConnection]:
        """
        检测SSH连接信息
        
        Args:
            shell_pid: Shell进程PID，如果不提供则自动检测
            
        Returns:
            SSHConnection对象或None
        """
        if shell_pid is None:
            shell_pid = self.get_active_terminal_pid()
            
        if shell_pid is None:
            return None
            
        # 方法1: 检查进程树中的SSH进程
        ssh_conn = self._detect_ssh_in_process_tree(shell_pid)
        if ssh_conn:
            return ssh_conn
            
        # 方法2: 检查环境变量
        ssh_conn = self._detect_ssh_from_env(shell_pid)
        if ssh_conn:
            return ssh_conn
            
        return None
        
    def _detect_ssh_in_process_tree(self, shell_pid: int) -> Optional[SSHConnection]:
        """从进程树中检测SSH连接"""
        try:
            current_proc = psutil.Process(shell_pid)
            
            # 向上遍历进程树
            while current_proc:
                try:
                    cmdline = current_proc.cmdline()
                    if cmdline and len(cmdline) > 0 and 'ssh' in cmdline[0]:
                        return self._parse_ssh_command(cmdline, current_proc.pid)
                        
                    # 检查父进程
                    parent = current_proc.parent()
                    if parent and parent.pid != current_proc.pid:
                        current_proc = parent
                    else:
                        break
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
                    
        except Exception as e:
            print(f"Error detecting SSH in process tree: {e}")
            
        return None
        
    def _detect_ssh_from_env(self, shell_pid: int) -> Optional[SSHConnection]:
        """从环境变量检测SSH连接"""
        try:
            proc = psutil.Process(shell_pid)
            env = proc.environ()
            
            # 检查SSH相关环境变量
            if 'SSH_CLIENT' in env or 'SSH_CONNECTION' in env:
                # 这种情况通常是我们在远程服务器上
                # 需要从SSH_CLIENT中解析出客户端信息
                ssh_client = env.get('SSH_CLIENT', '')
                if ssh_client:
                    parts = ssh_client.split()
                    if len(parts) >= 3:
                        # SSH_CLIENT格式: client_ip client_port server_port
                        client_ip = parts[0]
                        # 这里我们实际上在服务器上，所以返回None
                        # 或者可以返回reverse连接信息
                        return None
                        
        except Exception as e:
            print(f"Error detecting SSH from environment: {e}")
            
        return None
        
    def _parse_ssh_command(self, cmdline: List[str], pid: int) -> Optional[SSHConnection]:
        """解析SSH命令行"""
        try:
            if not cmdline or 'ssh' not in cmdline[0]:
                return None
                
            username = None
            hostname = None
            port = 22
            
            i = 1
            while i < len(cmdline):
                arg = cmdline[i]
                
                # -l user
                if arg == '-l' and i + 1 < len(cmdline):
                    username = cmdline[i + 1]
                    i += 2
                    continue
                    
                # -p port
                elif arg == '-p' and i + 1 < len(cmdline):
                    try:
                        port = int(cmdline[i + 1])
                    except ValueError:
                        pass
                    i += 2
                    continue
                    
                # 跳过其他选项
                elif arg.startswith('-'):
                    if arg in ['-o', '-i', '-F']:  # 需要参数的选项
                        i += 2
                    else:
                        i += 1
                    continue
                    
                # 这应该是 user@host 格式的目标
                else:
                    if '@' in arg:
                        username, hostname = arg.split('@', 1)
                    else:
                        hostname = arg
                        
                    # 检查是否是SSH配置中的别名
                    if hostname in self.ssh_config_cache:
                        config = self.ssh_config_cache[hostname]
                        if 'hostname' in config:
                            hostname = config['hostname']
                        if 'user' in config and not username:
                            username = config['user']
                        if 'port' in config:
                            try:
                                port = int(config['port'])
                            except ValueError:
                                pass
                                
                    break
                    
            if hostname:
                # 如果没有指定用户名，使用当前用户名
                if not username:
                    username = os.getenv('USER', 'unknown')
                    
                return SSHConnection(
                    username=username,
                    hostname=hostname,
                    port=port,
                    pid=pid
                )
                
        except Exception as e:
            print(f"Error parsing SSH command: {e}")
            
        return None
        
    def get_current_connection_info(self) -> Dict[str, any]:
        """
        获取当前连接信息
        
        Returns:
            包含连接信息的字典
        """
        shell_pid = self.get_active_terminal_pid()
        ssh_conn = self.detect_ssh_connection(shell_pid)
        
        if ssh_conn:
            return {
                'is_ssh': True,
                'username': ssh_conn.username,
                'hostname': ssh_conn.hostname,
                'port': ssh_conn.port,
                'pid': ssh_conn.pid
            }
        else:
            return {
                'is_ssh': False,
                'username': os.getenv('USER', 'unknown'),
                'hostname': 'localhost',
                'port': None,
                'pid': shell_pid
            }


def test_terminal_detector():
    """测试终端检测器"""
    detector = TerminalDetector()
    
    print("=== Terminal Detection Test ===")
    
    # 获取活跃终端PID
    shell_pid = detector.get_active_terminal_pid()
    print(f"Active shell PID: {shell_pid}")
    
    # 检测SSH连接
    ssh_conn = detector.detect_ssh_connection(shell_pid)
    if ssh_conn:
        print(f"SSH connection detected:")
        print(f"  Username: {ssh_conn.username}")
        print(f"  Hostname: {ssh_conn.hostname}")
        print(f"  Port: {ssh_conn.port}")
        print(f"  PID: {ssh_conn.pid}")
    else:
        print("No SSH connection detected (running locally)")
        
    # 获取完整连接信息
    conn_info = detector.get_current_connection_info()
    print(f"Connection info: {json.dumps(conn_info, indent=2)}")


if __name__ == "__main__":
    test_terminal_detector()