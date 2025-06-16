import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Callable, Dict, List
from command_manager import CommandManager


class CommandRetrieverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("命令检索器")
        self.root.geometry("1280x800")  # 宽度从800增加到1200

        self.cmd_manager = CommandManager()
        # 在初始化方法中添加底部状态栏
        self.bottom_frame = ttk.Frame(self.root)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self._setup_ui()

    def _setup_ui(self):
        """设置用户界面（右侧命令预览）"""
        # 主窗口初始尺寸增大
        
        # 主容器框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧面板（搜索+列表+按钮）
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 搜索框
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self._on_search)

        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        search_entry.focus()

        # 命令列表
        self.tree = ttk.Treeview(
            left_frame,
            columns=('ID', 'Name', 'Group', 'Description'),
            show='headings',
            selectmode='browse'
        )
        self.tree.heading('ID', text='ID')
        self.tree.heading('Name', text='名称')
        self.tree.heading('Group', text='分组')
        self.tree.heading('Description', text='描述')
        self.tree.column('ID', width=50, stretch=False)
        self.tree.column('Name', width=150, stretch=False)
        self.tree.column('Group', width=100, stretch=False)
        self.tree.column('Description', width=300, stretch=True)  # 描述列可拉伸
        self.tree.pack(fill=tk.BOTH, expand=True)

        # 添加按钮
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(side=tk.BOTTOM, pady=15, anchor=tk.CENTER)

        add_group_button = ttk.Button(button_frame, text="添加分组", command=self._add_group)
        add_group_button.pack(side=tk.LEFT, padx=(0, 10), expand=True)

        add_button = ttk.Button(button_frame, text="添加命令", command=self._add_command)
        add_button.pack(side=tk.LEFT, expand=True)


        # 右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="复制命令", command=self._copy_command)
        self.context_menu.add_command(label="编辑命令", command=self._edit_command)
        self.context_menu.add_command(label="添加命令", command=self._add_command)
        self.context_menu.add_command(
            label="删除命令", command=self._delete_command)
        self.tree.bind('<Button-3>', self._show_context_menu)

        # ===== 右侧命令预览区 =====
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        preview_label = ttk.Label(
            right_frame, text="命令预览", font=('Arial', 10, 'bold'))
        preview_label.pack(anchor=tk.W, pady=(0, 5))

        # 修改Text组件的宽度以适应120个字符
        self.command_text = tk.Text(
            right_frame,
            wrap=tk.WORD,
            state='disabled',
            background='#f5f5f5',
            font=('Consolas', 10),
            padx=5,
            pady=5,
            height=15,
            width=120  # 调整为约120个字符宽度
        )
        self.command_text.pack(fill=tk.BOTH, expand=True)

        # 参数说明区域
        param_frame = ttk.Frame(right_frame)
        param_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(param_frame, text="参数说明:", font=(
            'Arial', 9)).pack(anchor=tk.W)
        self.param_hint = ttk.Label(
            param_frame,
            text="红色部分为需要替换的参数",
            foreground='red',
            font=('Arial', 9)
        )
        self.param_hint.pack(anchor=tk.W)

        # 绑定选中事件
        self.tree.bind('<<TreeviewSelect>>', self._update_preview)

        # 初始加载数据
        self._refresh_command_list()

    def _update_preview(self, event=None):
        """更新命令预览区（带参数高亮）"""
        cmd = self._get_selected_command()
        self.command_text.config(state='normal')
        self.command_text.delete(1.0, tk.END)

        if cmd:
            import re
            parts = re.split(r'(<[^>]+>)', cmd['command'])

            for part in parts:
                if re.match(r'<[^>]+>', part):
                    self.command_text.insert(tk.END, part, 'param')
                else:
                    self.command_text.insert(tk.END, part)

            # 配置标签样式
            self.command_text.tag_config(
                'param',
                foreground='red',
                font=('Consolas', 10, 'underline')
            )

        self.command_text.config(state='disabled')

    def _refresh_command_list(self, commands: List[Dict] = None):
        """刷新命令列表"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        commands = commands or self.cmd_manager.search_commands('')
        for cmd in commands:
            self.tree.insert('', tk.END, values=(
                cmd['id'],
                cmd['name'],
                cmd['group'],
                cmd['description']
            ), iid=str(cmd['id']))

    def _on_search(self, *args):
        """搜索回调"""
        query = self.search_var.get()
        results = self.cmd_manager.search_commands(query)
        self._refresh_command_list(results)

    def _show_context_menu(self, event):
        """显示右键菜单并确保选中项"""
        item = self.tree.identify_row(event.y)
        if item:
            # 先清除当前选择，然后选中右键点击的行
            self.tree.selection_clear()
            self.tree.selection_set(item)
            self.tree.focus(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _get_selected_command(self) -> Dict:
        """获取当前选中的命令"""
        selection = self.tree.selection()
        if not selection:
            return None
        try:
            cmd_id = int(self.tree.item(selection[0], 'values')[0])  # 获取ID列的值
            return self.cmd_manager.get_command_by_id(cmd_id)
        except (IndexError, ValueError):
            return None
    def _copy_command(self):
        cmd = self._get_selected_command()
        if not cmd:
            return

        params = self.cmd_manager.parse_parameters(cmd['command'])
        if not params:
            self._copy_to_clipboard(cmd['command'])
            self.cmd_manager.increase_copy_count(cmd['id'])
            return

        param_window = tk.Toplevel(self.root)
        param_window.title(f"参数替换 - {cmd['name']}")
        param_window.resizable(False, False)
        
        # 添加预览标签
        ttk.Label(param_window, text="命令预览:", font=('Arial', 9, 'bold')).grid(
            row=0, columnspan=2, pady=(0, 5), sticky=tk.W)
        
        preview_var = tk.StringVar()
        preview_label = ttk.Label(
            param_window, 
            textvariable=preview_var,
            wraplength=350,
            foreground="#333"
        )
        preview_label.grid(row=1, columnspan=2, sticky=tk.W)
        
        entries = {}
        for row, (param, (required, default)) in enumerate(params.items(), start=2):
            label_text = f"{param}:" + ("" if required else f" (默认: {default})")
            ttk.Label(param_window, text=label_text).grid(
                row=row, column=0, padx=5, pady=2, sticky=tk.E)
            
            entry = ttk.Entry(param_window)
            entry.grid(row=row, column=1, padx=5, pady=2, sticky=tk.EW)
            
            if not required and default:
                entry.insert(0, default)
            
            entries[param] = entry
            
            # 动态更新预览 - 修复绑定问题
            entry.bind('<KeyRelease>', lambda event, p=param, e=entries, pv=preview_var, c=cmd['command'], ps=params: self._update_param_preview(pv, c, ps, e))
        
        # 初始预览
        self._update_param_preview(preview_var, cmd['command'], params, entries)
        
        # 底部按钮
        button_frame = ttk.Frame(param_window)
        button_frame.grid(row=len(params)+2, columnspan=2, pady=10)
        
        def _on_copy_submit():
            final_command = cmd['command']
            missing_required = []
            
            for param, (required, default) in params.items():
                value = entries[param].get()
                
                if required and not value:
                    missing_required.append(param)
                    continue
                    
                if not value and default:
                    value = default
                    
                final_command = final_command.replace(
                    f'<{param}>' if required else f'<{param}={default}>', 
                    value
                )
            
            if missing_required:
                messagebox.showerror(
                    "错误", 
                    f"以下必需参数未填写:\n{', '.join(missing_required)}")
                return
            
            self._copy_to_clipboard(final_command)
            self.cmd_manager.increase_copy_count(final_command['id'])
            param_window.destroy()
        
        ttk.Button(
            button_frame, 
            text="复制", 
            command=_on_copy_submit,  # 直接使用函数引用
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="取消", 
            command=param_window.destroy,
            width=10
        ).pack(side=tk.LEFT)
        
        param_window.bind('<Return>', lambda e: _on_copy_submit())
        next(iter(entries.values())).focus()

    def _update_param_preview(self, preview_var, command, params, entries):
        """更新参数预览"""
        temp_cmd = command
        for param, (required, default) in params.items():
            value = entries[param].get() or default or f"<{param}>"
            temp_cmd = temp_cmd.replace(
                f'<{param}>' if required else f'<{param}={default}>',
                value
            )
        preview_var.set(temp_cmd)

    def _copy_to_clipboard(self, text):
        """复制文本到剪贴板并显示提示"""
        
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

        # 显示临时提示（无需点击关闭）
        x, y = self.root.winfo_pointerxy()
        tooltip = tk.Toplevel(self.root)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x+20}+{y+20}")
        label = ttk.Label(
            tooltip,
            text="✓ 已复制到剪贴板",
            background='lightgreen',
            padding=(10, 2),
            font=('Arial', 9)
        )
        label.pack()
        tooltip.after(1500, tooltip.destroy)

    def _show_temp_message(self, message, duration=2000):
        """显示临时消息（自动消失）"""
        if hasattr(self, 'temp_message_label'):
            self.temp_message_label.destroy()

        self.temp_message_label = ttk.Label(
            self.root,
            text=message,
            foreground='green',
            padding=5
        )
        self.temp_message_label.pack(side=tk.BOTTOM, fill=tk.X)

        # 定时消失
        self.root.after(duration, self.temp_message_label.destroy)

    def _add_command(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("添加命令")
        add_window.geometry("600x500")

        # 基本信息字段
        ttk.Label(add_window, text="名称:").grid(
            row=0, column=0, sticky=tk.E, padx=5, pady=5)
        name_entry = ttk.Entry(add_window)
        name_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

        ttk.Label(add_window, text="分组:").grid(
            row=1, column=0, sticky=tk.E, padx=5, pady=5)
        # 使用 Combobox
        group_var = tk.StringVar()
        group_combo = ttk.Combobox(add_window, textvariable=group_var)
        group_combo['values'] = self.cmd_manager.get_all_groups()
        group_combo.set('')  # 默认空
        group_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        group_combo['state'] = 'normal'  # 可输入

        ttk.Label(add_window, text="描述:").grid(
            row=2, column=0, sticky=tk.E, padx=5, pady=5)
        desc_entry = ttk.Entry(add_window)
        desc_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)

        # 参数说明标签
        ttk.Label(add_window, text="参数格式说明:", font=('Arial', 9, 'bold')).grid(
            row=3, columnspan=2, pady=(10, 0), sticky=tk.W)

        ttk.Label(add_window,
                  text="• 必需参数: <param>\n• 可选参数(带默认值): <param=default>",
                  foreground="#666").grid(
            row=4, columnspan=2, sticky=tk.W, padx=10)

        # 命令内容编辑区
        ttk.Label(add_window, text="命令内容:").grid(
            row=5, column=0, sticky=tk.NE, padx=5, pady=5)

        cmd_frame = ttk.Frame(add_window)
        cmd_frame.grid(row=5, column=1, sticky=tk.NSEW, padx=5, pady=5)

        self.cmd_text = tk.Text(cmd_frame, wrap=tk.WORD, width=50, height=10)
        v_scroll = ttk.Scrollbar(
            cmd_frame, orient=tk.VERTICAL, command=self.cmd_text.yview)
        self.cmd_text.configure(yscrollcommand=v_scroll.set)

        self.cmd_text.grid(row=0, column=0, sticky=tk.NSEW)
        v_scroll.grid(row=0, column=1, sticky=tk.NS)

        # 配置网格权重
        add_window.columnconfigure(1, weight=1)
        add_window.rowconfigure(5, weight=1)
        cmd_frame.columnconfigure(0, weight=1)
        cmd_frame.rowconfigure(0, weight=1)

        # 提交按钮
        def on_submit():
            name = name_entry.get()
            group = group_var.get().strip()
            command = self.cmd_text.get("1.0", tk.END).strip()

            if not name or not command:
                messagebox.showerror("错误", "名称和命令内容不能为空")
                return

            if self.cmd_manager.add_command(
                name=name,
                group=group,
                description=desc_entry.get(),
                command=command
            ):
                messagebox.showinfo("成功", "命令添加成功")
                add_window.destroy()
                self._refresh_command_list()

        ttk.Button(add_window, text="添加", command=on_submit).grid(
            row=7, columnspan=2, pady=10)

    def _edit_command(self):
        """编辑命令 - 同样使用多行文本框"""
        cmd = self._get_selected_command()
        if not cmd:
            return

        edit_window = tk.Toplevel(self.root)
        edit_window.title("编辑命令")
        edit_window.geometry("600x400")

        # 布局与_add_command相同，只是初始值不同
        ttk.Label(edit_window, text="名称:").grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.E)
        name_entry = ttk.Entry(edit_window)
        name_entry.insert(0, cmd['name'])
        name_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)

        ttk.Label(edit_window, text="分组:").grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.E)
        group_entry = ttk.Entry(edit_window)
        group_entry.insert(0, cmd['group'])
        group_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W+tk.E)

        ttk.Label(edit_window, text="描述:").grid(
            row=2, column=0, padx=5, pady=5, sticky=tk.E)
        desc_entry = ttk.Entry(edit_window)
        desc_entry.insert(0, cmd['description'])
        desc_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W+tk.E)

        ttk.Label(edit_window, text="命令内容:").grid(
            row=3, column=0, padx=5, pady=5, sticky=tk.NE)

        cmd_frame = ttk.Frame(edit_window)
        cmd_frame.grid(row=3, column=1, padx=5, pady=5,
                       sticky=tk.W+tk.E+tk.N+tk.S)

        cmd_text = tk.Text(cmd_frame, wrap=tk.WORD, width=60, height=15)
        cmd_text.insert("1.0", cmd['command'])
        v_scroll = ttk.Scrollbar(
            cmd_frame, orient=tk.VERTICAL, command=cmd_text.yview)
        cmd_text.configure(yscrollcommand=v_scroll.set)

        cmd_text.grid(row=0, column=0, sticky=tk.W+tk.E+tk.N+tk.S)
        v_scroll.grid(row=0, column=1, sticky=tk.N+tk.S)

        cmd_frame.columnconfigure(0, weight=1)
        cmd_frame.rowconfigure(0, weight=1)
        edit_window.columnconfigure(1, weight=1)
        edit_window.rowconfigure(3, weight=1)

        def on_submit():
            updates = {
                'name': name_entry.get(),
                'group': group_entry.get(),
                'description': desc_entry.get(),
                'command': cmd_text.get("1.0", tk.END).strip()
            }

            if not updates['name'] or not updates['command']:
                messagebox.showerror("错误", "名称和命令内容不能为空")
                return

            if self.cmd_manager.update_command(cmd['id'], **updates):
                messagebox.showinfo("成功", "命令更新成功")
                edit_window.destroy()
                self._refresh_command_list()
            else:
                messagebox.showerror("错误", "更新命令失败")

        button_frame = ttk.Frame(edit_window)
        button_frame.grid(row=4, columnspan=2, pady=10)

        submit_btn = ttk.Button(button_frame, text="更新", command=on_submit)
        submit_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = ttk.Button(button_frame, text="取消",
                                command=edit_window.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        name_entry.focus()
        edit_window.bind('<Return>', lambda e: on_submit())

    def _delete_command(self):
        """删除命令"""
        cmd = self._get_selected_command()
        if not cmd:
            return

        if messagebox.askyesno("确认", f"确定要删除命令 '{cmd['name']}' 吗？"):
            if self.cmd_manager.delete_command(cmd['id']):
                messagebox.showinfo("成功", "命令已删除")
                self._refresh_command_list()
            else:
                messagebox.showerror("错误", "删除命令失败")

    def _add_group(self):
        """弹窗添加新分组"""
        group_name = simpledialog.askstring("添加分组", "请输入新分组名称：", parent=self.root)
        if group_name:
            group_name = group_name.strip()
            if not group_name:
                messagebox.showerror("错误", "分组名称不能为空")
                return
            groups = self.cmd_manager.get_all_groups()
            if group_name in groups:
                messagebox.showinfo("提示", "该分组已存在")
                return
            # 创建一个虚拟命令用于存储新分组（也可以不存，只用于下拉刷新）
            # 这里不需要存储，只需刷新下拉框即可
            messagebox.showinfo("成功", f"分组“{group_name}”已添加，下次添加命令时可选")