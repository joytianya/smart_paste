#!/usr/bin/env python3
"""
调试进程树，理解SSH检测问题
"""

import os
import sys
import psutil
from pathlib import Path

# 添加SmartPaste模块路径
sys.path.insert(0, str(Path.home() / '.smartpaste'))

def debug_current_process_tree():
    """调试当前进程树"""
    print("🔍 当前进程树分析")
    print("=" * 60)
    
    current_pid = os.getpid()
    print(f"当前进程PID: {current_pid}")
    
    try:
        current_proc = psutil.Process(current_pid)
        print(f"当前进程: {current_proc.name()} - {' '.join(current_proc.cmdline())}")
        
        # 向上遍历进程树
        level = 0
        proc = current_proc
        while proc and level < 10:  # 最多检查10层
            try:
                cmdline = ' '.join(proc.cmdline()) if proc.cmdline() else 'N/A'
                print(f"{'  ' * level}├─ PID {proc.pid}: {proc.name()} - {cmdline}")
                
                # 检查是否包含SSH
                if 'ssh' in cmdline.lower():
                    print(f"{'  ' * level}   🔗 发现SSH进程!")
                
                parent = proc.parent()
                if parent and parent.pid != proc.pid:
                    proc = parent
                    level += 1
                else:
                    break
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"{'  ' * level}├─ 无法访问进程: {e}")
                break
                
    except Exception as e:
        print(f"错误: {e}")
    
    print("\n" + "=" * 60)

def debug_all_terminals():
    """调试所有终端相关进程"""
    print("📱 所有终端进程分析")
    print("=" * 60)
    
    terminal_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            name = proc.info['name']
            cmdline = proc.info['cmdline'] or []
            
            # 查找终端相关进程
            if (name in ['Terminal', 'iTerm2', 'iTerm', 'bash', 'zsh', 'fish', 'sh', 'ssh'] or
                any('ssh' in arg for arg in cmdline)):
                terminal_processes.append((proc.info['pid'], name, ' '.join(cmdline)))
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # 按进程名分组显示
    terminal_processes.sort(key=lambda x: x[1])
    
    current_group = None
    for pid, name, cmdline in terminal_processes:
        if name != current_group:
            print(f"\n📁 {name} 进程:")
            current_group = name
        print(f"  PID {pid}: {cmdline}")
        
        # 特殊标记SSH进程
        if 'ssh' in cmdline.lower():
            print(f"    🔗 SSH连接进程")
    
    print("\n" + "=" * 60)

def debug_ssh_env():
    """调试SSH相关环境变量"""
    print("🌍 SSH环境变量检查")
    print("=" * 60)
    
    ssh_vars = ['SSH_CLIENT', 'SSH_CONNECTION', 'SSH_TTY', 'SSH_AUTH_SOCK', 'SSH_AGENT_PID']
    
    found_ssh_env = False
    for var in ssh_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}={value}")
            found_ssh_env = True
        else:
            print(f"❌ {var}: 未设置")
    
    if not found_ssh_env:
        print("\n⚠️ 未找到SSH环境变量")
        print("这表明当前不在SSH会话中，或者环境变量未正确传递")
    
    print("\n" + "=" * 60)

def main():
    print("SmartPaste 进程树调试工具")
    print("=" * 60)
    print()
    
    debug_current_process_tree()
    print()
    debug_all_terminals()
    print()
    debug_ssh_env()

if __name__ == "__main__":
    main()