import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

class LinkManager:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("链接管理器")
        self.window.geometry("800x600")
        
        # 存储链接配置的列表
        self.links = []
        self.config_file = 'link_config.json'
        
        # 加载已有配置
        self.load_configs()
        
        self.confirmed = False  # 添加确认标志
        
        self.create_widgets()
        
    def load_configs(self):
        """加载已保存的配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.links = json.load(f)
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {str(e)}")
            self.links = []
    
    def save_configs(self):
        """保存当前配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.links, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def create_widgets(self):
        # 链接列表区域
        list_frame = ttk.LabelFrame(self.window, text="链接列表", padding=5)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建表格
        columns = ('url', 'thread_count', 'view_count', 'view_time', 'headless')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # 定义列
        self.tree.heading('url', text='链接')
        self.tree.heading('thread_count', text='线程数')
        self.tree.heading('view_count', text='浏览次数')
        self.tree.heading('view_time', text='浏览时间(秒)')
        self.tree.heading('headless', text='无头模式')
        
        # 设置列宽
        self.tree.column('url', width=300)
        self.tree.column('thread_count', width=80)
        self.tree.column('view_count', width=80)
        self.tree.column('view_time', width=100)
        self.tree.column('headless', width=80)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 编辑区域
        edit_frame = ttk.LabelFrame(self.window, text="链接配置", padding=5)
        edit_frame.pack(fill='x', padx=5, pady=5)
        
        # URL输入
        ttk.Label(edit_frame, text="链接:").grid(row=0, column=0, padx=5, pady=5)
        self.url_entry = ttk.Entry(edit_frame, width=50)
        self.url_entry.grid(row=0, column=1, columnspan=3, padx=5, pady=5)
        
        # 线程数量
        ttk.Label(edit_frame, text="线程数:").grid(row=1, column=0, padx=5, pady=5)
        self.thread_count = ttk.Spinbox(edit_frame, from_=1, to=10, width=10)
        self.thread_count.set(3)
        self.thread_count.grid(row=1, column=1, padx=5, pady=5)
        
        # 浏览次数
        ttk.Label(edit_frame, text="浏览次数:").grid(row=1, column=2, padx=5, pady=5)
        self.view_count = ttk.Spinbox(edit_frame, from_=1, to=1000, width=10)
        self.view_count.set(1)
        self.view_count.grid(row=1, column=3, padx=5, pady=5)
        
        # 浏览时间
        ttk.Label(edit_frame, text="浏览时间(秒):").grid(row=2, column=0, padx=5, pady=5)
        self.view_time = ttk.Spinbox(edit_frame, from_=1, to=3600, width=10)
        self.view_time.set(10)
        self.view_time.grid(row=2, column=1, padx=5, pady=5)
        
        # 无头模式
        self.headless_var = tk.BooleanVar()
        ttk.Checkbutton(edit_frame, text="无头模式", variable=self.headless_var).grid(row=2, column=2, columnspan=2, padx=5, pady=5)
        
        # 按钮区域
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text="添加链接", command=self.add_link).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="修改选中", command=self.edit_link).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="删除选中", command=self.delete_link).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="批量导入", command=self.batch_import).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="导出配置", command=self.export_config).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="确认配置", command=self.confirm).pack(side='right', padx=5)
        
        # 在创建完表格后，加载已有配置到表格
        self.load_table()
    
    def load_table(self):
        """加载配置到表格"""
        for config in self.links:
            self.tree.insert('', 'end', values=(
                config['url'],
                config['thread_count'],
                config['view_count'],
                config['view_time'],
                '是' if config['headless'] else '否'
            ))
    
    def add_link(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入链接")
            return
            
        config = {
            'url': url,
            'thread_count': int(self.thread_count.get()),
            'view_count': int(self.view_count.get()),
            'view_time': int(self.view_time.get()),
            'headless': self.headless_var.get()
        }
        
        self.links.append(config)
        self.tree.insert('', 'end', values=(
            config['url'],
            config['thread_count'],
            config['view_count'],
            config['view_time'],
            '是' if config['headless'] else '否'
        ))
        
        # 清空输入
        self.url_entry.delete(0, 'end')
        
    def edit_link(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要修改的链接")
            return
            
        item = selected[0]
        index = self.tree.index(item)
        
        config = {
            'url': self.url_entry.get().strip(),
            'thread_count': int(self.thread_count.get()),
            'view_count': int(self.view_count.get()),
            'view_time': int(self.view_time.get()),
            'headless': self.headless_var.get()
        }
        
        self.links[index] = config
        self.tree.item(item, values=(
            config['url'],
            config['thread_count'],
            config['view_count'],
            config['view_time'],
            '是' if config['headless'] else '否'
        ))
        
    def delete_link(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的链接")
            return
            
        for item in selected:
            index = self.tree.index(item)
            self.links.pop(index)
            self.tree.delete(item)
            
    def batch_import(self):
        text = self.url_entry.get().strip()
        if not text:
            messagebox.showerror("错误", "请输入链接")
            return
            
        urls = text.split('\n')
        for url in urls:
            url = url.strip()
            if url:
                config = {
                    'url': url,
                    'thread_count': int(self.thread_count.get()),
                    'view_count': int(self.view_count.get()),
                    'view_time': int(self.view_time.get()),
                    'headless': self.headless_var.get()
                }
                
                self.links.append(config)
                self.tree.insert('', 'end', values=(
                    config['url'],
                    config['thread_count'],
                    config['view_count'],
                    config['view_time'],
                    '是' if config['headless'] else '否'
                ))
                
        self.url_entry.delete(0, 'end')
        
    def export_config(self):
        if not self.links:
            messagebox.showwarning("提示", "没有可导出的配置")
            return
            
        try:
            with open('link_config.json', 'w', encoding='utf-8') as f:
                json.dump(self.links, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("成功", "配置已导出到 link_config.json")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
            
    def confirm(self):
        if not self.links:
            messagebox.showwarning("提示", "请先添加链接")
            return
        
        self.save_configs()  # 保存配置
        self.confirmed = True  # 设置确认标志
        self.window.destroy()
        
    def get_configs(self):
        """只有在确认后才返回配置"""
        return self.links if self.confirmed else None 