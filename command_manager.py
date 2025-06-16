import json
import os
import re
from collections import OrderedDict
from typing import List, Dict, Optional
from tkinter import messagebox

class CommandManager:
    def __init__(self, data_file: str = 'data/commands.json'):
        self.data_file = data_file
        self.commands = []
        self._ensure_data_file()
        self._load_commands()
    
    def _ensure_data_file(self):
        """确保数据文件存在"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump([], f)
    
    def _load_commands(self):
        """加载命令数据"""
        with open(self.data_file, 'r') as f:
            self.commands = json.load(f)
    
    def _save_commands(self):
        """保存命令数据"""
        with open(self.data_file, 'w') as f:
            json.dump(self.commands, f, indent=2)
    
    def add_command(self, name: str, group: str, description: str, command: str) -> bool:
        """添加新命令（增加参数验证）"""
        if not name or not command:
            messagebox.showerror("错误", "名称和命令内容不能为空")
            return False
        
        # 检查名称是否已存在
        if any(cmd['name'].lower() == name.lower() for cmd in self.commands):
            messagebox.showerror("错误", f"名称 '{name}' 已存在")
            return False
        
        new_cmd = {
            'id': len(self.commands) + 1,
            'name': name.strip(),
            'group': group.strip(),
            'description': description.strip(),
            'command': command.strip(),
            'copy_count': 0
        }
        self.commands.append(new_cmd)
        self._save_commands()
        return True
    
    def delete_command(self, command_id: int) -> bool:
        """删除命令"""
        for i, cmd in enumerate(self.commands):
            if cmd['id'] == command_id:
                del self.commands[i]
                self._save_commands()
                return True
        return False
    
    def update_command(self, command_id: int, **kwargs) -> bool:
        """更新命令"""
        for cmd in self.commands:
            if cmd['id'] == command_id:
                for key, value in kwargs.items():
                    if key in cmd:
                        cmd[key] = value
                self._save_commands()
                return True
        return False
    
    def search_commands(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索命令，按复制次数排序"""
        if not query:
            # 直接按 copy_count 排序
            return sorted(self.commands, key=lambda c: c.get('copy_count', 0), reverse=True)[:limit]
        
        query = query.lower()
        scored_commands = []
        
        for cmd in self.commands:
            score = 0
            if query in cmd['name'].lower():
                score += 5
            if query in cmd['group'].lower():
                score += 3
            if query in cmd['description'].lower():
                score += 1
            if query in cmd['command'].lower():
                score += 1
            
            if score > 0:
                scored_commands.append((score, cmd))
        
        # 先按分数，再按 copy_count 排序
        scored_commands.sort(key=lambda x: (x[0], x[1].get('copy_count', 0)), reverse=True)
        return [cmd for score, cmd in scored_commands[:limit]]
    
    def get_command_by_id(self, command_id: int) -> Optional[Dict]:
        """根据ID获取命令"""
        for cmd in self.commands:
            if cmd['id'] == command_id:
                return cmd
        return None

    def parse_parameters(self, command):
        """
        参数解析方法，匹配以下格式：
        1. 必需参数: <param>
        2. 可选参数: <param=default> 或 <param="default with spaces">
        """
        params = OrderedDict()
        # 匹配 <param> 或 <param=value> 或 <param="value with spaces">
        pattern = r'<([^>=]+)(?:=([^>]*))?>'
        
        for match in re.finditer(pattern, command):
            param_name, default_value = match.groups()
            is_required = default_value is None
            # 处理带引号的默认值
            if default_value and default_value.startswith('"') and default_value.endswith('"'):
                default_value = default_value[1:-1]
            params[param_name] = (is_required, default_value if not is_required else None)
        
        return params

    def increase_copy_count(self, command_id: int):
        """复制次数+1"""
        for cmd in self.commands:
            if cmd['id'] == command_id:
                cmd['copy_count'] = cmd.get('copy_count', 0) + 1
                self._save_commands()
                break

    def get_all_groups(self) -> list:
        """获取所有分组（去重）"""
        return sorted(set(cmd['group'] for cmd in self.commands if cmd['group']))
