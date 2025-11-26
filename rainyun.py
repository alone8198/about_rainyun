#!/usr/bin/env python3

import os
import sys
import time
import random
import logging
import re

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
except ImportError:
    print("错误: 缺少 Selenium 库。请运行 'pip install selenium' 进行安装。")
    sys.exit(1)

try:
    import ddddocr
except ImportError:
    print("错误: 缺少 ddddocr 库。请运行 'pip install ddddocr' 进行安装。")
    sys.exit(1)


# ==========================================
# 通知模块导入
# 尝试从 notify.py 导入 send 函数
# 如果找不到 notify.py，定义一个空函数，避免脚本报错
# ==========================================
try:
    from notify import send
    logging.getLogger(__name__).info("已加载通知模块 (notify.py)")
except ImportError:
    logging.getLogger(__name__).warning("未找到 notify.py，将无法发送通知。请确保 notify.py 与主脚本在同一目录下。")
    def send(*args, **kwargs):
        pass
# ==========================================


# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_selenium(debug=False, headless=False):
    """
    初始化 Selenium WebDriver。
    :param debug: 是否启用调试模式（不退出浏览器）。
    :param headless: 是否启用无头模式。
    :return: WebDriver 实例。
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--incognito")
    options.add_argument("--log-level=3")  # Suppress info/warning messages from Chrome
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("blink-settings=imagesEnabled=false") # 禁用图片加载
    # if debug:
    #     options.add_experimental_option("detach", True) # 调试模式下不自动关闭浏览器

    if headless:
        options.add_argument("--headless=new")
        logger.info("以无头模式启动浏览器。")
    else:
        logger.info("以有头模式启动浏览器。")

    # 尝试查找 Chrome 浏览器路径
    chrome_paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        # WSL 路径
        "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
        "/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"
    ]
    
    driver_executable_path = None
    for path in chrome_paths:
        if os.path.exists(path):
            options.binary_location = path
            logger.info(f"找到 Chrome/Chromium 浏览器于: {path}")
            # 对于 Selenium 4.6+，如果指定了 binary_location，通常不需要单独的 chromedriver 路径
            # 但是为了兼容性，我们可以尝试设置 Service
            try:
                # 尝试使用 WebDriverManager 自动下载 ChromeDriver
                from webdriver_manager.chrome import ChromeDriverManager
                service = ChromeService(ChromeDriverManager().install())
                logger.info("使用 WebDriverManager 自动下载并设置 ChromeDriver。")
                return webdriver.Chrome(service=service, options=options)
            except ImportError:
                logger.warning("未安装 webdriver_manager，请手动确保 ChromeDriver 可用或安装。尝试直接创建 WebDriver。")
                break # 退出循环，尝试直接创建，依赖PATH或手动设置

    # 如果没有找到 WebDriverManager 或手动设置路径
    try:
        # 尝试从系统 PATH 或默认位置查找 ChromeDriver
        return webdriver.Chrome(options=options)
    except WebDriverException as e:
        logger.error(f"无法初始化 Chrome WebDriver。错误: {e}")
        logger.error("请确保您的系统上已安装 Chrome 浏览器，并且 ChromeDriver 与您的 Chrome 版本兼容并已放置在 PATH 中。")
        logger.error("或者安装 'webdriver-manager' 库 (pip install webdriver-manager)。")
        raise


def process_captcha():
    """处理滑动验证码。"""
    logger.info("开始处理滑动验证码...")
    
    driver.switch_to.default_content() # 确保在主文档中
    
    # 找到验证码iframe并切换
    try:
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'tcaptcha_iframe')))
    except TimeoutException:
        logger.error("验证码 iframe 加载超时，可能未触发验证码或页面结构改变。")
        return False

    time.sleep(2)  # 等待 iframe 内容加载

    try:
        # 获取背景图和滑动块图
        slide_block = wait.until(EC.visibility_of_element_located((By.ID, 'slideBlock')))
        bg_img = wait.until(EC.visibility_of_element_located((By.ID, 'slideBg')))

        # 获取图片 base64
        slide_block_base64 = driver.execute_script(
            "var c = document.createElement('canvas');"
            "var ctx = c.getContext('2d');"
            "var img = arguments[0];"
            "c.width = img.naturalWidth;"
            "c.height = img.naturalHeight;"
            "ctx.drawImage(img, 0, 0);"
            "return c.toDataURL('image/png').substring(22);", slide_block
        )
        bg_img_base64 = driver.execute_script(
            "var c = document.createElement('canvas');"
            "var ctx = c.getContext('2d');"
            "var img = arguments[0];"
            "c.width = img.naturalWidth;"
            "c.height = img.naturalHeight;"
            "ctx.drawImage(img, 0, 0);"
            "return c.toDataURL('image/png').substring(22);", bg_img
        )
        
        # 保存图片（可选，用于调试）
        # with open("slide_block.png", "wb") as f:
        #     f.write(base64.b64decode(slide_block_base64))
        # with open("bg_img.png", "wb") as f:
        #     f.write(base64.b64decode(bg_img_base64))

        target_x = ocr.slide_match(slide_block_base64, bg_img_base64, simple_target=True)
        logger.info(f"计算出滑动距离: {target_x} 像素")

        # 获取滑动按钮
        slide_button = wait.until(EC.element_to_be_clickable((By.ID, 'slide-button')))
        
        # 获取滑动按钮的实际宽度（在页面上的渲染尺寸）
        button_width = slide_button.size['width']
        # 计算滑动比例，并转换为实际滑动距离
        # 这里的 target_x 是图片像素距离，需要根据实际图片和显示比例进行调整
        # 雨云验证码的图片原始宽度是 340px，而页面上可能渲染的宽度不同
        # 假设滑动块图片实际渲染宽度是 slideBlock.size['width']
        # 并且背景图的渲染宽度 bg_img.size['width'] 对应 ocr 识别的 340
        
        # 尝试根据背景图渲染宽度来调整
        bg_rendered_width = bg_img.size['width']
        # 假设 ddddocr 返回的是基于原始图片宽度的距离，这里原始图片宽度通常是 340
        original_bg_width = 340 
        
        # 计算滑动比例
        if original_bg_width > 0:
            scale = bg_rendered_width / original_bg_width
            move_distance = target_x * scale
        else:
            move_distance = target_x # 如果获取不到渲染宽度，就用OCR的原始距离
        
        # 还需要减去滑动按钮本身的宽度的一半或一个固定偏移量
        # 确保滑块左边缘对齐到目标位置
        # 经验值调整，根据实际验证码情况可能需要微调
        move_distance -= 30 # 这是一个经验值，确保滑块中心或右边缘对齐目标
        if move_distance < 0:
            move_distance = 0
            
        logger.info(f"调整后的滑动距离: {move_distance} 像素")


        # 执行滑动操作
        webdriver.ActionChains(driver).click_and_hold(slide_button).perform()
        time.sleep(0.5)

        # 模拟鼠标平滑拖动
        for x_offset in range(0, int(move_distance), 10): # 每次移动10像素
            webdriver.ActionChains(driver).move_by_offset(10, 0).perform()
            time.sleep(random.uniform(0.01, 0.05)) # 随机短暂停顿

        # 最后移动到精确位置
        remaining_distance = int(move_distance) - (int(move_distance) // 10) * 10
        if remaining_distance > 0:
            webdriver.ActionChains(driver).move_by_offset(remaining_distance, 0).perform()
            time.sleep(random.uniform(0.1, 0.3))

        webdriver.ActionChains(driver).release().perform()
        logger.info("滑动操作完成，等待验证结果...")
        time.sleep(3)  # 等待验证结果

        # 检查验证结果
        try:
            # 验证码成功后通常iframe会消失或有成功提示
            # 如果iframe还在且出现错误提示
            error_message = driver.find_elements(By.XPATH, "//*[contains(text(), '失败') or contains(text(), '校验失败')]")
            if error_message:
                logger.warning(f"验证码校验失败: {error_message[0].text if error_message[0].text else '未知错误'}")
                # 尝试点击刷新按钮
                refresh_button = driver.find_element(By.CLASS_NAME, 'tcaptcha-icon-refresh')
                if refresh_button:
                    refresh_button.click()
                    logger.info("点击验证码刷新按钮，重试...")
                    time.sleep(2)
                    return process_captcha() # 递归重试
                return False
            else:
                logger.info("验证码校验成功！")
                return True
        except NoSuchElementException:
            logger.info("未检测到验证失败信息，验证码可能已成功。")
            return True

    except Exception as e:
        logger.error(f"处理验证码时发生错误: {e}")
        driver.switch_to.default_content() # 切换回主文档，避免后续操作在iframe中
        return False
    finally:
        driver.switch_to.default_content() # 确保最后切换回主文档


if __name__ == "__main__":
    # 连接超时等待
    timeout = 15

    user = os.environ.get("RAINYUN_USER")
    pwd = os.environ.get("RAINYUN_PASS")

    # 确保有用户名和密码
    if not user or not pwd:
        err_msg = "错误: 未设置用户名或密码，请在环境变量中设置RAINYUN_USER和RAINYUN_PASS"
        print(err_msg)
        # 即使没密码也要尝试发送通知（虽然可能因为配置问题发不出去）
        send("雨云签到配置错误", err_msg)
        sys.exit(1) # 使用 sys.exit(1) 表示异常退出

    # 环境变量判断是否在GitHub Actions中运行
    is_github_actions = os.environ.get("GITHUB_ACTIONS", "false") == "true"
    # 从环境变量读取模式设置
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    headless = os.environ.get('HEADLESS', 'false').lower() == 'true'

    # 如果在GitHub Actions环境中，强制使用无头模式
    if is_github_actions:
        headless = True

    ver = "2.2" # 版本号
    logger.info("------------------------------------------------------------------")
    logger.info(f"雨云自动签到工作流 v{ver} by 筱序二十 ~")
    logger.info("------------------------------------------------------------------")
    logger.info(f"DEBUG 模式: {debug}")
    logger.info(f"HEADLESS 模式: {headless}")
    logger.info(f"是否在 GitHub Actions 环境: {is_github_actions}")
    logger.info("------------------------------------------------------------------")

    driver = None # 初始化 driver 变量，用于 finally 中判断

    try: # 【新增】开始 try 块，包裹主逻辑
        if not debug:
            delay_sec = random.randint(5, 600) # 随机延时等待 5秒到10分钟
            logger.info(f"随机延时等待 {delay_sec} 秒以避免被检测...")
            time.sleep(delay_sec)
        
        logger.info("初始化 ddddocr")
        ocr = ddddocr.DdddOcr(ocr=True, show_ad=False)
        det = ddddocr.DdddOcr(det=True, show_ad=False)
        logger.info("初始化 Selenium")

        # 传递 headless 参数给 init_selenium
        driver = init_selenium(debug=debug, headless=headless)
        wait = WebDriverWait(driver, timeout) # 在 driver 初始化后创建 WebDriverWait
        
        # 过 Selenium 检测
        # 由于这里不能直接提供 stealth.min.js 的内容，你需要确保这个文件存在
        # 或者注释掉这部分，但可能更容易被检测
        try:
            with open("stealth.min.js", mode="r") as f:
                js = f.read()
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": js
            })
            logger.info("已加载 stealth.min.js 绕过 Selenium 检测。")
        except FileNotFoundError:
            logger.warning("未找到 'stealth.min.js' 文件，可能增加被检测的风险。")
        except Exception as e:
            logger.warning(f"加载 stealth.min.js 时发生错误: {e}")


        logger.info("发起登录请求")
        driver.get("https://app.rainyun.com/auth/login")
        
        # 改进的登录逻辑，添加重试机制
        max_retries = 3
        retry_count = 0
        login_success = False

        while retry_count < max_retries and not login_success:
            try:
                username_field = wait.until(EC.visibility_of_element_located((By.NAME, 'login-field')))
                password_field = wait.until(EC.visibility_of_element_located((By.NAME, 'login-password')))
                login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))

                username_field.clear()
                password_field.clear()
                username_field.send_keys(user)
                password_field.send_keys(pwd)
                time.sleep(random.uniform(0.5, 1.5)) # 模拟人类输入
                
                # 使用JavaScript点击，避免元素遮挡问题
                driver.execute_script("arguments[0].click();", login_button)
                logger.info(f"登录尝试 {retry_count + 1}/{max_retries}")
                
                # 等待页面跳转或判断登录是否成功
                wait.until(EC.url_contains("dashboard") or EC.url_contains("login"))
                if "dashboard" in driver.current_url:
                    login_success = True
                    logger.info("登录成功！")
                else:
                    # 如果仍在登录页，检查是否有错误消息
                    error_elements = driver.find_elements(By.XPATH, 
                        "//*[contains(@class, 'el-message__content') or contains(@class, 'error-message')]")
                    if error_elements:
                        error_text = error_elements[0].text
                        logger.warning(f"登录失败，页面提示: {error_text}")
                    else:
                        logger.warning("登录失败，未检测到明确错误提示。")
                    
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.warning(f"等待 {retry_count*2} 秒后重试登录...")
                        time.sleep(retry_count * 2)
                        driver.refresh() # 刷新页面重新尝试
                    else:
                        raise Exception("登录失败，已达到最大重试次数。") # 抛出异常以便外部捕获

            except TimeoutException:
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"登录页面加载超时，{retry_count*2}秒后重试...")
                    time.sleep(retry_count * 2)
                    driver.refresh()
                else:
                    raise Exception("登录页面加载超时，已达到最大重试次数。") # 抛出异常以便外部捕获
            except Exception as e:
                logger.error(f"登录过程中发生意外错误: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"等待 {retry_count*2} 秒后重试登录...")
                    time.sleep(retry_count * 2)
                    driver.refresh()
                else:
                    raise Exception(f"登录过程中发生致命错误，已达到最大重试次数: {e}")


        # 检查是否登录成功，如果成功则继续，否则退出
        if not login_success:
            err_msg = "登录失败！未能进入仪表盘页面，可能是账号密码错误或验证码验证失败。"
            logger.error(err_msg)
            send("雨云签到失败", err_msg)
            sys.exit(1)


        # 尝试处理登录后的二次验证码 (腾讯防水墙)
        # 注意: 腾讯防水墙的 iframe ID 通常是 'tcaptcha_iframe_dy' 或 'tcaptcha_iframe'
        try:
            # 优先检查是否存在 'tcaptcha_iframe_dy' (雨云实际使用的ID)
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'tcaptcha_iframe_dy')))
            logger.warning("触发腾讯滑动验证码！")
            captcha_processed = process_captcha()
            if not captcha_processed:
                raise Exception("验证码处理失败或被多次拒绝。")
            driver.switch_to.default_content() # 处理完验证码后切换回主文档
        except TimeoutException:
            logger.info("未触发腾讯滑动验证码。")
            driver.switch_to.default_content() # 确保在主文档中
        except Exception as e:
            err_msg = f"处理登录后验证码时发生错误: {e}"
            logger.error(err_msg)
            send("雨云登录验证码失败", err_msg)
            sys.exit(1) # 验证码失败也算致命错误

        time.sleep(2) # 给页面一点时间跳转和加载
        
        # 验证登录状态并处理赚取积分
        if "dashboard" in driver.current_url:
            logger.info("登录成功并进入仪表盘！")
            logger.info("正在转到赚取积分页")

            # 尝试多次访问赚取积分页面和点击按钮
            max_earn_retries = 3
            for attempt in range(max_earn_retries):
                try:
                    driver.get("https://app.rainyun.com/account/reward/earn")
                    logger.info(f"第 {attempt + 1} 次尝试加载赚取积分页面...")
                    
                    # 等待页面加载完成
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                    time.sleep(3)  # 额外等待确保页面完全渲染

                    # 使用多种策略查找赚取积分按钮
                    earn_button = None
                    strategies = [
                        (By.XPATH, '//*[@id="app"]/div[1]/div[3]/div[2]/div/div/div[2]/div[2]/div/div/div/div[1]/div/div[1]/div/div[1]/div/span[2]/a'),
                        (By.XPATH, '//a[contains(@href, "earn") and contains(text(), "赚取")]'),
                        (By.CSS_SELECTOR, 'a[href*="/account/reward/earn"]'),
                        (By.XPATH, '//a[contains(@class, "earn-button")]') # 假设存在一个类名
                    ]

                    for by, selector in strategies:
                        try:
                            earn_button = wait.until(EC.element_to_be_clickable((by, selector)))
                            logger.info(f"使用策略 {by}={selector} 找到赚取积分按钮")
                            break
                        except:
                            logger.debug(f"策略 {by}={selector} 未找到按钮，尝试下一种")
                            continue

                    if earn_button:
                        # 滚动到元素位置
                        driver.execute_script("arguments[0].scrollIntoView(true);", earn_button)
                        time.sleep(random.uniform(0.5, 1.5))
                        
                        # 使用JavaScript点击
                        logger.info("点击赚取积分")
                        driver.execute_script("arguments[0].click();", earn_button)

                        # 处理可能出现的赚取积分后的验证码 (如果和登录验证码不同)
                        try:
                            logger.info("检查赚取积分后是否需要验证码")
                            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "tcaptcha_iframe_dy")))
                            logger.info("处理赚取积分验证码")
                            captcha_processed = process_captcha()
                            if not captcha_processed:
                                raise Exception("赚取积分后的验证码处理失败。")
                            driver.switch_to.default_content()
                        except TimeoutException:
                            logger.info("未触发赚取积分验证码。")
                            driver.switch_to.default_content()
                        except Exception as e:
                            logger.error(f"处理赚取积分验证码时发生错误: {e}")
                            send("雨云赚取积分验证码失败", f"处理赚取积分验证码时发生错误: {e}")
                            # 不中断主流程，尝试继续获取积分，但也标记可能失败

                        logger.info("赚取积分操作完成")
                        break # 成功点击并处理后退出重试循环
                    else:
                        logger.warning(f"第 {attempt + 1} 次尝试: 未找到赚取积分按钮，刷新页面重试...")
                        driver.refresh()
                        time.sleep(random.uniform(3, 5))
                except Exception as e:
                    logger.error(f"第 {attempt + 1} 次访问赚取积分页面或点击时出错: {e}")
                    time.sleep(random.uniform(3, 5))
            else:
                # 如果多次尝试失败，记录错误并发送通知（不抛出异常，尝试获取当前积分）
                err_msg = "多次尝试后仍无法找到或点击赚取积分按钮，本次可能未获取到积分。"
                logger.error(err_msg)
                send("雨云签到部分失败", err_msg)

            driver.implicitly_wait(5) # 隐式等待，用于后续快速查找元素

            # 尝试获取当前积分
            current_points_str = "未知"
            try:
                # 尝试获取积分元素
                points_element = wait.until(EC.visibility_of_element_located(
                    (By.XPATH, '//*[@id="app"]/div[1]/div[3]/div[2]/div/div/div[2]/div[1]/div[1]/div/p/div/h3')
                ))
                points_raw = points_element.get_attribute("textContent")
                current_points = int(''.join(re.findall(r'\d+', points_raw)))
                current_points_str = f"{current_points} | 约为 {current_points / 2000:.2f} 元"
                
                # 【新增】构建成功消息并发送通知
                success_msg = f"当前剩余积分: {current_points_str}"
                logger.info(success_msg)
                logger.info("任务执行成功！")
                send("雨云签到成功", success_msg)
                
            except TimeoutException:
                err_msg = "任务执行完毕，但获取当前积分元素超时。"
                logger.error(err_msg)
                send("雨云签到结果未知", err_msg)
            except NoSuchElementException:
                err_msg = "任务执行完毕，但未找到当前积分元素。"
                logger.error(err_msg)
                send("雨云签到结果未知", err_msg)
            except Exception as e:
                 err_msg = f"任务执行完毕，但获取当前积分失败: {str(e)}"
                 logger.error(err_msg)
                 send("雨云签到结果未知", err_msg)

        else:
            # 【新增】登录失败分支的通知
            err_msg = "登录失败！未能进入仪表盘页面，可能是账号密码错误或验证码验证失败。"
            logger.error(err_msg)
            send("雨云签到失败", err_msg)

    except Exception as e:
        # 【新增】捕获整个执行过程中的任何未处理异常
        err_msg = f"脚本运行期间发生致命异常: {str(e)}"
        logger.error(err_msg, exc_info=True) # 打印详细堆栈信息
        send("雨云脚本运行异常", err_msg)

    finally:
        # 【新增】确保浏览器被关闭
        if driver:
            logger.info("正在关闭浏览器...")
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"关闭浏览器时发生错误: {e}")
        logger.info("脚本执行结束。")
