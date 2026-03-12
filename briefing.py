import requests
import os
import datetime
import yfinance as yf

GEMINI_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
NEWS_KEY = os.environ["NEWS_API_KEY"]

today = datetime.date.today()

# -------------------------
# 미국 주요 종목
# -------------------------

us_tickers = ["GOOGL","RIG","KHC","LULU"]

us_data = []

for t in us_tickers:
    s = yf.Ticker(t)
    hist = s.history(period="2d")

    price = round(hist["Close"].iloc[-1],2)
    prev = round(hist["Close"].iloc[-2],2)

    change = round(price-prev,2)
    pct = round((change/prev)*100,2)

    us_data.append(f"{t} | {price} | {change} | {pct}%")

us_market = "\n".join(us_data)

# -------------------------
# 한국 종목
# -------------------------

kr_tickers = {
"대덕전자":"353200.KQ",
"한미사이언스":"008930.KS",
"케이알엠":"093640.KQ",
"서흥":"008490.KS",
"대정화금":"120240.KQ",
"대한항공":"003490.KS",
"F&F":"383220.KS",
"AJ네트웍스":"095570.KS"
}

kr_data=[]

for name,ticker in kr_tickers.items():

    s=yf.Ticker(ticker)
    hist=s.history(period="2d")

    price=round(hist["Close"].iloc[-1],0)
    #prev=round(hist["Close"].iloc[-2],0)
    if len(hist) >= 2:
    prev = round(hist["Close"].iloc[-2], 0)
else:
    prev = round(hist["Close"].iloc[-1], 0)

    change=round(price-prev,0)
    pct=round((change/prev)*100,2)

    kr_data.append(f"{name} | {price} | {change} | {pct}%")

kr_market="\n".join(kr_data)

# -------------------------
# 지수
# -------------------------

indexes={
"S&P500":"^GSPC",
"NASDAQ":"^IXIC",
"BTC":"BTC-USD",
"USD/KRW":"KRW=X"
}

idx_data=[]

for name,ticker in indexes.items():

    s=yf.Ticker(ticker)
    hist=s.history(period="2d")

    price=round(hist["Close"].iloc[-1],2)
    prev=round(hist["Close"].iloc[-2],2)

    change=round(price-prev,2)
    pct=round((change/prev)*100,2)

    idx_data.append(f"{name} | {price} | {change} | {pct}%")

index_market="\n".join(idx_data)

# -------------------------
# 뉴스 수집
# -------------------------

url=f"https://newsapi.org/v2/top-headlines?category=business&pageSize=10&apiKey={NEWS_KEY}"

news=requests.get(url).json()

headlines=[]

for n in news["articles"]:
    headlines.append(n["title"])

news_text="\n".join(headlines)

# -------------------------
# AI 분석
# -------------------------

prompt=f"""
You are a macro financial analyst.

Create a professional morning briefing.

Date: {today}

Market Index
{index_market}

US Stocks
{us_market}

Korea Stocks
{kr_market}

News Headlines
{news_text}

Return format

1 Global Macro Summary (5 bullets)

2 Market Snapshot tables

3 Korea Market Analysis

4 Key Risks Today

5 Important Economic Events

6 Weather Korea
"""

gemini_url=f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

data={
"contents":[{"parts":[{"text":prompt}]}]
}

res=requests.post(gemini_url,json=data)

briefing=res.json()["candidates"][0]["content"]["parts"][0]["text"]

# -------------------------
# Telegram 전송
# -------------------------

telegram_url=f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

payload={
"chat_id":CHAT_ID,
"text":briefing
}

requests.post(telegram_url,data=payload)
