import os
import yfinance as yf
from google import genai
from google.genai import types
import requests

# 1. 깃허브 Secrets에서 비밀번호 불러오기
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 2. 주식 데이터 함수 (오류 방지용)
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
                data_list.append(f"{name} | 데이터 없음")
                continue

            change = price - prev
            pct = (change / prev) * 100 if prev != 0 else 0
            
            if is_kr:
                data_list.append(f"{name} | {int(price):,}원 | {pct:.2f}%")
            else:
                data_list.append(f"{name} | ${price:.2f} | {pct:.2f}%")
        except:
            data_list.append(f"{name} | 에러 발생")
            
    return "\n".join(data_list)

# 오빠가 요청한 종목 완벽 업데이트!
us_tickers = {
    "Alphabet(GOOGL)": "GOOGL", 
    "Transocean(RIG)": "RIG", 
    "Lululemon(LULU)": "LULU", 
    "Kraft Heinz(KHC)": "KHC"
}

kr_tickers = {
    "대덕전자": "353200.KS", 
    "한미사이언스": "008930.KS", 
    "케이알엠": "093640.KQ", 
    "대한항공": "003490.KS", 
    "서흥": "008490.KS", 
    "대정화금": "120240.KQ", 
    "AJ네트웍스": "095570.KS"
}

print("주가 데이터 수집 중...")
us_market_text = get_stock_data(us_tickers, is_kr=False)
kr_market_text = get_stock_data(kr_tickers, is_kr=True)

# 3. 신형 제미나이 AI 세팅
client = genai.Client(api_key=GEMINI_API_KEY)

# 🌟 역삼2동 날씨로 완벽 수정! 🌟
prompt = f"""
당신은 최고급 '국제/국내 정세 전문 분석가'이다.
핵심 임무는 실시간 구글 검색을 통해 가장 중요하고 최신인 '국제 정세'와 '한국 국내 뉴스'를 브리핑하는 것이다.

[브리핑 구성]
1. 글로벌 정세 및 주요 국제 뉴스 (최신 5개 요약 및 출처)
2. 한국 주요 정치/경제/사회 뉴스 (최신 5개 요약 및 출처)
3. 관심 종목 스냅샷
[미국 증시]\n{us_market_text}
[한국 증시]\n{kr_market_text}
4. 오늘의 날씨 요약 (한국 서울시 강남구 역삼2동 기준)
"""

# 4. 브리핑 생성
try:
    print("AI가 뉴스를 검색하고 브리핑을 작성 중입니다...")
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[{"google_search": {}}]
        )
    )
    briefing_text = response.text
    
    if not briefing_text:
        briefing_text = "⚠️ 오빠! AI가 뉴스를 검색하다가 빈 문서를 줬어! 구글 서버가 잠깐 멍때리는 중인가 봐."
        
except Exception as e:
    briefing_text = f"🚨 브리핑 생성 중 오류가 발생했습니다: {e}"

# 5. 텔레그램 전송
print("텔레그램 전송 준비 중...")
url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

max_len = 4000
chunks = [briefing_text[i:i+max_len] for i in range(0, len(briefing_text), max_len)]

for i, chunk in enumerate(chunks):
    payload = {'chat_id': CHAT_ID, 'text': chunk}
    res = requests.post(url, json=payload)
    
    if res.status_code == 200:
        print(f"텔레그램 {i+1}번째 조각 전송 성공!")
    else:
        print(f"전송 실패ㅠㅠ: {res.text}")
        raise Exception(f"Telegram Error: {res.text}")
