from __future__ import annotations

from collections import defaultdict
import html

import pandas as pd
import streamlit as st

def theme():
    # The global StockDash theme is applied in ui_v2.apply_theme().
    # Keep this function as a compatibility hook for callers that used bi_view.theme().
    return

def overview(details, snapshot):
    reports = [r for _, r, _, _ in details.values() if r]
    positions = (snapshot or {}).get('positions', [])
    a,b,c = st.columns(3)
    if positions:
        value = sum(float(p['value']) for p in positions)
        pnl = sum(float(p['pnl']) for p in positions)
        a.metric('국내주식 평가금액', f'{value:,.0f}원')
        b.metric('평가손익', f'{pnl:+,.0f}원', f'{pnl/(value-pnl)*100:+.1f}%' if value-pnl>0 else None)
        c.metric('보유 / 관심종목', f'{len(positions)} / {len(details)}')
        st.caption('계좌 조회 시점 기준 · 예수금 제외 · ' + str(snapshot.get('fetched','')))
    else:
        a.metric('내 관심종목', f'{len(details)}개')
        b.metric('조사 자료 보유', f'{len(reports)}개')
        c.metric('추가 조사 필요', f'{len(details)-len(reports)}개')
    left,right=st.columns([1,1.5],gap='large')
    with left, st.container(border=True):
        st.subheader('어디에 투자하고 있나요?')
        if positions:
            df=pd.DataFrame([{'종목':p['name'],'평가액':p['value']} for p in positions if p['value']>0])
            if not df.empty:
                df['비중']=df['평가액']/df['평가액'].sum()
                st.dataframe(df[['종목','평가액','비중']], hide_index=True, use_container_width=True)
                st.caption('조회된 국내주식 평가액 기준 · 현금 제외')
        else:
            st.markdown('**계좌를 연결하면 보유 비중을 보여드립니다.**')
            st.write('관심종목만 등록해도 오른쪽에서 기업별 실적을 비교할 수 있습니다.')
            st.caption('왼쪽 메뉴 → 계좌 연결')
            st.markdown(' · '.join(html.escape(s['name']) for s,_,_,_ in details.values()))
    with right, st.container(border=True):
        st.subheader('이익이 더 빠르게 늘어나는 기업은?')
        groups=defaultdict(list)
        for r in reports:
            f=r.get('financial')
            if f:
                key=(f['period'],f['prior_period'],f['basis'],f['currency'],f['unit'])
                groups[key].append((r,f))
        if not groups:
            st.info('종목 조사 결과가 들어오면 실적 그래프가 표시됩니다.')
        else:
            keys=list(groups)
            key=st.selectbox('비교 기간·기준',keys,format_func=lambda k:f'{k[0]} 누적 / 전년 {k[1]} · {k[2]}',key='bi_period') if len(keys)>1 else keys[0]
            bars=[]; special=[]
            for r,f in groups[key]:
                prior=f['prior_operating_profit'];now=f['operating_profit']
                if prior>0:bars.append({'종목':r['name'],'증가율':(now/prior-1)*100})
                else:special.append(r['name']+' · 전년 이익이 0 이하: 상세 실적 확인')
            if bars:
                df=pd.DataFrame(bars)
                st.bar_chart(df.set_index('종목')[['증가율']], use_container_width=True, height=245)
            st.caption(f'{key[0]} / {key[1]} · {key[2]} · 같은 기간과 회계기준의 기업만 비교')
            for text in special:st.caption(text)


def detail(r):
    a,b,c=st.columns([1.15,1,1],gap='large')
    with a,st.container(border=True):
        st.subheader('주력사업과 기업 특징')
        business=r.get('business') or r.get('summary')
        if business:st.markdown('<div class="px-business">'+html.escape(business['text'])+'</div>',unsafe_allow_html=True)
        else:st.info('사업 내용 조사 필요')
    with b,st.container(border=True):
        st.subheader('영업이익 변화')
        f=r.get('financial')
        if f:
            df=pd.DataFrame([{'기간':f['prior_period'],'영업이익':f['prior_operating_profit']},{'기간':f['period'],'영업이익':f['operating_profit']}])
            st.bar_chart(df.set_index('기간')[['영업이익']], use_container_width=True, height=210)
            margin=f['operating_profit']/f['revenue']*100 if f['revenue']>0 else None
            st.caption(f"{f['basis']} · {f['currency']} {f['unit']}"+(f' · 영업이익률 {margin:.1f}%' if margin is not None else ''))
        else:st.info('같은 기간의 전년·당년 실적이 필요합니다.')
    with c,st.container(border=True):
        st.subheader('가격과 가치의 거리')
        v=r.get('valuation')
        if v:
            df=pd.DataFrame([{'구분':label,'가격':v[k]} for k,label in [('low','낮은 참고가'),('base','기본 참고가'),('high','높은 참고가'),('current_price','비교 주가')]])
            st.dataframe(df, hide_index=True, use_container_width=True)
            st.metric('기본 참고가',f"{v['base']:,.0f}원")
            st.caption(f"가격 기준일 {v['price_date']} · 평가 가정은 상세 탭에서 확인")
        else:
            st.write('**평가 근거를 기다리고 있습니다.**')
            st.caption('현재 주가와 실적 전망, 적용 배수의 근거가 모이면 참고가 범위를 표시합니다.')


def peers_chart(peers):
    df=pd.DataFrame(peers['rows']).rename(columns={'name':'기업','operating_profit':'영업이익'})
    st.bar_chart(df.set_index('기업')[['영업이익']], use_container_width=True, height=max(150,min(400,len(df)*45)))
