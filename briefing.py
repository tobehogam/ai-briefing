import os
import yfinance as yf
from google import genai
from google.genai import types
import requests

# 1. 깃허브 Secrets에서 비밀번호 불러오기
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 2. 주식 데이터 함수 (글머리 기호 추가해서 예쁘게!)
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
                data_list.append(f"• {name} | 데이터 없음")
                continue

            change = price - prev
            pct = (change / prev) * 100 if prev != 0 else 0
            
            if is_kr:
                data_list.append(f"• {name} | {int(price):,}원 | {pct:.2f}%")
            else:
                data_list.append(f"• {name} | ${price:.2f} | {pct:.2f}%")
        except:
            data_list.append(f"• {name} | 에러 발생")
            
    return "\n".join(data_list)

us_tickers = {"Alphabet(GOOGL)": "GOOGL", "Transocean(RIG)": "RIG", "Lululemon(LULU)": "LULU", "Kraft Heinz(KHC)": "KHC"}
kr_tickers = {"대덕전자": "353200.KS", "한미사이언스": "008930.KS", "케이알엠": "093640.KQ", "대한항공": "003490.KS", "서흥": "008490.KS", "대정화금": "120240.KQ", "AJ네트웍스": "095570.KS"}

us_market_text = get_stock_data(us_tickers, is_kr=False)
kr_market_text = get_stock_data(kr_tickers, is_kr=True)

# 3. 신형 제미나이 AI 세팅 (HTML 강제 지시!)
client = genai.Client(api_key=GEMINI_API_KEY)

prompt = f"""
당신은 최고급 '국제/국내 정세 전문 분석가'이다.

[가독성 및 출력 절대 규칙]
- 마크다운 특수기호(*, **, # 등)는 절대 사용하지 말 것. 텔레그램 전송 에러의 원인이 됨.
- 굵은 글씨로 강조하고 싶은 부분은 반드시 HTML 태그인 <b>와 </b>로 감쌀 것.
- 각 뉴스 항목 사이에는 반드시 '빈 줄(엔터)'을 넉넉히 넣을 것.
- 날씨는 반드시 '섭씨(℃)' 온도와 한국 단위(강수량 mm 등)를 사용할 것. 화씨 금지.

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
            tools=[{"google_search": {}}]
        )
    )
    briefing_text = response.text
    
    if not briefing_text:
        briefing_text = "⚠️ 오빠! AI가 뉴스를 검색하다가 빈 문서를 줬어!"
        
except Exception as e:
    briefing_text = f"🚨 브리핑 생성 중 오류가 발생했습니다: {e}"

# 5. 텔레그램 전송 (HTML 파싱 + 에러 알림 부활!)
url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
max_len = 4000
chunks = [briefing_text[i:i+max_len] for i in range(0, len(briefing_text), max_len)]

for chunk in chunks:
    # 안전하고 예쁜 HTML 모드로 전송!
    payload = {'chat_id': CHAT_ID, 'text': chunk, 'parse_mode': 'HTML'}
    res = requests.post(url, json=payload)
    
    # 🚨 내가 빼먹었던 방어막 부활! 텔레그램이 거절하면 깃허브에 빨간불 띄우기!
    if res.status_code != 200:
        raise Exception(f"Telegram Error: {res.text}")
