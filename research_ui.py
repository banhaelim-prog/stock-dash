import hashlib
import re
from datetime import date

import pandas as pd
import streamlit as st

from ui_v2 import hero, card, empty_state, section_title, panel_title, topbar
from automatic import brief
from bi_view import overview, detail, peers_chart
from chat_research import published, parse_bundle, trends, growth, request_text


def _stock_status(stock, report):
    if report:
        return "분석 완료"
    if stock.get("report"):
        return "기존 분석 있음"
    return "조사 필요"


def _status_badge(status):
    cls = {"분석 완료": "ok", "기존 분석 있음": "ok", "조사 필요": "wait"}.get(status, "wait")
    st.markdown(
        f'<span class="planx-source planx-status-{cls}">{status}</span>',
        unsafe_allow_html=True,
    )


def _add_stock(store, state):
    stocks = {s["code"]: s for s in state.get("stocks", [])}
    with st.container(border=True):
        a, b = st.columns([4, 1.15])
        with a:
            st.markdown("**관심종목 관리**")
            st.caption("기업명을 입력해 대시보드에 종목을 추가합니다.")
        with b:
            add_open = st.button("＋ 종목 추가", type="primary", use_container_width=True)

        if add_open or not stocks:
            with st.form("research_manual"):
                c1, c2, c3 = st.columns([3, 1.5, 1.2])
                with c1:
                    name = st.text_input("종목명", placeholder="예: 삼성전자", label_visibility="collapsed")
                with c2:
                    code = st.text_input("종목코드", placeholder="6자리 · 선택", max_chars=6, label_visibility="collapsed")
                with c3:
                    submitted = st.form_submit_button("목록에 추가", type="primary", use_container_width=True)
                if submitted:
                    if not name.strip() or (code and not re.fullmatch(r"[0-9]{6}", code)):
                        st.error("종목명과 숫자 6자리 코드를 확인하세요. 코드는 생략할 수 있습니다.")
                    else:
                        known = next(
                            (s for s in state.get("stocks", [])
                             if s["name"].strip().casefold() == name.strip().casefold()),
                            {},
                        )
                        identity = (
                            known.get("code")
                            or code
                            or "pending-" + hashlib.sha256(name.strip().casefold().encode()).hexdigest()[:16]
                        )
                        try:
                            store.save_stock(
                                {"code": identity, "name": name.strip(), "kind": known.get("kind", "관심")}
                            )
                            st.session_state.selected_code = identity
                            st.rerun()
                        except Exception:
                            st.error("목록 저장에 실패했습니다. 저장 공간 설정을 확인하세요.")


def _build_details(state):
    research = published()
    for item in state.get("chat_research", []):
        if item["code"] not in research or item["as_of"] >= research[item["code"]]["as_of"]:
            research[item["code"]] = item

    stocks = {s["code"]: s for s in state.get("stocks", [])}
    for p in st.session_state.get("account_snapshot", {}).get("positions", []):
        stocks[p["code"]] = {**stocks.get(p["code"], {}), "code": p["code"], "name": p["name"]}

    details = {}
    rows = []
    for key, stock in stocks.items():
        r = research.get(key)
        if not r and key.startswith("pending-"):
            matches = [
                v for v in research.values()
                if v["name"].strip().casefold() == stock["name"].strip().casefold()
            ]
            if len(matches) == 1:
                r = matches[0]

        r = r or {}
        f = r.get("financial") or {}
        v = r.get("valuation") or {}
        flow = r.get("flow") or {}
        trend, frame = trends(r.get("prices"), r.get("as_of", date.today().isoformat()))

        rows.append({
            "종목": stock["name"],
            "코드": r.get("code", key if not key.startswith("pending-") else "확인 필요"),
            "매출 성장": growth(f["revenue"], f["prior_revenue"]) if f else "조사 필요",
            "영업이익 성장": growth(f["operating_profit"], f["prior_operating_profit"]) if f else "조사 필요",
            "외국인 / 기관": (
                f"{flow['foreign']:+,.0f} / {flow['institution']:+,.0f} {flow['unit']}"
                if flow else "조사 필요"
            ),
            "적정주가 참고": f"{v['base']:,.0f}원" if v else "조사 필요",
            "상태": _stock_status(stock, r),
            "조사일": r.get("as_of", "미조사"),
        })
        details[key] = (stock, r, trend, frame)

    return stocks, details, rows


