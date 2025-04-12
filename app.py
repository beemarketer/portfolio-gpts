import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib import rcParams
from openai import OpenAI
import os

# 한글 폰트 설정
rcParams['font.family'] = 'DejaVu Sans'

st.set_page_config(page_title="주식 포트폴리오 분석", layout="wide")
st.title("주식 포트폴리오 분석")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or st.secrets["OPENAI_API_KEY"])

uploaded_file = st.file_uploader("📂 포트폴리오 파일 업로드 (CSV 또는 Excel)", type=["xlsx", "csv"])

st.sidebar.subheader("📌 투자 성향 설정")
risk_pref = st.sidebar.slider("안정성 (1: 매우 공격적 ~ 5: 매우 안정적)", 1, 5, 3)
dividend_pref = st.sidebar.slider("배당 선호도 (1: 중요하지 않음 ~ 5: 매우 중요)", 1, 5, 3)

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


# 산업/ETF 정보 가져오는 함수
def get_business_info(ticker):
    try:
        info = yf.Ticker(ticker).info
        if 'fundFamily' in info or 'category' in info or 'trackingSymbol' in info:
            # ETF로 간주
            index_info = info.get('category') or info.get('trackingSymbol') or "지수 정보 없음"
            return "ETF", index_info
        else:
            sector = info.get("sector", "정보 없음")
            industry = info.get("industry", "정보 없음")
            return sector, industry
    except Exception:
        return "정보 없음", "정보 없음"


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
        price_df = pd.DataFrame({
            "종목": tickers,
            "현재가": [current_prices[t] for t in tickers],
            "금액": weights
        })
        price_df["수량"] = price_df["금액"] / price_df["현재가"]
        st.dataframe(price_df)

        st.subheader("📈 종목 구성 비중")
        fig, ax = plt.subplots()
        ax.pie(weights, labels=tickers, autopct="%1.1f%%")
        ax.axis("equal")
        st.pyplot(fig)

        # 비즈니스 및 섹터 분석
        st.subheader("🏢 비즈니스 섹터 및 ETF 분석")
        sector_summary = []
        for ticker in tickers:
            sector, industry = get_business_info(ticker)
            if sector == "ETF":
                summary = f"{ticker} (ETF) → 추종 지수: {industry}"
            else:
                summary = f"{ticker} → 섹터: {sector}, 산업군: {industry}"
            sector_summary.append(summary)

        sector_info_str = "\n".join(sector_summary)
        st.markdown("```\n" + sector_info_str + "\n```")

        # GPT 분석 요청
        if df is not None and not df.empty:
            st.subheader("💬 GPT에게 포트폴리오 해석 및 추천 요청")

            famous_investors = [
                "Warren Buffett",
                "Ray Dalio",
                "Cathie Wood",
                "Michael Burry"
            ]
            all_investors_str = ", ".join(famous_investors)

            if st.button("🔍 GPT 반응 시작"):
                portfolio_str = "\n".join([
                    f"{r['종목']}: {r['금액']}원" for _, r in df.iterrows()
                ])

                prompt = f"""
                다음은 사용자의 투자 포트폴리오입니다:
                {portfolio_str}

                각 종목의 산업 및 ETF 추종 지수 정보는 다음과 같습니다:
                {sector_info_str}

                유명 투자자들은 다음과 같습니다: {all_investors_str}

                이 포트폴리오를 종목 구성, 비중, 산업 섹터, 스타일(가치/성장/배당) 기준으로 분석해줘.
                또한 위 투자자들과 비교해 유사한 투자 성향이 있는지 알려줘.

                사용자의 투자 성향은 다음과 같아:
                - 안정성 선호도: {risk_pref} / 5
                - 배당 선호도: {dividend_pref} / 5

                이 성향을 고려하여 아래 항목을 제안해줘:
                1. 포트폴리오의 위험도와 수익성에 대한 종합 평가
                2. 리밸런싱 전략: 줄이거나 늘려야 할 종목 또는 섹터
                3. 현재 종목 중 교체 추천이 필요한 항목과 그 이유
                4. 성향에 맞는 신규 종목 또는 ETF 추천 리스트

                각 제안은 간결하게 요약하고, 비중 조절도 수치로 포함해줘.
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
                st.markdown("#### 📝 GPT 분석 결과 및 리밸런싱 전략")
                st.markdown(gpt_output)
    else:
        st.error("[종목] 과 [금액] 컬럼이 필요합니다.")
else:
    st.info("CSV 또는 Excel 포트폴리오 파일을 업로드해주세요. 예: 종목, 금액")
