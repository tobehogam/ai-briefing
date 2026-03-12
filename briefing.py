import os
import yfinance as yf
import google.generativeai as genai
import requests

# 1. 깃허브 Secrets에서 비밀번호 불러오기 (뉴스 키 같은 건 필요 없어!)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 2. yfinance 안전하게 데이터 가져오기 함수 (휴장일 에러 완벽 차단!)
def get_stock_data(tickers, is_kr=False):
    data_list = []
    for name, ticker in tickers.items():
        try:
            s = yf.Ticker(ticker)
            hist = s.history(period="5d") # 주말 대비 넉넉하게 5일치!
            
            # 여기서 띄어쓰기(들여쓰기) 완벽하게 맞춤!
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
            
            # 한국 주식은 원화/소수점 버림, 미국 주식은 달러/소수점 2자리
            if is_kr:
                data_list.append(f"{name} | {int(price):,}원 | {int(change):,}원 | {pct:.2f}%")
            else:
                data_list.append(f"{name} | ${price:.2f} | ${change:.2f} | {pct:.2f}%")
        except:
            data_list.append(f"{name} | 데이터 불러오기 실패")
            
    return "\n".join(data_list)

# 오빠 계좌 종목 리스트 세팅
us_tickers = {"Alphabet(GOOGL)":"GOOGL", "Transocean(RIG)":"RIG", "Kraft Heinz(KHC)":"KHC", "Lululemon(LULU)":"LULU"}
kr_tickers = {"대덕전자":"353200.KQ", "한미사이언스":"008930.KS", "케이알엠":"093640.KQ", "서흥":"008490.KS", "대정화금":"120240.KQ", "대한항공":"003490.KS", "F&F":"383220.KS", "AJ네트웍스":"095570.KS"}

print("주가 데이터 수집 중...")
us_market_text = get_stock_data(us_tickers, is_kr=False)
kr_market_text = get_stock_data(kr_tickers, is_kr=True)

# 3. 제미나이 AI 세팅 (구글 검색 도구 탑재)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-latest",
    tools='google_search_retrieval' # 뉴스와 날씨는 제미나이가 알아서 구글 검색!
)

# 4. 오빠의 완벽한 프롬프트 + 정확한 주식 데이터 결합!
prompt = f"""
당신은 ‘데이터 기반 뉴스 브리핑 분석가’이다.
아래 제공된 [오늘의 증시 데이터]를 표에 그대로 복사해서 넣고, 
뉴스와 날씨, 일정은 당신이 직접 구글 최신 정보를 검색하여 브리핑을 완성하라.

[오늘의 증시 데이터] (이 데이터를 표에 그대로 사용할 것)
- 미국 증시:
{us_market_text}

- 한국 증시:
{kr_market_text}

[절대 규칙]
- 추정, 상상, 일반 지식 기반 작성은 금지한다.
- 뉴스는 반드시 최근 24시간 기준으로 작성하며 출처 언론사를 명시한다.
- 모든 금융 수치는 제공된 데이터를 사용하여 '종목 | 현재가 | 전일 대비 | 변동률' 형식으로 작성한다.

[브리핑 구성]
1. 국제 정세 및 글로벌 경제 뉴스 (핵심 뉴스 5개, 3줄 요약, 언론사 표시)
2. 국제 증시 주요 종목 표 (제공된 데이터 사용)
3. 한국 정치·경제·사회 주요 뉴스 (핵심 뉴스 5개, 3줄 요약, 출처 표시)
4. 한국 증시 주요 종목 표 (제공된 데이터 사용)
5. 오늘의 주요 일정 (경제, 정치)
6. 거주지 기준 날씨 (한국 경기도 기준 - 현재 온도, 최고/최저, 강수확률, 미세먼지 요약)

[출력 스타일]
간결하고 보고서 스타일, 불필요한 수식어 금지.
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