def _render_kpis(details):
    reports = [r for _, r, _, _ in details.values() if r]
    positions = st.session_state.get("account_snapshot", {}).get("positions", [])

    if positions:
        value = sum(float(p.get("value", 0)) for p in positions)
        pnl = sum(float(p.get("pnl", 0)) for p in positions)
        kpis = [
            ("국내주식 평가금액", f"{value:,.0f}원", "계좌 조회 시점 기준", ""),
            ("평가손익", f"{pnl:+,.0f}원", "예수금 제외", "positive" if pnl >= 0 else "negative"),
            ("보유 / 관심종목", f"{len(positions)} / {len(details)}", "현재 등록 종목", ""),
            ("조사 완료", f"{len(reports)} / {len(details)}", "공식·조사 자료 기준", ""),
        ]
    else:
        kpis = [
            ("내 관심종목", f"{len(details)}개", "현재 등록 종목", ""),
            ("조사 완료", f"{len(reports)}개", "저장된 분석 자료", ""),
            ("조사 필요", f"{len(details) - len(reports)}개", "다음 확인 대상", ""),
            ("계좌 연결", "미연결", "연결하면 보유 비중 표시", ""),
        ]

    cols = st.columns(4)
    for col, (title, value, note, tone) in zip(cols, kpis):
        with col:
            card(title, value, note, tone=tone)


def _render_market_snapshot(details):
    section_title("시장 스냅샷", "연결된 데이터만 표시")
    cols = st.columns(4)
    positions = st.session_state.get("account_snapshot", {}).get("positions", [])
    reports = [r for _, r, _, _ in details.values() if r]

    values = [
        ("KOSPI", "API 연결 대기", "시장 지수"),
        ("KOSDAQ", "API 연결 대기", "시장 지수"),
        ("외국인 수급", "종목별 조사 필요", "보유/관심종목 기준"),
        ("원/달러", "API 연결 대기", "거시 지표"),
    ]
    if positions:
        values[2] = (
            "조회 완료",
            f"{len(positions)}개 보유 종목",
            "계좌 스냅샷 기준",
        )
    elif reports:
        flow_count = sum(bool(r.get("flow")) for r in reports)
        values[2] = ("조회 완료" if flow_count else "조사 필요", f"{flow_count}개 종목", "외국인·기관 수급")

    for col, (title, value, note) in zip(cols, values):
        with col:
            card(title, value, note)


def _render_main_panels(details):
    section_title("시장 & 주요 변화", "시장 전체 데이터는 API 연결 후 활성화됩니다.")
    left, right = st.columns([2.05, 1], gap="large")

    with left:
        with st.container(border=True):
            panel_title("주요 지수 추이")
            empty_state(
                "시장 시계열 API 연결 대기",
                "KOSPI·KOSDAQ 시계열 API가 연결되면 이 영역에 차트를 표시합니다. 가상 지수는 사용하지 않습니다.",
            )

    with right:
        with st.container(border=True):
            panel_title("오늘의 주요 변화")
            candidates = []
            for stock, r, _, _ in details.values():
                for item in r.get("disclosures", [])[:8]:
                    candidates.append((item.get("date", ""), stock["name"], item.get("title", ""), item.get("url", "")))
            candidates.sort(reverse=True)
            if candidates:
                for day, name, title, url in candidates[:5]:
                    st.caption(f"{day} · {name}")
                    if url:
                        st.link_button(title, url, use_container_width=True)
                    else:
                        st.write(title)
            else:
                empty_state(
                    "최근 변화 없음",
                    "관심종목을 분석하면 최근 공시와 주요 변화를 이곳에 모읍니다.",
                )


