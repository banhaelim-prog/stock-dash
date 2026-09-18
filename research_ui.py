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
    cls = {
        "분석 완료": "ok",
        "기존 분석 있음": "ok",
        "조사 필요": "wait",
    }.get(status, "wait")
    st.markdown(
        f'<span class="planx-source planx-status-{cls}">{status}</span>',
        unsafe_allow_html=True,
    )


def render_research(store, state, sample_mode):
    # This is the actual default page wired from app.py ("내 종목").
    # Keep all existing research/data behavior, but present it as the redesigned dashboard.
    topbar("반혜림")
    hero(
        "내 투자 대시보드",
        "관심종목의 실적·수급·가치·주가 흐름을 한 화면에서 확인합니다.",
        "STOCKDASH · INVESTMENT DASHBOARD",
    )

    research = published()
    for item in state.get("chat_research", []):
        if item["code"] not in research or item["as_of"] >= research[item["code"]]["as_of"]:
            research[item["code"]] = item

    stocks = {s["code"]: s for s in state.get("stocks", [])}
    for p in st.session_state.get("account_snapshot", {}).get("positions", []):
        stocks[p["code"]] = {**stocks.get(p["code"], {}), "code": p["code"], "name": p["name"]}

    # Add stock
    with st.container(border=True):
        a, b = st.columns([4, 1.1])
        with a:
            st.markdown("**관심종목 추가**")
            st.caption("기업명만 입력해도 저장할 수 있습니다. 종목코드는 선택입니다.")
        with b:
            add_open = st.button("＋ 종목 추가", type="primary", use_container_width=True)

        if add_open or not stocks:
            with st.form("research_manual"):
                name = st.text_input("종목명", placeholder="예: 삼성전자", label_visibility="collapsed")
                c1, c2 = st.columns([2, 1])
                with c1:
                    code = st.text_input("종목코드", placeholder="종목코드 6자리 · 선택", max_chars=6)
                with c2:
                    submitted = st.form_submit_button("내 목록에 추가", type="primary", use_container_width=True)
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

    if sample_mode:
        st.info("둘러보기 중입니다. 실제 관심종목 저장은 앱의 저장소 설정 후 사용할 수 있습니다.")

    if not stocks:
        empty_state(
            "첫 관심종목을 담아보세요",
            "위에서 기업명을 입력하면 이 대시보드에 실적과 분석 결과가 표시됩니다.",
        )
        return

    # Build dashboard rows from the same research source as the old page.
    rows, details = [], {}
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

        rows.append(
            {
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
            }
        )
        details[key] = (stock, r, trend, frame)

    # KPI strip
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
            ("조사 자료", f"{len(reports)}개", "현재 저장된 자료", ""),
            ("조사 필요", f"{len(details) - len(reports)}개", "다음 확인 대상", ""),
            ("계좌 연결", "미연결", "연결하면 보유 비중 표시", ""),
        ]

    cols = st.columns(4)
    for col, (title, value, note, tone) in zip(cols, kpis):
        with col:
            card(title, value, note, tone=tone)

    section_title("내 종목 현황", "종목별 핵심 지표")
    with st.container(border=True):
        display = pd.DataFrame(rows)
        st.dataframe(
            display[
                ["종목", "코드", "매출 성장", "영업이익 성장",
                 "외국인 / 기관", "적정주가 참고", "상태", "조사일"]
            ],
            hide_index=True,
            use_container_width=True,
        )

    # Visual BI area remains backed by the existing data.
    section_title("투자 현황", "계좌가 연결되면 보유 비중과 기업별 비교가 표시됩니다.")
    overview(details, st.session_state.get("account_snapshot"))

    # Research request is secondary, not the page's main layout.
    with st.expander("조사 요청 · 최신 내용으로 업데이트"):
        st.write(
            "① 종목을 추가하거나 포트폴리오에서 계좌를 불러옵니다. "
            "② 아래 요청문을 이 대화창에 보냅니다. ③ 조사 결과가 반영되면 새로고침합니다."
        )
        st.code(request_text(list(stocks.values())), language=None)
        if st.button("반영된 조사 결과 다시 읽기"):
            st.rerun()

        if not sample_mode:
            with st.expander("조사 파일 가져오기 · 고급"):
                upload = st.file_uploader(
                    "조사 JSON 가져오기 · 선택", type=["json"], key="research_upload"
                )
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

    section_title("기업 하나를 깊게 보기", "종목을 선택하면 상세 분석이 열립니다.")
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
            st.info(
                "이 종목의 조사 결과가 아직 없습니다. 위 조사 요청문을 대화창에 보내면 "
                "기업·실적·주가·가치 자료를 채울 수 있습니다."
            )
            if stock.get("report"):
                st.write("기존 공식 결산 분석: " + brief(stock["report"])["summary"])
        return

    with st.container(border=True):
        st.markdown(f"### {stock['name']}")
        st.caption(
            "조사일 " + r["as_of"]
            + " · 각 자료의 기간과 출처는 상세 탭에서 확인합니다. 실시간 분석이 아닙니다."
        )
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
            st.caption(
                f"누적 {f['period']} / 전년 {f['prior_period']} · "
                f"{f['basis']} · {f['currency']} {f['unit']}"
            )
            st.dataframe(
                [
                    {
                        "항목": "매출",
                        "이번 누적": f["revenue"],
                        "전년 누적": f["prior_revenue"],
                        "변화": growth(f["revenue"], f["prior_revenue"]),
                    },
                    {
                        "항목": "영업이익",
                        "이번 누적": f["operating_profit"],
                        "전년 누적": f["prior_operating_profit"],
                        "변화": growth(f["operating_profit"], f["prior_operating_profit"]),
                    },
                ],
                hide_index=True,
                use_container_width=True,
            )
            st.link_button("실적 근거", f["source"], key="research_financial")
        else:
            st.info("전년 같은 기간 누적 실적 조사 필요")

        peers = r.get("peers")
        st.subheader("경쟁사 영업이익 비교")
        if peers and peers["rows"]:
            st.write(peers["selection_reason"])
            peers_chart(peers)
            df = pd.DataFrame(peers["rows"])
            df["순위"] = df["operating_profit"].rank(method="min", ascending=False).astype(int)
            st.dataframe(
                df.sort_values("순위")[
                    ["순위", "name", "operating_profit", "source"]
                ].rename(
                    columns={
                        "name": "기업",
                        "operating_profit": "영업이익",
                        "source": "출처",
                    }
                ),
                hide_index=True,
                use_container_width=True,
            )
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
        else:
            st.info("가격 시계열 자료 조사 필요")

    with tabs[3]:
        v = r.get("valuation")
        if v:
            a, b, c = st.columns(3)
            a.metric("낮은 참고가", f"{v['low']:,.0f}원")
            b.metric("기본 참고가", f"{v['base']:,.0f}원")
            c.metric("높은 참고가", f"{v['high']:,.0f}원")
            st.write(v["method"])
            st.caption(
                f"비교 가격 {v['current_price']:,.0f}원 · {v['price_date']} · "
                f"기본 참고가 대비 차이 {(v['base']/v['current_price']-1)*100:+.1f}%"
            )
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
                        store.log(
                            "journal",
                            {
                                "code": selected,
                                "at": datetime.now(timezone.utc).isoformat(),
                                "kind": "note",
                                "note": note.strip(),
                            },
                        )
                        st.success("일지를 저장했습니다.")
                    except Exception:
                        st.error("저장 실패. 입력 내용을 보관하세요.")
