## 1. 导入
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import threading
from queue import Queue, Empty
import time
from liulan_url import liulan_url
from proxy_setting import ProxyManager
from link_manager import LinkManager
import random
from datetime import datetime, timedelta
import requests
import urllib3
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

## 2. 主体 可视化界面 要求：
## 2.1 自定义抖音输入抖音视频链接输入   支持单链接、批量链接处理、链接文件导入、json格式链接输入，自定义参数有 线程数量、浏览时间、浏览任务次数
## 2.2 进行浏览器打开访问 自定义是否显示窗口
## 2.3 根据liulan_url.py 进行视频浏览,处理登录窗口，视频浏览等，视屏资源加载完成代表一个任务完成
## 2.4 实时显示任务进度，所有任务完成后，显示完成，在窗口弹出浏览次数，完成数量 成功数量，失败数量 ，失败原因等
## 2.5 自定义是否使用代理 代理ip：port ，代理过期时间，会显示在窗口上 
## 2.6 代理测试功能，逻辑在proxy_setting.py 中

## 3. 代理配置
## 3.1 自定义代理链接输入，根据proxy_setting.py 进行代理获取测试相关逻辑，获取到的代理保存到文件中，文件只留存一个代理，每次选择使用代理，首先检查文件中代理是否可用，可用就用，不可用重新申请保存进去，浏览任务每个次数任务进行前都检查一次代理是否可用，不可用就重新申请保存进去
## 4. 主函数


## 5.多线程配置，要求，一个线程最多只能打开一个浏览器
## 5.1 多线程配置，要求，一个线程最多只能打开一个浏览器
## 5.2 浏览器实例在线程范围，一个线程一个浏览器实例，线程数量自定义
## 5.3 根据浏览次数，给每个线程平均分配浏览任务

## 6. 任务进度显示
## 6.1 实时显示任务进度，所有任务完成后，显示完成，在窗口弹出浏览次数，完成数量 成功数量，失败数量 ，失败原因等

## 7.每个浏览任务使用随机真实的请求头

## 8. 浏览器配置
## 8.1 自定义无头还是有头
## 8.2 默认关闭声音，优化打开速度
## 8.3 默认关闭cookie，优化打开速度
## 8.4 默认关闭浏览器缓存，优化打开速度
## 8.5 默认关闭浏览器插件，优化打开速度
## 8.6 默认关闭浏览器插件，优化打开速度

class RateLimiter:
    def __init__(self, max_requests, time_window):
        self.max_requests = max_requests  # 最大请求数
        self.time_window = time_window    # 时间窗口(秒)
        self.requests = []
        self.lock = threading.Lock()
        
    def acquire(self):
        with self.lock:
            now = datetime.now()
            # 清理过期的请求记录
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < timedelta(seconds=self.time_window)]
            
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False
            
    def wait(self):
        while not self.acquire():
            time.sleep(0.5)

class BrowserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("抖音视频浏览工具")
        self.root.geometry("800x600")
        
        # 任务状态变量
        self.total_tasks = 0
        self.success_count = 0
        self.failed_count = 0
        self.running = False
        self.task_queue = Queue()
        self.threads = []
        self.driver_list = []  # 存储所有浏览器实例
        
        self.progress_bar = None
        self.progress_var = None
        self.network_semaphore = threading.Semaphore(2)  # 限制最大并发网络请求数为2
        self.rate_limiter = RateLimiter(max_requests=3, time_window=10)  # 10秒内最多3个请求
        self.browser_pool = {}  # 存储线程ID到浏览器实例的映射
        self.proxy_pool = {}    # 存储线程ID到代理的映射
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # 全局禁用警告
        self.create_widgets()
        
    def create_widgets(self):
        # 创建标签页
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 主设置页面
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="主设置")
        
        # URL输入区域
        url_frame = ttk.LabelFrame(main_frame, text="视频链接输入", padding=5)
        url_frame.pack(fill='x', padx=5, pady=5)
        
        self.url_text = tk.Text(url_frame, height=5)
        self.url_text.pack(fill='x')
        
        # 导入按钮
        btn_frame = ttk.Frame(url_frame)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="导入文件", command=self.import_file).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="导入JSON", command=self.import_json).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="生成JSON", command=self.generate_json).pack(side='left', padx=5)
        
        # 任务设置
        settings_frame = ttk.LabelFrame(main_frame, text="任务设置", padding=5)
        settings_frame.pack(fill='x', padx=5, pady=5)
        
        # 线程数量
        ttk.Label(settings_frame, text="线程数量:").grid(row=0, column=0, padx=5, pady=5)
        self.thread_count = ttk.Spinbox(settings_frame, from_=1, to=10, width=10)
        self.thread_count.set(3)
        self.thread_count.grid(row=0, column=1, padx=5, pady=5)
        
        # 浏览次数
        ttk.Label(settings_frame, text="浏览次数:").grid(row=0, column=2, padx=5, pady=5)
        self.view_count = ttk.Spinbox(settings_frame, from_=1, to=1000, width=10)
        self.view_count.set(1)
        self.view_count.grid(row=0, column=3, padx=5, pady=5)
        
        # 浏览时间
        ttk.Label(settings_frame, text="浏览时间(秒):").grid(row=1, column=0, padx=5, pady=5)
        self.view_time = ttk.Spinbox(settings_frame, from_=1, to=3600, width=10)
        self.view_time.set(10)
        self.view_time.grid(row=1, column=1, padx=5, pady=5)
        
        # 浏览器设置
        browser_frame = ttk.LabelFrame(main_frame, text="浏览器设置", padding=5)
        browser_frame.pack(fill='x', padx=5, pady=5)
        
        self.headless_var = tk.BooleanVar()
        ttk.Checkbutton(browser_frame, text="无头模式", variable=self.headless_var).pack(side='left', padx=5)
        
        # 代理设置
        proxy_frame = ttk.LabelFrame(main_frame, text="代理设置", padding=5)
        proxy_frame.pack(fill='x', padx=5, pady=5)
        
        # 添加代理API输入
        ttk.Label(proxy_frame, text="代理API链接:").pack(side='left', padx=5)
        self.proxy_api = ttk.Entry(proxy_frame, width=50)
        self.proxy_api.pack(side='left', padx=5, fill='x', expand=True)
        self.proxy_api.insert(0, 'https://sch.shanchendaili.com/api.html?action=get_ip&key=HU827fb6a19392790683Fgfd&time=10&count=1&type=json&only=0')
        
        # 代理状态显示
        self.proxy_status = tk.StringVar(value="未使用代理")
        self.proxy_label = ttk.Label(proxy_frame, textvariable=self.proxy_status)
        self.proxy_label.pack(side='top', padx=5, pady=5)
        
        self.use_proxy_var = tk.BooleanVar()
        ttk.Checkbutton(proxy_frame, text="使用代理", variable=self.use_proxy_var, command=self.toggle_proxy).pack(side='left', padx=5)
        ttk.Button(proxy_frame, text="测试代理", command=self.test_proxy).pack(side='left', padx=5)
        
        # 进度显示
        progress_frame = ttk.LabelFrame(main_frame, text="任务进度", padding=5)
        progress_frame.pack(fill='x', padx=5, pady=5)
        
        self.progress_var = tk.StringVar(value="准备就绪")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack(fill='x')
        
        # 使用确定模式的进度条
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', maximum=100)
        self.progress_bar.pack(fill='x', pady=5)
        
        # 修改按钮区域
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(control_frame, text="链接管理", command=self.manage_links).pack(side='left', padx=5)
        self.start_btn = ttk.Button(control_frame, text="开始任务", command=self.start_tasks)
        self.start_btn.pack(side='left', padx=5)
        self.stop_btn = ttk.Button(control_frame, text="停止任务", command=self.stop_tasks, state='disabled')
        self.stop_btn.pack(side='left', padx=5)

    def import_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.url_text.delete('1.0', tk.END)
                    self.url_text.insert('1.0', f.read())
            except Exception as e:
                messagebox.showerror("错误", f"导入文件失败: {str(e)}")

    def import_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.url_text.delete('1.0', tk.END)
                        self.url_text.insert('1.0', '\n'.join(data))
                    else:
                        messagebox.showerror("错误", "JSON格式不正确，应为URL列表")
            except Exception as e:
                messagebox.showerror("错误", f"导入JSON失败: {str(e)}")

    def generate_json(self):
        """生成JSON格式的链接配置"""
        try:
            urls = self.url_text.get('1.0', tk.END).strip().split('\n')
            urls = [url.strip() for url in urls if url.strip()]
            
            if not urls:
                messagebox.showerror("错误", "请先输入链接")
                return
                
            json_data = []
            for url in urls:
                task = {
                    "url": url,
                    "thread_count": int(self.thread_count.get()),
                    "view_count": int(self.view_count.get()),
                    "view_time": int(self.view_time.get()),
                    "headless": self.headless_var.get()
                }
                json_data.append(task)
                
            # 将当前输入框内容替换为JSON格式
            self.url_text.delete('1.0', tk.END)
            self.url_text.insert('1.0', json.dumps(json_data, indent=2, ensure_ascii=False))
            
        except Exception as e:
            messagebox.showerror("错误", f"生成JSON失败: {str(e)}")

    def toggle_proxy(self):
        if self.use_proxy_var.get():
            proxy_manager = ProxyManager()
            # 使用输入框中的API链接
            api_url = self.proxy_api.get().strip()
            if not api_url:
                self.use_proxy_var.set(False)
                messagebox.showerror("错误", "请输入代理API链接")
                self.proxy_status.set("未使用代理")
                return
            
            proxy, message = proxy_manager.get_valid_proxy(api_url)
            if proxy:
                self.proxy_status.set(f"当前代理: {proxy['ip']}:{proxy['port']}\n过期时间: {proxy['expire']}")
            else:
                self.use_proxy_var.set(False)
                messagebox.showerror("错误", f"获取代理失败: {message}")
                self.proxy_status.set("未使用代理")
        else:
            self.proxy_status.set("未使用代理")

    def test_proxy(self):
        if not self.use_proxy_var.get():
            messagebox.showinfo("提示", "请先启用代理")
            return
        
        api_url = self.proxy_api.get().strip()
        if not api_url:
            messagebox.showerror("错误", "请输入代理API链接")
            return
        
        proxy_manager = ProxyManager()
        proxy, message = proxy_manager.get_valid_proxy(api_url)
        if proxy:
            if proxy_manager.test_proxy(proxy['ip'], proxy['port']):
                messagebox.showinfo("成功", f"代理测试成功\nIP: {proxy['ip']}\n端口: {proxy['port']}\n过期时间: {proxy['expire']}")
            else:
                messagebox.showerror("错误", "代理测试失败")
        else:
            messagebox.showerror("错误", f"获取代理失败: {message}")

    def check_network():
        """检查网络状态"""
        try:
            requests.get("https://www.douyin.com", timeout=5)
            return True
        except:
            return False

    def worker(self, thread_id):
        """工作线程"""
        proxy_manager = ProxyManager()
        driver = None
        max_proxy_retries = 3
        
        try:
            # 获取该线程专用的代理
            if self.use_proxy_var.get():
                proxy_retry_count = 0
                while proxy_retry_count < max_proxy_retries:
                    api_url = self.proxy_api.get().strip()
                    proxy, message = proxy_manager.get_valid_proxy(api_url)
                    if proxy:
                        proxy_str = f"http://{proxy['ip']}:{proxy['port']}"
                        self.proxy_pool[thread_id] = proxy_str
                        self.update_status(f"线程 {thread_id}: 使用代理 {proxy_str}")
                        break
                    proxy_retry_count += 1
                    if proxy_retry_count >= max_proxy_retries:
                        self.update_status(f"线程 {thread_id}: 获取代理失败，将不使用代理")
                    time.sleep(2)
        
            while self.running:
                try:
                    task = self.task_queue.get_nowait()
                    remaining_views = task['view_count']
                    
                    # 只在第一次访问时创建浏览器实例
                    if driver is None:
                        success, message, driver = liulan_url(
                            url=task['url'],
                            proxy=self.proxy_pool.get(thread_id),
                            headless=task['headless'],
                            view_time=1,  # 创建浏览器时设置较短的等待时间
                            max_retries=1,
                            keep_browser=True
                        )
                        
                        if not success or not driver:
                            self.update_status(f"线程 {thread_id}: 创建浏览器失败 - {message}")
                            self.failed_count += 1
                            self.update_progress()
                            continue
                        
                        self.browser_pool[thread_id] = driver
                        self.update_status(f"线程 {thread_id}: {'无头模式' if task['headless'] else '有头模式'}浏览器创建成功")
                    
                    # 使用已创建的浏览器实例完成剩余的浏览次数
                    while remaining_views > 0 and self.running:
                        try:
                            self.update_status(f"线程 {thread_id}: 正在处理第 {task['view_count'] - remaining_views + 1}/{task['view_count']} 次浏览")
                            
                            # 访问URL
                            driver.get(task['url'])
                            
                            # 处理登录窗口
                            try:
                                # 等待登录窗口出现（使用多个可能的选择器）
                                login_selectors = [
                                    '//*[@id="login-pannel"]/div/div/div[1]/div[1]',
                                    '//div[contains(@class, "login-guide-container")]',
                                    '//div[contains(@class, "login")]//div[contains(@class, "close")]',
                                    '//div[contains(@class, "modal")]//div[contains(@class, "close")]'
                                ]
                                
                                for selector in login_selectors:
                                    try:
                                        element = WebDriverWait(driver, 3).until(
                                            EC.presence_of_element_located((By.XPATH, selector))
                                        )
                                        print(f"找到登录窗口元素: {selector}")
                                        
                                        # 尝试点击关闭按钮
                                        close_buttons = driver.find_elements(By.XPATH, 
                                            '//div[contains(@class, "close") or contains(@class, "cancel")]')
                                        for button in close_buttons:
                                            try:
                                                button.click()
                                                print("成功关闭登录窗口")
                                                time.sleep(1)
                                                break
                                            except:
                                                continue
                                        break
                                    except:
                                        continue
                            except Exception as e:
                                print(f"处理登录窗口时出错: {str(e)}")
                            
                            # 等待视频加载
                            video_found = False
                            video_selectors = [
                                '//*[@id="douyin-right-container"]/div[2]/div/div/div[1]/div[2]/div/xg-video-container/video',
                                '//video[contains(@class, "video")]',
                                '//div[contains(@class, "video-container")]//video'
                            ]
                            
                            for selector in video_selectors:
                                try:
                                    video = WebDriverWait(driver, 5).until(
                                        EC.presence_of_element_located((By.XPATH, selector))
                                    )
                                    print(f"找到视频元素: {selector}")
                                    video_found = True
                                    break
                                except:
                                    continue
                            
                            if video_found:
                                time.sleep(task['view_time'])
                                self.success_count += 1
                            else:
                                raise Exception("未找到视频元素")
                            
                        except Exception as e:
                            self.failed_count += 1
                            self.update_status(f"线程 {thread_id}: 浏览失败 - {str(e)}")
                        
                        remaining_views -= 1
                        self.update_progress()
                    
                    self.task_queue.task_done()
                    
                except Empty:
                    break
                
        except Exception as e:
            if self.running:
                self.update_status(f"线程 {thread_id} 发生错误: {str(e)}")
        finally:
            # 清理资源
            if thread_id in self.browser_pool:
                try:
                    self.browser_pool[thread_id].quit()
                except:
                    pass
                del self.browser_pool[thread_id]
            if thread_id in self.proxy_pool:
                del self.proxy_pool[thread_id]

    def reset_progress(self):
        """重置进度条和计数"""
        self.total_tasks = 0
        self.success_count = 0
        self.failed_count = 0
        self.progress_bar['value'] = 0
        self.progress_var.set("准备就绪")
        self.root.update()
        
    def update_progress(self):
        """更新进度条和状态显示"""
        try:
            completed = self.success_count + self.failed_count
            if self.total_tasks > 0:  # 防止除以零
                progress = (completed / self.total_tasks) * 100
                
                # 更新进度条
                self.progress_bar['value'] = progress
                
                # 更新状态文本
                status = (
                    f"总任务: {self.total_tasks} | "
                    f"成功: {self.success_count} | "
                    f"失败: {self.failed_count} | "
                    f"进度: {progress:.1f}%"
                )
                self.progress_var.set(status)
                
                # 强制更新界面
                self.root.update_idletasks()
                
                # 检查是否完成所有任务
                if completed >= self.total_tasks:
                    self.running = False
                    self.start_btn['state'] = 'normal'
                    self.stop_btn['state'] = 'disabled'
                    messagebox.showinfo("完成", 
                        f"任务完成\n"
                        f"总任务数: {self.total_tasks}\n"
                        f"成功数量: {self.success_count}\n"
                        f"失败数量: {self.failed_count}"
                    )
                    self.reset_progress()
        except Exception as e:
            print(f"更新进度出错: {str(e)}")

    def start_tasks(self):
        """开始任务"""
        try:
            # 重置进度
            self.reset_progress()
            
            # 获取配置
            configs = self.get_task_configs()
            if not configs:
                return
                
            # 清空输入框，避免重复执行
            self.url_text.delete('1.0', tk.END)
            
            # 初始化任务队列
            self.task_queue = Queue()
            
            # 添加任务到队列，使用链接管理器中的配置参数
            for task in configs:
                self.task_queue.put({
                    'url': task['url'],
                    'view_count': task['view_count'],
                    'headless': task['headless'],
                    'view_time': task['view_time'],  # 使用链接管理器中的浏览时间
                    'thread_count': task['thread_count']  # 使用链接管理器中的线程数
                })
                self.total_tasks += task['view_count']  # 总任务数是浏览次数的总和
            
            # 更新初始进度显示
            self.progress_var.set(f"总任务: {self.total_tasks} | 开始执行...")
            self.progress_bar['value'] = 0
            
            # 启动工作线程，使用链接管理器中设置的线程数
            self.running = True
            self.threads = []
            
            # 获取所有任务中设置的最大线程数
            max_thread_count = max(task['thread_count'] for task in configs)
            thread_count = min(max_thread_count, self.task_queue.qsize())  # 线程数不超过任务数
            
            # 启动工作线程
            for i in range(thread_count):
                thread = threading.Thread(
                    target=self.worker,
                    args=(f"线程-{i+1}",)
                )
                thread.daemon = True
                thread.start()
                self.threads.append(thread)
                time.sleep(0.5)  # 短暂延时，避免同时启动
            
            self.start_btn['state'] = 'disabled'
            self.stop_btn['state'] = 'normal'
            
        except Exception as e:
            messagebox.showerror("错误", f"启动任务失败: {str(e)}")
            self.reset_progress()

    def stop_tasks(self):
        """立即停止所有任务"""
        try:
            # 先设置停止标志
            self.running = False
            
            # 等待所有任务完成
            while not self.task_queue.empty():
                try:
                    self.task_queue.get_nowait()
                    self.task_queue.task_done()
                except Empty:
                    break
            
            # 关闭所有浏览器实例
            for driver in self.driver_list[:]:  # 使用列表副本进行遍历
                try:
                    driver.quit()
                except:
                    pass
                try:
                    self.driver_list.remove(driver)
                except:
                    pass
            
            # 等待所有线程结束
            for thread in self.threads[:]:  # 使用列表副本进行遍历
                try:
                    thread.join(timeout=1)  # 给每个线程1秒钟时间结束
                except:
                    pass
                try:
                    self.threads.remove(thread)
                except:
                    pass
            
            # 重置所有状态
            self.threads.clear()
            self.driver_list.clear()
            self.task_queue = Queue()
            self.total_tasks = 0
            self.success_count = 0
            self.failed_count = 0
            
            # 更新界面状态
            self.start_btn['state'] = 'normal'
            self.stop_btn['state'] = 'disabled'
            self.progress_var.set("任务已停止")
            self.progress_bar['value'] = 0
            self.root.update()
            
            messagebox.showinfo("停止", "已停止所有任务")
            
        except Exception as e:
            messagebox.showerror("错误", f"停止任务时出错: {str(e)}")
        finally:
            # 确保清理所有资源
            self.running = False
            self.threads.clear()
            self.driver_list.clear()
            self.task_queue = Queue()

    def get_task_configs(self):
        """获取任务配置，优先使用链接管理器的配置"""
        try:
            # 首先尝试从链接管理器配置文件读取
            try:
                with open('link_config.json', 'r', encoding='utf-8') as f:
                    configs = json.load(f)
                
                if configs:
                    # 确认是否要执行这些任务
                    tasks_info = "\n".join([
                        f"链接: {c['url']}, "
                        f"线程数: {c['thread_count']}, "
                        f"浏览次数: {c['view_count']}, "
                        f"浏览时间: {c['view_time']}秒, "
                        f"无头模式: {'是' if c['headless'] else '否'}"
                        for c in configs[:3]
                    ])
                    if len(configs) > 3:
                        tasks_info += f"\n... 等共 {len(configs)} 个任务"
                    
                    if messagebox.askyesno("确认", f"是否执行链接管理器中的任务？\n\n{tasks_info}"):
                        return configs
                
            except Exception as e:
                print(f"读取链接配置文件失败: {str(e)}")
            
            # 如果没有链接管理器配置，则使用主界面输入
            urls = self.url_text.get('1.0', tk.END).strip().split('\n')
            urls = [url.strip() for url in urls if url.strip()]
            
            if urls:
                # 使用主界面输入的链接和参数
                configs = []
                for url in urls:
                    config = {
                        'url': url,
                        'thread_count': int(self.thread_count.get()),
                        'view_count': int(self.view_count.get()),
                        'view_time': int(self.view_time.get()),
                        'headless': self.headless_var.get()
                    }
                    configs.append(config)
                    
                # 显示任务信息并确认
                tasks_info = "\n".join([
                    f"链接: {c['url']}, "
                    f"线程数: {c['thread_count']}, "
                    f"浏览次数: {c['view_count']}, "
                    f"浏览时间: {c['view_time']}秒, "
                    f"无头模式: {'是' if c['headless'] else '否'}"
                    for c in configs[:3]
                ])
                if len(configs) > 3:
                    tasks_info += f"\n... 等共 {len(configs)} 个任务"
                
                if messagebox.askyesno("确认", f"是否执行以下任务？\n\n{tasks_info}"):
                    return configs
            else:
                messagebox.showwarning("提示", "请输入视频链接或使用链接管理器添加任务")
            
            return None
            
        except Exception as e:
            messagebox.showerror("错误", f"获取任务配置失败: {str(e)}")
            return None

    def update_status(self, message):
        """更新状态信息"""
        try:
            self.progress_var.set(message)
            self.root.update_idletasks()  # 使用update_idletasks代替update
        except Exception as e:
            print(f"更新状态出错: {str(e)}")

    def manage_links(self):
        manager = LinkManager(self.root)
        self.root.wait_window(manager.window)
        # 只有在确认后才更新配置
        configs = manager.get_configs()
        if configs:
            messagebox.showinfo("成功", "链接配置已保存")

# 移除所有直接执行的代码，只保留主程序入口
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = BrowserApp(root)
        print("程序启动成功，正在显示界面...")
        root.mainloop()
    except Exception as e:
        print(f"程序启动失败: {str(e)}")