def _render_focus(details):
    section_title("내 분석 포커스", "기업 · 재무 · 가치")
    if not details:
        empty_state("아직 분석된 종목이 없습니다", "관심종목을 추가하면 기업 분석이 이곳에 표시됩니다.")
        return

    selected = st.selectbox(
        "분석할 종목",
        list(details),
        format_func=lambda k: details[k][0]["name"],
        key="dashboard_focus",
        label_visibility="collapsed",
    )
    stock, report, trend, frame = details[selected]

    left, mid, right = st.columns([1.35, 1, 1], gap="large")
    with left:
        with st.container(border=True):
            panel_title("선택 종목")
            st.markdown(f"### {stock['name']}")
            st.caption(stock.get("code", ""))
            if report.get("business"):
                st.write(report["business"].get("text", ""))
            elif stock.get("report"):
                st.write(brief(stock["report"])["summary"])
            else:
                st.caption("분석 자료를 기다리고 있습니다.")

    with mid:
        with st.container(border=True):
            panel_title("핵심 지표")
            f = report.get("financial") or {}
            if f:
                st.metric("매출 성장", growth(f["revenue"], f["prior_revenue"]))
                st.metric("영업이익 성장", growth(f["operating_profit"], f["prior_operating_profit"]))
                margin = f["operating_profit"] / f["revenue"] * 100 if f["revenue"] else None
                st.metric("영업이익률", f"{margin:.1f}%" if margin is not None else "자료 부족")
            else:
                empty_state("재무자료 없음", "같은 기간 실적 조사 후 표시됩니다.")

    with right:
        with st.container(border=True):
            panel_title("가격 · 가치")
            v = report.get("valuation") or {}
            if v:
                st.metric("기본 참고가", f"{v['base']:,.0f}원")
                st.caption(
                    f"현재 {v['current_price']:,.0f}원 · 기준일 {v['price_date']}"
                )
            else:
                empty_state("평가 보류", "가격과 과거 기준점이 확인되면 참고가를 표시합니다.")

    with st.container(border=True):
        panel_title("실적 추이")
        f = report.get("financial") or {}
        if f:
            df = pd.DataFrame([
                {"기간": f["prior_period"], "영업이익": f["prior_operating_profit"]},
                {"기간": f["period"], "영업이익": f["operating_profit"]},
            ]).set_index("기간")
            st.bar_chart(df)
            st.caption(f"{f['basis']} · {f['currency']} {f['unit']}")
        elif frame is not None:
            st.line_chart(frame.set_index("date")["close"])
        else:
            empty_state("차트 자료 없음", "실적 또는 가격 시계열 자료를 조사하면 표시됩니다.")


def _render_deep_analysis(details, stocks, store, sample_mode):
    if not details:
        return

    section_title("기업 하나를 깊게 보기", "상세 근거와 원문 링크")
    selected = st.selectbox(
        "자세히 볼 종목",
        list(details),
        format_func=lambda k: stocks[k]["name"],
        key="research_selected",
        label_visibility="collapsed",
    )
    stock, r, trend, frame = details[selected]

    if not r:
        with st.container(border=True):
            panel_title(stock["name"] + " · 분석 대기")
            st.info("이 종목의 조사 결과가 아직 없습니다. 아래 조사 요청문을 사용하세요.")
            if stock.get("report"):
                st.write("기존 공식 결산 분석: " + brief(stock["report"])["summary"])
        return

    with st.container(border=True):
        st.markdown(f"### {stock['name']}")
        st.caption("조사일 " + r["as_of"] + " · 각 자료의 기간과 출처는 상세 탭에서 확인합니다.")
        detail(r)

    tabs = st.tabs(["기업", "실적", "주가·수급", "가격·가치"])
    with tabs[0]:
        entry = r.get("business")
        if entry:
            st.subheader("주력사업과 기업 특징")
            st.write(entry["text"])
            st.link_button("설명의 원문 근거", entry["source"], key="research_business")
        else:
            st.info("사업 내용 조사 필요")

    with tabs[1]:
        f = r.get("financial")
        if f:
            st.caption(f"누적 {f['period']} / 전년 {f['prior_period']} · {f['basis']} · {f['currency']} {f['unit']}")
            st.dataframe([
                {"항목": "매출", "이번 누적": f["revenue"], "전년 누적": f["prior_revenue"], "변화": growth(f["revenue"], f["prior_revenue"])},
                {"항목": "영업이익", "이번 누적": f["operating_profit"], "전년 누적": f["prior_operating_profit"], "변화": growth(f["operating_profit"], f["prior_operating_profit"])},
            ], hide_index=True, use_container_width=True)
            st.link_button("실적 근거", f["source"], key="research_financial")

        peers = r.get("peers")
        st.subheader("경쟁사 영업이익 비교")
        if peers and peers["rows"]:
            st.write(peers["selection_reason"])
            peers_chart(peers)
        else:
            st.info("같은 기간·회계기준의 경쟁사 실적 조사 필요")

    with tabs[2]:
        flow = r.get("flow")
        if flow:
            a, b = st.columns(2)
            a.metric("외국인 순매수", f"{flow['foreign']:+,.0f}")
            b.metric("기관 순매수", f"{flow['institution']:+,.0f}")
            st.caption(flow["start"] + " ~ " + flow["end"] + " · " + flow["unit"])
            st.link_button("수급 근거", flow["source"], key="research_flow")
        else:
            st.info("외국인·기관 수급 조사 필요")
        a, b = st.columns(2)
        a.metric("일봉 추세", trend["daily"])
        b.metric("완료 주봉 추세", trend["weekly"])
        if frame is not None:
            st.line_chart(frame.set_index("date")["close"])
            st.link_button("가격 자료 근거", r["prices"]["source"], key="research_prices")

    with tabs[3]:
        v = r.get("valuation")
        if v:
            a, b, c = st.columns(3)
            a.metric("낮은 참고가", f"{v['low']:,.0f}원")
            b.metric("기본 참고가", f"{v['base']:,.0f}원")
            c.metric("높은 참고가", f"{v['high']:,.0f}원")
            st.write(v["method"])
            st.caption(f"비교 가격 {v['current_price']:,.0f}원 · {v['price_date']}")
            st.link_button("평가 근거", v["source"], key="research_valuation")
        else:
            st.info("평가 가정과 가격 근거 조사 필요")
        for gap in r.get("data_gaps", []):
            st.write("확인 필요 · " + str(gap))

    if not sample_mode:
        with st.expander("투자일지 남기기"):
            with st.form("research_note"):
                note = st.text_area("투자일지 · 다음 확인할 조건")
                if st.form_submit_button("기록 저장") and note.strip():
                    try:
                        from datetime import datetime, timezone
                        store.log("journal", {
                            "code": selected,
                            "at": datetime.now(timezone.utc).isoformat(),
                            "kind": "note",
                            "note": note.strip(),
                        })
                        st.success("일지를 저장했습니다.")
                    except Exception:
                        st.error("저장 실패. 입력 내용을 보관하세요.")


