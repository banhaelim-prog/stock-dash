from __future__ import annotations

import html
import streamlit as st


def apply_theme():
    st.markdown(
        """
<style>
:root {
  --bg: #f5f7fb;
  --surface: #ffffff;
  --surface-2: #f8fafc;
  --line: #e5eaf1;
  --text: #172033;
  --muted: #718096;
  --sidebar: #172033;
  --sidebar-2: #202b40;
  --blue: #2563eb;
  --blue-soft: #edf4ff;
  --green: #08a66a;
  --green-soft: #e9fbf3;
  --red: #e04b4b;
  --red-soft: #fff0f0;
}
html, body, [class*="css"] {
  font-family: Pretendard, "Noto Sans KR", "Apple SD Gothic Neo", sans-serif;
}
.stApp {
  background: var(--bg);
  color: var(--text);
}
.block-container {
  max-width: 1440px;
  padding: 1.6rem 2rem 4rem;
}
header[data-testid="stHeader"] {
  background: rgba(245,247,251,.9);
  backdrop-filter: blur(14px);
}
section[data-testid="stSidebar"] {
  background: var(--sidebar);
  border-right: 0;
}
section[data-testid="stSidebar"] > div {
  padding: 1rem .85rem;
}
[data-testid="stSidebar"] .stRadio > label { display:none; }
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] { gap: 6px; }
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
  border-radius: 11px;
  padding: 9px 11px;
  color: #cbd5e1;
  transition: background .15s ease;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
  background: var(--sidebar-2);
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked) {
  background: #33415a;
  color: #ffffff;
  font-weight: 700;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label p { color: inherit; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color:#8fa0b8; }
h1,h2,h3,h4 { color:var(--text); letter-spacing:-.035em; }
h1 { font-weight:800; }
h2,h3 { font-weight:760; }
[data-testid="stMetric"] {
  background:var(--surface);
  border:1px solid var(--line);
  border-radius:15px;
  padding:16px 18px;
  box-shadow:0 6px 22px rgba(23,32,51,.035);
}
[data-testid="stMetricLabel"] { color:var(--muted); }
[data-testid="stMetricValue"] { color:var(--text); font-weight:800; }
[data-testid="stVerticalBlockBorderWrapper"] {
  border-color:var(--line) !important;
  border-radius:15px !important;
  background:var(--surface);
  box-shadow:0 6px 22px rgba(23,32,51,.03);
}
.stButton > button, .stFormSubmitButton > button {
  border-radius:10px;
  min-height:2.55rem;
  font-weight:700;
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
  background:var(--blue);
  border-color:var(--blue);
}
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
  border-radius:10px !important;
}
.stDataFrame { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
.stTabs [data-baseweb="tab-list"] { gap:6px; }
.stTabs [data-baseweb="tab"] { border-radius:9px; padding:8px 12px; }

.planx-brand {
  display:flex;
  align-items:center;
  gap:10px;
  margin:3px 4px 26px;
}
.planx-brand-mark {
  width:36px; height:36px; border-radius:10px;
  display:flex; align-items:center; justify-content:center;
  background:linear-gradient(145deg,#2563eb,#60a5fa);
  color:white; font-size:18px; font-weight:800;
}
.planx-brand-title { color:#fff; font-size:18px; line-height:1.15; font-weight:800; letter-spacing:-.03em; }
.planx-brand-sub { color:#91a0b7; font-size:10px; margin-top:3px; }

.planx-topbar {
  display:flex; justify-content:space-between; align-items:flex-start;
  margin-bottom:18px;
}
.planx-greeting { font-size:14px; color:var(--muted); margin-bottom:3px; }
.planx-greeting strong { color:var(--text); font-size:20px; }
.planx-date { color:var(--muted); font-size:12px; padding-top:5px; }

.planx-hero {
  background:linear-gradient(135deg,#fff 0%,#f9fbff 62%,#eef5ff 100%);
  border:1px solid var(--line);
  border-radius:18px;
  padding:24px 26px;
  margin-bottom:16px;
  box-shadow:0 10px 30px rgba(23,32,51,.035);
}
.planx-eyebrow { color:var(--blue); font-size:11px; font-weight:800; letter-spacing:.1em; text-transform:uppercase; margin-bottom:7px; }
.planx-hero h1 { margin:0; font-size:30px; line-height:1.18; }
.planx-hero p { margin:8px 0 0; color:var(--muted); font-size:14px; }

.planx-card {
  background:#fff; border:1px solid var(--line); border-radius:15px;
  padding:17px 18px; min-height:112px;
  box-shadow:0 6px 20px rgba(23,32,51,.025);
}
.planx-card-title { font-size:12px; color:var(--muted); margin-bottom:8px; font-weight:700; }
.planx-card-value { font-size:22px; color:var(--text); font-weight:800; letter-spacing:-.03em; font-variant-numeric:tabular-nums; }
.planx-card-note { margin-top:7px; font-size:11px; color:#96a1b2; }
.planx-card-positive .planx-card-value { color:var(--green); }
.planx-card-negative .planx-card-value { color:var(--red); }

.planx-section-title {
  display:flex; justify-content:space-between; align-items:center;
  margin:22px 0 10px;
}
.planx-section-title h3 { margin:0; font-size:17px; }
.planx-section-title span { color:#96a1b2; font-size:11px; }

.planx-panel {
  background:#fff; border:1px solid var(--line); border-radius:15px;
  padding:18px; box-shadow:0 6px 20px rgba(23,32,51,.025);
}
.planx-panel-title { font-size:14px; font-weight:800; margin-bottom:12px; }

.planx-kpi-row {
  display:flex; align-items:baseline; gap:8px;
}
.planx-kpi { font-size:27px; font-weight:850; letter-spacing:-.04em; }
.planx-up { color:var(--green); font-weight:750; }
.planx-down { color:var(--red); font-weight:750; }

.planx-empty {
  background:#fff; border:1px dashed #cbd5e1; border-radius:14px;
  padding:20px; color:var(--muted);
}
.planx-source {
  display:inline-flex; align-items:center; gap:5px;
  color:#64748b; background:#f8fafc; border:1px solid #e2e8f0;
  padding:4px 8px; border-radius:999px; font-size:10px;
}
.planx-status-ok { color:#047857; background:#ecfdf5; border-color:#a7f3d0; }
.planx-status-wait { color:#92400e; background:#fffbeb; border-color:#fde68a; }
.planx-status-bad { color:#b91c1c; background:#fef2f2; border-color:#fecaca; }

hr { border-color:var(--line) !important; }
@media (max-width:900px) {
  .block-container { padding:1rem 1rem 3rem; }
  .planx-hero h1 { font-size:26px; }
  .planx-topbar { margin-bottom:12px; }
}
</style>
""",
        unsafe_allow_html=True,
    )


