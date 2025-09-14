#!/usr/bin/env python3
"""
文件传输模块
使用SCP协议上传文件到远程服务器
"""

import os
import stat
import time
import socket
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass

try:
    import paramiko
    from paramiko import SSHClient, AutoAddPolicy
    from scp import SCPClient
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False
    print("Warning: paramiko and scp not available, install with: pip install paramiko scp")

@dataclass
class TransferResult:
    """文件传输结果"""
    success: bool
    remote_path: str = ""
    error_message: str = ""
    transfer_time: float = 0.0
    file_size: int = 0

class FileTransfer:
    """文件传输器类"""
    
    def __init__(self):
        """初始化文件传输器"""
        self.ssh_client = None
        self.known_hosts_path = os.path.expanduser("~/.ssh/known_hosts")
        self.ssh_config_path = os.path.expanduser("~/.ssh/config")
        self.default_key_paths = [
            "~/.ssh/id_rsa",
            "~/.ssh/id_ecdsa", 
            "~/.ssh/id_ed25519",
            "~/.ssh/id_dsa"
        ]
        
    def _get_ssh_config(self, hostname: str) -> Dict[str, Any]:
        """获取SSH配置信息"""
        config = {
            'hostname': hostname,
            'port': 22,
            'username': os.getenv('USER', 'unknown'),
            'key_filename': None,
            'password': None
        }
        
        if not HAS_PARAMIKO:
            return config
            
        try:
            ssh_config = paramiko.SSHConfig()
            if os.path.exists(self.ssh_config_path):
                with open(self.ssh_config_path) as f:
                    ssh_config.parse(f)
                    
                host_config = ssh_config.lookup(hostname)
                config.update({
                    'hostname': host_config.get('hostname', hostname),
                    'port': int(host_config.get('port', 22)),
                    'username': host_config.get('user', config['username']),
                })
                
                # 处理密钥文件
                if 'identityfile' in host_config:
                    identity_files = host_config['identityfile']
                    if isinstance(identity_files, list):
                        config['key_filename'] = [os.path.expanduser(f) for f in identity_files]
                    else:
                        config['key_filename'] = os.path.expanduser(identity_files)
                        
        except Exception as e:
            print(f"Error reading SSH config: {e}")
            
        return config
        
    def _find_ssh_keys(self) -> list:
        """查找可用的SSH密钥"""
        keys = []
        for key_path in self.default_key_paths:
            expanded_path = os.path.expanduser(key_path)
            if os.path.exists(expanded_path):
                keys.append(expanded_path)
        return keys
        
    def connect_ssh(self, hostname: str, username: str, port: int = 22, 
                   password: Optional[str] = None, 
                   key_filename: Optional[str] = None) -> bool:
        """
        建立SSH连接
        
        Args:
            hostname: 主机地址
            username: 用户名
            port: 端口号
            password: 密码（可选）
            key_filename: 密钥文件路径（可选）
            
        Returns:
            是否连接成功
        """
        if not HAS_PARAMIKO:
            print("Error: paramiko not available")
            return False
            
        try:
            self.ssh_client = SSHClient()
            
            # 加载已知主机
            if os.path.exists(self.known_hosts_path):
                self.ssh_client.load_host_keys(self.known_hosts_path)
                
            # 自动添加未知主机（在生产环境中应该谨慎使用）
            self.ssh_client.set_missing_host_key_policy(AutoAddPolicy())
            
            # 获取SSH配置
            config = self._get_ssh_config(hostname)
            actual_hostname = config['hostname']
            actual_port = port if port != 22 else config['port']
            actual_username = username if username != 'unknown' else config['username']
            
            # 尝试连接
            connect_kwargs = {
                'hostname': actual_hostname,
                'port': actual_port,
                'username': actual_username,
                'timeout': 10,
                'banner_timeout': 10,
                'auth_timeout': 10
            }
            
            # 优先使用提供的密钥或密码
            if key_filename and os.path.exists(os.path.expanduser(key_filename)):
                connect_kwargs['key_filename'] = os.path.expanduser(key_filename)
            elif password:
                connect_kwargs['password'] = password
            elif config.get('key_filename'):
                connect_kwargs['key_filename'] = config['key_filename']
            else:
                # 尝试所有可用密钥
                keys = self._find_ssh_keys()
                if keys:
                    connect_kwargs['key_filename'] = keys
                    
            # 尝试SSH Agent
            try:
                connect_kwargs['allow_agent'] = True
                connect_kwargs['look_for_keys'] = True
            except:
                pass
                
            self.ssh_client.connect(**connect_kwargs)
            print(f"SSH connected to {actual_username}@{actual_hostname}:{actual_port}")
            return True
            
        except paramiko.AuthenticationException:
            print("SSH authentication failed")
            return False
        except paramiko.SSHException as e:
            print(f"SSH connection error: {e}")
            return False
        except socket.error as e:
            print(f"Network error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error connecting to SSH: {e}")
            return False
            
    def upload_file(self, local_path: str, remote_path: str, 
                   progress_callback: Optional[Callable] = None) -> TransferResult:
        """
        上传文件到远程服务器
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程文件路径
            progress_callback: 进度回调函数
            
        Returns:
            TransferResult对象
        """
        if not self.ssh_client:
            return TransferResult(success=False, error_message="No SSH connection")
            
        if not os.path.exists(local_path):
            return TransferResult(success=False, error_message=f"Local file not found: {local_path}")
            
        try:
            start_time = time.time()
            file_size = os.path.getsize(local_path)
            
            def progress_wrapper(filename, size, sent):
                if progress_callback:
                    progress_callback(filename, size, sent)
                    
            # 创建SCP客户端
            with SCPClient(self.ssh_client.get_transport(), progress=progress_wrapper) as scp:
                # 确保远程目录存在
                remote_dir = os.path.dirname(remote_path)
                if remote_dir:
                    try:
                        self.ssh_client.exec_command(f"mkdir -p {remote_dir}")
                    except:
                        pass  # 目录可能已存在
                        
                # 上传文件
                scp.put(local_path, remote_path)
                
            transfer_time = time.time() - start_time
            
            # 验证文件是否上传成功
            stdin, stdout, stderr = self.ssh_client.exec_command(f"test -f {remote_path} && echo 'OK'")
            result = stdout.read().decode().strip()
            
            if result == 'OK':
                print(f"File uploaded successfully: {remote_path}")
                return TransferResult(
                    success=True, 
                    remote_path=remote_path,
                    transfer_time=transfer_time,
                    file_size=file_size
                )
            else:
                return TransferResult(success=False, error_message="Upload verification failed")
                
        except Exception as e:
            return TransferResult(success=False, error_message=f"Upload failed: {str(e)}")
            
    def upload_file_with_retry(self, local_path: str, remote_path: str, 
                              max_retries: int = 3,
                              progress_callback: Optional[Callable] = None) -> TransferResult:
        """
        带重试的文件上传
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程文件路径
            max_retries: 最大重试次数
            progress_callback: 进度回调函数
            
        Returns:
            TransferResult对象
        """
        last_error = ""
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                print(f"Retrying upload (attempt {attempt + 1}/{max_retries + 1})...")
                time.sleep(1)  # 等待1秒后重试
                
            result = self.upload_file(local_path, remote_path, progress_callback)
            
            if result.success:
                return result
            else:
                last_error = result.error_message
                
        return TransferResult(success=False, error_message=f"Upload failed after {max_retries + 1} attempts: {last_error}")
        
    def generate_remote_path(self, local_path: str, remote_base_dir: str = "/tmp") -> str:
        """
        生成远程文件路径
        
        Args:
            local_path: 本地文件路径
            remote_base_dir: 远程基础目录
            
        Returns:
            远程文件路径
        """
        filename = os.path.basename(local_path)
        return os.path.join(remote_base_dir, filename).replace('\\', '/')
        
    def close(self):
        """关闭SSH连接"""
        if self.ssh_client:
            try:
                self.ssh_client.close()
                print("SSH connection closed")
            except:
                pass
            finally:
                self.ssh_client = None
                
    def __del__(self):
        """析构函数"""
        self.close()
        
    def test_connection(self, hostname: str, username: str, port: int = 22) -> bool:
        """
        测试SSH连接
        
        Args:
            hostname: 主机地址
            username: 用户名
            port: 端口号
            
        Returns:
            是否连接成功
        """
        if self.connect_ssh(hostname, username, port):
            self.close()
            return True
        return False


