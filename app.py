...
        st.subheader("💬 GPT에게 포트폴리오 해석 및 추천 요청")
        if st.button("🔍 GPT 반응 시작"):
            portfolio_str = "\n".join([f"{r['종목']}: {r['금액']}원" for _, r in df.iterrows()])
            all_investors_str = "\n".join([f"{name}: {', '.join(info['tickers'])}" for name, info in famous_investors.items()])
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
...
