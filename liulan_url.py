import requests
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from selenium.webdriver.chrome.options import Options
import random
import platform

dy_url = 'https://www.douyin.com/video/7407849464334961935'

def generate_random_headers():
    """生成随机的真实请求头"""
    # 操作系统和平台信息
    os_info = {
        'Windows': [
            ('Windows NT 10.0', 'Win64; x64'),
            ('Windows NT 10.0', 'WOW64'),
            ('Windows NT 11.0', 'Win64; x64')
        ],
        'Mac': [
            ('Macintosh; Intel Mac OS X 10_15_7',),
            ('Macintosh; Intel Mac OS X 11_0_1',),
            ('Macintosh; Intel Mac OS X 12_0_1',)
        ]
    }

    # Chrome版本范围（最近的稳定版本）
    chrome_versions = [str(x) for x in range(120, 123)]  # Chrome 120-122
    
    # 随机生成 Chrome 小版本号
    build_numbers = [
        f"{random.randint(0, 99)}.{random.randint(0, 9999)}.{random.randint(0, 99)}"
        for _ in range(3)
    ]

    # 根据实际系统选择操作系统信息
    current_os = 'Windows' if platform.system() == 'Windows' else 'Mac'
    os_choice = random.choice(os_info[current_os])
    
    # 生成完整的User-Agent
    chrome_version = random.choice(chrome_versions)
    build_number = random.choice(build_numbers)
    
    user_agent = f"Mozilla/5.0 ({'; '.join(os_choice)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.{build_number} Safari/537.36"
    
    # 生成随机的 Accept 和 Accept-Language
    accept_language = random.choice([
        "zh-CN,zh;q=0.9,en;q=0.8",
        "zh-CN,zh;q=0.9",
        "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "zh-CN,zh;q=0.9,en-GB;q=0.8,en;q=0.7"
    ])
    
    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': accept_language,
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'sec-ch-ua-platform': f'"{current_os}"',
        'sec-ch-ua': f'"Google Chrome";v="{chrome_version}"',
        'sec-ch-ua-mobile': '?0'
    }
    
    return headers

