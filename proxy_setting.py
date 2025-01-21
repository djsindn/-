##代理配置文件
import requests
import json
import os
import urllib3

class ProxyManager:
    def __init__(self):
        self.proxy_file = "proxy_config.json"
        self.api_url = 'https://sch.shanchendaili.com/api.html?action=get_ip&key=HU827fb6a19392790683Fgfd&time=10&count=1&type=json&only=0'
        
    def save_proxy(self, proxy_data):
        with open(self.proxy_file, 'w') as f:
            json.dump(proxy_data, f)
            
    def load_proxy(self):
        if os.path.exists(self.proxy_file):
            try:
                with open(self.proxy_file, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None
        
    def test_proxy(self, proxy_ip, proxy_port):
        """测试代理是否可用"""
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # 禁用警告
            
            proxy_str = f"http://{proxy_ip}:{proxy_port}"
            proxies = {
                'http': proxy_str,
                'https': proxy_str
            }
            
            # 使用更可靠的测试网站
            test_urls = [
                'http://www.baidu.com',
                'http://www.douyin.com'
            ]
            
            session = requests.Session()
            session.verify = False  # 禁用SSL验证
            
            for url in test_urls:
                response = session.get(
                    url,
                    proxies=proxies,
                    timeout=10
                )
                if response.status_code == 200:
                    return True
            return False
            
        except Exception as e:
            print(f"代理测试失败: {str(e)}")
            return False
            
    def get_proxy(self, api_url):
        """从API获取新代理"""
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # 禁用警告
            
            session = requests.Session()
            session.verify = False  # 禁用SSL验证
            
            response = session.get(api_url, timeout=10)
            data = response.json()
            
            # 解析返回的数据
            if 'list' in data and len(data['list']) > 0:
                proxy_info = data['list'][0]
                proxy = {
                    'ip': proxy_info['sever'],  # 注意这里是 'sever' 而不是 'server'
                    'port': proxy_info['port'],
                    'expire': data.get('expire', 'unknown')
                }
                return proxy, "获取代理成功"
            return None, "API返回数据格式错误"
            
        except Exception as e:
            return None, f"获取代理失败: {str(e)}"
            
    def get_valid_proxy(self, api_url=None):
        """获取有效代理，如果当前代理无效则获取新代理"""
        if api_url is None:
            return None, "未提供代理API链接"
            
        # 获取新代理
        proxy, message = self.get_proxy(api_url)
        if not proxy:
            return None, message
            
        # 测试代理是否可用
        if self.test_proxy(proxy['ip'], proxy['port']):
            # 保存可用代理
            self.save_proxy(proxy)
            return proxy, "代理可用"
        
        return None, "代理不可用"

if __name__ == "__main__":
    proxy_manager = ProxyManager()
    proxy, status = proxy_manager.get_valid_proxy()
    print(f"代理状态: {status}")
    if proxy:
        print(f"代理ip: {proxy['ip']}, 代理端口: {proxy['port']}, 代理过期时间: {proxy['expire']}")
        print(f"http://{proxy['ip']}:{proxy['port']}")
    else:
        print("没有可用的代理")


