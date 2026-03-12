import os
import yfinance as yf
# 완전히 바뀐 신형 구글 라이브러리 불러오기!
from google import genai
from google.genai import types
import requests

# 1. 깃허브 Secrets에서 비밀번호 불러오기
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 2. 주식 데이터 함수 (오빠 종목들 안전하게 가져오기)
def get_stock_data(tickers, is_kr=False):
    data_list = []
    for name, ticker in tickers.items():
        try:
            s = yf.Ticker(ticker)
            hist = s.history(period="5d")
            
            if len(hist) >= 2:
                price = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[-2]
            elif len(hist) == 1:
                price = hist["Close"].iloc[-1]
                prev = price
            else:
                continue

            change = price - prev
            pct = (change / prev) * 100 if prev != 0 else 0
            
            if is_kr:
                data_list.append(f"{name} | {int(price):,}원 | {pct:.2f}%")
            else:
                data_list.append(f"{name} | ${price:.2f} | {pct:.2f}%")
        except:
            pass
    return "\n".join(data_list)

us_tickers = {"Alphabet(GOOGL)":"GOOGL", "Transocean(RIG)":"RIG"}
kr_tickers = {"대덕전자":"353200.KQ", "한미사이언스":"008930.KS", "AJ네트웍스":"095570.KS"}

print("주가 데이터 수집 중...")
us_market_text = get_stock_data(us_tickers, is_kr=False)
kr_market_text = get_stock_data(kr_tickers, is_kr=True)

# 3. 🌟 신형 제미나이 AI 세팅 (구글 최신 규칙 완벽 적용) 🌟
client = genai.Client(api_key=GEMINI_API_KEY)

prompt = f"""
당신은 최고급 '국제/국내 정세 전문 분석가'이다.
제공된 주식 데이터는 하단에 간단히 첨부하고, 당신의 핵심 임무는 실시간 구글 검색을 통해 가장 중요하고 최신인 '국제 정세'와 '한국 국내 뉴스'를 심도 있게 브리핑하는 것이다.

[브리핑 구성]
1. 글로벌 정세 및 주요 국제 뉴스 (5개 요약 및 출처)
2. 한국 주요 정치/경제/사회 뉴스 (5개 요약 및 출처)
3. 관심 종목 스냅샷 (아래 표 데이터 활용)
[미국 증시]\n{us_market_text}
[한국 증시]\n{kr_market_text}
4. 오늘의 날씨 요약 (한국 경기도 기준)
"""

# 4. 브리핑 생성 및 텔레그램 발송 (신형 검색 도구 규칙!)
try:
    print("AI가 뉴스를 검색하고 브리핑을 작성 중입니다...")
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[{"google_search": {}}] # 신형 검색기능 문법!
        )
    )
    briefing_text = response.text
except Exception as e:
    briefing_text = f"브리핑 생성 중 오류가 발생했습니다: {e}"

print("텔레그램 전송 중...")
url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

max_len = 4000
for i in range(0, len(briefing_text), max_len):
    chunk = briefing_text[i:i+max_len]
    payload = {'chat_id': CHAT_ID, 'text': chunk}
    res = requests.post(url, data=payload)