def liulan_url(url, proxy=None, headless=False, view_time=10, max_retries=3, keep_browser=False):
    driver = None
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"尝试访问URL: {url}")
            if proxy:
                print(f"使用代理: {proxy}")
            
            # 配置Chrome选项
            chrome_options = Options()
            
            # 无头模式设置
            if headless:
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--window-size=1920,1080')  # 设置窗口大小
            
            # 设置代理
            if proxy:
                chrome_options.add_argument(f'--proxy-server={proxy}')
            
            # 设置随机请求头
            headers = generate_random_headers()
            for key, value in headers.items():
                chrome_options.add_argument(f'--header={key}: {value}')
            
            # 基础优化配置
            chrome_options.add_argument('--mute-audio')  # 关闭声音
            chrome_options.add_argument('--disable-dev-shm-usage')  # 禁用/dev/shm使用
            
            # 性能优化
            chrome_options.add_argument('--disable-logging')  # 禁用日志
            chrome_options.add_argument('--disable-dev-tools')  # 禁用开发者工具
            chrome_options.add_argument('--disable-web-security')  # 禁用网页安全性检查
            chrome_options.add_argument('--disable-client-side-phishing-detection')  # 禁用钓鱼检测
            chrome_options.add_argument('--disable-popup-blocking')  # 禁用弹窗拦截
            chrome_options.add_argument('--disable-sync')  # 禁用同步
            chrome_options.add_argument('--disable-default-apps')  # 禁用默认应用
            
            # 后台优化
            chrome_options.add_argument('--disable-background-networking')  # 禁用后台网络
            chrome_options.add_argument('--disable-background-timer-throttling')  # 禁用后台计时器限制
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')  # 禁用后台窗口
            chrome_options.add_argument('--disable-breakpad')  # 禁用崩溃报告
            
            # 缓存优化
            chrome_options.add_argument('--disk-cache-size=1')  # 最小化磁盘缓存
            chrome_options.add_argument('--media-cache-size=1')  # 最小化媒体缓存
            
            # 实验性优化
            chrome_options.add_argument('--ignore-certificate-errors')  # 忽略证书错误
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # 禁用自动化标记
            
            # 设置页面加载策略
            chrome_options.page_load_strategy = 'eager'  # 等待 DOMContentLoaded 事件
            
            # 添加实验性选项
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 优化预加载设置
            chrome_options.add_experimental_option('prefs', {
                'profile.default_content_setting_values': {
                    'notifications': 2,  # 禁用通知
                    'plugins': 2  # 禁用插件
                },
                'profile.managed_default_content_settings': {
                    'plugins': 2
                },
                'profile.managed_default_content_settings.images': 1,  # 允许图片加载
                'profile.managed_default_content_settings.javascript': 1,  # 允许JavaScript
                'profile.default_content_settings.cookies': 2,  # 禁用cookies
                'profile.managed_default_content_settings.plugins': 2,  # 禁用插件
                'profile.default_content_settings.popups': 2,  # 禁用弹窗
                'profile.default_content_settings.geolocation': 2,  # 禁用地理位置
                'profile.default_content_settings.media_stream': 2,  # 禁用媒体流
            })
            
            # 创建浏览器实例
            driver = webdriver.Chrome(options=chrome_options)
            
            # 如果是保持浏览器模式，直接返回driver
            if keep_browser:
                if headless:
                    print("无头模式浏览器创建成功")
                return True, "浏览器创建成功", driver
            
            # 访问URL
            driver.get(url)
            print('页面加载完成')
            
            # 处理登录窗口 - 使用多个可能的选择器
            try:
                # 等待登录窗口出现（使用多个可能的选择器）
                login_selectors = [
                    '//*[@id="login-pannel"]/div/div/div[1]/div[1]',  # 原始选择器
                    '//div[contains(@class, "login-guide-container")]',  # 类名选择器
                    '//div[contains(@class, "login")]//div[contains(@class, "close")]',  # 关闭按钮
                    '//div[contains(@class, "modal")]//div[contains(@class, "close")]'   # 通用模态框关闭按钮
                ]
                
                for selector in login_selectors:
                    try:
                        # 等待元素出现
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
                                time.sleep(1)  # 等待关闭动画
                                break
                            except:
                                continue
                        break
                    except:
                        continue
                        
            except Exception as e:
                print(f"处理登录窗口时出错: {str(e)}")
                # 继续执行，不要因为登录窗口处理失败就中断
            
            # 等待视频加载
            try:
                video_selectors = [
                    '//*[@id="douyin-right-container"]/div[2]/div/div/div[1]/div[2]/div/xg-video-container/video',
                    '//video[contains(@class, "video")]',
                    '//div[contains(@class, "video-container")]//video'
                ]
                
                video_found = False
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
                    print('视频元素加载完成')
                    time.sleep(view_time)
                    driver.quit()
                    return True, "浏览成功", None
                else:
                    raise Exception("未找到视频元素")
                    
            except Exception as e:
                print(f"等待视频加载失败: {str(e)}")
                if driver:
                    driver.quit()
                retry_count += 1
                continue
                
        except Exception as e:
            print(f"访问出错: {str(e)}")
            error_msg = str(e)
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            
            retry_count += 1
            if retry_count >= max_retries:
                return False, f"重试{max_retries}次后失败: {error_msg}", None
            
            print(f"第{retry_count}次重试...")
            time.sleep(2)
            continue
    
    # 如果所有重试都失败
    return False, f"重试 {max_retries} 次后仍然失败", None

if __name__ == "__main__":
    dy_url = 'https://www.douyin.com/video/7407849464334961935'
    success, message, driver = liulan_url(dy_url)
    print(f"结果: {success}, 信息: {message}")