def test_file_transfer():
    """测试文件传输功能"""
    transfer = FileTransfer()
    
    print("=== File Transfer Test ===")
    
    # 创建测试文件
    test_file = "/tmp/test_upload.txt"
    with open(test_file, 'w') as f:
        f.write(f"Test file created at {time.ctime()}\n")
        f.write("This is a test file for smart paste functionality.\n")
        
    print(f"Created test file: {test_file}")
    
    # 模拟SSH连接参数（请根据实际情况修改）
    hostname = input("Enter hostname (or 'local' for local test): ").strip()
    
    if hostname.lower() == 'local':
        # 本地测试
        print("Running local test...")
        local_copy = "/tmp/test_upload_copy.txt"
        import shutil
        shutil.copy2(test_file, local_copy)
        print(f"Local copy created: {local_copy}")
        return
        
    username = input(f"Enter username [{os.getenv('USER')}]: ").strip() or os.getenv('USER')
    
    # 测试连接
    if transfer.test_connection(hostname, username):
        print("✓ SSH connection successful")
        
        # 连接并上传
        if transfer.connect_ssh(hostname, username):
            def progress_callback(filename, size, sent):
                percent = int((sent / size) * 100) if size > 0 else 0
                print(f"\rUploading {filename}: {percent}% ({sent}/{size} bytes)", end='')
                
            remote_path = transfer.generate_remote_path(test_file)
            print(f"\nUploading to: {remote_path}")
            
            result = transfer.upload_file_with_retry(test_file, remote_path, progress_callback=progress_callback)
            
            print()  # 换行
            if result.success:
                print(f"✓ Upload successful!")
                print(f"  Remote path: {result.remote_path}")
                print(f"  Transfer time: {result.transfer_time:.2f}s")
                print(f"  File size: {result.file_size} bytes")
            else:
                print(f"✗ Upload failed: {result.error_message}")
                
            transfer.close()
        else:
            print("✗ Failed to establish SSH connection")
    else:
        print("✗ SSH connection test failed")
        
    # 清理测试文件
    try:
        os.unlink(test_file)
        print(f"Cleaned up test file: {test_file}")
    except:
        pass


if __name__ == "__main__":
    test_file_transfer()