def brand():
    st.markdown(
        """
<div class="planx-brand">
  <div class="planx-brand-mark">↗</div>
  <div>
    <div class="planx-brand-title">StockDash</div>
    <div class="planx-brand-sub">Data to Insight.</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def topbar(name: str = "투자자"):
    st.markdown(
        f"""
<div class="planx-topbar">
  <div>
    <div class="planx-greeting">안녕하세요, <strong>{html.escape(name)}님</strong></div>
    <div class="planx-greeting">오늘도 현명한 투자를 준비합니다.</div>
  </div>
  <div class="planx-date">StockDash · 투자 대시보드</div>
</div>
""",
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, eyebrow: str = "PLANX INVESTMENT OS"):
    st.markdown(
        f"""
<div class="planx-hero">
  <div class="planx-eyebrow">{html.escape(eyebrow)}</div>
  <h1>{html.escape(title)}</h1>
  <p>{html.escape(subtitle)}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def card(title: str, value: str, note: str = "", status: str = "", tone: str = ""):
    status_html = f'<div class="planx-card-note">{html.escape(status)}</div>' if status else ""
    cls = f" planx-card-{tone}" if tone in {"positive", "negative"} else ""
    st.markdown(
        f"""
<div class="planx-card{cls}">
  <div class="planx-card-title">{html.escape(title)}</div>
  <div class="planx-card-value">{html.escape(value)}</div>
  <div class="planx-card-note">{html.escape(note)}</div>
  {status_html}
</div>
""",
        unsafe_allow_html=True,
    )


def section_title(title: str, note: str = ""):
    st.markdown(
        f"""
<div class="planx-section-title">
  <h3>{html.escape(title)}</h3>
  <span>{html.escape(note)}</span>
</div>
""",
        unsafe_allow_html=True,
    )


def panel_title(title: str):
    st.markdown(f'<div class="planx-panel-title">{html.escape(title)}</div>', unsafe_allow_html=True)


def empty_state(title: str, message: str):
    st.markdown(
        f"""
<div class="planx-empty">
  <strong style="color:#334155">{html.escape(title)}</strong><br>
  <span>{html.escape(message)}</span>
</div>
""",
        unsafe_allow_html=True,
    )


def source_badge(label: str, state: str = "wait"):
    cls = {"ok": "planx-status-ok", "bad": "planx-status-bad"}.get(state, "planx-status-wait")
    st.markdown(
        f'<span class="planx-source {cls}">{html.escape(label)}</span>',
        unsafe_allow_html=True,
    )
