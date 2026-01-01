"""
雨云账号登录测试脚本
用途：测试自己的雨云账号是否能正常登录
"""

import requests
import getpass
import json

class RainyunLogin:
    def __init__(self):
        self.base_url = "https://api.v2.rainyun.com"
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def login(self, username: str, password: str) -> dict:
        """
        登录雨云账号
        
        Args:
            username: 用户名/邮箱/手机号
            password: 密码
            
        Returns:
            登录结果字典
        """
        login_url = f"{self.base_url}/user/login"
        
        payload = {
            "field": username,
            "password": password
        }
        
        try:
            response = self.session.post(login_url, json=payload, timeout=30)
            result = response.json()
            return result
            
        except requests.exceptions.Timeout:
            return {"code": -1, "message": "请求超时"}
        except requests.exceptions.ConnectionError:
            return {"code": -1, "message": "网络连接错误"}
        except json.JSONDecodeError:
            return {"code": -1, "message": "响应解析失败"}
        except Exception as e:
            return {"code": -1, "message": f"未知错误: {str(e)}"}
def main():
    print("=" * 50)
    print("        雨云账号登录测试工具")
    print("=" * 50)
    print()
    username = input("请输入用户名/邮箱/手机号: ").strip()
    if not username:
        print("❌ 用户名不能为空!")
        return
    
    password = getpass.getpass("请输入密码(不显示密码): ").strip()
    if not password:
        print("❌ 密码不能为空!")
        return
    
    print()
    print("正在登录...")
    print("-" * 50)
    
    # 执行登录
    client = RainyunLogin()
    result = client.login(username, password)
    
    # 处理登录结果
    if result.get("code") == 200:
        print("✅ 登录成功!")
        print()
    else:
        print("❌ 登录失败!")
        print(f"   错误信息: {result.get('message', '未知错误')}")
        print(f"   错误代码: {result.get('code', 'N/A')}")
if __name__ == "__main__":
    main()
