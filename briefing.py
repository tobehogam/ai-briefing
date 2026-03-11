import requests
import os

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

message = "자동 브리핑 테스트 성공"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

payload = {
 "chat_id": CHAT_ID,
 "text": message
}

requests.post(url, data=payload)
