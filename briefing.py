import os
import yfinance as yf
from google import genai
from google.genai import types
import requests
import datetime
import pytz
import concurrent.futures

# 1. 환경 변수 불러오기
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 오늘 날짜 (KST 기준) 설정
kst = pytz.timezone('Asia/Seoul')
today_date = datetime.datetime.now(kst).strftime("%Y년 %m월 %d일")

# 2. 주식 데이터 함수 (멀티스레딩 적용으로 속도 향상)
def fetch_single_stock(name, ticker, is_kr):
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
            return f"• {name} | 데이터 없음"

        change = price - prev
        pct = (change / prev) * 100 if prev != 0 else 0
        
        if is_kr:
            return f"• {name} | {int(price):,}원 | {pct:.2f}%"
        else:
            return f"• {name} | ${price:.2f} | {pct:.2f}%"
    except:
        return f"• {name} | 에러 발생"

def get_stock_data_concurrent(tickers, is_kr=False):
    results = []
    # ThreadPoolExecutor를 사용해 데이터를 동시에 긁어옴 (최대 10개 작업 동시 진행)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_name = {executor.submit(fetch_single_stock, name, ticker, is_kr): name for name, ticker in tickers.items()}
        for future in concurrent.futures.as_completed(future_to_name):
            results.append(future.result())
            
    # 결과를 딕셔너리 키 순서(원래 순서)에 맞게 정렬하기 위한 로직
    ordered_results = []
    for name in tickers.keys():
        for res in results:
            if res.startswith(f"• {name}"):
                ordered_results.append(res)
                break
    return "\n".join(ordered_results)

us_tickers = {"Alphabet(GOOGL)": "GOOGL", "Transocean(RIG)": "RIG", "Lululemon(LULU)": "LULU", "Kraft Heinz(KHC)": "KHC"}
kr_tickers = {"대덕전자": "353200.KS", "한미사이언스": "008930.KS", "케이알엠": "093640.KQ", "대한항공": "003490.KS", "서흥": "008490.KS", "대정화금": "120240.KQ", "AJ네트웍스": "095570.KS"}

us_market_text = get_stock_data_concurrent(us_tickers, is_kr=False)
kr_market_text = get_stock_data_concurrent(kr_tickers, is_kr=True)

# 3. 신형 제미나이 AI 세팅
client = genai.Client(api_key=GEMINI_API_KEY)

# 본문 프롬프트 (오늘 날짜 명시)
prompt = f"""
기준일: {today_date}

[가독성 및 출력 절대 규칙]
- 마크다운 특수기호(*, **, # 등)는 절대 사용하지 말 것. 
- 굵은 글씨는 반드시 HTML 태그인 <b>와 </b>로만 감쌀 것.
- [중요] 줄바꿈(엔터)을 할 때 절대로 <br> 태그를 쓰지 말고, 실제 텍스트 줄바꿈 기호(\n)를 사용할 것.
- 날씨는 반드시 '섭씨(℃)' 온도와 한국 단위(강수량 mm 등)를 사용할 것.

[브리핑 구성]
<b>🌍 글로벌 정세 및 주요 국제 뉴스</b> (최신 5개)
<b>🇰🇷 한국 주요 정치/경제/사회 뉴스</b> (최신 5개)

<b>📈 관심 종목 스냅샷</b>
[미국 증시]\n{us_market_text}
[한국 증시]\n{kr_market_text}

<b>☀️ 오늘의 날씨 요약</b> (한국 서울시 강남구 역삼2동 기준)
"""

# 4. 브리핑 생성
try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction="당신은 최고급 '국제/국내 정세 전문 분석가'이다.",
            tools=[{"google_search": {}}]
        )
    )
    briefing_text = response.text
    
    if not briefing_text:
        briefing_text = "⚠️ 오빠! AI가 뉴스를 검색하다가 빈 문서를 줬어!"
        
    # AI가 말 안 듣고 <br> 썼을 경우 세척
    briefing_text = briefing_text.replace("<br>", "\n").replace("<br/>", "\n").replace("</br>", "\n")
        
except Exception as e:
    briefing_text = f"🚨 브리핑 생성 중 오류가 발생했습니다: {e}"

# 5. 텔레그램 전송
url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
max_len = 4000
chunks = [briefing_text[i:i+max_len] for i in range(0, len(briefing_text), max_len)]

for chunk in chunks:
    payload = {'chat_id': CHAT_ID, 'text': chunk, 'parse_mode': 'HTML'}
    res = requests.post(url, json=payload)
    
    # 🚨 [핵심 안전장치] HTML 파싱 오류로 전송 실패 시, 포맷 다 떼고 순수 텍스트로 재전송
    if res.status_code != 200:
        print(f"HTML Parse Error. Retrying without formatting... (Error: {res.text})")
        fallback_payload = {'chat_id': CHAT_ID, 'text': chunk}
        requests.post(url, json=fallback_payload)
