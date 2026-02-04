import requests
import os

# 配置
INTERVAL = 20  # 变动阈值
LOG_FILE = "last_price.txt"

def get_gold_price():
    # 获取黄金实时数据 (Yahoo Finance)
    url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1m&range=1d"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers).json()
        price = res['chart']['result'][0]['indicators']['quote'][0]['close'][-1]
        return round(price, 2)
    except:
        return None

def send_wechat(price, trend, diff):
    app_token = os.environ.get("WXP_APP_TOKEN")
    # 注意这里：我们从 Secrets 读取 Topic ID
    topic_id = os.environ.get("WXP_TOPIC_ID")
    
    if not app_token or not topic_id:
        print("配置缺失")
        return

    direction = "📈 上涨" if trend == "up" else "📉 下跌"
    content = f"🔔 黄金节点提醒\n\n方向: {direction}\n当前价格: ${price}\n变动幅度: ${diff}"
    
    url = "https://wxpusher.zjiecode.com/api/send/message"
    data = {
        "appToken": app_token,
        "content": content,
        "summary": f"金价{direction}: ${price}",
        "contentType": 1,
        "topicIds": [int(topic_id)]  # 注意：这里改成了 topicIds，且必须是数字列表
    }
    
    res = requests.post(url, json=data)
    print("全员推送结果:", res.text)

def main():
    current_price = get_gold_price()
    if not current_price: return

    # 1. 读取上次记录的价格
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            last_price = float(f.read().strip().replace(',', ''))
    else:
        # 第一次运行，记录当前价格并退出
        with open(LOG_FILE, "w") as f:
            f.write(str(current_price))
        print(f"首次运行，初始化价格为: {current_price}")
        return

    # 2. 计算差异
    diff = current_price - last_price
    
    # 3. 判断是否超过 50 点节点
    if abs(diff) >= INTERVAL:
        trend = "up" if diff > 0 else "down"
        print(f"触发节点！当前:{current_price}, 上次:{last_price}, 变动:{diff}")
        
        # 推送通知
        send_wechat(current_price, trend, round(diff, 2))
        
        # 4. 更新记录的价格（关键：只有触发了才更新，或者你可以选择每次都更新）
        # 这里建议更新为当前价格，作为新的基准点
        with open(LOG_FILE, "w") as f:
            f.write(str(current_price))
    else:
        print(f"未触发节点。当前:{current_price}, 上次:{last_price}, 变动:{diff}")

if __name__ == "__main__":
    main()
