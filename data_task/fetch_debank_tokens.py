import requests
import time

def fetch_debank_tokens(address):
    url = f"https://openapi.debank.com/v1/user/token_list?id={address}&is_all=true"
    response = requests.get(url)
    return response.json()

addresses = ["0x742d35Cc6634C0532925a3b844Bc454e4438f44e"]

for addr in addresses:
    tokens = fetch_debank_tokens(addr)
    print(f"地址 {addr}：")
    for t in tokens:
        print(f"- {t['name']} ({t['symbol']}): {t['amount']}")
    time.sleep(1)  # 避免被限流