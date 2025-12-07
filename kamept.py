# -*- coding: utf-8 -*-
"""
cron: 0 9 * * *
new Env('KamePT');
"""
from notify import send
import requests
import re
import os
import time

requests.packages.urllib3.disable_warnings()


def start(cookie):
    max_retries = 3
    retries = 0
    msg = ""

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    headers = {
        'Cookie': cookie,
        'User-Agent': user_agent,
        'Referer': 'https://kamept.com/index.php',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Connection': 'keep-alive'
    }

    while retries < max_retries:
        try:
            sign_in_url = "https://kamept.com/attendance.php"

            # 发起请求
            rsp = requests.get(url=sign_in_url, headers=headers, timeout=20, verify=False)
            rsp_text = rsp.text

            # --- 状态判断 ---
            if "Just a moment" in rsp_text or "503 Service Temporarily" in rsp_text:
                print("触发 Cloudflare 盾，正在重试...")
                msg = "访问被拦截 (CF盾)，请检查 cf_clearance 是否过期。"

            elif "login.php" in rsp.url or "用户登录" in rsp_text:
                print("Cookie 失效，重定向到了登录页")
                msg = "Cookie 已失效，请重新获取。"
                break

            elif "这是您的第" in rsp_text or "已签到" in rsp_text or "签到成功" in rsp_text:
                # --- 成功逻辑 ---
                msg += 'KamePT 签到成功！\n'

                # 1. 提取魔力值 (兼容带逗号的数字)
                magic_match = re.search(r'魔力值.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', rsp_text)
                if magic_match:
                    msg += f"当前魔力: {magic_match.group(1)}\n"

                # 2. 提取天数
                days_match = re.search(r'这是您的第.*?(\d+).*?次签到', rsp_text)
                if days_match:
                    msg += f"累计签到: {days_match.group(1)} 天\n"

                # 3. 提取补签卡数量
                card_match = re.search(r'补签卡.*?(\d+).*?张', rsp_text)
                if card_match:
                    msg += f"补签卡数: {card_match.group(1)} 张\n"

                # 4. 提取今日排名
                rank_match = re.search(r'今日签到排名.*?(\d+)', rsp_text)
                if rank_match:
                    msg += f"今日排名: {rank_match.group(1)}"

                print(msg)
                send("KamePT 签到结果", msg)
                return

            else:
                msg = f"未检测到签到成功标识，状态码: {rsp.status_code}"

            retries += 1
            time.sleep(3)

        except Exception as e:
            msg = f"请求异常: {str(e)}"
            retries += 1
            time.sleep(3)

    # 循环结束仍未 return，发送失败通知
    print("最终执行失败")
    send("KamePT 签到失败", msg)


if __name__ == "__main__":
    cookie = os.getenv("KAMEPT_COOKIE")
    if not cookie:
        print("未找到环境变量 KAMEPT_COOKIE")
    else:
        start(cookie)