def render_research(store, state, sample_mode):
    # Actual default page: a dashboard-first layout matching the previously designed sample.
    topbar("반혜림")
    hero(
        "내 투자 대시보드",
        "관심종목과 투자 데이터를 한눈에 보고, 필요한 기업만 깊게 분석합니다.",
        "STOCKDASH · INVESTMENT DASHBOARD",
    )

    stocks, details, rows = _build_details(state)

    _render_kpis(details)

    # The watchlist is part of the dashboard, not a separate legacy page.
    section_title("내 종목 현황", "관심종목 · 보유종목 · 분석 상태")
    if rows:
        with st.container(border=True):
            st.dataframe(
                pd.DataFrame(rows)[[
                    "종목", "코드", "매출 성장", "영업이익 성장",
                    "외국인 / 기관", "적정주가 참고", "상태", "조사일"
                ]],
                hide_index=True,
                use_container_width=True,
            )
    else:
        empty_state("첫 관심종목을 추가하세요", "아래 관심종목 관리에서 기업을 등록하면 대시보드가 채워집니다.")

    _render_market_snapshot(details)
    _render_main_panels(details)
    _render_focus(details)

    section_title("종목 관리", "대시보드 하단에서 추가·업데이트")
    _add_stock(store, state)

    with st.expander("조사 요청 · 최신 내용으로 업데이트"):
        st.write(
            "① 종목을 추가합니다. ② 아래 요청문을 이 대화창에 보냅니다. "
            "③ 조사 결과가 반영되면 새로고침합니다."
        )
        st.code(request_text(list(stocks.values())), language=None)

        if st.button("반영된 조사 결과 다시 읽기"):
            st.rerun()

        if not sample_mode:
            with st.expander("조사 파일 가져오기 · 고급"):
                upload = st.file_uploader("조사 JSON 가져오기 · 선택", type=["json"], key="research_upload")
                if upload and st.button("조사 파일 검증·저장"):
                    try:
                        reports_to_save = parse_bundle(upload.getvalue())

                        def save(data):
                            merged = {r["code"]: r for r in data.get("chat_research", [])}
                            for item in reports_to_save:
                                if item["code"] not in merged or item["as_of"] >= merged[item["code"]]["as_of"]:
                                    merged[item["code"]] = item
                            data["chat_research"] = list(merged.values())

                        store.change(save)
                        st.rerun()
                    except (ValueError, KeyError, TypeError):
                        st.error("조사 파일의 형식·출처·기간을 확인하세요. 기존 결과는 유지했습니다.")
                    except Exception:
                        st.error("저장에 실패했습니다. 기존 결과는 유지했습니다.")

    _render_deep_analysis(details, stocks, store, sample_mode)
