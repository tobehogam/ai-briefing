import os
import yfinance as yf
import google.generativeai as genai
import requests

# 1. 깃허브 Secrets에서 비밀번호 불러오기
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 2. 주식 데이터는 심플하게 가져오기 (에러 방지용)
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

# 3. 제미나이 AI 세팅 (구글 검색 도구 탑재 필수!)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    tools='google_search' 
)

# 4. 🌟 오빠 맞춤형 '뉴스 집중' 프롬프트 🌟
prompt = f"""
당신은 최고급 '국제/국내 정세 전문 분석가'이다.
제공된 주식 데이터는 하단에 간단히 첨부하고, 당신의 핵심 임무는 실시간 구글 검색을 통해 가장 중요하고 최신인 '국제 정세 및 뉴스'와 '한국 국내 뉴스'를 심도 있게 브리핑하는 것이다.

[브리핑 구성]
1. 🌍 글로벌 정세 및 주요 국제 뉴스
- 최근 24시간 이내의 전 세계 핵심 뉴스 5가지를 선정하라.
- 각 뉴스는 제목, 3줄의 심도 있는 요약, 그리고 [출처 언론사]를 반드시 명시하라.

2. 🇰🇷 한국 주요 정치/경제/사회 뉴스
- 최근 24시간 이내의 한국 핵심 뉴스 5가지를 선정하라.
- 각 뉴스는 제목, 3줄의 심도 있는 요약, 그리고 [출처 언론사]를 반드시 명시하라.

3. 📊 오빠의 관심 종목 스냅샷
- 아래 데이터를 표 형식으로 깔끔하게 출력하라.
[미국 증시]
{us_market_text}
[한국 증시]
{kr_market_text}

4. ☀️ 오늘의 날씨 요약 (한국 경기도 기준)
- 간단한 날씨 요약 및 미세먼지 상태

[절대 규칙]
- 뉴스 검색 시 추정이나 상상은 절대 금지하며, 사실 기반의 데이터만 사용한다.
- 보고서 스타일로 가독성 좋게, 불필요한 수식어는 빼고 작성한다.
"""

# 5. 브리핑 생성 및 텔레그램 발송
try:
    print("AI가 뉴스를 검색하고 브리핑을 작성 중입니다...")
    response = model.generate_content(prompt)
    briefing_text = response.text
except Exception as e:
    briefing_text = f"브리핑 생성 중 오류가 발생했습니다: {e}"

print("텔레그램 전송 중...")
url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
payload = {'chat_id': CHAT_ID, 'text': briefing_text}
res = requests.post(url, data=payload)

if res.status_code == 200:
    print("텔레그램 전송 완벽하게 성공!")
else:
    print(f"전송 실패ㅠㅠ: {res.text}")
