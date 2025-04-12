import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib_venn import venn2
from openai import OpenAI
import os

st.set_page_config(page_title="GPTS 포트폴리오 배발", layout="wide")
st.title("포트폴리오 GPTS 배발")

# GPT API 키 설정
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or st.secrets["OPENAI_API_KEY"])

famous_investors = {
    "Warren Buffett": ["AAPL", "KO", "BAC", "AXP", "CVX"],
    "Ray Dalio": ["SPY", "VWO", "GLD", "EMB"],
    "Cathie Wood": ["TSLA", "ROKU", "SQ", "PATH"],
    "Michael Burry": ["GOOGL", "META", "BABA", "JD"]
}

uploaded_file = st.file_uploader("📂 포트폴리오 파일 업로드 (CSV 또는 Excel)", type=["xlsx", "csv"])

# 사용자 투자 성향 입력
st.sidebar.subheader("📌 투자 성향 설정")
risk_pref = st.sidebar.slider("안정성 (1: 매우 공격적 ~ 5: 매우 안정적)", 1, 5, 3)
dividend_pref = st.sidebar.slider("배당 선호도 (1: 중요하지 않음 ~ 5: 매우 중요)", 1, 5, 3)

# 스타일 태그 출력
st.sidebar.subheader("🏷️ 예측 스타일 태그")
style_tags = []
if risk_pref <= 2:
    style_tags.append("공격적")
elif risk_pref >= 4:
    style_tags.append("안정적")
else:
    style_tags.append("중립")

if dividend_pref <= 2:
    style_tags.append("성장 선호")
elif dividend_pref >= 4:
    style_tags.append("배당 선호")
else:
    style_tags.append("혼합형")

st.sidebar.markdown(f"**투자 스타일:** {' / '.join(style_tags)}")

if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("📄 업로드한 포트폴리오")
    st.dataframe(df)

    if "종목" in df.columns and "금액" in df.columns:
        tickers = df["종목"].astype(str).str.upper().tolist()
        weights = df["금액"].astype(float).tolist()

        st.subheader("📊 실시간 시세 반영")
        data = yf.download(tickers, period="1d")["Close"]
        current_prices = data.iloc[-1].to_dict()
        price_df = pd.DataFrame({"종목": tickers, "현재가": [current_prices[t] for t in tickers], "금액": weights})
        price_df["수량"] = price_df["금액"] / price_df["현재가"]
        st.dataframe(price_df)

        st.subheader("📈 종목 구성 비중")
        fig, ax = plt.subplots()
        ax.pie(weights, labels=tickers, autopct="%1.1f%%")
        ax.axis("equal")
        st.pyplot(fig)

        st.subheader("🧠 유명 트레이드 주식 대가와 보유 종목 비교")
        for investor, inv_tickers in famous_investors.items():
            overlap = list(set(tickers) & set(inv_tickers))
            with st.expander(f"{investor} 포트폴리오 비교"):
                st.write(f"💼 {investor}의 포트폴리오: {', '.join(inv_tickers)}")
                if overlap:
                    st.success(f"✅ 겹치는 종목: {', '.join(overlap)}")
                else:
                    st.warning("❌ 겹치는 종목 없음")

                fig, ax = plt.subplots()
                venn2([set(tickers), set(inv_tickers)], set_labels=("내 포트폴리오", investor))
                st.pyplot(fig)

        st.subheader("💬 GPT에게 포트폴리오 해석 및 추천 요청")
        if st.button("🔍 GPT 반응 시작"):
            portfolio_str = "\n".join([f"{r['종목']}: {r['금액']}원" for _, r in df.iterrows()])
            all_investors_str = "\n".join([f"{name}: {', '.join(tickers)}" for name, tickers in famous_investors.items()])
            prompt = f"""
            다음은 사용자의 투자 포트폴리오입니다:
            {portfolio_str}

            유명 투자자들의 포트폴리오는 다음과 같습니다:
            {all_investors_str}

            이 포트폴리오를 종목 구성, 비중, 산업 섹터, 스타일(가치/성장/배당) 기준으로 분석해줘.
            또한 Warren Buffett, Ray Dalio, Cathie Wood, Michael Burry 포트폴리오와 비교해서 겹치는 종목이 있는지, 투자 성향이 유사한지 알려줘.
            사용자의 투자 성향은 다음과 같아:
            - 안정성 선호도: {risk_pref} / 5
            - 배당 선호도: {dividend_pref} / 5
            이 성향을 고려하여 포트폴리오의 위험도와 수익성의 균형을 평가하고, 해당 성향에 맞는 종목 또는 ETF를 추천해줘.
            """
            with st.spinner("GPT 분석 중입니다..."):
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "당신은 금융 분석가입니다."},
                        {"role": "user", "content": prompt}
                    ]
                )
                gpt_output = response.choices[0].message.content
                st.markdown("#### 📝 GPT 분석 결과 및 추천")
                st.markdown(gpt_output)
    else:
        st.error("[종목] 과 [금액] 컬럼이 필요합니다.")
else:
    st.info("CSV 또는 Excel 포트폴리오 파일을 업로드해주세요. 예: 종목, 금액")
