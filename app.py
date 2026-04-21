import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from pathlib import Path
from supabase_config import supabase
from openai import OpenAI
import html
import json
import io
import uuid
import smtplib
import ssl
import base64
import urllib.parse
import time
import re
from email.message import EmailMessage
import streamlit.components.v1 as components

try:
    from PIL import Image as PILImage, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

st.set_page_config(
    page_title="Zentix",
    page_icon="icono_zentix_v2.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

DEFAULT_GASTOS = [
    "Comida", "Transporte", "Arriendo", "Servicios", "Salud",
    "Educación", "Compras", "Ocio", "Deudas", "Otros"
]

DEFAULT_INGRESOS = [
    "Salario", "Freelance", "Ventas", "Inversiones", "Regalos", "Otros"
]

CHART_COLORS = ["#22C55E", "#EF4444", "#3B82F6", "#8B5CF6", "#06B6D4", "#F59E0B"]

icono_path = Path("icono_zentix_v2.png")
if not icono_path.exists():
    icono_path = Path("icono_zentix.png")

avatar_path = Path("avatar_zentix.png")
zentix_floating_path = Path("zentix_ia_flotante.png")
if not zentix_floating_path.exists():
    zentix_floating_path = Path("a_2d_digital_illustration_features_zentix_ia_a_fu.png")


def _leer_timeout_ia_por_default():
    raw = os.getenv("ZENTIX_IA_TIMEOUT", "18")
    try:
        return float(str(raw).strip())
    except Exception:
        return 18.0


GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
ZENTIX_IA_TIMEOUT = _leer_timeout_ia_por_default()
GEMINI_MODEL_CANDIDATES = [
    model.strip() for model in [
        os.getenv("GEMINI_MODEL_PRIMARY", "gemini-2.5-flash"),
        os.getenv("GEMINI_MODEL_FALLBACK_1", "gemini-2.0-flash"),
        os.getenv("GEMINI_MODEL_FALLBACK_2", "gemini-1.5-flash"),
    ] if str(model).strip()
]
openai_client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    timeout=ZENTIX_IA_TIMEOUT,
    max_retries=0
) if GEMINI_API_KEY else None


def aplicar_estilo_zentix():
    st.markdown("""
    <style>
    :root {
        --app-bg: #F5F7FB;
        --app-bg-2: #EEF3FA;
        --surface: #FFFFFF;
        --surface-soft: #F8FAFC;
        --surface-alt: #F1F5F9;
        --line: rgba(15, 23, 42, 0.08);
        --line-strong: rgba(37, 99, 235, 0.18);
        --text: #0F172A;
        --muted: #64748B;
        --blue: #4F46E5;
        --blue-2: #2563EB;
        --cyan: #06B6D4;
        --purple: #7C3AED;
        --green: #22C55E;
        --red: #EF4444;
        --amber: #F59E0B;
        --pink: #EC4899;
        --shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
        --shadow-soft: 0 10px 24px rgba(15, 23, 42, 0.05);
        --radius-xl: 26px;
        --radius-lg: 22px;
        --radius-md: 18px;
    }

    html, body, [class*="css"]  {
        color: var(--text);
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(79,70,229,0.08), transparent 24%),
            radial-gradient(circle at top right, rgba(6,182,212,0.08), transparent 20%),
            linear-gradient(180deg, var(--app-bg) 0%, var(--app-bg-2) 100%);
    }

    [data-testid="stAppViewContainer"] {
        background: transparent;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 1.15rem;
        padding-right: 1.15rem;
        padding-left: 1.15rem;
        padding-bottom: 6rem;
    }

    header[data-testid="stHeader"] {
        background: rgba(255, 255, 255, 0.80);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(15,23,42,0.04);
    }

    [data-testid="stToolbar"],
    [data-testid="stDecoration"] {
        display: none !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(248,250,252,0.96));
        border-right: 1px solid rgba(15,23,42,0.06);
        box-shadow: inset -1px 0 0 rgba(255,255,255,0.8);
    }

    [data-testid="stSidebar"] * {
        color: var(--text);
    }

    [data-testid="stSidebarContent"] {
        padding-top: 1rem;
        padding-left: 0.6rem;
        padding-right: 0.6rem;
    }

    h1, h2, h3 {
        color: var(--text) !important;
        letter-spacing: -0.03em;
    }

    p, label, .stMarkdown, .stCaption, span, div {
        color: inherit;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.55rem;
        background: transparent;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }

    .stTabs [data-baseweb="tab"] {
        height: auto;
        padding: 0.72rem 1rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.84);
        border: 1px solid rgba(15,23,42,0.06);
        color: #334155;
        font-weight: 700;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(79,70,229,0.12), rgba(37,99,235,0.10));
        border-color: rgba(79,70,229,0.22);
        color: #312E81;
        box-shadow: 0 10px 24px rgba(79,70,229,0.08);
    }

    .stButton > button {
        width: 100%;
        min-height: 54px;
        border-radius: 18px;
        border: 1px solid rgba(15, 23, 42, 0.08);
        background: linear-gradient(180deg, rgba(255,255,255,1), rgba(248,250,252,1));
        color: #0F172A;
        font-weight: 800;
        font-size: 0.98rem;
        letter-spacing: 0.01em;
        padding: 0.82rem 1rem;
        box-shadow: 0 10px 20px rgba(15,23,42,0.05);
        transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, filter 0.18s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        border-color: rgba(79, 70, 229, 0.20);
        box-shadow: 0 16px 28px rgba(15,23,42,0.08);
    }

    .stButton > button[kind="primary"] {
        background:
            radial-gradient(circle at top left, rgba(255,255,255,0.22), transparent 30%),
            linear-gradient(135deg, #0F172A 0%, #172554 42%, #4F46E5 82%, #7C3AED 100%);
        border: none;
        color: #FFFFFF;
        box-shadow: 0 18px 32px rgba(15,23,42,0.24);
    }

    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 22px 38px rgba(15,23,42,0.28);
        filter: brightness(1.02);
    }

    .stButton > button[kind="secondary"] {
        background: linear-gradient(180deg, rgba(255,255,255,1), rgba(248,250,252,1));
        color: #334155;
        border: 1px solid rgba(148,163,184,0.22);
    }

    .stTextInput > div > div > input,
    .stNumberInput input,
    .stDateInput input,
    textarea,
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        background: rgba(255,255,255,0.96) !important;
        color: var(--text) !important;
        border: 1px solid rgba(148,163,184,0.20) !important;
        border-radius: 16px !important;
        min-height: 52px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.9), 0 6px 12px rgba(15,23,42,0.03);
    }

    .stTextInput > label, .stNumberInput > label, .stDateInput > label,
    .stSelectbox > label, .stRadio > label, .stMultiSelect > label {
        color: #334155 !important;
        font-weight: 700 !important;
    }

    .stRadio [role="radiogroup"] {
        gap: 0.6rem;
        flex-wrap: wrap;
    }

    .stRadio label {
        background: rgba(255,255,255,0.96);
        padding: 0.42rem 0.85rem;
        border-radius: 999px;
        border: 1px solid rgba(148,163,184,0.20);
        color: #334155 !important;
    }

    .stAlert {
        border-radius: 18px;
        border: 1px solid rgba(148,163,184,0.18);
    }

    .zentix-brand-shell {
        background: rgba(255,255,255,0.90);
        border: 1px solid rgba(15,23,42,0.06);
        border-radius: 24px;
        box-shadow: var(--shadow-soft);
        padding: 0.95rem 1.05rem;
        margin-bottom: 1rem;
    }

    .zentix-brand-title {
        font-size: 2.05rem;
        font-weight: 900;
        line-height: 1;
        margin: 0;
        letter-spacing: -0.04em;
        color: #0F172A;
    }

    .zentix-brand-sub {
        color: var(--muted);
        margin-top: 6px;
        font-size: 1rem;
    }

    .hero-card {
        background:
            radial-gradient(circle at top left, rgba(255,255,255,0.22), transparent 32%),
            radial-gradient(circle at bottom right, rgba(255,255,255,0.08), transparent 24%),
            linear-gradient(135deg, #0F172A 0%, #172554 42%, #4F46E5 82%, #7C3AED 100%);
        border: none;
        border-radius: 30px;
        padding: 1.3rem;
        box-shadow: 0 28px 50px rgba(15,23,42,0.24);
        margin-bottom: 1rem;
        color: #fff;
    }

    .hero-badge {
        display: inline-block;
        padding: 0.36rem 0.78rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.16);
        border: 1px solid rgba(255,255,255,0.18);
        color: #F8FAFC;
        font-size: 0.76rem;
        font-weight: 700;
        margin-bottom: 0.85rem;
    }

    .hero-title {
        font-size: 2rem;
        font-weight: 900;
        line-height: 1.02;
        margin: 0 0 0.35rem 0;
        color: #FFFFFF;
        letter-spacing: -0.04em;
    }

    .hero-subtitle {
        color: rgba(255,255,255,0.90);
        font-size: 1rem;
        line-height: 1.55;
        margin: 0;
    }

    .hero-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin-top: 1rem;
    }

    .hero-pill {
        display: inline-block;
        padding: 0.42rem 0.8rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.18);
        color: #FFFFFF;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .section-title {
        font-size: 1.18rem;
        font-weight: 900;
        color: var(--text);
        margin-top: 0.35rem;
        margin-bottom: 0.18rem;
        letter-spacing: -0.03em;
    }

    .section-caption,
    .tiny-muted,
    .kpi-foot,
    .chat-label,
    .chat-input-label,
    .quick-action-note,
    .sidebar-brand-sub,
    .sidebar-user-label,
    .movement-date,
    .movement-side-label,
    .spotlight-metric-label,
    .premium-list-copy,
    .assistant-mini,
    .feature-signal-sub,
    .spotlight-side-sub,
    .movement-meta,
    .report-image-note,
    .auth-step-copy,
    .launch-grid-copy,
    .sidebar-nav-note {
        color: var(--muted) !important;
    }

    .soft-card,
    .mini-soft-card,
    .premium-list-card,
    .feature-signal,
    .tutorial-card,
    .spotlight-shell,
    .spotlight-side-card,
    .movement-card,
    .launch-grid-card,
    .report-preview-shell,
    .report-image-shell,
    .movement-side-shell,
    .sticky-top-shell,
    .top-nav-premium,
    .legal-footer,
    .limit-card-premium,
    .auth-step-card,
    .sidebar-user-card,
    .movement-side-kpi,
    .spotlight-metric,
    .feature-chip,
    .tutorial-step-chip,
    .premium-list-badge,
    .hero-pill,
    .movement-chip {
        background: linear-gradient(180deg, rgba(255,255,255,1), rgba(248,250,252,1));
        border: 1px solid rgba(15,23,42,0.06);
        box-shadow: var(--shadow-soft);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }

    .soft-card,
    .mini-soft-card,
    .premium-list-card,
    .feature-signal,
    .tutorial-card,
    .spotlight-shell,
    .spotlight-side-card,
    .movement-card,
    .launch-grid-card,
    .report-preview-shell,
    .report-image-shell,
    .movement-side-shell,
    .sticky-top-shell,
    .top-nav-premium,
    .legal-footer,
    .limit-card-premium,
    .login-box,
    .auth-shell {
        border-radius: 24px;
        padding: 1rem 1.05rem;
    }

    .hero-card:hover,
    .soft-card:hover,
    .assistant-card:hover,
    .mini-soft-card:hover,
    .premium-list-card:hover,
    .feature-signal:hover,
    .tutorial-card:hover,
    .spotlight-shell:hover,
    .spotlight-side-card:hover,
    .kpi-card:hover,
    .movement-card:hover,
    .launch-grid-card:hover,
    .report-preview-shell:hover,
    .report-image-shell:hover,
    .auth-shell:hover,
    .movement-side-shell:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow);
        border-color: rgba(79,70,229,0.14);
    }

    .assistant-card,
    .auth-shell,
    .login-box,
    .empty-card,
    .premium-floating-guide {
        background:
            radial-gradient(circle at top left, rgba(255,255,255,0.18), transparent 30%),
            linear-gradient(135deg, #172554 0%, #1D4ED8 52%, #4F46E5 100%);
        border: none;
        color: #FFFFFF;
        box-shadow: 0 24px 46px rgba(37,99,235,0.18);
    }

    .assistant-title,
    .premium-floating-guide-title,
    .auth-step-title {
        color: #FFFFFF !important;
    }

    .assistant-text,
    .premium-floating-guide-copy,
    .chat-bubble-user {
        color: rgba(255,255,255,0.94) !important;
    }

    .chat-bubble-ai {
        background: rgba(255,255,255,0.16);
        border: 1px solid rgba(255,255,255,0.18);
        color: #FFFFFF;
        border-radius: 16px;
        padding: 0.8rem 0.9rem;
        margin-bottom: 0.55rem;
        line-height: 1.5;
        font-size: 0.92rem;
    }

    .chat-bubble-user {
        background: rgba(15,23,42,0.14);
        border: 1px solid rgba(255,255,255,0.16);
        border-radius: 16px;
        padding: 0.8rem 0.9rem;
        margin-bottom: 0.55rem;
        line-height: 1.5;
        font-size: 0.92rem;
    }

    .kpi-card {
        border-radius: 22px;
        padding: 1rem;
        min-height: 124px;
        border: 1px solid rgba(15,23,42,0.06);
        box-shadow: var(--shadow-soft);
    }

    .kpi-income { background: linear-gradient(180deg, #ECFDF5, #F0FDF4); border-color: rgba(34,197,94,0.18); }
    .kpi-expense { background: linear-gradient(180deg, #FEF2F2, #FFF1F2); border-color: rgba(239,68,68,0.18); }
    .kpi-balance { background: linear-gradient(180deg, #EFF6FF, #EEF2FF); border-color: rgba(37,99,235,0.18); }
    .kpi-saving { background: linear-gradient(180deg, #F5F3FF, #FAF5FF); border-color: rgba(124,58,237,0.18); }
    .kpi-debt { background: linear-gradient(180deg, #EEF2FF, #EFF6FF); border-color: rgba(59,130,246,0.18); }
    .kpi-pay { background: linear-gradient(180deg, #FFFBEB, #FEF3C7); border-color: rgba(245,158,11,0.18); }
    .kpi-receivable { background: linear-gradient(180deg, #F5F3FF, #F3E8FF); border-color: rgba(168,85,247,0.18); }
    .kpi-collected { background: linear-gradient(180deg, #ECFEFF, #CFFAFE); border-color: rgba(6,182,212,0.18); }

    .kpi-label { font-size: 0.82rem; color: #475569; margin-bottom: 0.55rem; font-weight: 700; }
    .kpi-value { font-size: 1.72rem; font-weight: 900; color: #0F172A; line-height: 1.05; margin-bottom: 0.25rem; letter-spacing: -0.04em; }
    .kpi-foot { font-size: 0.82rem; }

    .pill-ingreso, .pill-gasto, .pill-debt, .pill-pay {
        display: inline-block;
        padding: 0.42rem 0.82rem;
        border-radius: 999px;
        font-weight: 800;
        margin-bottom: 0.8rem;
    }
    .pill-ingreso { background: #DCFCE7; border: 1px solid #86EFAC; color: #166534; }
    .pill-gasto { background: #FEE2E2; border: 1px solid #FCA5A5; color: #B91C1C; }
    .pill-debt { background: #DBEAFE; border: 1px solid #93C5FD; color: #1D4ED8; }
    .pill-pay { background: #FEF3C7; border: 1px solid #FCD34D; color: #B45309; }

    .movement-chip { color: #334155; }
    .movement-chip-income { background: #DCFCE7; border-color: #86EFAC; color: #166534; }
    .movement-chip-expense { background: #FEE2E2; border-color: #FCA5A5; color: #B91C1C; }
    .movement-chip-debt { background: #DBEAFE; border-color: #93C5FD; color: #1D4ED8; }
    .movement-chip-pay { background: #FEF3C7; border-color: #FCD34D; color: #B45309; }
    .movement-chip-info { background: #E0F2FE; border-color: #7DD3FC; color: #0C4A6E; }
    .movement-chip-recurrent { background: #F5F3FF; border-color: #C4B5FD; color: #6D28D9; }
    .movement-chip-alert { background: #FFF1F2; border-color: #FDA4AF; color: #BE123C; }

    .spotlight-badge,
    .tutorial-badge,
    .premium-list-badge {
        background: rgba(79,70,229,0.10);
        border: 1px solid rgba(79,70,229,0.14);
        color: #4338CA;
    }

    .spotlight-title,
    .tutorial-title,
    .premium-list-title,
    .feature-signal-title,
    .spotlight-side-title,
    .movement-title,
    .movement-side-value,
    .spotlight-metric-value,
    .launch-grid-title,
    .sidebar-brand-title,
    .sidebar-user-name {
        color: #0F172A !important;
    }

    .premium-list-card,
    .premium-list-card *,
    .premium-list-head,
    .premium-list-title,
    .premium-list-badge,
    .premium-list-copy,
    .spotlight-list,
    .spotlight-list li,
    .spotlight-item,
    .spotlight-item *,
    .report-preview-shell,
    .report-preview-shell *,
    .spotlight-shell,
    .spotlight-shell * {
        color: #0F172A !important;
        text-shadow: none !important;
    }

    .premium-list-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FBFF 100%) !important;
        border: 1px solid rgba(148,163,184,0.20) !important;
        box-shadow: 0 14px 28px rgba(15,23,42,0.05) !important;
    }

    .premium-list-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        margin-bottom: 0.42rem;
    }

    .premium-list-title {
        color: #0F172A !important;
        font-weight: 900 !important;
    }

    .premium-list-badge {
        color: #4338CA !important;
        background: #EEF2FF !important;
        border: 1px solid #C7D2FE !important;
        box-shadow: none !important;
    }

    .premium-list-copy {
        color: #64748B !important;
        font-weight: 600 !important;
        margin-bottom: 0.62rem;
    }

    .spotlight-list {
        margin: 0.2rem 0 0 0 !important;
        padding-left: 1.15rem !important;
        color: #0F172A !important;
    }

    .spotlight-list li,
    .spotlight-item {
        color: #0F172A !important;
        font-weight: 600 !important;
        line-height: 1.7 !important;
        margin-bottom: 0.42rem !important;
        opacity: 1 !important;
    }

    .spotlight-list li::marker {
        color: #334155 !important;
    }

    .report-preview-shell,
    .spotlight-shell,
    .soft-card,
    .mini-soft-card {
        color: #0F172A !important;
    }

    .report-preview-shell .section-caption,
    .spotlight-shell .section-caption,
    .soft-card .section-caption,
    .mini-soft-card .section-caption {
        color: #64748B !important;
    }

    .sidebar-brand-title { font-size: 1.1rem; font-weight: 900; line-height: 1.1; }
    .sidebar-user-card { border-radius: 20px; }

    .empty-card {
        border-radius: 24px;
        padding: 1.15rem;
        text-align: center;
        color: rgba(255,255,255,0.92);
    }

    .top-nav-premium {
        position: sticky;
        top: 0.55rem;
        z-index: 40;
        padding: 0.95rem 1rem;
        margin-bottom: 1rem;
    }

    .top-nav-premium-title {
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #6366F1;
        font-weight: 900;
        margin-bottom: 0.75rem;
    }

    .quick-tile {
        border-radius: 22px;
        padding: 1rem;
        min-height: 120px;
        background: linear-gradient(180deg, rgba(255,255,255,1), rgba(248,250,252,1));
        border: 1px solid rgba(15,23,42,0.06);
        box-shadow: var(--shadow-soft);
        margin-bottom: 0.55rem;
    }

    .quick-tile-icon {
        width: 42px; height: 42px; border-radius: 14px; display:flex; align-items:center; justify-content:center;
        font-size: 1.15rem; font-weight: 800; margin-bottom: 0.8rem;
        background: linear-gradient(135deg, rgba(79,70,229,0.14), rgba(37,99,235,0.10));
        color: #4F46E5;
    }

    .quick-tile-title { color:#0F172A; font-weight:900; font-size:1rem; margin-bottom:0.18rem; }
    .quick-tile-copy { color:#64748B; font-size:0.84rem; line-height:1.55; }

    .activity-feed-item {
        display:flex; justify-content:space-between; gap:0.8rem; align-items:flex-start;
        padding:0.82rem 0; border-bottom:1px solid rgba(15,23,42,0.06);
    }
    .activity-feed-item:last-child { border-bottom:none; }
    .activity-feed-left { display:flex; gap:0.75rem; align-items:flex-start; }
    .activity-feed-bullet {
        width:38px; height:38px; border-radius:999px; display:flex; align-items:center; justify-content:center;
        font-weight:800; font-size:0.95rem; color:#fff;
        background: linear-gradient(135deg, #172554 0%, #312E81 100%);
        flex: 0 0 38px;
    }
    .activity-feed-title { font-weight:800; color:#0F172A; line-height:1.3; }
    .activity-feed-sub { color:#64748B; font-size:0.82rem; margin-top:0.12rem; }
    .activity-feed-amount { font-weight:900; white-space:nowrap; }
    .amount-income { color:#16A34A; }
    .amount-expense { color:#DC2626; }
    .amount-debt { color:#2563EB; }
    .amount-pay { color:#B45309; }

    .premium-floating-guide {
        position: fixed;
        right: 1rem;
        bottom: 1rem;
        z-index: 9998;
        width: min(360px, calc(100vw - 2rem));
        border-radius: 24px;
        padding: 1rem;
    }

    .assistant-mini, .premium-floating-guide .tiny-muted { color: rgba(255,255,255,0.82) !important; }

    .legal-footer a, a { color: #4F46E5; }

    .metric-income { color: #16A34A !important; }
    .metric-expense { color: #DC2626 !important; }
    .metric-debt { color: #2563EB !important; }
    .metric-pay { color: #B45309 !important; }

    div[data-testid="stProgressBar"] > div > div {
        background: linear-gradient(90deg, #4F46E5, #06B6D4);
    }

    @media (max-width: 900px) {
        .block-container { padding-left: 0.85rem; padding-right: 0.85rem; padding-bottom: 7rem; }
        .hero-title { font-size: 1.78rem; }
        .premium-floating-guide { width: calc(100vw - 1.5rem); right: 0.75rem; bottom: 0.75rem; }
    }

    /* ===== V2 · color, navegación y selector más vivos ===== */
    .soft-card,
    .mini-soft-card,
    .premium-list-card,
    .feature-signal,
    .tutorial-card,
    .spotlight-shell,
    .spotlight-side-card,
    .movement-card,
    .launch-grid-card,
    .report-preview-shell,
    .report-image-shell,
    .movement-side-shell,
    .sticky-top-shell,
    .top-nav-premium,
    .legal-footer,
    .limit-card-premium,
    .auth-step-card,
    .sidebar-user-card,
    .movement-side-kpi,
    .spotlight-metric {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FBFF 100%) !important;
        border: 1px solid rgba(99, 102, 241, 0.12) !important;
        box-shadow: 0 14px 28px rgba(79,70,229,0.06) !important;
    }

    .spotlight-side-card {
        background: linear-gradient(180deg, #EEF4FF 0%, #E0E7FF 100%) !important;
        border-color: rgba(59,130,246,0.16) !important;
    }

    .mini-soft-card {
        background: linear-gradient(180deg, #F5F3FF 0%, #EEF2FF 100%) !important;
    }

    .sidebar-section-title {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #6366F1;
        font-weight: 900;
        margin: 1rem 0 0.7rem 0.2rem;
    }

    [data-testid="stSidebar"] .stButton > button {
        min-height: 46px;
        border-radius: 16px;
        justify-content: flex-start;
        text-align: left;
        padding: 0.76rem 0.95rem;
        font-size: 0.98rem;
        font-weight: 800;
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        color: #0F172A;
        border: 1px solid rgba(148,163,184,0.20);
        box-shadow: 0 8px 16px rgba(15,23,42,0.04);
    }

    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0F172A 0%, #172554 42%, #4F46E5 82%, #7C3AED 100%);
        color: #FFFFFF;
        border: none;
        box-shadow: 0 14px 26px rgba(15,23,42,0.24);
    }

    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover,
    .top-nav-premium .stButton > button[kind="secondary"]:hover {
        border-color: rgba(79,70,229,0.22);
        box-shadow: 0 14px 24px rgba(79,70,229,0.08);
        background: linear-gradient(180deg, #FFFFFF 0%, #EEF2FF 100%);
    }

    .top-nav-premium .stButton > button {
        min-height: 44px;
        border-radius: 999px;
        font-size: 0.92rem;
    }

    .auth-visible-options {
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
        margin-bottom: 1rem;
    }

    .auth-visible-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.55rem 0.9rem;
        border-radius: 999px;
        font-weight: 800;
        font-size: 0.86rem;
        border: 1px solid transparent;
    }

    .auth-visible-chip.is-register { background: #E0E7FF; color: #172554; border-color: #A5B4FC; }
    .auth-visible-chip.is-login { background: #DBEAFE; color: #172554; border-color: #93C5FD; }
    .auth-visible-chip.is-reset { background: #EDE9FE; color: #312E81; border-color: #C4B5FD; }

    .stTabs [data-baseweb="tab-list"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.85), rgba(241,245,249,0.9));
        border: 1px solid rgba(99,102,241,0.10);
        border-radius: 22px;
        padding: 0.45rem;
    }

    .stTabs [data-baseweb="tab"] {
        font-weight: 800;
        color: #334155;
        background: transparent;
        border: none;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0F172A 0%, #172554 42%, #4F46E5 82%, #7C3AED 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 12px 24px rgba(15,23,42,0.20);
    }

    .stTabs [data-baseweb="tab"]:nth-child(4) {
        position: relative;
        border: 1px solid rgba(79,70,229,0.18) !important;
        background: linear-gradient(180deg, #EEF2FF 0%, #FFFFFF 100%) !important;
        color: #312E81 !important;
        box-shadow: 0 10px 22px rgba(79,70,229,0.10);
        overflow: hidden;
    }

    .stTabs [data-baseweb="tab"]:nth-child(4)::after {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: 999px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent);
        transform: translateX(-120%);
        animation: zentixTabGlow 3.4s linear infinite;
        pointer-events: none;
    }

    .stTabs [data-baseweb="tab"]:nth-child(4)[aria-selected="true"] {
        background: linear-gradient(135deg, #0F172A 0%, #172554 42%, #4F46E5 82%, #7C3AED 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 16px 30px rgba(79,70,229,0.18), 0 0 0 1px rgba(255,255,255,0.08) inset;
    }

    @keyframes zentixTabGlow {
        0% { transform: translateX(-120%); }
        100% { transform: translateX(120%); }
    }

    .stRadio [role="radiogroup"] {
        display: flex;
        gap: 0.7rem;
        flex-wrap: wrap;
        align-items: stretch;
    }

    .stRadio [role="radiogroup"] > label {
        position: relative;
        margin: 0 !important;
        padding: 0.82rem 1rem 0.82rem 2.1rem !important;
        border-radius: 999px !important;
        border: 1px solid rgba(148,163,184,0.24) !important;
        box-shadow: 0 8px 18px rgba(15,23,42,0.05);
        min-height: 50px;
        display: flex !important;
        align-items: center !important;
        background: #FFFFFF !important;
    }

    .stRadio [role="radiogroup"] > label p,
    .stRadio [role="radiogroup"] > label span {
        color: #0F172A !important;
        font-weight: 800 !important;
        opacity: 1 !important;
    }

    .stRadio [role="radiogroup"] > label::before {
        content: "";
        position: absolute;
        left: 0.95rem;
        top: 50%;
        transform: translateY(-50%);
        width: 12px;
        height: 12px;
        border-radius: 999px;
        background: #CBD5E1;
        box-shadow: 0 0 0 4px rgba(255,255,255,0.9);
    }

    .stRadio [role="radiogroup"] > label:nth-child(1) { background: linear-gradient(180deg, #ECFDF5, #F0FDF4) !important; border-color: #86EFAC !important; }
    .stRadio [role="radiogroup"] > label:nth-child(1)::before { background: #22C55E; }
    .stRadio [role="radiogroup"] > label:nth-child(2) { background: linear-gradient(180deg, #FEF2F2, #FFF1F2) !important; border-color: #FCA5A5 !important; }
    .stRadio [role="radiogroup"] > label:nth-child(2)::before { background: #EF4444; }
    .stRadio [role="radiogroup"] > label:nth-child(3) { background: linear-gradient(180deg, #EFF6FF, #EEF2FF) !important; border-color: #93C5FD !important; }
    .stRadio [role="radiogroup"] > label:nth-child(3)::before { background: #3B82F6; }
    .stRadio [role="radiogroup"] > label:nth-child(4) { background: linear-gradient(180deg, #FFFBEB, #FEF3C7) !important; border-color: #FCD34D !important; }
    .stRadio [role="radiogroup"] > label:nth-child(4)::before { background: #F59E0B; }
    .stRadio [role="radiogroup"] > label:nth-child(5) { background: linear-gradient(180deg, #F5F3FF, #F3E8FF) !important; border-color: #C4B5FD !important; }
    .stRadio [role="radiogroup"] > label:nth-child(5)::before { background: #8B5CF6; }
    .stRadio [role="radiogroup"] > label:nth-child(6) { background: linear-gradient(180deg, #ECFEFF, #CFFAFE) !important; border-color: #67E8F9 !important; }
    .stRadio [role="radiogroup"] > label:nth-child(6)::before { background: #06B6D4; }

    .stRadio [role="radiogroup"] > label:has(input:checked) {
        box-shadow: 0 16px 28px rgba(79,70,229,0.12) !important;
        transform: translateY(-1px);
        border-width: 1.5px !important;
    }

    .stRadio [role="radiogroup"] > label:has(input:checked) p,
    .stRadio [role="radiogroup"] > label:has(input:checked) span {
        color: #0F172A !important;
    }

    .register-chip-note {
        display: inline-block;
        margin-top: 0.25rem;
        margin-bottom: 0.8rem;
        padding: 0.5rem 0.85rem;
        border-radius: 999px;
        font-size: 0.84rem;
        font-weight: 800;
        color: #1E293B;
        background: linear-gradient(180deg, #FFFFFF, #F8FAFC);
        border: 1px solid rgba(148,163,184,0.22);
        box-shadow: 0 8px 18px rgba(15,23,42,0.05);
    }


    /* ===== V3 · contraste, sidebar desplegable y pastel charts ===== */
    [data-testid="collapsedControl"] {
        display: block !important;
        position: fixed !important;
        top: 0.85rem;
        left: 0.85rem;
        z-index: 1001 !important;
        background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,250,252,0.98));
        border: 1px solid rgba(99,102,241,0.16);
        border-radius: 16px;
        box-shadow: 0 14px 28px rgba(79,70,229,0.10);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
    }

    [data-testid="collapsedControl"] button {
        border-radius: 14px !important;
        min-height: 42px !important;
        min-width: 42px !important;
        background: transparent !important;
        color: #4338CA !important;
        border: none !important;
        box-shadow: none !important;
    }

    [data-testid="collapsedControl"] svg {
        fill: #4338CA !important;
        color: #4338CA !important;
    }

    .premium-floating-guide {
        background:
            radial-gradient(circle at top left, rgba(255,255,255,0.20), transparent 28%),
            linear-gradient(135deg, #1E1B4B 0%, #312E81 42%, #4F46E5 100%) !important;
        border: 1px solid rgba(191,219,254,0.20) !important;
        box-shadow: 0 26px 50px rgba(49,46,129,0.24) !important;
        color: #FFFFFF !important;
    }

    .premium-floating-guide-title,
    .premium-floating-guide-copy,
    .premium-floating-guide .tiny-muted,
    .premium-floating-guide .assistant-mini,
    .premium-floating-guide .section-caption,
    .premium-floating-guide .sidebar-nav-note {
        color: #FFFFFF !important;
    }

    .premium-floating-guide .tiny-muted {
        opacity: 0.84;
    }

    .spotlight-side-card,
    .movement-side-shell,
    .mini-soft-card,
    .feature-signal,
    .launch-grid-card {
        background: linear-gradient(180deg, #F7FAFF 0%, #EEF4FF 100%) !important;
        border-color: rgba(59,130,246,0.16) !important;
        box-shadow: 0 16px 30px rgba(37,99,235,0.06) !important;
    }

    .spotlight-side-card .spotlight-side-title,
    .spotlight-side-card .spotlight-side-sub,
    .spotlight-side-card .tiny-muted,
    .movement-side-shell .movement-side-value,
    .movement-side-shell .movement-side-label,
    .movement-side-shell .tiny-muted,
    .mini-soft-card .tiny-muted,
    .feature-signal .feature-signal-title,
    .feature-signal .feature-signal-sub,
    .launch-grid-card .launch-grid-title,
    .launch-grid-card .launch-grid-copy {
        color: #0F172A !important;
    }

    .sidebar-user-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFF 100%) !important;
        border: 1px solid rgba(99,102,241,0.12) !important;
        box-shadow: 0 12px 24px rgba(79,70,229,0.06) !important;
    }

    [data-testid="stSidebar"] .stButton > button {
        min-height: 48px !important;
        border-radius: 18px !important;
        font-weight: 800 !important;
        letter-spacing: 0.01em;
    }

    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0F172A 0%, #172554 42%, #4F46E5 82%, #7C3AED 100%) !important;
        box-shadow: 0 16px 30px rgba(15,23,42,0.22) !important;
    }

    .home-pie-card {
        border-radius: 24px;
        padding: 1rem 1.05rem;
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FBFF 100%);
        border: 1px solid rgba(148,163,184,0.16);
        box-shadow: 0 14px 26px rgba(15,23,42,0.05);
        margin-bottom: 0.9rem;
    }

    .home-pie-title {
        font-size: 1rem;
        font-weight: 900;
        color: #0F172A;
        margin-bottom: 0.18rem;
    }

    .home-pie-sub {
        font-size: 0.85rem;
        color: #64748B;
        margin-bottom: 0.55rem;
    }


    /* ===== V4 · drawer lateral + contraste definitivo ===== */
    [data-testid="collapsedControl"] { display: none !important; }

    .hero-pill {
        background: rgba(255,255,255,0.18) !important;
        border: 1px solid rgba(255,255,255,0.28) !important;
        color: #FFFFFF !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.18);
        text-shadow: 0 1px 1px rgba(0,0,0,0.16);
    }
    .hero-pill * { color: #FFFFFF !important; }

    .soft-card,
    .mini-soft-card,
    .spotlight-side-card,
    .movement-side-shell,
    .feature-signal,
    .launch-grid-card,
    .report-preview-shell,
    .report-image-shell,
    .sidebar-user-card,
    .limit-card-premium,
    .sticky-top-shell,
    .top-nav-premium,
    .legal-footer,
    .home-pie-card,
    .stExpander {
        background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(247,250,255,0.98)) !important;
        border: 1px solid rgba(148,163,184,0.18) !important;
        box-shadow: 0 14px 28px rgba(15,23,42,0.05) !important;
    }

    .soft-card *,
    .mini-soft-card *,
    .spotlight-side-card *,
    .movement-side-shell *,
    .feature-signal *,
    .launch-grid-card *,
    .report-preview-shell *,
    .report-image-shell *,
    .sidebar-user-card *,
    .limit-card-premium *,
    .sticky-top-shell *,
    .top-nav-premium *,
    .legal-footer *,
    .home-pie-card * {
        color: #0F172A !important;
    }

    .soft-card .section-caption,
    .soft-card .tiny-muted,
    .mini-soft-card .tiny-muted,
    .spotlight-side-card .section-caption,
    .spotlight-side-card .tiny-muted,
    .movement-side-shell .tiny-muted,
    .feature-signal .feature-signal-sub,
    .launch-grid-card .launch-grid-copy,
    .report-preview-shell .section-caption,
    .report-image-shell .report-image-note,
    .sidebar-user-card .sidebar-user-label,
    .sidebar-user-card .tiny-muted,
    .top-nav-premium .tiny-muted,
    .legal-footer,
    .legal-footer a,
    .home-pie-sub {
        color: #64748B !important;
    }

    .soft-card .form-preview-value,
    .mini-soft-card .form-preview-value,
    .spotlight-side-card .form-preview-value,
    .movement-side-shell .form-preview-value,
    .soft-card .kpi-value,
    .mini-soft-card .kpi-value,
    .soft-card .kpi-label,
    .mini-soft-card .kpi-label {
        color: #0F172A !important;
    }

    .soft-card .pill-ingreso { color: #166534 !important; background: #DCFCE7 !important; border-color: #86EFAC !important; }
    .soft-card .pill-gasto { color: #B91C1C !important; background: #FEE2E2 !important; border-color: #FCA5A5 !important; }
    .soft-card .pill-debt { color: #1D4ED8 !important; background: #DBEAFE !important; border-color: #93C5FD !important; }
    .soft-card .pill-pay { color: #B45309 !important; background: #FEF3C7 !important; border-color: #FCD34D !important; }

    .movement-chip-income { color: #166534 !important; }
    .movement-chip-expense { color: #B91C1C !important; }
    .movement-chip-debt { color: #1D4ED8 !important; }
    .movement-chip-pay { color: #B45309 !important; }
    .movement-chip-info { color: #0C4A6E !important; }
    .movement-chip-recurrent { color: #6D28D9 !important; }
    .movement-chip-alert { color: #BE123C !important; }

    div[data-testid="stExpander"] {
        border-radius: 18px !important;
        overflow: hidden !important;
        background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(247,250,255,0.98)) !important;
        border: 1px solid rgba(148,163,184,0.18) !important;
        box-shadow: 0 12px 24px rgba(15,23,42,0.04) !important;
    }

    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] summary *,
    div[data-testid="stExpander"] label,
    div[data-testid="stExpander"] p,
    div[data-testid="stExpander"] span,
    div[data-testid="stExpander"] div {
        color: #0F172A !important;
    }

    div[data-testid="stExpander"] .tiny-muted,
    div[data-testid="stExpander"] .section-caption,
    div[data-testid="stExpander"] .launch-grid-copy,
    div[data-testid="stExpander"] .sidebar-user-label {
        color: #64748B !important;
    }

    .premium-floating-guide {
        background:
            radial-gradient(circle at top left, rgba(255,255,255,0.14), transparent 28%),
            linear-gradient(135deg, #111827 0%, #1E293B 58%, #312E81 100%) !important;
        border: 1px solid rgba(129,140,248,0.24) !important;
        box-shadow: 0 24px 48px rgba(15,23,42,0.22) !important;
    }

    .premium-floating-guide *,
    .premium-floating-guide-title,
    .premium-floating-guide-copy,
    .premium-floating-guide .tiny-muted,
    .premium-floating-guide .assistant-mini {
        color: #F8FAFC !important;
    }

    .premium-floating-guide .tiny-muted {
        opacity: 0.82;
    }

    .sidebar-brand-title,
    .sidebar-user-name,
    .top-nav-premium-title {
        color: #0F172A !important;
    }

    [data-testid="stSidebar"] {
        box-shadow: inset -1px 0 0 rgba(255,255,255,0.8), 10px 0 28px rgba(15,23,42,0.04) !important;
    }

    @media (max-width: 900px) {
        .premium-floating-guide {
            width: min(360px, calc(100vw - 1rem)) !important;
            right: 0.5rem !important;
            bottom: 0.5rem !important;
        }
    }


    /* ===== V5 · contraste explícito IA ===== */
    .assistant-card {
        background:
            radial-gradient(circle at top left, rgba(255,255,255,0.10), transparent 28%),
            linear-gradient(135deg, #0F172A 0%, #1E293B 56%, #312E81 100%) !important;
        border: 1px solid rgba(129,140,248,0.18) !important;
        box-shadow: 0 24px 48px rgba(15,23,42,0.18) !important;
    }
    .assistant-card,
    .assistant-card *,
    .assistant-card .assistant-title,
    .assistant-card .assistant-text,
    .assistant-card .assistant-mini,
    .assistant-card .quick-action-note,
    .assistant-card .chat-label,
    .assistant-card .chat-input-label,
    .assistant-card label,
    .assistant-card p,
    .assistant-card span,
    .assistant-card div {
        color: #F8FAFC !important;
    }
    .assistant-card .assistant-mini,
    .assistant-card .quick-action-note {
        color: rgba(248,250,252,0.88) !important;
    }
    .assistant-card .stTextInput > div > div > input {
        background: rgba(255,255,255,0.96) !important;
        color: #0F172A !important;
        border: 1px solid rgba(255,255,255,0.18) !important;
    }
    .assistant-card .stButton > button[kind="secondary"] {
        background: rgba(255,255,255,0.12) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255,255,255,0.18) !important;
    }
    .premium-floating-guide {
        background:
            radial-gradient(circle at top left, rgba(255,255,255,0.12), transparent 28%),
            linear-gradient(135deg, #0B1220 0%, #172554 54%, #312E81 100%) !important;
        border: 1px solid rgba(129,140,248,0.22) !important;
        box-shadow: 0 24px 48px rgba(15,23,42,0.22) !important;
    }
    .premium-floating-guide,
    .premium-floating-guide *,
    .premium-floating-guide-title,
    .premium-floating-guide-copy,
    .premium-floating-guide .tiny-muted,
    .premium-floating-guide .assistant-mini,
    .premium-floating-guide p,
    .premium-floating-guide span,
    .premium-floating-guide div {
        color: #F8FAFC !important;
    }
    .premium-floating-guide .tiny-muted {
        color: rgba(248,250,252,0.82) !important;
    }



    /* ===== V6 · contraste final avatar + gráficas ===== */
    .assistant-card,
    .assistant-card *,
    .assistant-card .assistant-title,
    .assistant-card .assistant-text,
    .assistant-card .assistant-mini,
    .assistant-card .chat-label,
    .assistant-card .chat-input-label,
    .assistant-card label,
    .assistant-card p,
    .assistant-card span,
    .assistant-card div {
        color: #0F172A !important;
        text-shadow: none !important;
    }

    .assistant-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%) !important;
        border: 1px solid rgba(148,163,184,0.24) !important;
        box-shadow: 0 14px 28px rgba(15,23,42,0.06) !important;
    }

    .assistant-card .assistant-title,
    .assistant-card .assistant-text {
        color: #0F172A !important;
    }

    .assistant-card .assistant-mini,
    .assistant-card .chat-label,
    .assistant-card .chat-input-label {
        color: #475569 !important;
    }

    .assistant-card .chat-bubble-ai {
        background: #FFFFFF !important;
        border: 1px solid rgba(148,163,184,0.22) !important;
        color: #0F172A !important;
        box-shadow: 0 8px 18px rgba(15,23,42,0.04) !important;
    }

    .assistant-card .chat-bubble-user {
        background: #EEF2FF !important;
        border: 1px solid rgba(129,140,248,0.18) !important;
        color: #0F172A !important;
        box-shadow: 0 8px 18px rgba(79,70,229,0.05) !important;
    }

    .assistant-card .chat-bubble-ai strong,
    .assistant-card .chat-bubble-user strong,
    .assistant-card .chat-bubble-ai br,
    .assistant-card .chat-bubble-user br {
        color: #0F172A !important;
    }

    .assistant-card .stTextInput > div > div > input,
    .assistant-card textarea,
    .assistant-card [data-baseweb="input"],
    .assistant-card [data-baseweb="base-input"] {
        background: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid rgba(148,163,184,0.24) !important;
    }

    .assistant-card .stButton > button {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%) !important;
        color: #0F172A !important;
        border: 1px solid rgba(148,163,184,0.22) !important;
    }

    .assistant-card .stButton > button[kind="primary"] {
        color: #FFFFFF !important;
    }

    .assistant-card img {
        filter: none !important;
        opacity: 1 !important;
    }

    .js-plotly-plot,
    .plotly-graph-div {
        background: #0F172A !important;
        border-radius: 18px !important;
        padding: 8px !important;
    }

    .js-plotly-plot .plotly text,
    .js-plotly-plot .plotly .gtitle,
    .js-plotly-plot .plotly .xtitle,
    .js-plotly-plot .plotly .ytitle,
    .js-plotly-plot .plotly .legendtext,
    .js-plotly-plot .plotly .annotation-text {
        fill: #F8FAFC !important;
        color: #F8FAFC !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)


def money(value):
    return f"${float(value):,.0f}"

TIPO_DISPLAY = {
    "Ingreso (Deuda)": "Crédito solicitado",
    "Pago de deuda": "Pago a crédito",
    "Cuenta por cobrar": "Prestaste Dinero",
    "Cobro cuenta por cobrar": "Ya me pagaron",
}

def tipo_display(tipo):
    return TIPO_DISPLAY.get(str(tipo or "").strip(), str(tipo or ""))


def limpiar_formulario_registrar():
    defaults = {
        "registrar_fecha_mov": date.today(),
        "registrar_descripcion": "",
        "registrar_recurrente": False,
        "registrar_frecuencia": "Semanal",
        "registrar_proxima_fecha": date.today() + timedelta(days=7),
        "registrar_fin_toggle": False,
        "registrar_fecha_fin": date.today() + timedelta(days=7),
        "registrar_categoria_ingreso": None,
        "registrar_monto_ingreso": 0.0,
        "registrar_categoria_gasto": None,
        "registrar_monto_gasto": 0.0,
        "registrar_emocion": "",
        "registrar_deuda_nombre": "",
        "registrar_prestamista": "",
        "registrar_monto_deuda": 0.0,
        "registrar_deuda_limite_toggle": False,
        "registrar_deuda_limite": date.today() + timedelta(days=30),
        "registrar_pago_deuda_select": None,
        "registrar_pago_deuda_monto": 0.0,
        "registrar_cxc_nombre": "",
        "registrar_cxc_cliente": "",
        "registrar_cxc_monto": 0.0,
        "registrar_cxc_limite_toggle": False,
        "registrar_cxc_limite": date.today() + timedelta(days=30),
        "registrar_cobro_cxc_select": None,
        "registrar_cobro_cxc_monto": 0.0,
    }

    for key, value in defaults.items():
        st.session_state[key] = value


def ejecutar_reset_registrar_si_aplica():
    if st.session_state.get("reset_registrar_form", False):
        limpiar_formulario_registrar()
        st.session_state["reset_registrar_form"] = False


def aplicar_estilo_plotly(fig, height=360):
    titulo_actual = None
    try:
        titulo_actual = fig.layout.title.text
    except Exception:
        titulo_actual = None

    if titulo_actual in {None, "undefined"}:
        titulo_actual = ""

    fig.update_layout(
        paper_bgcolor="#0F172A",
        plot_bgcolor="#111827",
        font_color="#F8FAFC",
        title_text=titulo_actual,
        title_font_size=20,
        title_font_color="#F8FAFC",
        title_x=0.03,
        margin=dict(l=20, r=20, t=70, b=45),
        height=height,
        legend_title_text="",
        legend=dict(
            bgcolor="rgba(15,23,42,0)",
            font=dict(color="#F8FAFC")
        )
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.12)",
        zeroline=False,
        linecolor="rgba(255,255,255,0.20)",
        tickfont=dict(color="#E5E7EB"),
        title_font=dict(color="#F8FAFC")
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.12)",
        zeroline=False,
        linecolor="rgba(255,255,255,0.20)",
        tickfont=dict(color="#E5E7EB"),
        title_font=dict(color="#F8FAFC")
    )

    try:
        fig.update_traces(textfont_color="#FFFFFF")
    except Exception:
        pass

    return fig






def ir_a_pagina(destino):
    destino = str(destino or "Inicio")
    if st.session_state.get("pagina") == destino:
        return
    st.session_state.pagina = destino
    st.session_state["zentix_show_transition"] = True
    st.rerun()


def aplicar_nav_desde_query(paginas_validas):
    try:
        nav = st.query_params.get("nav")
    except Exception:
        nav = None

    if isinstance(nav, list):
        nav = nav[0] if nav else None

    if nav in paginas_validas:
        st.session_state.pagina = nav
        try:
            del st.query_params["nav"]
        except Exception:
            try:
                st.query_params.clear()
            except Exception:
                pass



def maybe_handle_special_nav_actions():
    try:
        nav = st.query_params.get("nav")
    except Exception:
        nav = None

    if isinstance(nav, list):
        nav = nav[0] if nav else None

    if nav == "__logout__":
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        st.session_state.user = None
        st.session_state["zentix_access_token"] = None
        st.session_state["zentix_refresh_token"] = None
        try:
            del st.query_params["nav"]
        except Exception:
            try:
                st.query_params.clear()
            except Exception:
                pass
        st.rerun()

def render_transition_overlay():
    if not st.session_state.get("zentix_show_transition"):
        return
    logo_html = ""
    if icono_path.exists():
        try:
            logo_b64 = base64.b64encode(Path(icono_path).read_bytes()).decode()
            logo_html = f"<img src='data:image/png;base64,{logo_b64}' style='width:110px;height:110px;object-fit:contain;margin-bottom:16px;'/>"
        except Exception:
            logo_html = ""
    splash = f"""
    <script>
    const doc = window.parent.document;
    const prev = doc.getElementById('zentix-transition-overlay');
    if (prev) prev.remove();
    const layer = doc.createElement('div');
    layer.id = 'zentix-transition-overlay';
    layer.innerHTML = `
      <style>
        #zentix-transition-overlay {{ position: fixed; inset:0; z-index:999999; display:flex; align-items:center; justify-content:center; background: linear-gradient(180deg, rgba(245,247,251,0.98), rgba(238,243,250,0.98)); backdrop-filter: blur(14px); opacity:1; transition: opacity .35s ease; }}
        #zentix-transition-overlay.hide {{ opacity:0; }}
        #zentix-transition-card {{ display:flex; flex-direction:column; align-items:center; justify-content:center; padding:28px 34px; border-radius:28px; background:rgba(255,255,255,0.96); border:1px solid rgba(79,70,229,0.10); box-shadow:0 24px 50px rgba(15,23,42,0.10); color:#0F172A; font-family:Inter,system-ui,sans-serif; }}
        #zentix-spinner {{ width:36px;height:36px;border-radius:999px;border:4px solid rgba(79,70,229,0.12);border-top-color:#4F46E5;animation:zentixSpin .8s linear infinite;margin-top:8px; }}
        @keyframes zentixSpin {{ from {{ transform:rotate(0deg); }} to {{ transform:rotate(360deg); }} }}
      </style>
      <div id='zentix-transition-card'>
        {logo_html}
        <div style='font-size:1.12rem;font-weight:900;margin-bottom:0.2rem;'>Zentix</div>
        <div style='font-size:0.92rem;color:#64748B;margin-bottom:10px;'>Preparando tu siguiente vista…</div>
        <div id='zentix-spinner'></div>
      </div>`;
    doc.body.appendChild(layer);
    setTimeout(() => layer.classList.add('hide'), 110);
    setTimeout(() => {{ try {{ layer.remove(); }} catch(e) {{}} }}, 220);
    </script>
    """
    components.html(splash, height=0)
    st.session_state["zentix_show_transition"] = False



def inyectar_sidebar_drawer(nombre_usuario, plan_actual, consultas_usadas, consultas_limite, pagina_actual):
    payload = {
        "nombre": str(nombre_usuario or "Usuario"),
        "plan": str((plan_actual or {}).get("plan", "free")).upper(),
        "consultas": int(consultas_usadas or 0),
        "limite": int(consultas_limite or 0),
        "pagina": str(pagina_actual or "Inicio"),
        "items": [
            {"page": "Inicio", "label": "Inicio", "icon": "🏠", "streamlit_label": "🏠 Inicio"},
            {"page": "Registrar", "label": "Registrar", "icon": "➕", "streamlit_label": "➕ Registrar"},
            {"page": "Análisis", "label": "Análisis", "icon": "📈", "streamlit_label": "📈 Análisis"},
            {"page": "Ahorro", "label": "Ahorro", "icon": "🎯", "streamlit_label": "🎯 Ahorro"},
            {"page": "Perfil", "label": "Perfil", "icon": "⚙️", "streamlit_label": "⚙️ Perfil"},
            {"page": "Zentix IA", "label": "Zentix IA", "icon": "🤖", "streamlit_label": "🤖 Zentix IA"},
        ]
    }

    drawer_html = f"""
    <script>
    (function() {{
      const data = {json.dumps(payload, ensure_ascii=False)};
      const doc = window.parent.document;
      const rootId = "zentix-drawer-root";
      const prev = doc.getElementById(rootId);
      if (prev) prev.remove();

      const root = doc.createElement("div");
      root.id = rootId;
      root.innerHTML = `
        <style>
          #zentix-drawer-root * {{ box-sizing: border-box; font-family: Inter, system-ui, -apple-system, sans-serif; }}
          #zentix-drawer-fab {{
            position: fixed; top: 14px; left: 14px; z-index: 1000000;
            width: 52px; height: 52px; border: none; border-radius: 18px; cursor: pointer;
            background: linear-gradient(135deg, #0F172A 0%, #172554 42%, #4F46E5 82%, #7C3AED 100%);
            color: white; box-shadow: 0 18px 32px rgba(15,23,42,0.24);
            display:flex; align-items:center; justify-content:center; font-size: 22px; font-weight: 900;
          }}
          #zentix-drawer-overlay {{ position: fixed; inset: 0; z-index: 999999; pointer-events: none; }}
          #zentix-drawer-overlay.is-open {{ pointer-events: auto; }}
          #zentix-drawer-backdrop {{
            position: absolute; inset: 0; background: rgba(15,23,42,0.18); backdrop-filter: blur(4px);
            opacity: 0; transition: opacity .22s ease;
          }}
          #zentix-drawer-overlay.is-open #zentix-drawer-backdrop {{ opacity: 1; }}
          #zentix-drawer-panel {{
            position: absolute; top: 0; left: 0; height: 100%; width: min(320px, 88vw);
            background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(247,250,255,0.99));
            border-right: 1px solid rgba(148,163,184,0.18);
            box-shadow: 18px 0 40px rgba(15,23,42,0.10);
            transform: translateX(-104%); transition: transform .22s ease;
            padding: 18px 16px 18px 16px; overflow-y: auto;
          }}
          #zentix-drawer-overlay.is-open #zentix-drawer-panel {{ transform: translateX(0); }}
          #zentix-drawer-close {{
            position: absolute; top: 14px; right: 14px; width: 40px; height: 40px; border: none; border-radius: 14px;
            background: #EEF2FF; color: #4338CA; cursor: pointer; font-size: 22px; font-weight: 700;
          }}
          #zentix-drawer-brand {{ padding: 8px 4px 16px 4px; border-bottom: 1px solid rgba(148,163,184,0.14); margin-bottom: 16px; }}
          #zentix-drawer-brand-title {{ font-size: 1.2rem; font-weight: 900; color: #0F172A; }}
          #zentix-drawer-brand-sub {{ color: #64748B; font-size: 0.88rem; margin-top: 4px; }}
          #zentix-drawer-user {{
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FBFF 100%);
            border: 1px solid rgba(148,163,184,0.18); border-radius: 18px; padding: 12px 14px; margin-bottom: 16px;
          }}
          #zentix-drawer-user .label {{ color: #64748B; font-size: 0.78rem; }}
          #zentix-drawer-user .name {{ color: #0F172A; font-size: 1rem; font-weight: 900; margin-top: 2px; }}
          #zentix-drawer-user .meta {{ color: #475569; font-size: 0.86rem; margin-top: 6px; }}
          #zentix-drawer-section {{ color: #475569; text-transform: uppercase; letter-spacing: .11em; font-size: 0.73rem; font-weight: 900; margin: 14px 4px 10px 4px; }}
          .zentix-drawer-link {{
            display:flex; align-items:center; gap: 12px; width: 100%; padding: 12px 14px; margin-bottom: 10px;
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%); border: 1px solid rgba(148,163,184,0.18);
            border-radius: 16px; color: #0F172A; cursor: pointer; text-align: left; font-size: 0.97rem; font-weight: 800;
            box-shadow: 0 10px 20px rgba(15,23,42,0.04);
          }}
          .zentix-drawer-link.active {{
            background: linear-gradient(135deg, #0F172A 0%, #172554 42%, #4F46E5 82%, #7C3AED 100%);
            color: white; border-color: transparent; box-shadow: 0 16px 30px rgba(79,70,229,0.20);
          }}
          .zentix-drawer-link .icon {{ width: 24px; text-align: center; font-size: 1rem; }}
          #zentix-drawer-footer {{ margin-top: 18px; padding-top: 16px; border-top: 1px solid rgba(148,163,184,0.14); }}
          #zentix-drawer-logout {{
            width: 100%; padding: 12px 14px; border-radius: 16px; border: 1px solid rgba(239,68,68,0.18);
            background: linear-gradient(180deg, #FFF1F2 0%, #FFFFFF 100%); color: #B91C1C; cursor: pointer; font-weight: 800;
          }}
          @media (max-width: 900px) {{
            #zentix-drawer-fab {{ width: 50px; height: 50px; top: 12px; left: 12px; }}
            #zentix-drawer-panel {{ width: min(320px, 90vw); }}
          }}
        </style>
        <button id="zentix-drawer-fab" aria-label="Abrir menú lateral">☰</button>
        <div id="zentix-drawer-overlay">
          <div id="zentix-drawer-backdrop"></div>
          <aside id="zentix-drawer-panel" aria-label="Menú lateral Zentix">
            <button id="zentix-drawer-close" aria-label="Cerrar menú">×</button>
            <div id="zentix-drawer-brand">
              <div id="zentix-drawer-brand-title">Zentix</div>
              <div id="zentix-drawer-brand-sub">Menú premium desplegable</div>
            </div>
            <div id="zentix-drawer-user">
              <div class="label">Sesión activa</div>
              <div class="name">${{data.nombre}}</div>
              <div class="meta">Plan ${{data.plan}} · IA ${{data.consultas}}/${{data.limite}}</div>
            </div>
            <div id="zentix-drawer-section">Navegación</div>
            <div id="zentix-drawer-links"></div>
            <div id="zentix-drawer-footer">
              <button id="zentix-drawer-logout">Cerrar sesión</button>
            </div>
          </aside>
        </div>
      `;
      doc.body.appendChild(root);

      const overlay = doc.getElementById("zentix-drawer-overlay");
      const fab = doc.getElementById("zentix-drawer-fab");
      const closeBtn = doc.getElementById("zentix-drawer-close");
      const backdrop = doc.getElementById("zentix-drawer-backdrop");
      const linksContainer = doc.getElementById("zentix-drawer-links");
      const logoutBtn = doc.getElementById("zentix-drawer-logout");

      function openDrawer() {{ overlay.classList.add("is-open"); }}
      function closeDrawer() {{ overlay.classList.remove("is-open"); }}
      function normalize(txt) {{ return String(txt || "").replace(/\s+/g, " ").trim(); }}
      function clickStreamlitButton(label) {{
        const wanted = normalize(label);
        const buttons = Array.from(doc.querySelectorAll('button'));
        for (const btn of buttons) {{
          const txt = normalize(btn.innerText || btn.textContent || "");
          if (txt === wanted || txt.includes(wanted)) {{
            btn.click();
            return true;
          }}
        }}
        return false;
      }}

      data.items.forEach((item) => {{
        const btn = doc.createElement("button");
        btn.className = "zentix-drawer-link" + (item.page === data.pagina ? " active" : "");
        btn.innerHTML = `<span class="icon">${{item.icon}}</span><span>${{item.label}}</span>`;
        btn.addEventListener("click", function() {{
          closeDrawer();
          const ok = clickStreamlitButton(item.streamlit_label || item.label);
          if (!ok) {{
            const url = new URL(window.parent.location.href);
            url.searchParams.set("nav", item.page);
            window.parent.location.href = url.toString();
          }}
        }});
        linksContainer.appendChild(btn);
      }});

      fab.addEventListener("click", function(ev) {{
        ev.preventDefault();
        ev.stopPropagation();
        overlay.classList.toggle("is-open");
      }});
      closeBtn.addEventListener("click", closeDrawer);
      backdrop.addEventListener("click", closeDrawer);
      logoutBtn.addEventListener("click", function() {{
        closeDrawer();
        const ok = clickStreamlitButton("Cerrar sesión");
        if (!ok) {{
          const url = new URL(window.parent.location.href);
          url.searchParams.set("nav", "__logout__");
          window.parent.location.href = url.toString();
        }}
      }});

      if (window.parent.innerWidth >= 1200) {{
        openDrawer();
      }}
    }})();
    </script>
    """
    components.html(drawer_html, height=0)

def zentix_brand_header():
    st.markdown("<div class='zentix-brand-shell fade-up'>", unsafe_allow_html=True)
    col_logo, col_title, col_side = st.columns([1.25, 5.95, 2.2])
    with col_logo:
        if icono_path.exists():
            st.image(str(icono_path), width=102)
    with col_title:
        st.markdown('<div class="zentix-brand-title">Zentix</div>', unsafe_allow_html=True)
        st.markdown('<div class="zentix-brand-sub">Controla ingresos, gastos, metas y deuda desde una experiencia clara en móvil, tablet y PC.</div>', unsafe_allow_html=True)
    with col_side:
        st.markdown(
            f"""
            <div style='text-align:right;padding-top:0.2rem;'>
                <div class='tiny-muted'>Experiencia activa</div>
                <div style='font-weight:900;color:#312E81;'>Orden + claridad</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown("</div>", unsafe_allow_html=True)


def zentix_hero(nombre, saldo_disponible, total_ingresos, total_gastos):
    balance_label = "Balance positivo" if saldo_disponible >= 0 else "Atención al balance"

    st.markdown(
        f"""
        <div class="hero-card fade-up">
            <div class="hero-badge">Zentix · panel principal</div>
            <div class="hero-title">Hola, {nombre} 👋</div>
            <div class="hero-subtitle">
                Tu resumen principal queda arriba, las acciones importantes al alcance y el detalle profundo disponible cuando lo necesites.
            </div>
            <div class="hero-pills">
                <span class="hero-pill">Disponible: {money(saldo_disponible)}</span>
                <span class="hero-pill">Ingresos: {money(total_ingresos)}</span>
                <span class="hero-pill">Gastos: {money(total_gastos)}</span>
                <span class="hero-pill">{balance_label}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def section_header(titulo, subtitulo=""):
    st.markdown(f'<div class="section-title">{titulo}</div>', unsafe_allow_html=True)
    if subtitulo:
        st.markdown(f'<div class="section-caption">{subtitulo}</div>', unsafe_allow_html=True)


def kpi_card(label, value, foot="", variant="balance"):
    classes = {
        "income": "kpi-card kpi-income",
        "expense": "kpi-card kpi-expense",
        "balance": "kpi-card kpi-balance",
        "saving": "kpi-card kpi-saving",
    }
    st.markdown(
        f"""
        <div class="{classes.get(variant, 'kpi-card')}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-foot">{foot}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def empty_state(title, text):
    st.markdown(
        f"""
        <div class="empty-card">
            <div style="font-size:1.05rem;font-weight:800;color:#F8FAFC;margin-bottom:0.35rem;">{title}</div>
            <div style="font-size:0.92rem;line-height:1.6;">{text}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def obtener_plan_default():
    return {
        "plan": "free",
        "estado": "active",
        "consultas_ia_dia": 10,
        "categorias_extra": 10
    }


def obtener_o_crear_plan_usuario(user_id):
    plan_default = obtener_plan_default()

    try:
        result = (
            supabase.table("planes_usuario")
            .select("*")
            .eq("usuario_id", user_id)
            .limit(1)
            .execute()
        )
        if result.data:
            plan = result.data[0]
            return {
                "plan": plan.get("plan", "free"),
                "estado": plan.get("estado", "active"),
                "consultas_ia_dia": int(plan.get("consultas_ia_dia", 10) or 10),
                "categorias_extra": int(plan.get("categorias_extra", 10) or 10)
            }

        nuevo_plan = {
            "usuario_id": user_id,
            "plan": "free",
            "estado": "active",
            "consultas_ia_dia": 10,
            "categorias_extra": 10,
            "actualizado_en": datetime.now().isoformat()
        }
        supabase.table("planes_usuario").insert(nuevo_plan).execute()
    except Exception:
        pass

    return plan_default


def obtener_uso_ia_hoy(user_id):
    hoy = date.today().isoformat()
    session_key = f"uso_ia_local_{user_id}_{hoy}"

    try:
        result = (
            supabase.table("uso_ia_diario")
            .select("*")
            .eq("usuario_id", user_id)
            .eq("fecha", hoy)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]

        nuevo_uso = {
            "usuario_id": user_id,
            "fecha": hoy,
            "consultas_usadas": 0,
            "actualizado_en": datetime.now().isoformat()
        }
        insert_result = supabase.table("uso_ia_diario").insert(nuevo_uso).execute()
        if insert_result.data:
            return insert_result.data[0]
    except Exception:
        pass

    if session_key not in st.session_state:
        st.session_state[session_key] = 0

    return {"id": None, "usuario_id": user_id, "fecha": hoy, "consultas_usadas": st.session_state[session_key]}


def puede_usar_ia(user_id):
    plan = obtener_o_crear_plan_usuario(user_id)
    uso = obtener_uso_ia_hoy(user_id)

    limite = int(plan.get("consultas_ia_dia", 10) or 10)
    usadas = int(uso.get("consultas_usadas", 0) or 0)
    restantes = max(0, limite - usadas)

    return usadas < limite, usadas, limite, restantes, plan


def registrar_uso_ia(user_id):
    hoy = date.today().isoformat()
    session_key = f"uso_ia_local_{user_id}_{hoy}"
    uso = obtener_uso_ia_hoy(user_id)
    nuevas_usadas = int(uso.get("consultas_usadas", 0) or 0) + 1

    try:
        if uso.get("id") is not None:
            (
                supabase.table("uso_ia_diario")
                .update({
                    "consultas_usadas": nuevas_usadas,
                    "actualizado_en": datetime.now().isoformat()
                })
                .eq("id", uso["id"])
                .execute()
            )
        else:
            st.session_state[session_key] = nuevas_usadas
    except Exception:
        st.session_state[session_key] = nuevas_usadas


def insertar_movimiento_seguro(payload):
    candidatos = [
        dict(payload),
        {k: v for k, v in payload.items() if k not in {
            "es_recurrente", "frecuencia_recurrencia", "proxima_fecha_recurrencia",
            "fecha_fin_recurrencia", "recurrente_activo"
        }},
        {k: v for k, v in payload.items() if k not in {
            "deuda_id", "deuda_nombre", "prestamista", "fecha_limite_deuda",
            "es_recurrente", "frecuencia_recurrencia", "proxima_fecha_recurrencia",
            "fecha_fin_recurrencia", "recurrente_activo"
        }},
        {k: v for k, v in payload.items() if k not in {
            "emocion", "deuda_id", "deuda_nombre", "prestamista", "fecha_limite_deuda",
            "es_recurrente", "frecuencia_recurrencia", "proxima_fecha_recurrencia",
            "fecha_fin_recurrencia", "recurrente_activo"
        }},
    ]

    last_error = None
    for candidate in candidatos:
        try:
            return supabase.table("movimientos").insert(candidate).execute()
        except Exception as e:
            last_error = e

    raise last_error


def obtener_preferencias_default(email_contacto=""):
    return {
        "usuario_id": None,
        "recordatorio_email": True,
        "recordatorio_sms": False,
        "frecuencia_recordatorios": "suave",
        "recordatorio_registro": True,
        "recordatorio_meta": False,
        "resumen_semanal": False,
        "silencio_activado": False,
        "silencio_inicio": "21:00",
        "silencio_fin": "07:00",
        "email_contacto": email_contacto or "",
        "telefono": "",
        "ultimo_recordatorio_en": None,
        "actualizado_en": None
    }


@st.cache_data(ttl=60, show_spinner=False)
def obtener_preferencias_usuario(user_id, email_contacto=""):
    prefs = obtener_preferencias_default(email_contacto)

    try:
        result = (
            supabase.table("preferencias_usuario")
            .select("*")
            .eq("usuario_id", user_id)
            .limit(1)
            .execute()
        )
        if result.data:
            row = result.data[0]
            prefs.update({
                "usuario_id": user_id,
                "recordatorio_email": bool(row.get("recordatorio_email", prefs["recordatorio_email"])),
                "recordatorio_sms": bool(row.get("recordatorio_sms", prefs["recordatorio_sms"])),
                "frecuencia_recordatorios": row.get("frecuencia_recordatorios", prefs["frecuencia_recordatorios"]) or "suave",
                "recordatorio_registro": bool(row.get("recordatorio_registro", prefs["recordatorio_registro"])),
                "recordatorio_meta": bool(row.get("recordatorio_meta", prefs["recordatorio_meta"])),
                "resumen_semanal": bool(row.get("resumen_semanal", prefs["resumen_semanal"])),
                "silencio_activado": bool(row.get("silencio_activado", prefs["silencio_activado"])),
                "silencio_inicio": row.get("silencio_inicio", prefs["silencio_inicio"]) or "21:00",
                "silencio_fin": row.get("silencio_fin", prefs["silencio_fin"]) or "07:00",
                "email_contacto": row.get("email_contacto", email_contacto) or email_contacto or "",
                "telefono": row.get("telefono", "") or "",
                "ultimo_recordatorio_en": row.get("ultimo_recordatorio_en"),
                "actualizado_en": row.get("actualizado_en")
            })
    except Exception:
        prefs["usuario_id"] = user_id

    return prefs


def guardar_preferencias_usuario(user_id, payload):
    base = {
        "usuario_id": user_id,
        "recordatorio_email": bool(payload.get("recordatorio_email", True)),
        "recordatorio_sms": bool(payload.get("recordatorio_sms", False)),
        "frecuencia_recordatorios": payload.get("frecuencia_recordatorios", "suave"),
        "recordatorio_registro": bool(payload.get("recordatorio_registro", True)),
        "recordatorio_meta": bool(payload.get("recordatorio_meta", False)),
        "resumen_semanal": bool(payload.get("resumen_semanal", False)),
        "silencio_activado": bool(payload.get("silencio_activado", False)),
        "silencio_inicio": payload.get("silencio_inicio", "21:00"),
        "silencio_fin": payload.get("silencio_fin", "07:00"),
        "email_contacto": payload.get("email_contacto", "") or "",
        "telefono": payload.get("telefono", "") or "",
        "actualizado_en": datetime.now().isoformat()
    }

    try:
        return supabase.table("preferencias_usuario").upsert(base, on_conflict="usuario_id").execute()
    except Exception:
        try:
            existe = (
                supabase.table("preferencias_usuario")
                .select("usuario_id")
                .eq("usuario_id", user_id)
                .limit(1)
                .execute()
            )
            if existe.data:
                return (
                    supabase.table("preferencias_usuario")
                    .update(base)
                    .eq("usuario_id", user_id)
                    .execute()
                )
            return supabase.table("preferencias_usuario").insert(base).execute()
        except Exception:
            return None


def obtener_config_smtp():
    def _leer(clave, default=None):
        valor = None
        try:
            valor = st.secrets.get(clave)
        except Exception:
            valor = None
        if valor in (None, ""):
            valor = os.getenv(clave, default)
        return valor if valor is not None else default

    def _texto(valor, default=""):
        return str(valor if valor is not None else default).strip()

    puerto_raw = _leer("SMTP_PORT", 587)
    try:
        puerto = int(str(puerto_raw).strip())
    except Exception:
        puerto = 587

    usar_tls_raw = _texto(_leer("SMTP_USE_TLS", "true"), "true").lower()
    host = _texto(_leer("SMTP_HOST", ""))
    user = _texto(_leer("SMTP_USER", ""))
    password = _texto(_leer("SMTP_PASSWORD", ""))
    password = password.replace(" ", "")
    from_email = _texto(_leer("SMTP_FROM_EMAIL", user or ""))
    from_name = _texto(_leer("SMTP_FROM_NAME", "Zentix"), "Zentix") or "Zentix"

    return {
        "host": host,
        "port": puerto,
        "user": user,
        "password": password,
        "from_email": from_email,
        "from_name": from_name,
        "use_tls": usar_tls_raw not in {"0", "false", "no"},
        "provider_hint": "gmail" if "gmail" in host.lower() or "gmail" in from_email.lower() else "generic"
    }

def smtp_disponible(config=None):
    config = config or obtener_config_smtp()
    return bool(config.get("host") and config.get("port") and config.get("from_email"))


def describir_config_smtp(config=None):
    config = config or obtener_config_smtp()
    faltantes = []
    for clave in ["host", "port", "user", "password", "from_email"]:
        if not config.get(clave):
            faltantes.append(clave)
    if faltantes:
        return {
            "ok": False,
            "titulo": "SMTP incompleto",
            "detalle": f"Faltan: {', '.join(faltantes)}."
        }
    modo = "TLS" if bool(config.get("use_tls", True)) else ("SSL" if int(config.get("port", 0) or 0) == 465 else "sin TLS")
    proveedor = "Gmail" if config.get("provider_hint") == "gmail" else "SMTP"
    return {
        "ok": True,
        "titulo": f"{proveedor} listo",
        "detalle": f"Puerto {config.get('port')} · modo {modo} · remitente {config.get('from_email')}."
    }


def _leer_secret_texto(clave, default=""):
    try:
        valor = st.secrets.get(clave)
    except Exception:
        valor = None
    if valor in (None, ""):
        valor = os.getenv(clave, default)
    return str(valor if valor is not None else default).strip()


def _leer_secret_bool(clave, default=False):
    raw = _leer_secret_texto(clave, str(default)).lower()
    return raw in {"1", "true", "yes", "si", "sí", "on"}


def obtener_config_lanzamiento():
    etapa = _leer_secret_texto("APP_STAGE", "beta").lower() or "beta"
    allow_default = etapa != "private"
    cfg = {
        "app_stage": etapa,
        "allow_public_signup": _leer_secret_bool("ALLOW_PUBLIC_SIGNUP", allow_default),
        "support_email": _leer_secret_texto("SUPPORT_EMAIL", ""),
        "support_whatsapp": _leer_secret_texto("SUPPORT_WHATSAPP", ""),
        "privacy_url": _leer_secret_texto("PRIVACY_POLICY_URL", ""),
        "terms_url": _leer_secret_texto("TERMS_URL", ""),
        "website_url": _leer_secret_texto("WEBSITE_URL", ""),
        "status_url": _leer_secret_texto("STATUS_PAGE_URL", ""),
        "launch_label": _leer_secret_texto("LAUNCH_LABEL", "Zentix beta premium"),
        "support_label": _leer_secret_texto("SUPPORT_LABEL", "Soporte Zentix"),
    }
    return cfg


def mostrar_paneles_internos():
    return _leer_secret_bool("SHOW_INTERNAL_PANELS", False)


def mostrar_plan_comercial():
    return _leer_secret_bool("SHOW_PLAN_MARKETING", False)


def texto_plan_avatar(plan_actual, consultas_usadas, consultas_limite):
    if mostrar_plan_comercial():
        return f"Plan: {plan_actual.get('plan', 'free').upper()} · IA hoy: {consultas_usadas}/{consultas_limite}"
    return f"IA hoy: {consultas_usadas}/{consultas_limite}"


def registrar_evento_producto(evento, user_id=None, pagina="", detalle="", valor=None):
    session_id = st.session_state.get("zentix_session_id")
    if not session_id:
        session_id = uuid.uuid4().hex[:16]
        st.session_state["zentix_session_id"] = session_id

    detalle_txt = str(detalle or "").strip()[:700]
    payload = {
        "usuario_id": user_id,
        "evento": str(evento or "evento").strip()[:80],
        "pagina": str(pagina or "").strip()[:80] or None,
        "detalle": detalle_txt or None,
        "valor": float(valor) if valor not in (None, "") else None,
        "session_id": session_id,
        "creado_en": datetime.now().isoformat()
    }
    candidatos = [
        dict(payload),
        {k: v for k, v in payload.items() if k != "valor"},
        {k: v for k, v in payload.items() if k not in {"valor", "session_id"}},
        {k: v for k, v in payload.items() if k in {"usuario_id", "evento", "pagina", "detalle", "creado_en"}},
    ]
    tablas = ["analytics_eventos", "eventos_producto", "analytics"]
    for tabla in tablas:
        for candidate in candidatos:
            try:
                supabase.table(tabla).insert(candidate).execute()
                return True
            except Exception:
                continue
    return False


def track_page_view_once(user_id, pagina):
    key = f"zentix_page_view_{user_id}_{pagina}"
    if st.session_state.get(key):
        return
    registrar_evento_producto("page_view", user_id=user_id, pagina=pagina, detalle=f"Vista de {pagina}")
    st.session_state[key] = True


def construir_links_lanzamiento_html(cfg):
    enlaces = []
    if cfg.get("privacy_url"):
        enlaces.append(f"<a href='{html.escape(cfg['privacy_url'])}' target='_blank'>Privacidad</a>")
    if cfg.get("terms_url"):
        enlaces.append(f"<a href='{html.escape(cfg['terms_url'])}' target='_blank'>Términos</a>")
    if cfg.get("website_url"):
        enlaces.append(f"<a href='{html.escape(cfg['website_url'])}' target='_blank'>Sitio</a>")
    if cfg.get("status_url"):
        enlaces.append(f"<a href='{html.escape(cfg['status_url'])}' target='_blank'>Estado</a>")
    if cfg.get("support_email"):
        enlaces.append(f"<a href='mailto:{html.escape(cfg['support_email'])}'>Soporte</a>")
    return " · ".join(enlaces)


def render_contexto_lanzamiento_acceso(cfg):
    if mostrar_paneles_internos():
        etapa = (cfg.get("app_stage") or "beta").upper()
        acceso = "Registro abierto" if cfg.get("allow_public_signup") else "Registro cerrado"
        chips = [
            f"<span class='launch-chip-soft'>{html.escape(etapa)}</span>",
            f"<span class='launch-chip-{'ok' if cfg.get('allow_public_signup') else 'warn'}'>{html.escape(acceso)}</span>"
        ]
        if cfg.get("support_email"):
            chips.append("<span class='launch-chip-ok'>Soporte listo</span>")
        if cfg.get("privacy_url") and cfg.get("terms_url"):
            chips.append("<span class='launch-chip-ok'>Legal visible</span>")
        st.markdown(
            f"""
            <div class='mini-soft-card fade-up'>
                <div class='tiny-muted'>Estado público de producto</div>
                <div style='font-weight:800;font-size:1.02rem;line-height:1.45;'>{html.escape(cfg.get('launch_label') or 'Zentix')}</div>
                <div class='launch-chip-row'>{''.join(chips)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    st.markdown(
        """
        <div class='mini-soft-card fade-up'>
            <div class='tiny-muted'>Acceso premium</div>
            <div style='font-weight:800;font-size:1.02rem;line-height:1.45;'>Tu espacio financiero personal ya está listo</div>
            <div class='tiny-muted' style='margin-top:0.35rem;'>Ingresa con tu correo para probar la experiencia completa de Zentix.</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_auth_visibility_strip():
    st.markdown(
        """
        <div class='auth-visible-options'>
            <span class='auth-visible-chip is-register'>🟣 Registro</span>
            <span class='auth-visible-chip is-login'>🔵 Login</span>
            <span class='auth-visible-chip is-reset'>🟠 Recuperar contraseña</span>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_footer_producto(cfg):
    links_html = construir_links_lanzamiento_html(cfg)
    if mostrar_paneles_internos():
        soporte = html.escape(cfg.get("support_email") or cfg.get("support_label") or "Soporte no configurado")
        etapa = html.escape((cfg.get("app_stage") or "beta").upper())
        extra = f"<div style='margin-top:0.35rem;'>{links_html}</div>" if links_html else ""
        st.markdown(
            f"""
            <div class='legal-footer'>
                <strong>Zentix</strong> · modo {etapa}.
                Para soporte: {soporte}.
                {extra}
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    soporte_publico = ""
    if cfg.get("support_email"):
        soporte_publico = f" · <a href='mailto:{html.escape(cfg['support_email'])}'>Soporte</a>"
    extra = f"<div style='margin-top:0.35rem;'>{links_html}</div>" if links_html else ""
    st.markdown(
        f"""
        <div class='legal-footer'>
            <strong>Zentix</strong> · Finanzas personales con experiencia premium.{soporte_publico}
            {extra}
        </div>
        """,
        unsafe_allow_html=True
    )


def obtener_estado_lanzamiento(cfg, smtp_cfg=None, automation_cfg=None):
    smtp_cfg = smtp_cfg or obtener_config_smtp()
    automation_cfg = automation_cfg or obtener_automation_runtime_config()
    checks = [
        ("Canal SMTP", smtp_disponible(smtp_cfg), "Listo para correos" if smtp_disponible(smtp_cfg) else "Faltan credenciales SMTP"),
        ("Soporte", bool(cfg.get("support_email")), cfg.get("support_email") or "Falta SUPPORT_EMAIL"),
        ("Legal", bool(cfg.get("privacy_url") and cfg.get("terms_url")), "Privacidad y términos visibles" if cfg.get("privacy_url") and cfg.get("terms_url") else "Agrega PRIVACY_POLICY_URL y TERMS_URL"),
        ("Automatización", bool(automation_cfg.get("enabled") and automation_cfg.get("app_base_url")), "Job background listo" if automation_cfg.get("enabled") and automation_cfg.get("app_base_url") else "Opcional: background aún no activado"),
        ("Registro público", bool(cfg.get("allow_public_signup")), "Usuarios pueden crear cuenta" if cfg.get("allow_public_signup") else "Registro cerrado / beta privada"),
    ]
    pendientes = [texto for _, ok, texto in checks if not ok]
    return checks, pendientes


def render_centro_lanzamiento(cfg, plan_actual):
    if not mostrar_paneles_internos():
        return

    smtp_cfg = obtener_config_smtp()
    automation_cfg = obtener_automation_runtime_config()
    checks, pendientes = obtener_estado_lanzamiento(cfg, smtp_cfg, automation_cfg)

    st.markdown(
        """
        <div class='soft-card fade-up'>
            <div class='section-title'>Centro de lanzamiento</div>
            <div class='section-caption'>Zentix ya está listo para operar en beta o abrirse al público con una base más seria de producto.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_spotlight_metric("Etapa", (cfg.get("app_stage") or "beta").upper(), "Modo público")
    with c2:
        render_spotlight_metric("Registro", "Abierto" if cfg.get("allow_public_signup") else "Cerrado", "Control de acceso")
    with c3:
        render_spotlight_metric("Plan visible", plan_actual.get("plan", "free").upper(), "Free / Pro activo")
    with c4:
        render_spotlight_metric("Checks listos", str(sum(1 for _, ok, _ in checks if ok)), f"de {len(checks)}")

    col_l, col_r = st.columns([1.1, 0.9])
    with col_l:
        for titulo, ok, detalle in checks:
            chip = "launch-chip-ok" if ok else "launch-chip-warn"
            st.markdown(
                f"""
                <div class='launch-grid-card'>
                    <div class='launch-grid-title'>{html.escape(titulo)}</div>
                    <div class='launch-grid-copy'>{html.escape(detalle)}</div>
                    <div class='launch-chip-row'><span class='{chip}'>{'Listo' if ok else 'Pendiente'}</span></div>
                </div>
                """,
                unsafe_allow_html=True
            )
    with col_r:
        render_list_card(
            "Checklist antes de abrir tráfico",
            [
                "Rotar claves expuestas antes del lanzamiento.",
                "Verificar RLS y políticas por usuario en Supabase.",
                "Probar login, registro, reportes y correo con 3 cuentas reales.",
                "Definir soporte visible y enlaces legales públicos.",
            ],
            "Esto no rompe tu app; solo te ayuda a salir más blindado."
        )
        if pendientes:
            render_list_card("Pendientes detectados", pendientes, "Los faltantes de abajo no tumban la app, pero sí conviene resolverlos antes del lanzamiento abierto.")
        else:
            st.success("Zentix ya tiene una base muy sana para una beta pública o lanzamiento controlado.")


def obtener_destino_recordatorio(preferencias, fallback_email=""):
    return str(preferencias.get("email_contacto") or fallback_email or "").strip()


def parse_datetime_seguro(valor):
    try:
        ts = pd.to_datetime(valor, errors="coerce")
        if pd.isna(ts):
            return None
        try:
            if getattr(ts, "tzinfo", None) is not None:
                ts = ts.tz_convert(None)
        except Exception:
            try:
                ts = ts.tz_localize(None)
            except Exception:
                pass
        if hasattr(ts, "to_pydatetime"):
            return ts.to_pydatetime()
        return ts
    except Exception:
        return None


def misma_semana_calendario(dt_a, dt_b):
    if dt_a is None or dt_b is None:
        return False
    try:
        iso_a = dt_a.isocalendar()
        iso_b = dt_b.isocalendar()
        return (iso_a[0], iso_a[1]) == (iso_b[0], iso_b[1])
    except Exception:
        return False


def horario_silencioso_activo(preferencias, now=None):
    if not bool(preferencias.get("silencio_activado", False)):
        return False
    now = now or datetime.now()
    try:
        inicio = datetime.strptime(str(preferencias.get("silencio_inicio", "21:00") or "21:00"), "%H:%M").time()
        fin = datetime.strptime(str(preferencias.get("silencio_fin", "07:00") or "07:00"), "%H:%M").time()
    except Exception:
        return False
    hora_actual = now.time()
    if inicio <= fin:
        return inicio <= hora_actual <= fin
    return hora_actual >= inicio or hora_actual <= fin


def obtener_control_recordatorios_usuario(user_id):
    session_key = f"zentix_recordatorio_control_{user_id}"
    base = {
        "ultimo_recordatorio_en": None,
        "ultimo_recordatorio_tipo": None,
        "ultimo_resumen_semanal_en": None,
        "ultimo_alerta_meta_en": None,
        "ultimo_intento_recordatorio_en": None
    }
    if session_key in st.session_state:
        base.update(st.session_state[session_key])

    try:
        result = (
            supabase.table("preferencias_usuario")
            .select("*")
            .eq("usuario_id", user_id)
            .limit(1)
            .execute()
        )
        if result.data:
            row = result.data[0]
            for clave in list(base.keys()):
                if row.get(clave) is not None:
                    base[clave] = row.get(clave)
    except Exception:
        pass

    st.session_state[session_key] = base
    return base


def guardar_control_recordatorios_usuario(user_id, updates):
    session_key = f"zentix_recordatorio_control_{user_id}"
    current = obtener_control_recordatorios_usuario(user_id)
    current.update(updates or {})
    current["actualizado_en"] = datetime.now().isoformat()
    st.session_state[session_key] = current

    base = {"usuario_id": user_id, **current}
    candidates = [
        dict(base),
        {k: v for k, v in base.items() if k not in {"ultimo_intento_recordatorio_en"}},
        {k: v for k, v in base.items() if k not in {"ultimo_resumen_semanal_en", "ultimo_alerta_meta_en", "ultimo_recordatorio_tipo", "ultimo_intento_recordatorio_en"}},
        {k: v for k, v in base.items() if k in {"usuario_id", "ultimo_recordatorio_en", "actualizado_en"}},
        {k: v for k, v in base.items() if k in {"usuario_id", "actualizado_en"}},
    ]

    for candidate in candidates:
        try:
            supabase.table("preferencias_usuario").upsert(candidate, on_conflict="usuario_id").execute()
            break
        except Exception:
            continue

    return current


def construir_correo_recordatorio(tipo, nombre, resumen_recordatorios, total_ingresos, total_gastos, saldo_disponible, meta_actual, proyeccion_meta, alertas):
    nombre = nombre or "Hola"
    accion = proyeccion_meta.get("mensaje", "Sigue registrando para que Zentix afine más tu lectura.") if isinstance(proyeccion_meta, dict) else "Sigue registrando para que Zentix afine más tu lectura."

    if tipo == "inactividad":
        dias = resumen_recordatorios.get("dias_inactividad") if isinstance(resumen_recordatorios, dict) else None
        asunto = f"Zentix · Llevas {dias if dias is not None else 'varios'} día(s) sin registrar"
        titulo = "Tu panel necesita una pequeña actualización"
        lineas = [
            f"Han pasado {dias if dias is not None else 'algunos'} día(s) desde tu último registro.",
            f"Disponible actual: {money(saldo_disponible)}.",
            f"Ingresos reales del mes: {money(total_ingresos)} · Gastos del mes: {money(total_gastos)}.",
            "Registrar uno o dos movimientos hoy ya mejora la lectura de patrones, alertas y metas.",
        ]
    elif tipo == "resumen_semanal":
        asunto = "Zentix · Tu resumen semanal premium"
        titulo = "Tu semana financiera, en limpio"
        alerta = (alertas[0] if alertas else "No hay alertas fuertes esta semana.")
        lineas = [
            f"Ingresos reales del periodo: {money(total_ingresos)}.",
            f"Gastos operativos del periodo: {money(total_gastos)}.",
            f"Disponible actual: {money(saldo_disponible)}.",
            f"Alerta destacada: {alerta}",
            f"Próximo mejor paso: {accion}",
        ]
    elif tipo == "alerta_meta":
        asunto = "Zentix · Tu meta necesita un pequeño impulso"
        titulo = "Tu meta sigue viva, pero conviene empujarla"
        lineas = [
            f"Meta actual: {money(meta_actual)}.",
            f"Disponible actual: {money(saldo_disponible)}.",
            accion,
            "Una corrección pequeña hoy puede acercarte mucho más rápido.",
        ]
    else:
        asunto = "Zentix · Correo de prueba"
        titulo = "Tu canal de recordatorios ya está listo"
        lineas = [
            f"Disponible actual: {money(saldo_disponible)}.",
            f"Ingresos reales del mes: {money(total_ingresos)} · Gastos del mes: {money(total_gastos)}.",
            "Este es un correo de prueba para validar que Zentix puede escribirte cuando haga falta.",
        ]

    bullets_text = "\n".join([f"- {line}" for line in lineas])
    bullets_html = "".join([f"<li style='margin-bottom:8px;'>{line}</li>" for line in lineas])

    texto = f"""{titulo}

Hola, {nombre}.

{bullets_text}

Equipo Zentix
"""
    html_msg = f"""
    <div style="background:#07111f;padding:28px;font-family:Arial,sans-serif;color:#E2E8F0;">
      <div style="max-width:680px;margin:0 auto;background:linear-gradient(135deg,#0f172a,#0a1426);border:1px solid rgba(96,165,250,0.22);border-radius:20px;padding:28px;">
        <div style="font-size:12px;font-weight:700;color:#93C5FD;letter-spacing:.06em;margin-bottom:10px;">ZENTIX · RECORDATORIO PREMIUM</div>
        <div style="font-size:28px;font-weight:800;color:#F8FAFC;margin-bottom:8px;">{titulo}</div>
        <div style="font-size:15px;line-height:1.7;color:#CBD5E1;margin-bottom:14px;">Hola, {nombre}.</div>
        <ul style="padding-left:18px;line-height:1.7;color:#E2E8F0;">{bullets_html}</ul>
        <div style="margin-top:18px;padding:14px 16px;border-radius:14px;background:rgba(59,130,246,0.10);border:1px solid rgba(96,165,250,0.16);color:#BFDBFE;">
          Zentix detecta el momento y te escribe con tacto, sin volverse invasivo.
        </div>
      </div>
    </div>
    """
    return asunto, texto, html_msg


def enviar_correo_smtp(destino, asunto, texto, html_msg=None, config=None):
    config = config or obtener_config_smtp()
    if not smtp_disponible(config):
        return False, "Faltan credenciales SMTP para enviar correos."
    if not destino:
        return False, "No hay correo destino configurado."

    msg = EmailMessage()
    remitente = config.get("from_email")
    nombre = config.get("from_name", "Zentix")
    msg["Subject"] = asunto
    msg["From"] = f"{nombre} <{remitente}>" if remitente else nombre
    msg["To"] = destino
    msg.set_content(texto)
    if html_msg:
        msg.add_alternative(html_msg, subtype="html")

    try:
        puerto = int(config.get("port", 587) or 587)
        host = config.get("host")
        usar_tls = bool(config.get("use_tls", True))

        if puerto == 465 and not usar_tls:
            with smtplib.SMTP_SSL(host, puerto, timeout=25, context=ssl.create_default_context()) as server:
                if config.get("user") and config.get("password"):
                    server.login(config.get("user"), config.get("password"))
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, puerto, timeout=25) as server:
                if usar_tls:
                    server.starttls(context=ssl.create_default_context())
                if config.get("user") and config.get("password"):
                    server.login(config.get("user"), config.get("password"))
                server.send_message(msg)
        return True, f"Correo enviado a {destino}."
    except Exception as e:
        return False, f"No se pudo enviar el correo: {e}"

def disparar_recordatorio_automatico_si_aplica(user_id, nombre, preferencias, resumen_recordatorios, total_ingresos, total_gastos, saldo_disponible, meta_actual, proyeccion_meta, alertas, fallback_email=""):
    now = datetime.now()
    config = obtener_config_smtp()
    destino = obtener_destino_recordatorio(preferencias, fallback_email)
    status = {
        "smtp_configurado": smtp_disponible(config),
        "destino": destino or "",
        "enviado": False,
        "tipo": None,
        "detalle": "Sin evaluación automática.",
        "ultimo_envio": None,
        "modo": "automatico_oportunista"
    }

    if not bool(preferencias.get("recordatorio_email", True)):
        status["detalle"] = "El canal de correo está desactivado en preferencias."
        return status
    if not smtp_disponible(config):
        status["detalle"] = "SMTP aún no está configurado; el motor está listo pero sin salida real."
        return status
    if not destino:
        status["detalle"] = "Falta el correo destino para activar envíos automáticos."
        return status
    if horario_silencioso_activo(preferencias, now):
        status["detalle"] = "Horario silencioso activo; Zentix no envía nada ahora."
        return status

    control = obtener_control_recordatorios_usuario(user_id)
    ultimo_envio = parse_datetime_seguro(control.get("ultimo_recordatorio_en"))
    status["ultimo_envio"] = ultimo_envio.isoformat() if ultimo_envio else None

    guard_key = f"zentix_notif_guard_{user_id}_{date.today().isoformat()}"
    if st.session_state.get(guard_key):
        status["detalle"] = st.session_state.get(guard_key)
        return status

    if ultimo_envio and (now - ultimo_envio) < timedelta(days=7):
        status["detalle"] = "Ya hubo un envío en los últimos 7 días; se respeta el máximo de 1 por semana."
        return status

    tipo = None
    if bool(preferencias.get("recordatorio_registro", True)):
        dias_inactividad = resumen_recordatorios.get("dias_inactividad") if isinstance(resumen_recordatorios, dict) else None
        umbral = resumen_recordatorios.get("umbral", 5) if isinstance(resumen_recordatorios, dict) else 5
        if dias_inactividad is not None and dias_inactividad >= umbral:
            tipo = "inactividad"

    if tipo is None and bool(preferencias.get("resumen_semanal", False)):
        ultimo_resumen = parse_datetime_seguro(control.get("ultimo_resumen_semanal_en"))
        if now.weekday() in {0, 1} and not misma_semana_calendario(ultimo_resumen, now):
            tipo = "resumen_semanal"

    if tipo is None and bool(preferencias.get("recordatorio_meta", False)) and float(meta_actual or 0) > 0:
        ultimo_meta = parse_datetime_seguro(control.get("ultimo_alerta_meta_en"))
        if (float(saldo_disponible or 0) < float(meta_actual or 0) * 0.45) and ((ultimo_meta is None) or (now - ultimo_meta) >= timedelta(days=7)):
            tipo = "alerta_meta"

    if tipo is None:
        status["detalle"] = "Hoy no hay un disparador automático que justifique enviar correo."
        return status

    asunto, texto, html_msg = construir_correo_recordatorio(tipo, nombre, resumen_recordatorios, total_ingresos, total_gastos, saldo_disponible, meta_actual, proyeccion_meta, alertas)
    ok, detalle = enviar_correo_smtp(destino, asunto, texto, html_msg, config=config)
    if ok:
        payload = {
            "ultimo_recordatorio_en": now.isoformat(),
            "ultimo_recordatorio_tipo": tipo,
            "ultimo_intento_recordatorio_en": now.isoformat(),
        }
        if tipo == "resumen_semanal":
            payload["ultimo_resumen_semanal_en"] = now.isoformat()
        if tipo == "alerta_meta":
            payload["ultimo_alerta_meta_en"] = now.isoformat()
        guardar_control_recordatorios_usuario(user_id, payload)
        st.session_state[guard_key] = detalle
    else:
        guardar_control_recordatorios_usuario(user_id, {"ultimo_intento_recordatorio_en": now.isoformat()})

    status.update({"enviado": ok, "tipo": tipo, "detalle": detalle})
    return status


def enviar_correo_prueba_zentix(nombre, preferencias, total_ingresos, total_gastos, saldo_disponible):
    destino = obtener_destino_recordatorio(preferencias, getattr(st.session_state.user, "email", ""))
    asunto, texto, html_msg = construir_correo_recordatorio("prueba", nombre, {}, total_ingresos, total_gastos, saldo_disponible, 0, {}, [])
    return enviar_correo_smtp(destino, asunto, texto, html_msg, config=obtener_config_smtp())


def normalizar_estado_deuda(valor):
    valor = str(valor or "").strip().lower()
    if valor in {"pagada", "pagado", "paid", "cerrada", "cerrado"}:
        return "pagada"
    if valor in {"vencida", "vencido", "overdue"}:
        return "vencida"
    return "activa"


@st.cache_data(ttl=45, show_spinner=False)
def obtener_deudas_usuario(user_id):
    columnas = [
        "id", "usuario_id", "nombre", "prestamista", "monto_total",
        "saldo_pendiente", "fecha", "fecha_limite", "descripcion",
        "estado", "creado_en", "actualizado_en"
    ]

    try:
        result = (
            supabase.table("deudas")
            .select("*")
            .eq("usuario_id", user_id)
            .order("fecha", desc=True)
            .execute()
        )
        data = result.data if result.data else []
    except Exception:
        data = []

    df_local = pd.DataFrame(data)

    for col in columnas:
        if col not in df_local.columns:
            df_local[col] = None

    if not df_local.empty:
        for date_col in ["fecha", "fecha_limite", "creado_en", "actualizado_en"]:
            if date_col in df_local.columns:
                df_local[date_col] = pd.to_datetime(df_local[date_col], errors="coerce")
        for num_col in ["monto_total", "saldo_pendiente"]:
            if num_col in df_local.columns:
                df_local[num_col] = pd.to_numeric(df_local[num_col], errors="coerce").fillna(0)
        df_local["nombre"] = df_local["nombre"].fillna("Deuda sin nombre")
        df_local["prestamista"] = df_local["prestamista"].fillna("Sin prestamista")
        if "estado" in df_local.columns:
            df_local["estado"] = df_local["estado"].apply(normalizar_estado_deuda)
    else:
        df_local = pd.DataFrame(columns=columnas)

    return df_local


def crear_deuda_segura(payload):
    base = dict(payload)
    base["estado"] = normalizar_estado_deuda(base.get("estado"))

    candidatos = [
        dict(base),
        {k: v for k, v in base.items() if k not in {"descripcion", "actualizado_en"}},
        {k: v for k, v in base.items() if k in {"usuario_id", "nombre", "prestamista", "monto_total", "saldo_pendiente", "fecha", "fecha_limite", "estado"}},
    ]

    for candidate in candidatos:
        try:
            result = supabase.table("deudas").insert(candidate).execute()
            if result.data:
                return result.data[0]
        except Exception:
            continue

    return None


def actualizar_deuda_pago_seguro(deuda_id, nuevo_saldo):
    saldo_final = float(max(nuevo_saldo, 0))
    payload = {
        "saldo_pendiente": saldo_final,
        "estado": "pagada" if saldo_final <= 0 else "activa",
        "actualizado_en": datetime.now().isoformat()
    }

    try:
        return (
            supabase.table("deudas")
            .update(payload)
            .eq("id", deuda_id)
            .execute()
        )
    except Exception:
        try:
            return (
                supabase.table("deudas")
                .update({"saldo_pendiente": saldo_final})
                .eq("id", deuda_id)
                .execute()
            )
        except Exception:
            return None


def normalizar_estado_cxc(valor):
    valor = str(valor or "").strip().lower()
    if valor in {"cobrada", "cobrado", "paid", "cerrada", "cerrado"}:
        return "cobrada"
    if valor in {"vencida", "vencido", "overdue"}:
        return "vencida"
    return "activa"


def es_error_tabla_cxc_faltante(error):
    texto = str(error or "").lower()
    return (
        "cuentas_por_cobrar" in texto
        and (
            "could not find the table" in texto
            or "schema cache" in texto
            or "does not exist" in texto
            or "relation" in texto
        )
    )


def generar_cuenta_por_cobrar_virtual_id(nombre, cliente):
    semilla = f"{str(nombre or '').strip().lower()}||{str(cliente or '').strip().lower()}"
    return f"cxc_virtual_{uuid.uuid5(uuid.NAMESPACE_URL, semilla).hex}"


@st.cache_data(ttl=45, show_spinner=False)
def obtener_cuentas_por_cobrar_usuario(user_id):
    columnas = [
        "id", "usuario_id", "nombre", "cliente", "monto_total",
        "saldo_pendiente", "fecha", "fecha_limite", "descripcion",
        "estado", "creado_en", "actualizado_en"
    ]
    try:
        result = (
            supabase.table("cuentas_por_cobrar")
            .select("*")
            .eq("usuario_id", user_id)
            .order("fecha", desc=True)
            .execute()
        )
        data = result.data if result.data else []
    except Exception:
        data = []

    df_local = pd.DataFrame(data)

    for col in columnas:
        if col not in df_local.columns:
            df_local[col] = None

    if not df_local.empty:
        for date_col in ["fecha", "fecha_limite", "creado_en", "actualizado_en"]:
            if date_col in df_local.columns:
                df_local[date_col] = pd.to_datetime(df_local[date_col], errors="coerce")
        for num_col in ["monto_total", "saldo_pendiente"]:
            if num_col in df_local.columns:
                df_local[num_col] = pd.to_numeric(df_local[num_col], errors="coerce").fillna(0)
        df_local["nombre"] = df_local["nombre"].fillna("Cuenta por cobrar")
        df_local["cliente"] = df_local["cliente"].fillna("Sin cliente")
        if "estado" in df_local.columns:
            df_local["estado"] = df_local["estado"].apply(normalizar_estado_cxc)
    else:
        df_local = pd.DataFrame(columns=columnas)

    return df_local


def crear_cuenta_por_cobrar_segura(payload):
    base = dict(payload)
    base["estado"] = normalizar_estado_cxc(base.get("estado"))

    candidatos = [
        dict(base),
        {k: v for k, v in base.items() if k not in {"descripcion", "actualizado_en"}},
        {k: v for k, v in base.items() if k in {"usuario_id", "nombre", "cliente", "monto_total", "saldo_pendiente", "fecha", "fecha_limite", "estado"}},
    ]

    last_error = None
    for candidate in candidatos:
        try:
            result = supabase.table("cuentas_por_cobrar").insert(candidate).execute()
            if result.data:
                return result.data[0]
        except Exception as e:
            last_error = e
            if es_error_tabla_cxc_faltante(e):
                virtual = dict(base)
                virtual["id"] = generar_cuenta_por_cobrar_virtual_id(base.get("nombre"), base.get("cliente"))
                virtual["_virtual"] = True
                return virtual
            continue

    if es_error_tabla_cxc_faltante(last_error):
        virtual = dict(base)
        virtual["id"] = generar_cuenta_por_cobrar_virtual_id(base.get("nombre"), base.get("cliente"))
        virtual["_virtual"] = True
        return virtual

    return None


def actualizar_cuenta_por_cobrar_cobro_seguro(cxc_id, nuevo_saldo):
    saldo_final = float(max(nuevo_saldo, 0))
    payload = {
        "saldo_pendiente": saldo_final,
        "estado": "cobrada" if saldo_final <= 0 else "activa",
        "actualizado_en": datetime.now().isoformat()
    }

    try:
        return (
            supabase.table("cuentas_por_cobrar")
            .update(payload)
            .eq("id", cxc_id)
            .execute()
        )
    except Exception:
        try:
            return (
                supabase.table("cuentas_por_cobrar")
                .update({"saldo_pendiente": saldo_final})
                .eq("id", cxc_id)
                .execute()
            )
        except Exception:
            return None


def recalcular_cuentas_por_cobrar_desde_movimientos(user_id, df_movs, df_cxc_actuales=None):
    columnas = [
        "id", "usuario_id", "nombre", "cliente", "monto_total",
        "saldo_pendiente", "fecha", "fecha_limite", "descripcion",
        "estado", "creado_en", "actualizado_en"
    ]
    existentes = df_cxc_actuales.copy() if df_cxc_actuales is not None and not df_cxc_actuales.empty else obtener_cuentas_por_cobrar_usuario(user_id)

    if df_movs is None:
        df_movs = pd.DataFrame()

    df_base = df_movs.copy()
    for col in ["cuenta_cobrar_nombre", "cliente_cxc", "descripcion", "fecha_limite_cxc", "fecha", "monto", "tipo"]:
        if col not in df_base.columns:
            df_base[col] = None

    if not df_base.empty:
        df_base["fecha"] = pd.to_datetime(df_base["fecha"], errors="coerce")
        df_base["fecha_limite_cxc"] = pd.to_datetime(df_base["fecha_limite_cxc"], errors="coerce")
        df_base["monto"] = pd.to_numeric(df_base["monto"], errors="coerce").fillna(0)

    creadas = df_base[df_base["tipo"] == "Cuenta por cobrar"].copy() if not df_base.empty else pd.DataFrame()
    cobradas = df_base[df_base["tipo"] == "Cobro cuenta por cobrar"].copy() if not df_base.empty else pd.DataFrame()

    def build_key(nombre, cliente):
        return f"{str(nombre or '').strip().lower()}||{str(cliente or '').strip().lower()}"

    summaries = {}

    if not creadas.empty:
        creadas["cxc_key"] = creadas.apply(
            lambda row: build_key(row.get("cuenta_cobrar_nombre") or row.get("descripcion") or "Cuenta por cobrar", row.get("cliente_cxc") or "Sin cliente"),
            axis=1
        )

        if not cobradas.empty:
            cobradas["cxc_key"] = cobradas.apply(
                lambda row: build_key(row.get("cuenta_cobrar_nombre") or row.get("descripcion") or "Cuenta por cobrar", row.get("cliente_cxc") or "Sin cliente"),
                axis=1
            )
            cobros_por_key = cobradas.groupby("cxc_key", dropna=False)["monto"].sum().to_dict()
        else:
            cobros_por_key = {}

        for cxc_key, grupo in creadas.groupby("cxc_key", dropna=False):
            grupo = grupo.sort_values("fecha")
            primera = grupo.iloc[0]
            monto_total = float(pd.to_numeric(grupo["monto"], errors="coerce").fillna(0).sum())
            total_cobrado = float(cobros_por_key.get(cxc_key, 0) or 0)
            saldo_pendiente = max(monto_total - total_cobrado, 0)
            fechas_lim = pd.to_datetime(grupo["fecha_limite_cxc"], errors="coerce")
            fecha_limite_val = fechas_lim.dropna().max() if not fechas_lim.dropna().empty else None
            fecha_base = pd.to_datetime(primera.get("fecha"), errors="coerce")
            nombre_base = (primera.get("cuenta_cobrar_nombre") or primera.get("descripcion") or "Cuenta por cobrar").strip()
            cliente_base = (primera.get("cliente_cxc") or "Sin cliente").strip()
            summaries[cxc_key] = {
                "id": generar_cuenta_por_cobrar_virtual_id(nombre_base, cliente_base),
                "nombre": nombre_base,
                "cliente": cliente_base,
                "monto_total": monto_total,
                "saldo_pendiente": saldo_pendiente,
                "fecha": fecha_base,
                "fecha_limite": fecha_limite_val,
                "descripcion": (primera.get("descripcion") or "").strip(),
                "estado": "cobrada" if saldo_pendiente <= 0 else "activa"
            }

    existentes_map = {}
    if existentes is not None and not existentes.empty:
        existentes = existentes.copy()
        existentes["cxc_key"] = existentes.apply(lambda row: build_key(row.get("nombre"), row.get("cliente")), axis=1)
        for _, row in existentes.iterrows():
            key = row["cxc_key"]
            if key not in existentes_map:
                existentes_map[key] = row

    all_keys = set(existentes_map.keys()) | set(summaries.keys())

    for cxc_key in all_keys:
        summary = summaries.get(cxc_key)
        existente = existentes_map.get(cxc_key)

        if summary:
            if existente is not None and existente.get("id"):
                summary["id"] = existente.get("id")

            payload = {
                "usuario_id": user_id,
                "nombre": summary["nombre"],
                "cliente": summary["cliente"],
                "monto_total": float(summary["monto_total"]),
                "saldo_pendiente": float(summary["saldo_pendiente"]),
                "fecha": summary["fecha"].isoformat() if pd.notna(summary["fecha"]) else datetime.now().isoformat(),
                "fecha_limite": summary["fecha_limite"].isoformat() if pd.notna(summary["fecha_limite"]) else None,
                "descripcion": summary["descripcion"],
                "estado": normalizar_estado_cxc(summary["estado"]),
                "actualizado_en": datetime.now().isoformat()
            }
            if existente is not None and existente.get("id") and not str(existente.get("id")).startswith("cxc_virtual_"):
                try:
                    (
                        supabase.table("cuentas_por_cobrar")
                        .update(payload)
                        .eq("id", existente["id"])
                        .execute()
                    )
                except Exception:
                    try:
                        (
                            supabase.table("cuentas_por_cobrar")
                            .update({k: v for k, v in payload.items() if k not in {"descripcion", "actualizado_en"}})
                            .eq("id", existente["id"])
                            .execute()
                        )
                    except Exception:
                        pass
            else:
                creado = crear_cuenta_por_cobrar_segura(payload)
                if isinstance(creado, dict) and creado.get("id"):
                    summary["id"] = creado.get("id")
        else:
            if existente is not None and existente.get("id") and not str(existente.get("id")).startswith("cxc_virtual_"):
                payload = {
                    "saldo_pendiente": 0.0,
                    "estado": "cobrada",
                    "actualizado_en": datetime.now().isoformat()
                }
                try:
                    (
                        supabase.table("cuentas_por_cobrar")
                        .update(payload)
                        .eq("id", existente["id"])
                        .execute()
                    )
                except Exception:
                    try:
                        (
                            supabase.table("cuentas_por_cobrar")
                            .update({"saldo_pendiente": 0.0})
                            .eq("id", existente["id"])
                            .execute()
                        )
                    except Exception:
                        pass

    rows = []
    if summaries:
        for cxc_key, summary in summaries.items():
            existente = existentes_map.get(cxc_key)
            row = {
                "id": summary.get("id") or (existente.get("id") if existente is not None else generar_cuenta_por_cobrar_virtual_id(summary.get("nombre"), summary.get("cliente"))),
                "usuario_id": user_id,
                "nombre": summary.get("nombre"),
                "cliente": summary.get("cliente"),
                "monto_total": float(summary.get("monto_total", 0) or 0),
                "saldo_pendiente": float(summary.get("saldo_pendiente", 0) or 0),
                "fecha": summary.get("fecha"),
                "fecha_limite": summary.get("fecha_limite"),
                "descripcion": summary.get("descripcion") or "",
                "estado": normalizar_estado_cxc(summary.get("estado")),
                "creado_en": existente.get("creado_en") if existente is not None else None,
                "actualizado_en": datetime.now().isoformat(),
            }
            rows.append(row)
    elif existentes is not None and not existentes.empty:
        return existentes[columnas] if all(col in existentes.columns for col in columnas) else existentes

    df_resultado = pd.DataFrame(rows)
    for col in columnas:
        if col not in df_resultado.columns:
            df_resultado[col] = None

    if not df_resultado.empty:
        for date_col in ["fecha", "fecha_limite", "creado_en", "actualizado_en"]:
            df_resultado[date_col] = pd.to_datetime(df_resultado[date_col], errors="coerce")
        for num_col in ["monto_total", "saldo_pendiente"]:
            df_resultado[num_col] = pd.to_numeric(df_resultado[num_col], errors="coerce").fillna(0)
        df_resultado["nombre"] = df_resultado["nombre"].fillna("Cuenta por cobrar")
        df_resultado["cliente"] = df_resultado["cliente"].fillna("Sin cliente")
        df_resultado["estado"] = df_resultado["estado"].apply(normalizar_estado_cxc)
    else:
        df_resultado = pd.DataFrame(columns=columnas)

    return df_resultado[columnas]


def actualizar_movimiento_seguro(movimiento_id, payload):
    base = dict(payload)
    candidatos = [
        dict(base),
        {k: v for k, v in base.items() if k not in {
            "es_recurrente", "frecuencia_recurrencia", "proxima_fecha_recurrencia",
            "fecha_fin_recurrencia", "recurrente_activo"
        }},
        {k: v for k, v in base.items() if k not in {
            "deuda_id", "deuda_nombre", "prestamista", "fecha_limite_deuda",
            "es_recurrente", "frecuencia_recurrencia", "proxima_fecha_recurrencia",
            "fecha_fin_recurrencia", "recurrente_activo"
        }},
        {k: v for k, v in base.items() if k not in {
            "emocion", "deuda_id", "deuda_nombre", "prestamista", "fecha_limite_deuda",
            "es_recurrente", "frecuencia_recurrencia", "proxima_fecha_recurrencia",
            "fecha_fin_recurrencia", "recurrente_activo"
        }},
    ]

    last_error = None
    for candidate in candidatos:
        try:
            return (
                supabase.table("movimientos")
                .update(candidate)
                .eq("id", movimiento_id)
                .execute()
            )
        except Exception as e:
            last_error = e
    raise last_error


def eliminar_movimiento_seguro(movimiento_id):
    return (
        supabase.table("movimientos")
        .delete()
        .eq("id", movimiento_id)
        .execute()
    )


def recalcular_deudas_usuario_desde_movimientos(user_id, df_movs, df_deudas_actuales=None):
    existentes = df_deudas_actuales.copy() if df_deudas_actuales is not None and not df_deudas_actuales.empty else obtener_deudas_usuario(user_id)

    if df_movs is None:
        df_movs = pd.DataFrame()

    df_base = df_movs.copy()
    for col in ["deuda_nombre", "prestamista", "descripcion", "fecha_limite_deuda", "fecha", "monto", "tipo"]:
        if col not in df_base.columns:
            df_base[col] = None

    if not df_base.empty:
        df_base["fecha"] = pd.to_datetime(df_base["fecha"], errors="coerce")
        df_base["fecha_limite_deuda"] = pd.to_datetime(df_base["fecha_limite_deuda"], errors="coerce")
        df_base["monto"] = pd.to_numeric(df_base["monto"], errors="coerce").fillna(0)

    ingresos_deuda = df_base[df_base["tipo"] == "Ingreso (Deuda)"].copy() if not df_base.empty else pd.DataFrame()
    pagos_deuda = df_base[df_base["tipo"] == "Pago de deuda"].copy() if not df_base.empty else pd.DataFrame()

    def build_key(nombre, prestamista):
        return f"{str(nombre or '').strip().lower()}||{str(prestamista or '').strip().lower()}"

    summaries = {}

    if not ingresos_deuda.empty:
        ingresos_deuda["deuda_key"] = ingresos_deuda.apply(
            lambda row: build_key(row.get("deuda_nombre") or row.get("descripcion") or "Deuda sin nombre", row.get("prestamista") or "Sin prestamista"),
            axis=1
        )

        if not pagos_deuda.empty:
            pagos_deuda["deuda_key"] = pagos_deuda.apply(
                lambda row: build_key(row.get("deuda_nombre") or row.get("descripcion") or "Deuda sin nombre", row.get("prestamista") or "Sin prestamista"),
                axis=1
            )
            pagos_por_key = pagos_deuda.groupby("deuda_key", dropna=False)["monto"].sum().to_dict()
        else:
            pagos_por_key = {}

        for deuda_key, grupo in ingresos_deuda.groupby("deuda_key", dropna=False):
            grupo = grupo.sort_values("fecha")
            primera = grupo.iloc[0]
            monto_total = float(pd.to_numeric(grupo["monto"], errors="coerce").fillna(0).sum())
            total_pagado = float(pagos_por_key.get(deuda_key, 0) or 0)
            saldo_pendiente = max(monto_total - total_pagado, 0)
            fechas_lim = pd.to_datetime(grupo["fecha_limite_deuda"], errors="coerce")
            fecha_limite_val = fechas_lim.dropna().max() if not fechas_lim.dropna().empty else None
            fecha_base = pd.to_datetime(primera.get("fecha"), errors="coerce")
            summaries[deuda_key] = {
                "nombre": (primera.get("deuda_nombre") or primera.get("descripcion") or "Deuda sin nombre").strip(),
                "prestamista": (primera.get("prestamista") or "Sin prestamista").strip(),
                "monto_total": monto_total,
                "saldo_pendiente": saldo_pendiente,
                "fecha": fecha_base,
                "fecha_limite": fecha_limite_val,
                "descripcion": (primera.get("descripcion") or "").strip(),
                "estado": "pagada" if saldo_pendiente <= 0 else "activa"
            }

    existentes_map = {}
    if existentes is not None and not existentes.empty:
        existentes = existentes.copy()
        existentes["deuda_key"] = existentes.apply(lambda row: build_key(row.get("nombre"), row.get("prestamista")), axis=1)
        for _, row in existentes.iterrows():
            key = row["deuda_key"]
            if key not in existentes_map:
                existentes_map[key] = row

    all_keys = set(existentes_map.keys()) | set(summaries.keys())

    for deuda_key in all_keys:
        summary = summaries.get(deuda_key)
        existente = existentes_map.get(deuda_key)

        if summary:
            payload = {
                "usuario_id": user_id,
                "nombre": summary["nombre"],
                "prestamista": summary["prestamista"],
                "monto_total": float(summary["monto_total"]),
                "saldo_pendiente": float(summary["saldo_pendiente"]),
                "fecha": summary["fecha"].isoformat() if pd.notna(summary["fecha"]) else datetime.now().isoformat(),
                "fecha_limite": summary["fecha_limite"].isoformat() if pd.notna(summary["fecha_limite"]) else None,
                "descripcion": summary["descripcion"],
                "estado": normalizar_estado_deuda(summary["estado"]),
                "actualizado_en": datetime.now().isoformat()
            }
            if existente is not None and existente.get("id") is not None:
                try:
                    (
                        supabase.table("deudas")
                        .update(payload)
                        .eq("id", existente["id"])
                        .execute()
                    )
                except Exception:
                    try:
                        (
                            supabase.table("deudas")
                            .update({k: v for k, v in payload.items() if k not in {"descripcion", "actualizado_en"}})
                            .eq("id", existente["id"])
                            .execute()
                        )
                    except Exception:
                        pass
            else:
                crear_deuda_segura(payload)
        else:
            if existente is not None and existente.get("id") is not None:
                payload = {
                    "saldo_pendiente": 0.0,
                    "estado": "pagada",
                    "actualizado_en": datetime.now().isoformat()
                }
                try:
                    (
                        supabase.table("deudas")
                        .update(payload)
                        .eq("id", existente["id"])
                        .execute()
                    )
                except Exception:
                    try:
                        (
                            supabase.table("deudas")
                            .update({"saldo_pendiente": 0.0})
                            .eq("id", existente["id"])
                            .execute()
                        )
                    except Exception:
                        pass

    return obtener_deudas_usuario(user_id)



def render_editor_movimientos(user_id, df_movs, df_deudas_local):
    st.markdown(
        """
        <div class="spotlight-side-card fade-up" style="margin-top:0.9rem;">
            <div class="spotlight-side-title">Editor avanzado del movimiento</div>
            <div class="spotlight-side-sub">Puedes entrar desde las fichas rápidas o seguir usando este panel completo para editar con precisión.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if df_movs is None or df_movs.empty or "id" not in df_movs.columns:
        st.info("Todavía no hay movimientos editables.")
        return

    df_editor = df_movs.copy().sort_values("fecha", ascending=False)
    df_editor["fecha"] = pd.to_datetime(df_editor["fecha"], errors="coerce")
    df_editor["monto"] = pd.to_numeric(df_editor["monto"], errors="coerce").fillna(0)

    def build_label(row):
        fecha_txt = row["fecha"].strftime("%Y-%m-%d") if pd.notna(row["fecha"]) else "Sin fecha"
        deuda_txt = f" · {row.get('deuda_nombre')}" if str(row.get("deuda_nombre") or "").strip() else ""
        descripcion_txt = str(row.get("descripcion") or "").strip()
        if len(descripcion_txt) > 36:
            descripcion_txt = descripcion_txt[:36] + "..."
        return f"{fecha_txt} · {tipo_display(row.get('tipo', 'Sin tipo'))} · {money(row.get('monto', 0))} · {descripcion_txt or 'Sin descripción'}{deuda_txt}"

    labels = {str(row["id"]): build_label(row) for _, row in df_editor.iterrows() if pd.notna(row.get("id"))}
    if not labels:
        st.info("No encontré identificadores válidos para editar movimientos.")
        return

    preselected = st.session_state.get("zentix_selected_movimiento_id")
    opciones = list(labels.keys())
    default_index = opciones.index(str(preselected)) if preselected and str(preselected) in opciones else 0
    expanded = bool(st.session_state.get("zentix_open_editor")) or bool(preselected)

    with st.expander("🛠️ Gestionar un movimiento registrado", expanded=expanded):
        selected_id = st.selectbox(
            "Selecciona un movimiento",
            opciones,
            index=default_index,
            format_func=lambda x: labels.get(x, x),
            key="editor_movimiento_select"
        )
        st.session_state["zentix_selected_movimiento_id"] = str(selected_id)

        row = df_editor[df_editor["id"].astype(str) == str(selected_id)].iloc[0]
        modo_editor = str(st.session_state.get("zentix_editor_mode") or "edit").lower()
        if modo_editor == "delete":
            st.warning("Entraste en modo eliminación desde una ficha rápida. Revisa el movimiento y confirma si realmente quieres borrarlo.")

        fecha_actual = row["fecha"].date() if pd.notna(row["fecha"]) else date.today()
        tipo_actual = row.get("tipo", "Gasto") or "Gasto"
        categoria_actual = row.get("categoria", "") or ""
        descripcion_actual = row.get("descripcion", "") or ""
        emocion_actual = row.get("emocion", "") or ""
        deuda_nombre_actual = row.get("deuda_nombre", "") or ""
        prestamista_actual = row.get("prestamista", "") or ""
        monto_actual = float(row.get("monto", 0) or 0)
        fecha_limite_actual = pd.to_datetime(row.get("fecha_limite_deuda"), errors="coerce")
        es_recurrente_actual = bool(row.get("es_recurrente", False))
        frecuencia_actual = row.get("frecuencia_recurrencia", "") or "Semanal"
        proxima_actual = pd.to_datetime(row.get("proxima_fecha_recurrencia"), errors="coerce")
        fecha_fin_actual = pd.to_datetime(row.get("fecha_fin_recurrencia"), errors="coerce")
        recurrente_activo_actual = bool(row.get("recurrente_activo", False))
        deuda_id_actual = row.get("deuda_id")

        st.markdown(
            f"""
            <div class="mini-soft-card">
                <div class="tiny-muted">Movimiento actual</div>
                <div style="font-weight:800;line-height:1.55;">{labels[str(selected_id)]}</div>
                <div class="movement-chip-row" style="margin-top:0.65rem;">{construir_chips_movimiento(row)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        tipo_edit = st.selectbox(
            "Tipo",
            ["Ingreso", "Gasto", "Ingreso (Deuda)", "Pago de deuda", "Cuenta por cobrar", "Cobro cuenta por cobrar"],
            index=["Ingreso", "Gasto", "Ingreso (Deuda)", "Pago de deuda", "Cuenta por cobrar", "Cobro cuenta por cobrar"].index(tipo_actual if tipo_actual in ["Ingreso", "Gasto", "Ingreso (Deuda)", "Pago de deuda", "Cuenta por cobrar", "Cobro cuenta por cobrar"] else "Gasto"),
            key=f"edit_tipo_{selected_id}",
            format_func=lambda x: tipo_display(x)
        )
        fecha_edit = st.date_input("Fecha", value=fecha_actual, key=f"edit_fecha_{selected_id}")
        descripcion_edit = st.text_input("Descripción", value=descripcion_actual, key=f"edit_descripcion_{selected_id}")

        categoria_edit = categoria_actual
        emocion_edit = emocion_actual
        deuda_nombre_edit = deuda_nombre_actual
        prestamista_edit = prestamista_actual
        deuda_id_edit = deuda_id_actual
        fecha_limite_edit = fecha_limite_actual.date() if pd.notna(fecha_limite_actual) else None

        if tipo_edit == "Ingreso":
            categorias = obtener_categorias_usuario(user_id, "Ingreso")
            if categoria_actual and categoria_actual not in categorias:
                categorias = [categoria_actual] + categorias
            if not categorias:
                categorias = ["Sin categorías"]
            categoria_edit = st.selectbox("Categoría", categorias, index=max(categorias.index(categoria_actual), 0) if categoria_actual in categorias else 0, key=f"edit_cat_ing_{selected_id}")
        elif tipo_edit == "Gasto":
            categorias = obtener_categorias_usuario(user_id, "Gasto")
            if categoria_actual and categoria_actual not in categorias:
                categorias = [categoria_actual] + categorias
            if not categorias:
                categorias = ["Sin categorías"]
            categoria_edit = st.selectbox("Categoría", categorias, index=max(categorias.index(categoria_actual), 0) if categoria_actual in categorias else 0, key=f"edit_cat_gas_{selected_id}")
            emocion_edit = st.selectbox(
                "Emoción",
                ["", "Tranquilidad", "Impulso", "Estrés", "Recompensa", "Urgencia", "Antojo"],
                index=(["", "Tranquilidad", "Impulso", "Estrés", "Recompensa", "Urgencia", "Antojo"].index(emocion_actual) if emocion_actual in ["", "Tranquilidad", "Impulso", "Estrés", "Recompensa", "Urgencia", "Antojo"] else 0),
                format_func=lambda x: "No registrar emoción" if x == "" else x,
                key=f"edit_emocion_{selected_id}"
            )
        elif tipo_edit == "Ingreso (Deuda)":
            categoria_edit = "Deuda"
            deuda_nombre_edit = st.text_input("Nombre del crédito", value=deuda_nombre_actual or descripcion_actual, key=f"edit_deuda_nombre_{selected_id}")
            prestamista_edit = st.text_input("Prestamista", value=prestamista_actual, key=f"edit_prestamista_{selected_id}")
            usar_fecha_limite = st.checkbox("Tiene fecha límite", value=pd.notna(fecha_limite_actual), key=f"edit_deuda_lim_toggle_{selected_id}")
            if usar_fecha_limite:
                fecha_limite_edit = st.date_input("Fecha límite", value=fecha_limite_actual.date() if pd.notna(fecha_limite_actual) else fecha_edit + timedelta(days=30), key=f"edit_fecha_lim_{selected_id}")
            else:
                fecha_limite_edit = None
        elif tipo_edit == "Cuenta por cobrar":
            categoria_edit = "Cuenta por cobrar"
            deuda_nombre_edit = st.text_input("Nombre del dinero prestado", value=deuda_nombre_actual or descripcion_actual, key=f"edit_cxc_nombre_{selected_id}")
            prestamista_edit = st.text_input("Cliente / quién debe", value=prestamista_actual, key=f"edit_cxc_cliente_{selected_id}")
            usar_fecha_limite = st.checkbox("Tiene fecha límite", value=pd.notna(fecha_limite_actual), key=f"edit_cxc_lim_toggle_{selected_id}")
            if usar_fecha_limite:
                fecha_limite_edit = st.date_input("Fecha límite", value=fecha_limite_actual.date() if pd.notna(fecha_limite_actual) else fecha_edit + timedelta(days=30), key=f"edit_cxc_fecha_lim_{selected_id}")
            else:
                fecha_limite_edit = None
        elif tipo_edit == "Cobro cuenta por cobrar":
            categoria_edit = "Cobro cuenta por cobrar"
            deuda_nombre_edit = st.text_input("Nombre del dinero prestado", value=deuda_nombre_actual or descripcion_actual, key=f"edit_cobro_cxc_nombre_{selected_id}")
            prestamista_edit = st.text_input("Cliente / quién paga", value=prestamista_actual, key=f"edit_cobro_cxc_cliente_{selected_id}")
        else:
            categoria_edit = "Pago de deuda"
            deudas_ref = df_deudas_local.copy() if df_deudas_local is not None and not df_deudas_local.empty else pd.DataFrame()
            ref_options = ["Mantener deuda actual"]
            ref_map = {}
            if not deudas_ref.empty:
                for _, deuda_row in deudas_ref.iterrows():
                    label = f"{deuda_row['nombre']} · {deuda_row['prestamista']} · pendiente {money(deuda_row['saldo_pendiente'])}"
                    ref_options.append(label)
                    ref_map[label] = deuda_row
            deuda_ref = st.selectbox("Deuda vinculada", ref_options, index=0, key=f"edit_pago_deuda_ref_{selected_id}")
            if deuda_ref != "Mantener deuda actual" and deuda_ref in ref_map:
                deuda_row = ref_map[deuda_ref]
                deuda_nombre_edit = deuda_row["nombre"]
                prestamista_edit = deuda_row["prestamista"]
                deuda_id_edit = deuda_row["id"]
                fecha_limite_edit = deuda_row["fecha_limite"].date() if pd.notna(deuda_row["fecha_limite"]) else None
            deuda_nombre_edit = st.text_input("Nombre del crédito", value=deuda_nombre_edit, key=f"edit_pago_deuda_nombre_{selected_id}")
            prestamista_edit = st.text_input("Prestamista", value=prestamista_edit, key=f"edit_pago_prestamista_{selected_id}")

        monto_edit = st.number_input("Monto", min_value=0.0, step=1000.0, value=float(monto_actual), key=f"edit_monto_{selected_id}")

        es_recurrente_edit = st.checkbox("Es recurrente", value=es_recurrente_actual, key=f"edit_recurrente_{selected_id}")
        frecuencia_edit = frecuencia_actual if frecuencia_actual in ["Semanal", "Quincenal", "Mensual"] else "Semanal"
        proxima_edit = proxima_actual.date() if pd.notna(proxima_actual) else fecha_edit + timedelta(days=7)
        fecha_fin_edit = fecha_fin_actual.date() if pd.notna(fecha_fin_actual) else proxima_edit
        recurrente_activo_edit = recurrente_activo_actual

        if es_recurrente_edit:
            frecuencia_edit = st.selectbox("Frecuencia", ["Semanal", "Quincenal", "Mensual"], index=["Semanal", "Quincenal", "Mensual"].index(frecuencia_edit), key=f"edit_freq_{selected_id}")
            proxima_edit = st.date_input("Próxima fecha", value=proxima_edit, key=f"edit_proxima_{selected_id}")
            usar_fecha_fin = st.checkbox("Definir fecha fin", value=pd.notna(fecha_fin_actual), key=f"edit_fin_toggle_{selected_id}")
            if usar_fecha_fin:
                fecha_fin_edit = st.date_input("Fecha fin", value=fecha_fin_edit, key=f"edit_fin_{selected_id}")
            else:
                fecha_fin_edit = None
            recurrente_activo_edit = st.checkbox("Mantener activa", value=recurrente_activo_actual or True, key=f"edit_recurrente_activo_{selected_id}")
        else:
            frecuencia_edit = None
            proxima_edit = None
            fecha_fin_edit = None
            recurrente_activo_edit = False

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Guardar cambios del movimiento", key=f"guardar_edicion_mov_{selected_id}", use_container_width=True, type="primary"):
                errores = []
                if tipo_edit in ("Ingreso", "Gasto") and (not categoria_edit or categoria_edit.strip() == "Sin categorías"):
                    errores.append("Necesitas una categoría válida.")
                if float(monto_edit or 0) <= 0:
                    errores.append("El monto debe ser mayor que 0.")
                if tipo_edit == "Ingreso (Deuda)" and not str(deuda_nombre_edit or "").strip():
                    errores.append("Escribe un nombre para el crédito.")
                if tipo_edit == "Ingreso (Deuda)" and not str(prestamista_edit or "").strip():
                    errores.append("Indica quién te prestó.")
                if tipo_edit == "Pago de deuda" and not str(deuda_nombre_edit or "").strip():
                    errores.append("Define el crédito al que corresponde este pago.")
                if tipo_edit == "Cuenta por cobrar" and not str(deuda_nombre_edit or "").strip():
                    errores.append("Escribe un nombre para el dinero prestado.")
                if tipo_edit == "Cuenta por cobrar" and not str(prestamista_edit or "").strip():
                    errores.append("Indica quién te debe ese dinero.")
                if tipo_edit == "Cobro cuenta por cobrar" and not str(deuda_nombre_edit or "").strip():
                    errores.append("Define el registro de dinero prestado al que corresponde este pago recibido.")
                if es_recurrente_edit and proxima_edit and proxima_edit < fecha_edit:
                    errores.append("La próxima fecha recurrente no puede ser anterior al movimiento.")
                if es_recurrente_edit and fecha_fin_edit and proxima_edit and fecha_fin_edit < proxima_edit:
                    errores.append("La fecha fin recurrente no puede ser anterior a la próxima fecha.")
                if errores:
                    for err in errores:
                        st.error(err)
                else:
                    payload = {
                        "fecha": datetime.combine(fecha_edit, datetime.min.time()).isoformat(),
                        "tipo": tipo_edit,
                        "categoria": categoria_edit.strip() if categoria_edit else None,
                        "monto": float(monto_edit),
                        "descripcion": str(descripcion_edit or "").strip(),
                        "emocion": emocion_edit if tipo_edit == "Gasto" else None,
                        "deuda_id": deuda_id_edit if tipo_edit in ("Ingreso (Deuda)", "Pago de deuda", "Cuenta por cobrar", "Cobro cuenta por cobrar") else None,
                        "deuda_nombre": str(deuda_nombre_edit or "").strip() if tipo_edit in ("Ingreso (Deuda)", "Pago de deuda", "Cuenta por cobrar", "Cobro cuenta por cobrar") else None,
                        "prestamista": str(prestamista_edit or "").strip() if tipo_edit in ("Ingreso (Deuda)", "Pago de deuda", "Cuenta por cobrar", "Cobro cuenta por cobrar") else None,
                        "fecha_limite_deuda": datetime.combine(fecha_limite_edit, datetime.min.time()).isoformat() if fecha_limite_edit and tipo_edit in ("Ingreso (Deuda)", "Pago de deuda", "Cuenta por cobrar", "Cobro cuenta por cobrar") else None,
                        "cuenta_cobrar_nombre": str(deuda_nombre_edit or "").strip() if tipo_edit in ("Cuenta por cobrar", "Cobro cuenta por cobrar") else None,
                        "cliente_cxc": str(prestamista_edit or "").strip() if tipo_edit in ("Cuenta por cobrar", "Cobro cuenta por cobrar") else None,
                        "fecha_limite_cxc": datetime.combine(fecha_limite_edit, datetime.min.time()).isoformat() if fecha_limite_edit and tipo_edit in ("Cuenta por cobrar", "Cobro cuenta por cobrar") else None,
                        "es_recurrente": bool(es_recurrente_edit),
                        "frecuencia_recurrencia": frecuencia_edit if es_recurrente_edit else None,
                        "proxima_fecha_recurrencia": datetime.combine(proxima_edit, datetime.min.time()).isoformat() if es_recurrente_edit and proxima_edit else None,
                        "fecha_fin_recurrencia": datetime.combine(fecha_fin_edit, datetime.min.time()).isoformat() if es_recurrente_edit and fecha_fin_edit else None,
                        "recurrente_activo": bool(recurrente_activo_edit) if es_recurrente_edit else False
                    }
                    try:
                        actualizar_movimiento_seguro(selected_id, payload)
                        df_nuevo = obtener_movimientos(user_id)
                        recalcular_deudas_usuario_desde_movimientos(user_id, df_nuevo, obtener_deudas_usuario(user_id))
                        registrar_evento_producto("movement_updated", user_id=user_id, pagina="Análisis", detalle=f"{tipo_edit} · {categoria_edit}", valor=float(monto_edit))
                        st.session_state["zentix_editor_mode"] = "edit"
                        st.session_state["zentix_open_editor"] = False
                        st.success("Movimiento actualizado correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"No pude actualizar el movimiento: {e}")
        with c2:
            confirmar_default = True if modo_editor == "delete" else False
            confirmar = st.checkbox("Confirmo que quiero eliminar este movimiento", value=confirmar_default, key=f"confirm_delete_mov_{selected_id}")
            if st.button("Eliminar movimiento", key=f"eliminar_mov_{selected_id}", use_container_width=True, type="secondary"):
                if not confirmar:
                    st.error("Activa la confirmación para eliminar este movimiento.")
                else:
                    try:
                        eliminar_movimiento_seguro(selected_id)
                        df_nuevo = obtener_movimientos(user_id)
                        recalcular_deudas_usuario_desde_movimientos(user_id, df_nuevo, obtener_deudas_usuario(user_id))
                        registrar_evento_producto("movement_deleted", user_id=user_id, pagina="Análisis", detalle=str(selected_id))
                        st.session_state["zentix_selected_movimiento_id"] = None
                        st.session_state["zentix_editor_mode"] = "edit"
                        st.session_state["zentix_open_editor"] = False
                        st.success("Movimiento eliminado correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"No pude eliminar el movimiento: {e}")
def sincronizar_deudas_desde_movimientos(user_id, df_movs, df_deudas_actuales):
    if df_movs is None or df_movs.empty:
        return df_deudas_actuales if df_deudas_actuales is not None else pd.DataFrame()

    df_base = df_movs.copy()
    for col in ["deuda_nombre", "prestamista", "descripcion", "fecha_limite_deuda", "deuda_id", "fecha", "monto", "tipo"]:
        if col not in df_base.columns:
            df_base[col] = None

    ingresos_deuda = df_base[df_base["tipo"] == "Ingreso (Deuda)"].copy()
    if ingresos_deuda.empty:
        return df_deudas_actuales if df_deudas_actuales is not None else pd.DataFrame()

    pagos_deuda = df_base[df_base["tipo"] == "Pago de deuda"].copy()

    def build_key(nombre, prestamista):
        return f"{str(nombre or '').strip().lower()}||{str(prestamista or '').strip().lower()}"

    ingresos_deuda["deuda_key"] = ingresos_deuda.apply(
        lambda row: build_key(row.get("deuda_nombre") or row.get("descripcion") or "Deuda sin nombre", row.get("prestamista") or "Sin prestamista"),
        axis=1
    )

    if not pagos_deuda.empty:
        pagos_deuda["deuda_key"] = pagos_deuda.apply(
            lambda row: build_key(row.get("deuda_nombre") or row.get("descripcion") or "Deuda sin nombre", row.get("prestamista") or "Sin prestamista"),
            axis=1
        )
        pagos_por_key = pagos_deuda.groupby("deuda_key", dropna=False)["monto"].sum().to_dict()
    else:
        pagos_por_key = {}

    existentes = df_deudas_actuales.copy() if df_deudas_actuales is not None and not df_deudas_actuales.empty else pd.DataFrame()
    keys_existentes = set()
    if not existentes.empty:
        existentes["deuda_key"] = existentes.apply(lambda row: build_key(row.get("nombre"), row.get("prestamista")), axis=1)
        keys_existentes = set(existentes["deuda_key"].tolist())

    se_creo = False
    for deuda_key, grupo in ingresos_deuda.groupby("deuda_key", dropna=False):
        if deuda_key in keys_existentes:
            continue

        grupo = grupo.sort_values("fecha")
        primera = grupo.iloc[0]
        monto_total = float(pd.to_numeric(grupo["monto"], errors="coerce").fillna(0).sum())
        total_pagado = float(pagos_por_key.get(deuda_key, 0) or 0)
        saldo_pendiente = max(monto_total - total_pagado, 0)

        fechas_lim = pd.to_datetime(grupo["fecha_limite_deuda"], errors="coerce")
        fecha_limite_val = fechas_lim.dropna().iloc[0] if not fechas_lim.dropna().empty else None
        fecha_base = pd.to_datetime(primera.get("fecha"), errors="coerce")

        payload = {
            "usuario_id": user_id,
            "nombre": (primera.get("deuda_nombre") or primera.get("descripcion") or "Deuda sin nombre").strip(),
            "prestamista": (primera.get("prestamista") or "Sin prestamista").strip(),
            "monto_total": monto_total,
            "saldo_pendiente": saldo_pendiente,
            "fecha": fecha_base.isoformat() if pd.notna(fecha_base) else datetime.now().isoformat(),
            "fecha_limite": fecha_limite_val.isoformat() if pd.notna(fecha_limite_val) else None,
            "descripcion": (primera.get("descripcion") or "").strip(),
            "estado": "pagada" if saldo_pendiente <= 0 else "activa",
            "actualizado_en": datetime.now().isoformat()
        }
        creada = crear_deuda_segura(payload)
        if creada and isinstance(creada, dict) and creada.get("id"):
            se_creo = True

    if se_creo:
        return obtener_deudas_usuario(user_id)
    return df_deudas_actuales if df_deudas_actuales is not None else pd.DataFrame()
def obtener_categorias_favoritas(df_base, limite=4):
    if df_base is None or df_base.empty or "categoria" not in df_base.columns:
        return []

    df_tmp = df_base.copy()
    df_tmp["categoria"] = df_tmp["categoria"].fillna("").astype(str).str.strip()
    df_tmp = df_tmp[df_tmp["categoria"] != ""]
    if df_tmp.empty:
        return []

    favoritos = (
        df_tmp["categoria"]
        .value_counts()
        .head(limite)
        .index
        .tolist()
    )
    return favoritos


def estimar_aporte_semanal_meta(df_base):
    if df_base is None or df_base.empty or "fecha" not in df_base.columns:
        return 0.0

    df_tmp = df_base.copy()
    df_tmp["fecha"] = pd.to_datetime(df_tmp["fecha"], errors="coerce", utc=True)
    df_tmp = df_tmp.dropna(subset=["fecha"]).copy()

    if df_tmp.empty:
        return 0.0

    try:
        df_tmp["fecha"] = df_tmp["fecha"].dt.tz_convert(None)
    except Exception:
        try:
            df_tmp["fecha"] = df_tmp["fecha"].dt.tz_localize(None)
        except Exception:
            pass

    df_tmp["fecha"] = pd.to_datetime(df_tmp["fecha"], errors="coerce")
    df_tmp = df_tmp.dropna(subset=["fecha"]).copy()

    if df_tmp.empty:
        return 0.0

    df_tmp["fecha"] = df_tmp["fecha"].dt.normalize()
    hoy = pd.Timestamp.now().normalize()
    inicio = hoy - pd.Timedelta(days=27)
    reciente = df_tmp.loc[df_tmp["fecha"] >= inicio].copy()

    if reciente.empty:
        reciente = df_tmp.copy()

    ingresos_reales = reciente.loc[reciente["tipo"].isin(["Ingreso", "Cobro cuenta por cobrar"]), "monto"].sum()
    gastos_operativos = reciente.loc[reciente["tipo"] == "Gasto", "monto"].sum()
    pagos_deuda = reciente.loc[reciente["tipo"] == "Pago de deuda", "monto"].sum()

    aporte = float((ingresos_reales - gastos_operativos - pagos_deuda) / 4.0)
    return max(aporte, 0.0)


def calcular_proyeccion_meta(meta_objetivo, ahorro_actual, aporte_semanal):
    meta_objetivo = float(meta_objetivo or 0)
    ahorro_actual = float(max(ahorro_actual, 0))
    aporte_semanal = float(max(aporte_semanal, 0))

    if meta_objetivo <= 0:
        return {
            "aporte_semanal": aporte_semanal,
            "semanas": None,
            "fecha_estimada": None,
            "mensaje": "Define una meta y Zentix estimará un ritmo de llegada."
        }

    faltante = max(meta_objetivo - ahorro_actual, 0)
    if faltante <= 0:
        return {
            "aporte_semanal": aporte_semanal,
            "semanas": 0,
            "fecha_estimada": date.today(),
            "mensaje": "Con tu disponible actual ya alcanzaste esta meta."
        }

    if aporte_semanal <= 0:
        return {
            "aporte_semanal": 0.0,
            "semanas": None,
            "fecha_estimada": None,
            "mensaje": "Aún no hay un ritmo semanal positivo suficiente para estimar llegada."
        }

    semanas = int((faltante + aporte_semanal - 1) // aporte_semanal)
    fecha_estimada = date.today() + timedelta(days=semanas * 7)

    return {
        "aporte_semanal": aporte_semanal,
        "semanas": semanas,
        "fecha_estimada": fecha_estimada,
        "mensaje": f"Si ahorras {money(aporte_semanal)} por semana, llegas en ~{semanas} semana(s), hacia {fecha_estimada.strftime('%Y-%m-%d')}."
    }


def construir_resumen_recordatorios(df_base, preferencias):
    dias_inactividad = None
    ultimo_mov = None

    if df_base is not None and not df_base.empty and "fecha" in df_base.columns:
        df_tmp = df_base.copy()
        df_tmp["fecha"] = pd.to_datetime(df_tmp["fecha"], errors="coerce")
        df_tmp = df_tmp.dropna(subset=["fecha"]).copy()
        if not df_tmp.empty:
            ultimo_mov = df_tmp["fecha"].max().date()
            dias_inactividad = (date.today() - ultimo_mov).days

    umbral = 4 if preferencias.get("frecuencia_recordatorios") == "normal" else 5
    sugerencia = "Sin envíos pendientes."
    if preferencias.get("recordatorio_email") and preferencias.get("recordatorio_registro"):
        if dias_inactividad is None:
            sugerencia = "Cuando empieces a registrar, Zentix podrá medir inactividad y sugerir recordatorios suaves."
        elif dias_inactividad >= umbral:
            sugerencia = f"Ya podrías disparar un recordatorio suave por inactividad ({dias_inactividad} días sin registrar)."
        else:
            sugerencia = f"No hace falta recordar todavía. Llevas {dias_inactividad} día(s) desde tu último registro."

    return {
        "ultimo_movimiento": ultimo_mov.isoformat() if ultimo_mov else "Sin movimientos",
        "dias_inactividad": dias_inactividad,
        "umbral": umbral,
        "sugerencia": sugerencia
    }


def obtener_movimientos_periodo(df_base, periodicidad="Mensual", fecha_referencia=None):
    if df_base is None or df_base.empty or "fecha" not in df_base.columns:
        return pd.DataFrame(), None, None

    df_tmp = df_base.copy()
    df_tmp["fecha"] = pd.to_datetime(df_tmp["fecha"], errors="coerce")
    df_tmp = df_tmp.dropna(subset=["fecha"]).copy()
    if df_tmp.empty:
        return pd.DataFrame(), None, None

    try:
        if getattr(df_tmp["fecha"].dt, "tz", None) is not None:
            df_tmp["fecha"] = df_tmp["fecha"].dt.tz_localize(None)
    except Exception:
        pass

    fecha_ref = pd.Timestamp(fecha_referencia or date.today()).normalize()
    if str(periodicidad).strip().lower().startswith("sem"):
        inicio = fecha_ref - pd.Timedelta(days=fecha_ref.weekday())
        fin = inicio + pd.Timedelta(days=6)
        etiqueta = "Semanal"
    else:
        inicio = fecha_ref.replace(day=1)
        fin = (inicio + pd.offsets.MonthEnd(0)).normalize()
        etiqueta = "Mensual"

    df_tmp["fecha"] = df_tmp["fecha"].dt.normalize()
    filtrado = df_tmp[(df_tmp["fecha"] >= inicio) & (df_tmp["fecha"] <= fin)].copy()
    filtrado = filtrado.sort_values(["fecha", "tipo"], ascending=[False, True])
    filtrado.attrs["periodicidad"] = etiqueta
    return filtrado, inicio.date(), fin.date()


def resumir_periodo_movimientos(df_periodo):
    if df_periodo is None or df_periodo.empty:
        return {
            "conteo": 0,
            "ingresos": 0.0,
            "gastos": 0.0,
            "ingresos_deuda": 0.0,
            "pagos_deuda": 0.0,
            "balance": 0.0,
            "categoria_top": "Sin movimientos",
            "monto_categoria_top": 0.0
        }

    ingresos = float(df_periodo[df_periodo["tipo"].isin(["Ingreso", "Cobro cuenta por cobrar"])]["monto"].sum())
    gastos = float(df_periodo[df_periodo["tipo"] == "Gasto"]["monto"].sum())
    ingresos_deuda = float(df_periodo[df_periodo["tipo"] == "Ingreso (Deuda)"]["monto"].sum())
    pagos_deuda = float(df_periodo[df_periodo["tipo"] == "Pago de deuda"]["monto"].sum())
    balance = ingresos + ingresos_deuda - gastos - pagos_deuda

    resumen_cat = (
        df_periodo.groupby("categoria", dropna=False)["monto"]
        .sum()
        .sort_values(ascending=False)
    )
    categoria_top = resumen_cat.index[0] if not resumen_cat.empty else "Sin categoría"
    monto_categoria_top = float(resumen_cat.iloc[0]) if not resumen_cat.empty else 0.0

    return {
        "conteo": int(len(df_periodo.index)),
        "ingresos": ingresos,
        "gastos": gastos,
        "ingresos_deuda": ingresos_deuda,
        "pagos_deuda": pagos_deuda,
        "balance": balance,
        "categoria_top": str(categoria_top or "Sin categoría"),
        "monto_categoria_top": monto_categoria_top
    }




def obtener_modo_dashboard():
    key = "zentix_dashboard_mode"
    if key not in st.session_state:
        st.session_state[key] = "Personal"
    return st.session_state[key]


def clasificar_estado_cxc_fila(row):
    saldo = float(pd.to_numeric(row.get("saldo_pendiente", 0), errors="coerce") or 0)
    total = float(pd.to_numeric(row.get("monto_total", 0), errors="coerce") or 0)
    fecha_limite = pd.to_datetime(row.get("fecha_limite"), errors="coerce")
    hoy = pd.Timestamp(date.today())

    if saldo <= 0:
        return "Cobrada total"
    if total > 0 and saldo < total:
        if pd.notna(fecha_limite) and fecha_limite.normalize() < hoy.normalize():
            return "Vencida parcial"
        return "Cobrada parcial"
    if pd.notna(fecha_limite) and fecha_limite.normalize() < hoy.normalize():
        return "Vencida"
    return "Activa"


def construir_resumen_cxc_dashboard(df_cxc_local):
    if df_cxc_local is None or df_cxc_local.empty:
        return {
            "pendiente_total": 0.0,
            "activas": 0,
            "vencidas": 0,
            "cobradas_parcial": 0,
            "cobradas_total": 0,
            "tabla": pd.DataFrame(columns=["nombre", "cliente", "saldo_pendiente", "monto_total", "fecha_limite", "estado_dashboard"])
        }

    df_tmp = df_cxc_local.copy()
    df_tmp["monto_total"] = pd.to_numeric(df_tmp.get("monto_total"), errors="coerce").fillna(0)
    df_tmp["saldo_pendiente"] = pd.to_numeric(df_tmp.get("saldo_pendiente"), errors="coerce").fillna(0)
    if "fecha_limite" in df_tmp.columns:
        df_tmp["fecha_limite"] = pd.to_datetime(df_tmp["fecha_limite"], errors="coerce")
    else:
        df_tmp["fecha_limite"] = pd.NaT
    df_tmp["estado_dashboard"] = df_tmp.apply(clasificar_estado_cxc_fila, axis=1)

    return {
        "pendiente_total": float(df_tmp["saldo_pendiente"].sum()),
        "activas": int((df_tmp["estado_dashboard"] == "Activa").sum()),
        "vencidas": int(df_tmp["estado_dashboard"].isin(["Vencida", "Vencida parcial"]).sum()),
        "cobradas_parcial": int((df_tmp["estado_dashboard"] == "Cobrada parcial").sum()),
        "cobradas_total": int((df_tmp["estado_dashboard"] == "Cobrada total").sum()),
        "tabla": df_tmp.sort_values(["saldo_pendiente", "fecha_limite"], ascending=[False, True]).copy()
    }


def construir_alertas_dashboard_pro(df_base, df_mes_actual, df_cxc_local, meta_actual, ahorro_actual):
    alertas = []
    if df_mes_actual is not None and not df_mes_actual.empty:
        gastos_mes = df_mes_actual[df_mes_actual["tipo"] == "Gasto"].copy()
        if not gastos_mes.empty:
            top_gasto = (
                gastos_mes.groupby("categoria", dropna=False)["monto"]
                .sum()
                .sort_values(ascending=False)
            )
            if not top_gasto.empty:
                cat = str(top_gasto.index[0] or "Sin categoría")
                monto_cat = float(top_gasto.iloc[0] or 0)
                share = (monto_cat / float(gastos_mes["monto"].sum() or 1)) if float(gastos_mes["monto"].sum() or 0) > 0 else 0
                if share >= 0.45:
                    alertas.append(f"Ojo: {cat} ya representa {round(share * 100, 1)}% de tus gastos del mes.")

        if meta_actual and float(meta_actual or 0) > 0 and float(ahorro_actual or 0) < float(meta_actual or 0) * 0.35:
            alertas.append("Si sigues así, podrías quedar corto frente a tu meta de ahorro actual.")

    resumen_cxc = construir_resumen_cxc_dashboard(df_cxc_local)
    if resumen_cxc["vencidas"] > 0:
        alertas.append(f"Tienes {resumen_cxc['vencidas']} cuenta(s) por cobrar vencida(s). Conviene gestionarlas primero.")

    if df_base is not None and not df_base.empty and "fecha" in df_base.columns:
        df_tmp = df_base.copy()
        df_tmp["fecha"] = pd.to_datetime(df_tmp["fecha"], errors="coerce", utc=True)
        df_tmp = df_tmp.dropna(subset=["fecha"]).copy()

        if not df_tmp.empty:
            try:
                df_tmp["fecha"] = df_tmp["fecha"].dt.tz_convert(None)
            except Exception:
                try:
                    df_tmp["fecha"] = df_tmp["fecha"].dt.tz_localize(None)
                except Exception:
                    pass

            df_tmp["fecha"] = pd.to_datetime(df_tmp["fecha"], errors="coerce")
            df_tmp = df_tmp.dropna(subset=["fecha"]).copy()

        if not df_tmp.empty:
            df_tmp["fecha_norm"] = df_tmp["fecha"].dt.normalize()
            hoy = pd.Timestamp(date.today()).normalize()
            inicio_semana = hoy - pd.Timedelta(days=hoy.weekday())
            inicio_semana_prev = inicio_semana - pd.Timedelta(days=7)
            fin_semana_prev = inicio_semana - pd.Timedelta(days=1)

            actual = df_tmp[(df_tmp["fecha_norm"] >= inicio_semana) & (df_tmp["fecha_norm"] <= hoy)]
            previa = df_tmp[(df_tmp["fecha_norm"] >= inicio_semana_prev) & (df_tmp["fecha_norm"] <= fin_semana_prev)]

            gasto_actual = float(actual[actual["tipo"] == "Gasto"]["monto"].sum()) if not actual.empty else 0.0
            gasto_previo = float(previa[previa["tipo"] == "Gasto"]["monto"].sum()) if not previa.empty else 0.0

            if gasto_previo > 0:
                cambio = ((gasto_actual - gasto_previo) / gasto_previo) * 100
                if cambio >= 25:
                    alertas.append(f"Tu gasto de esta semana subió {round(cambio, 1)}% frente a la semana pasada.")

    if not alertas:
        alertas.append("Tu panel está estable. Sigue registrando para que Zentix detecte alertas más finas.")
    return alertas[:4]


def construir_timeline_bancario(df_base, limite=12):
    if df_base is None or df_base.empty:
        return []

    df_tmp = df_base.copy()
    for col in ["fecha", "tipo", "categoria", "descripcion", "monto"]:
        if col not in df_tmp.columns:
            df_tmp[col] = None

    df_tmp["fecha"] = pd.to_datetime(df_tmp["fecha"], errors="coerce", utc=True)
    df_tmp = df_tmp.dropna(subset=["fecha"]).copy()

    if df_tmp.empty:
        return []

    try:
        df_tmp["fecha"] = df_tmp["fecha"].dt.tz_convert(None)
    except Exception:
        try:
            df_tmp["fecha"] = df_tmp["fecha"].dt.tz_localize(None)
        except Exception:
            pass

    df_tmp["fecha"] = pd.to_datetime(df_tmp["fecha"], errors="coerce")
    df_tmp["monto"] = pd.to_numeric(df_tmp["monto"], errors="coerce").fillna(0)
    df_tmp = df_tmp.dropna(subset=["fecha"]).sort_values("fecha", ascending=False).head(limite).copy()

    if df_tmp.empty:
        return []

    hoy = pd.Timestamp(date.today()).normalize()
    agrupado = []

    for _, row in df_tmp.iterrows():
        fecha_norm = pd.Timestamp(row["fecha"]).normalize()
        diff = int((hoy - fecha_norm).days)
        if diff == 0:
            grupo = "Hoy"
        elif diff == 1:
            grupo = "Ayer"
        else:
            grupo = f"Hace {diff} días"

        tipo = str(row.get("tipo") or "")
        monto = float(row.get("monto") or 0)
        signo = "+" if tipo in ["Ingreso", "Cobro cuenta por cobrar", "Ingreso (Deuda)"] else "-"
        color = "#4ADE80" if tipo in ["Ingreso", "Cobro cuenta por cobrar"] else "#93C5FD" if tipo == "Ingreso (Deuda)" else "#F87171" if tipo == "Gasto" else "#FCD34D" if tipo == "Pago de deuda" else "#C4B5FD"
        titulo = str(row.get("descripcion") or row.get("categoria") or tipo or "Movimiento").strip()
        subtitulo = str(row.get("categoria") or tipo or "").strip()
        agrupado.append({
            "grupo": grupo,
            "fecha": row["fecha"],
            "titulo": titulo,
            "subtitulo": subtitulo,
            "tipo": tipo,
            "monto_txt": f"{signo}{money(monto)}",
            "color": color
        })

    return agrupado


def construir_asesor_dashboard(nombre, modo_dashboard, total_ingresos_local, total_gastos_local, saldo_caja_real, saldo_cxc_pendiente, saldo_deuda_pendiente, df_mes_actual, df_cxc_local):
    mensajes = []

    if saldo_cxc_pendiente > max(float(total_ingresos_local or 0) * 0.35, 1):
        mensajes.append(f"{nombre}, tienes una porción importante de tu flujo atrapada en cuentas por cobrar. Conviene cobrar antes de asumir que esa plata ya está disponible.")

    if float(total_gastos_local or 0) > float(total_ingresos_local or 0) and float(total_ingresos_local or 0) > 0:
        mensajes.append("Tus gastos del mes están por encima de tus ingresos reales. La prioridad es frenar fuga antes de expandir metas.")
    elif float(total_ingresos_local or 0) > 0:
        mensajes.append("Tus ingresos reales ya sostienen el mes. El foco ahora es mejorar calidad de caja y no mezclar cobros pendientes con dinero disponible.")

    if saldo_deuda_pendiente > 0:
        mensajes.append(f"Todavía cargas {money(saldo_deuda_pendiente)} en deuda pendiente. Mantenerla visible evita sobreestimar tu caja real.")

    if df_mes_actual is not None and not df_mes_actual.empty:
        gastos_mes = df_mes_actual[df_mes_actual["tipo"] == "Gasto"].copy()
        if not gastos_mes.empty:
            top = gastos_mes.groupby("categoria", dropna=False)["monto"].sum().sort_values(ascending=False)
            if not top.empty:
                mensajes.append(f"Este mes estás gastando más en {top.index[0]} que en otras categorías. Ahí está tu principal palanca de ajuste.")

    resumen_cxc = construir_resumen_cxc_dashboard(df_cxc_local)
    if resumen_cxc["vencidas"] > 0:
        mensajes.append(f"Te conviene cobrar primero las {resumen_cxc['vencidas']} cuenta(s) vencida(s); esa acción mejora caja sin recortar operación.")
    elif resumen_cxc["activas"] > 0:
        mensajes.append(f"Tienes {resumen_cxc['activas']} cuenta(s) por cobrar activas. Buenas ventas, pero aún no son caja real.")

    if modo_dashboard == "Negocio":
        mensajes.append("Modo negocio activo: aquí importa más flujo real, cartera por cobrar y presión operativa que solo el ahorro personal.")
    else:
        mensajes.append("Modo personal activo: Zentix prioriza claridad de caja, control de gasto y avance hacia tus metas.")

    mensajes = [m for m in mensajes if m]
    return mensajes[:4]


def render_dashboard_pro(nombre, df_base, df_mes_actual, df_cxc_local, total_ingresos_local, total_gastos_local,
                         entradas_deuda_local, pagos_deuda_local, saldo_deuda_pendiente, meta_objetivo, ahorro_actual):
    modo = obtener_modo_dashboard()
    resumen_cxc = construir_resumen_cxc_dashboard(df_cxc_local)
    saldo_caja_real = float(total_ingresos_local or 0) - float(total_gastos_local or 0) - float(pagos_deuda_local or 0)
    flujo_neto_real = float(total_ingresos_local or 0) - float(total_gastos_local or 0)
    alertas_dashboard = construir_alertas_dashboard_pro(df_base, df_mes_actual, df_cxc_local, meta_objetivo, ahorro_actual)
    timeline = construir_timeline_bancario(df_base, limite=12)
    mensajes_asesor = construir_asesor_dashboard(
        nombre, modo, total_ingresos_local, total_gastos_local, saldo_caja_real,
        resumen_cxc["pendiente_total"], saldo_deuda_pendiente, df_mes_actual, df_cxc_local
    )

    section_header("Dashboard pro", "Dinero real vs dinero proyectado, alertas, cartera y lectura ejecutiva en una sola vista.")

    st.radio(
        "Modo del dashboard",
        ["Personal", "Negocio"],
        horizontal=True,
        key="zentix_dashboard_mode",
        label_visibility="visible"
    )

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        kpi_card("Dinero en caja real", money(saldo_caja_real), "Ingreso real - gasto - pagos de deuda", "balance")
    with p2:
        kpi_card("Por cobrar", money(resumen_cxc["pendiente_total"]), f"Activas: {resumen_cxc['activas']} · Vencidas: {resumen_cxc['vencidas']}", "saving")
    with p3:
        kpi_card("Deuda pendiente", money(saldo_deuda_pendiente), f"Entradas por deuda: {money(entradas_deuda_local)}", "balance")
    with p4:
        kpi_card("Flujo neto real", money(flujo_neto_real), "Ingresos reales - gastos operativos", "income" if flujo_neto_real >= 0 else "expense")

    q1, q2, q3, q4 = st.columns(4)
    with q1:
        render_spotlight_metric("Cobradas total", str(resumen_cxc["cobradas_total"]), "Cuentas totalmente resueltas")
    with q2:
        render_spotlight_metric("Cobradas parcial", str(resumen_cxc["cobradas_parcial"]), "Abonos ya realizados")
    with q3:
        render_spotlight_metric("Vencidas", str(resumen_cxc["vencidas"]), "Requieren seguimiento")
    with q4:
        render_spotlight_metric("Modo activo", modo, "Personal o negocio")

    col_left, col_right = st.columns([1.12, 0.88])

    with col_left:
        st.markdown(
            """
            <div class="soft-card">
                <div class="section-title">Alertas inteligentes</div>
                <div class="section-caption">Zentix te habla como asesor, no solo como registro.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        render_list_card("Alertas del momento", alertas_dashboard, "Acciones concretas para cuidar caja, cartera y meta.")

        st.markdown(
            """
            <div class="soft-card">
                <div class="section-title">Timeline premium</div>
                <div class="section-caption">Historial reciente con lectura natural, tipo banco.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if timeline:
            grupos = []
            actual = None
            for item in timeline:
                if actual != item["grupo"]:
                    if actual is not None:
                        grupos.append("</div>")
                    grupos.append(f"<div class='premium-list-card'><div class='premium-list-head'><div class='premium-list-title'>{item['grupo']}</div><div class='premium-list-badge'>{item['fecha'].strftime('%Y-%m-%d')}</div></div>")
                    actual = item["grupo"]
                grupos.append(
                    f"<div style='display:flex;justify-content:space-between;gap:1rem;padding:0.55rem 0;border-bottom:1px solid rgba(148,163,184,0.10);'>"
                    f"<div><div style='font-weight:800;color:#F8FAFC;'>{item['titulo']}</div><div class='tiny-muted'>{item['subtitulo']} · {item['tipo']}</div></div>"
                    f"<div style='font-weight:900;color:{item['color']};white-space:nowrap;'>{item['monto_txt']}</div></div>"
                )
            grupos.append("</div>")
            st.markdown("".join(grupos), unsafe_allow_html=True)
        else:
            empty_state("Sin timeline todavía", "Cuando tengas movimientos recientes, aquí aparecerá una lectura tipo banco más natural y premium.")

    with col_right:
        st.markdown(
            """
            <div class="assistant-card">
                <div class="assistant-title">Zentix asesor</div>
                <div class="assistant-text">Lectura breve, accionable y con criterio de caja real.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        render_list_card("Qué te diría Zentix hoy", mensajes_asesor, "Interpretación premium para decidir mejor.")

        tabla = resumen_cxc["tabla"]
        st.markdown(
            """
            <div class="soft-card">
                <div class="section-title">Estados de cuentas por cobrar</div>
                <div class="section-caption">Verde = cobrada, amarillo = pendiente/parcial, rojo = vencida.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if tabla is not None and not tabla.empty:
            df_show = tabla[["nombre", "cliente", "saldo_pendiente", "monto_total", "fecha_limite", "estado_dashboard"]].copy()
            df_show["fecha_limite"] = pd.to_datetime(df_show["fecha_limite"], errors="coerce").dt.strftime("%Y-%m-%d")
            df_show["fecha_limite"] = df_show["fecha_limite"].fillna("—")
            df_show["saldo_pendiente"] = df_show["saldo_pendiente"].apply(money)
            df_show["monto_total"] = df_show["monto_total"].apply(money)
            st.dataframe(
                df_show.rename(columns={
                    "nombre": "Cuenta",
                    "cliente": "Cliente",
                    "saldo_pendiente": "Pendiente",
                    "monto_total": "Total",
                    "fecha_limite": "Vence",
                    "estado_dashboard": "Estado"
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            empty_state("Sin cartera activa", "Cuando registres cuentas por cobrar, aquí aparecerá su estado comercial.")


def _draw_footer_report(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(colors.HexColor("#94A3B8") if REPORTLAB_AVAILABLE else None)
    canvas_obj.drawString(doc.leftMargin, 10 * mm, "ZENTIX Intelligence · Reporte premium")
    canvas_obj.drawRightString(A4[0] - doc.rightMargin, 10 * mm, f"Pagina {canvas_obj.getPageNumber()}")
    canvas_obj.restoreState()


def _try_reportlab_image(path_obj, width_mm=22, height_mm=None):
    if not REPORTLAB_AVAILABLE:
        return None
    try:
        if not path_obj or not Path(path_obj).exists():
            return None
        img = Image(str(path_obj))
        img.drawWidth = width_mm * mm
        img.drawHeight = (height_mm * mm) if height_mm else (width_mm * mm)
        return img
    except Exception:
        return None


def construir_resumen_ejecutivo_reporte(df_periodo, resumen_periodo):
    lines = []
    balance = float(resumen_periodo.get("balance", 0) or 0)
    ingresos = float(resumen_periodo.get("ingresos", 0) or 0)
    gastos = float(resumen_periodo.get("gastos", 0) or 0)
    top_cat = str(resumen_periodo.get("categoria_top", "Sin categoría") or "Sin categoría")
    top_monto = float(resumen_periodo.get("monto_categoria_top", 0) or 0)

    if balance >= 0:
        lines.append(f"El periodo cerró con balance positivo de {money(balance)}.")
    else:
        lines.append(f"El periodo cerró con presión de caja de {money(balance)}.")
    if ingresos > 0 or gastos > 0:
        lines.append(f"Ingresos reales {money(ingresos)} frente a gastos operativos de {money(gastos)}.")
    if top_monto > 0:
        lines.append(f"La categoría con mayor peso fue {top_cat} con {money(top_monto)}.")
    if df_periodo is not None and not df_periodo.empty and "tipo" in df_periodo.columns:
        deuda_in = float(df_periodo[df_periodo["tipo"] == "Ingreso (Deuda)"]["monto"].sum() or 0)
        deuda_out = float(df_periodo[df_periodo["tipo"] == "Pago de deuda"]["monto"].sum() or 0)
        if deuda_in > 0 or deuda_out > 0:
            lines.append(f"Los flujos de deuda se mantuvieron visibles por separado: {money(deuda_in)} recibidos y {money(deuda_out)} devueltos.")
    if not lines:
        lines.append("No hubo suficientes movimientos para una lectura ejecutiva más profunda.")
    return lines[:4]


def generar_pdf_reporte_premium(nombre_usuario, plan_nombre, periodicidad, inicio, fin, df_periodo, resumen_periodo):
    if not REPORTLAB_AVAILABLE:
        return None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Reporte premium Zentix"
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ZentixTitle", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=colors.HexColor("#F8FAFC"), spaceAfter=8))
    styles.add(ParagraphStyle(name="ZentixSub", parent=styles["BodyText"], fontName="Helvetica", fontSize=10.5, leading=15, textColor=colors.HexColor("#CBD5E1"), spaceAfter=10))
    styles.add(ParagraphStyle(name="ZentixSection", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12.5, leading=15, textColor=colors.HexColor("#0F172A"), spaceAfter=6))
    styles.add(ParagraphStyle(name="ZentixBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=14, textColor=colors.HexColor("#334155")))
    styles.add(ParagraphStyle(name="ZentixSmall", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.5, leading=12, textColor=colors.HexColor("#475569")))
    styles.add(ParagraphStyle(name="ZentixHeroLight", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=colors.HexColor("#DBEAFE")))
    styles.add(ParagraphStyle(name="ZentixSignature", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=10.5, leading=14, textColor=colors.HexColor("#1D4ED8")))

    logo = _try_reportlab_image(icono_path if icono_path.exists() else None, width_mm=22, height_mm=22)
    avatar = _try_reportlab_image(avatar_path if avatar_path.exists() else None, width_mm=16, height_mm=16)

    story = []

    left_cell = []
    if logo:
        left_cell.append(logo)
        left_cell.append(Spacer(1, 4))
    left_cell.append(Paragraph("ZENTIX", styles["ZentixTitle"]))
    left_cell.append(Paragraph("Tu centro financiero, claro y visualmente fuerte.", styles["ZentixHeroLight"]))

    right_html = (
        f"<b>Reporte {periodicidad}</b><br/>{inicio.strftime('%Y-%m-%d')} al {fin.strftime('%Y-%m-%d')}<br/>"
        f"{html.escape(str(nombre_usuario))} · Plan {html.escape(str(plan_nombre))}<br/>"
        f"Preparado por Zentix Intelligence"
    )
    hero = Table([[left_cell, Paragraph(right_html, styles["ZentixSub"])]], colWidths=[62 * mm, 104 * mm])
    hero.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0F172A")),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#1D4ED8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.append(hero)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Resumen ejecutivo", styles["ZentixSection"]))
    ejecutivo = construir_resumen_ejecutivo_reporte(df_periodo, resumen_periodo)
    ejecutivo_html = "".join([f"<li>{html.escape(line)}</li>" for line in ejecutivo])
    ejecutivo_box = Table([[Paragraph(f"<ul>{ejecutivo_html}</ul>", styles["ZentixBody"])]], colWidths=[166 * mm])
    ejecutivo_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#DBEAFE")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(ejecutivo_box)
    story.append(Spacer(1, 10))

    resumen_data = [
        [Paragraph("Movimientos", styles["ZentixSmall"]), Paragraph("Ingresos reales", styles["ZentixSmall"]), Paragraph("Gastos", styles["ZentixSmall"]), Paragraph("Balance", styles["ZentixSmall"])],
        [Paragraph(str(resumen_periodo.get("conteo", 0)), styles["ZentixBody"]), Paragraph(money(resumen_periodo.get("ingresos", 0)), styles["ZentixBody"]), Paragraph(money(resumen_periodo.get("gastos", 0)), styles["ZentixBody"]), Paragraph(money(resumen_periodo.get("balance", 0)), styles["ZentixBody"])],
        [Paragraph("Ingreso deuda", styles["ZentixSmall"]), Paragraph("Pago deuda", styles["ZentixSmall"]), Paragraph("Categoria top", styles["ZentixSmall"]), Paragraph("Monto top", styles["ZentixSmall"])],
        [Paragraph(money(resumen_periodo.get("ingresos_deuda", 0)), styles["ZentixBody"]), Paragraph(money(resumen_periodo.get("pagos_deuda", 0)), styles["ZentixBody"]), Paragraph(str(resumen_periodo.get("categoria_top", "Sin datos")), styles["ZentixBody"]), Paragraph(money(resumen_periodo.get("monto_categoria_top", 0)), styles["ZentixBody"])],
    ]
    resumen_table = Table(resumen_data, colWidths=[40 * mm, 40 * mm, 50 * mm, 36 * mm])
    resumen_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DBEAFE")),
        ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#EDE9FE")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#E2E8F0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(resumen_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Detalle de movimientos", styles["ZentixSection"]))
    rows = [[
        Paragraph("Fecha", styles["ZentixSmall"]),
        Paragraph("Tipo", styles["ZentixSmall"]),
        Paragraph("Categoria", styles["ZentixSmall"]),
        Paragraph("Monto", styles["ZentixSmall"]),
        Paragraph("Descripcion", styles["ZentixSmall"]),
    ]]

    if df_periodo is None or df_periodo.empty:
        rows.append([Paragraph("Sin movimientos en el periodo", styles["ZentixBody"]), "", "", "", ""])
    else:
        vista = df_periodo.copy().sort_values("fecha", ascending=False)
        vista["fecha"] = pd.to_datetime(vista["fecha"], errors="coerce")
        for _, row in vista.iterrows():
            fecha_txt = row["fecha"].strftime("%Y-%m-%d") if pd.notna(row["fecha"]) else "-"
            descripcion = str(row.get("descripcion") or "Sin descripcion")
            deuda_nombre = str(row.get("deuda_nombre") or "").strip()
            if deuda_nombre:
                descripcion = f"{descripcion} | {deuda_nombre}"
            rows.append([
                Paragraph(fecha_txt, styles["ZentixBody"]),
                Paragraph(str(row.get("tipo") or "-"), styles["ZentixBody"]),
                Paragraph(str(row.get("categoria") or "-"), styles["ZentixBody"]),
                Paragraph(money(row.get("monto", 0)), styles["ZentixBody"]),
                Paragraph(descripcion, styles["ZentixBody"]),
            ])

    table = Table(rows, colWidths=[24 * mm, 33 * mm, 31 * mm, 24 * mm, 58 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#E2E8F0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 10))

    firma_parts = []
    if avatar:
        firma_parts.append(avatar)
    firma_parts.append(Paragraph("Zentix Intelligence · Lectura automatizada con criterio visual premium", styles["ZentixSignature"]))
    firma = Table([[firma_parts]], colWidths=[166 * mm])
    firma.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BFDBFE")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(firma)

    doc.build(story, onFirstPage=_draw_footer_report, onLaterPages=_draw_footer_report)
    buffer.seek(0)
    return buffer.getvalue()


def resetear_formulario_registro():
    defaults = {
        "registrar_tipo": "Ingreso",
        "registrar_fecha_mov": date.today(),
        "registrar_descripcion": "",
        "registrar_recurrente": False,
        "registrar_frecuencia": "Semanal",
        "registrar_proxima_fecha": date.today() + timedelta(days=7),
        "registrar_fin_toggle": False,
        "registrar_fecha_fin": date.today() + timedelta(days=7),
        "registrar_recurrente_activo": True,
        "registrar_categoria_ingreso": "Salario",
        "registrar_categoria_gasto": "Comida",
        "registrar_monto_ingreso": 0.0,
        "registrar_monto_gasto": 0.0,
        "registrar_emocion": "",
        "registrar_deuda_nombre": "",
        "registrar_prestamista": "",
        "registrar_monto_deuda": 0.0,
        "registrar_deuda_limite_toggle": False,
        "registrar_deuda_limite": date.today() + timedelta(days=30),
        "registrar_pago_deuda_select": None,
        "registrar_pago_deuda_monto": 0.0,
        "registrar_cxc_nombre": "",
        "registrar_cxc_cliente": "",
        "registrar_cxc_monto": 0.0,
        "registrar_cxc_limite_toggle": False,
        "registrar_cxc_limite": date.today() + timedelta(days=30),
        "registrar_cobro_cxc_select": None,
        "registrar_cobro_cxc_monto": 0.0,
    }
    for key, value in defaults.items():
        st.session_state[key] = value


def _font(size=24, bold=False):
    if not PIL_AVAILABLE:
        return None
    candidates = []
    if bold:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]
    else:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def generar_imagen_reporte_premium(nombre_usuario, plan_nombre, periodicidad, inicio, fin, resumen_periodo, df_periodo):
    if not PIL_AVAILABLE:
        return None

    width = 1600
    height = 2000
    img = PILImage.new("RGB", (width, height), "#07111f")
    draw = ImageDraw.Draw(img)

    # Background accents
    draw.rectangle((0, 0, width, height), fill="#07111f")
    draw.rounded_rectangle((50, 50, width - 50, 360), radius=36, fill="#0b1730", outline="#1d4ed8", width=2)
    draw.rounded_rectangle((50, 400, width - 50, 740), radius=30, fill="#f8fbff", outline="#dbeafe", width=2)
    draw.rounded_rectangle((50, 780, width - 50, height - 80), radius=30, fill="#f8fbff", outline="#dbeafe", width=2)

    font_title = _font(64, True)
    font_sub = _font(28, False)
    font_label = _font(24, True)
    font_body = _font(24, False)
    font_small = _font(20, False)

    draw.text((90, 95), "ZENTIX", fill="#ffffff", font=font_title)
    draw.text((92, 175), "Tu centro financiero, claro y visualmente fuerte.", fill="#bfdbfe", font=font_sub)
    draw.text((92, 225), f"Reporte {periodicidad} · {inicio.strftime('%Y-%m-%d')} a {fin.strftime('%Y-%m-%d')}", fill="#cbd5e1", font=font_sub)
    draw.text((92, 275), f"Usuario: {nombre_usuario} · Plan: {plan_nombre}", fill="#cbd5e1", font=font_sub)

    # KPI cards
    kpis = [
        ("Movimientos", str(int(resumen_periodo.get("conteo", 0) or 0)), "#ffffff"),
        ("Ingresos", money(resumen_periodo.get("ingresos", 0) or 0), "#22c55e"),
        ("Gastos", money(resumen_periodo.get("gastos", 0) or 0), "#ef4444"),
        ("Balance", money(resumen_periodo.get("balance", 0) or 0), "#3b82f6"),
    ]
    x_positions = [90, 450, 810, 1170]
    for (label, value, color), x in zip(kpis, x_positions):
        draw.rounded_rectangle((x, 450, x + 280, 690), radius=24, fill="#eef6ff", outline="#dbeafe", width=2)
        draw.text((x + 24, 490), label, fill="#475569", font=font_label)
        draw.text((x + 24, 565), value, fill=color, font=_font(36, True))

    # Executive summary
    y = 830
    draw.text((90, y), "Resumen ejecutivo", fill="#0f172a", font=_font(36, True))
    y += 70
    resumen_lineas = construir_resumen_ejecutivo_reporte(df_periodo, resumen_periodo)
    for line in resumen_lineas:
        draw.text((110, y), f"• {line}", fill="#334155", font=font_body)
        y += 50

    y += 20
    draw.text((90, y), "Movimientos destacados", fill="#0f172a", font=_font(34, True))
    y += 60

    vista = df_periodo.copy().sort_values("fecha", ascending=False).head(10) if df_periodo is not None and not df_periodo.empty else pd.DataFrame()
    if vista.empty:
        draw.text((110, y), "Sin movimientos en este periodo.", fill="#64748b", font=font_body)
    else:
        for _, row in vista.iterrows():
            fecha_txt = pd.to_datetime(row.get("fecha"), errors="coerce")
            fecha_txt = fecha_txt.strftime("%Y-%m-%d") if pd.notna(fecha_txt) else "-"
            tipo = str(row.get("tipo") or "-")
            categoria = str(row.get("categoria") or "-")
            monto = money(row.get("monto", 0) or 0)
            descripcion = str(row.get("descripcion") or "Sin descripción")[:52]
            color = "#22c55e" if tipo in ["Ingreso", "Cobro cuenta por cobrar"] else "#ef4444" if tipo == "Gasto" else "#3b82f6" if tipo == "Ingreso (Deuda)" else "#8b5cf6" if tipo == "Cuenta por cobrar" else "#f59e0b"
            draw.rounded_rectangle((90, y - 8, width - 90, y + 78), radius=18, fill="#ffffff", outline="#e2e8f0", width=1)
            draw.text((115, y + 10), f"{fecha_txt} · {tipo} · {categoria}", fill="#0f172a", font=font_label)
            draw.text((115, y + 42), descripcion, fill="#475569", font=font_small)
            draw.text((width - 310, y + 24), monto, fill=color, font=_font(28, True))
            y += 98
            if y > height - 160:
                break

    draw.text((90, height - 120), "Zentix Intelligence · Imagen premium lista para guardar o imprimir", fill="#475569", font=font_small)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def render_nav_rapida_premium():
    return


def render_reporte_descargable(nombre_usuario, plan_actual, df_base, user_id=None):

    section_header("Reporte premium imprimible", "Descarga un PDF semanal o mensual listo para imprimir con portada, resumen ejecutivo y firma de marca.")
    with st.expander("🖨️ Generar reporte PDF", expanded=False):
        periodicidad = st.radio("Periodo del reporte", ["Semanal", "Mensual"], horizontal=True, key="reporte_periodicidad")
        fecha_ref = st.date_input("Fecha de referencia", value=date.today(), key="reporte_fecha_ref")
        df_periodo, inicio_rep, fin_rep = obtener_movimientos_periodo(df_base if df_base is not None else pd.DataFrame(), periodicidad, fecha_ref)
        resumen_rep = resumir_periodo_movimientos(df_periodo)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_spotlight_metric("Movimientos", str(resumen_rep.get("conteo", 0)), "Incluidos en el PDF")
        with c2:
            render_spotlight_metric("Ingresos reales", money(resumen_rep.get("ingresos", 0)), "Periodo seleccionado")
        with c3:
            render_spotlight_metric("Gastos", money(resumen_rep.get("gastos", 0)), "Periodo seleccionado")
        with c4:
            render_spotlight_metric("Balance", money(resumen_rep.get("balance", 0)), "Lectura neta del periodo")

        if inicio_rep and fin_rep:
            st.caption(f"Periodo cubierto: {inicio_rep.strftime('%Y-%m-%d')} a {fin_rep.strftime('%Y-%m-%d')}")

        ejecutivo = construir_resumen_ejecutivo_reporte(df_periodo, resumen_rep)
        render_list_card("Resumen ejecutivo del PDF", ejecutivo, "La portada del reporte ya incluye estas conclusiones breves.")

        if df_periodo is None or df_periodo.empty:
            st.info("No hay movimientos en el periodo seleccionado todavía.")
            return

        preview = df_periodo.copy().sort_values("fecha", ascending=False).head(8)
        preview["fecha"] = pd.to_datetime(preview["fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
        cols = [col for col in ["fecha", "tipo", "categoria", "monto", "descripcion", "deuda_nombre", "prestamista"] if col in preview.columns]
        st.dataframe(preview[cols], use_container_width=True)

        if not REPORTLAB_AVAILABLE:
            st.warning("Instala reportlab en tu entorno de Streamlit Cloud para habilitar el PDF premium.")
            return

        pdf_bytes = generar_pdf_reporte_premium(nombre_usuario, plan_actual.get("plan", "free").upper(), periodicidad, inicio_rep, fin_rep, df_periodo, resumen_rep)
        if pdf_bytes:
            filename = f"zentix_reporte_{periodicidad.lower()}_{inicio_rep.strftime('%Y%m%d')}_{fin_rep.strftime('%Y%m%d')}.pdf"
            descargado = st.download_button("Descargar reporte PDF", data=pdf_bytes, file_name=filename, mime="application/pdf", use_container_width=True)
            if descargado:
                registrar_evento_producto("report_download", user_id=user_id, pagina="Análisis", detalle=f"{periodicidad} {inicio_rep} {fin_rep}")
            st.caption("Descarga el PDF y podrás imprimirlo desde tu navegador o visor favorito.")
def obtener_nombre_meta_guardado(user_id):
    try:
        result = (
            supabase.table("ahorro_meta")
            .select("nombre_meta")
            .eq("usuario_id", user_id)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0].get("nombre_meta") or ""
    except Exception:
        pass
    return ""


def guardar_meta_segura(user_id, meta_valor, nombre_meta, meta_result):
    payload = {
        "meta": float(meta_valor),
        "actualizado_en": datetime.now().isoformat(),
        "nombre_meta": (nombre_meta or "").strip() or None
    }

    try:
        if meta_result:
            return (
                supabase.table("ahorro_meta")
                .update(payload)
                .eq("usuario_id", user_id)
                .execute()
            )
        payload_insert = dict(payload)
        payload_insert["usuario_id"] = user_id
        return supabase.table("ahorro_meta").insert(payload_insert).execute()
    except Exception:
        payload_fallback = {
            "meta": float(meta_valor),
            "actualizado_en": datetime.now().isoformat()
        }
        if meta_result:
            return (
                supabase.table("ahorro_meta")
                .update(payload_fallback)
                .eq("usuario_id", user_id)
                .execute()
            )
        payload_insert = dict(payload_fallback)
        payload_insert["usuario_id"] = user_id
        return supabase.table("ahorro_meta").insert(payload_insert).execute()


def eliminar_meta_segura(user_id):
    return supabase.table("ahorro_meta").delete().eq("usuario_id", user_id).execute()


def calcular_ratio_fin_semana(df_base):
    if df_base is None or df_base.empty:
        return 0.0

    gastos = df_base[df_base["tipo"] == "Gasto"].copy()
    if gastos.empty:
        return 0.0

    gastos["dow"] = gastos["fecha"].dt.dayofweek
    gasto_fin_semana = gastos[gastos["dow"] >= 5]["monto"].sum()
    gasto_total = gastos["monto"].sum()
    return float(gasto_fin_semana / gasto_total) if gasto_total else 0.0


def obtener_top_categoria(df_base):
    if df_base is None or df_base.empty:
        return None, 0.0, 0.0

    gastos = df_base[df_base["tipo"] == "Gasto"].copy()
    if gastos.empty:
        return None, 0.0, 0.0

    resumen = gastos.groupby("categoria", dropna=False)["monto"].sum().sort_values(ascending=False)
    if resumen.empty:
        return None, 0.0, 0.0

    top_nombre = resumen.index[0]
    top_monto = float(resumen.iloc[0])
    total = float(resumen.sum())
    share = top_monto / total if total else 0.0
    return top_nombre, top_monto, share


def obtener_perfil_financiero(total_ingresos, total_gastos, saldo_disponible, df_mes_actual):
    if df_mes_actual is None or df_mes_actual.empty:
        return {
            "titulo": "Perfil en construcción",
            "descripcion": "Aún no hay suficiente información para definir tu estilo financiero. Sigue registrando y Zentix lo irá entendiendo.",
            "microcopy": "Empieza con 5 a 10 movimientos para activar una lectura más personal."
        }

    if total_ingresos <= 0 and total_gastos > 0:
        return {
            "titulo": "Registro incompleto",
            "descripcion": "Tienes gastos registrados, pero no ingresos en el periodo actual. Zentix necesita ambos para entender tu realidad financiera.",
            "microcopy": "Registra al menos una fuente de ingreso para afinar recomendaciones."
        }

    ratio_gasto = (total_gastos / total_ingresos) if total_ingresos > 0 else 0.0
    ratio_fin_semana = calcular_ratio_fin_semana(df_mes_actual)
    top_categoria, _, top_share = obtener_top_categoria(df_mes_actual)

    if ratio_gasto <= 0.45 and saldo_disponible >= 0:
        return {
            "titulo": "Ahorrador disciplinado",
            "descripcion": "Mantienes tus gastos bajo control y dejas margen real para ahorro o colchón financiero.",
            "microcopy": "Tu patrón sugiere buena disciplina y capacidad de planear."
        }

    if ratio_fin_semana >= 0.45 and total_gastos > 0:
        return {
            "titulo": "Impulsivo de fin de semana",
            "descripcion": "Una parte importante de tus gastos se concentra en fines de semana, lo que puede afectar metas sin que lo notes.",
            "microcopy": "Tu mejor ajuste está en sábado y domingo, no en toda la semana."
        }

    if top_share >= 0.45 and top_categoria:
        return {
            "titulo": "Concentrado en una categoría",
            "descripcion": f"Tu gasto depende mucho de {top_categoria}. Eso te da foco, pero también un punto crítico de fuga.",
            "microcopy": f"Si mejoras {top_categoria}, mejoras gran parte del panorama."
        }

    if ratio_gasto <= 0.75:
        return {
            "titulo": "Equilibrado estratégico",
            "descripcion": "Tu nivel de gasto va acompasado con tus ingresos. No estás sobrado, pero sí en una zona sana.",
            "microcopy": "Un par de ajustes bien hechos te acercan mucho a metas más ambiciosas."
        }

    if ratio_gasto <= 1.0:
        return {
            "titulo": "Activo con poco margen",
            "descripcion": "Tus gastos están cerca de tus ingresos. No estás desbordado, pero cualquier exceso te deja sin aire.",
            "microcopy": "Necesitas precisión más que recortes extremos."
        }

    return {
        "titulo": "Desbordado financiero",
        "descripcion": "Tus salidas ya están superando o presionando demasiado tus ingresos. Zentix detecta una zona de riesgo clara.",
        "microcopy": "La prioridad no es ahorrar más todavía; es recuperar margen."
    }


def obtener_comparativa_periodos(df_base):
    if df_base is None or df_base.empty or "fecha" not in df_base.columns:
        return {
            "gasto_semana_pct": 0.0,
            "ingreso_semana_pct": 0.0,
            "gasto_mes_pct": 0.0,
            "ingreso_mes_pct": 0.0
        }

    df_tmp = df_base.copy()
    df_tmp["fecha"] = pd.to_datetime(df_tmp["fecha"], errors="coerce")
    df_tmp = df_tmp.dropna(subset=["fecha"]).copy()

    try:
        if getattr(df_tmp["fecha"].dt, "tz", None) is not None:
            df_tmp["fecha"] = df_tmp["fecha"].dt.tz_localize(None)
    except Exception:
        pass

    df_tmp["fecha"] = df_tmp["fecha"].dt.normalize()

    if df_tmp.empty:
        return {
            "gasto_semana_pct": 0.0,
            "ingreso_semana_pct": 0.0,
            "gasto_mes_pct": 0.0,
            "ingreso_mes_pct": 0.0
        }

    hoy = pd.Timestamp.now().normalize()
    inicio_semana = hoy - pd.Timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + pd.Timedelta(days=7)
    inicio_semana_anterior = inicio_semana - pd.Timedelta(days=7)

    inicio_mes = hoy.replace(day=1)
    siguiente_mes = inicio_mes + pd.offsets.MonthBegin(1)
    inicio_mes_anterior = (inicio_mes - pd.Timedelta(days=1)).replace(day=1)

    semana_actual = df_tmp[(df_tmp["fecha"] >= inicio_semana) & (df_tmp["fecha"] < fin_semana)]
    semana_anterior = df_tmp[(df_tmp["fecha"] >= inicio_semana_anterior) & (df_tmp["fecha"] < inicio_semana)]
    mes_actual = df_tmp[(df_tmp["fecha"] >= inicio_mes) & (df_tmp["fecha"] < siguiente_mes)]
    mes_anterior = df_tmp[(df_tmp["fecha"] >= inicio_mes_anterior) & (df_tmp["fecha"] < inicio_mes)]

    def cambio_pct(actual, anterior):
        actual = float(actual or 0)
        anterior = float(anterior or 0)
        if anterior == 0:
            return 0.0
        return float(((actual - anterior) / anterior) * 100)

    return {
        "gasto_semana_pct": cambio_pct(
            semana_actual[semana_actual["tipo"] == "Gasto"]["monto"].sum(),
            semana_anterior[semana_anterior["tipo"] == "Gasto"]["monto"].sum()
        ),
        "ingreso_semana_pct": cambio_pct(
            semana_actual[semana_actual["tipo"].isin(["Ingreso", "Cobro cuenta por cobrar"])]["monto"].sum(),
            semana_anterior[semana_anterior["tipo"].isin(["Ingreso", "Cobro cuenta por cobrar"])]["monto"].sum()
        ),
        "gasto_mes_pct": cambio_pct(
            mes_actual[mes_actual["tipo"] == "Gasto"]["monto"].sum(),
            mes_anterior[mes_anterior["tipo"] == "Gasto"]["monto"].sum()
        ),
        "ingreso_mes_pct": cambio_pct(
            mes_actual[mes_actual["tipo"].isin(["Ingreso", "Cobro cuenta por cobrar"])]["monto"].sum(),
            mes_anterior[mes_anterior["tipo"].isin(["Ingreso", "Cobro cuenta por cobrar"])]["monto"].sum()
        )
    }
def construir_resumen_semanal_premium(df_base, meta_actual, ahorro_actual):
    if df_base is None or df_base.empty or "fecha" not in df_base.columns:
        return {
            "positivas": ["Aún no hay semana suficiente para resumir."],
            "alertas": ["Registra algunos movimientos y Zentix activará tu resumen premium."],
            "accion": "Empieza por registrar tus gastos e ingresos principales de esta semana."
        }

    df_tmp = df_base.copy()
    df_tmp["fecha"] = pd.to_datetime(df_tmp["fecha"], errors="coerce")
    df_tmp = df_tmp.dropna(subset=["fecha"]).copy()

    try:
        if getattr(df_tmp["fecha"].dt, "tz", None) is not None:
            df_tmp["fecha"] = df_tmp["fecha"].dt.tz_localize(None)
    except Exception:
        pass

    df_tmp["fecha"] = df_tmp["fecha"].dt.normalize()

    if df_tmp.empty:
        return {
            "positivas": ["Aún no hay semana suficiente para resumir."],
            "alertas": ["Registra algunos movimientos y Zentix activará tu resumen premium."],
            "accion": "Empieza por registrar tus gastos e ingresos principales de esta semana."
        }

    hoy = pd.Timestamp.now().normalize()
    inicio_semana = hoy - pd.Timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + pd.Timedelta(days=7)
    inicio_semana_anterior = inicio_semana - pd.Timedelta(days=7)

    semana_actual = df_tmp[(df_tmp["fecha"] >= inicio_semana) & (df_tmp["fecha"] < fin_semana)]
    semana_anterior = df_tmp[(df_tmp["fecha"] >= inicio_semana_anterior) & (df_tmp["fecha"] < inicio_semana)]

    positivos = []
    alertas = []

    gasto_actual = float(semana_actual[semana_actual["tipo"] == "Gasto"]["monto"].sum() or 0)
    gasto_anterior = float(semana_anterior[semana_anterior["tipo"] == "Gasto"]["monto"].sum() or 0)
    ingreso_actual = float(semana_actual[semana_actual["tipo"].isin(["Ingreso", "Cobro cuenta por cobrar"])]["monto"].sum() or 0)

    if gasto_anterior > 0 and gasto_actual < gasto_anterior:
        positivos.append(f"Bajaste tus gastos semanales en {money(gasto_anterior - gasto_actual)} frente a la semana pasada.")
    if ingreso_actual > 0:
        positivos.append(f"Generaste {money(ingreso_actual)} en ingresos durante la semana actual.")
    if len(semana_actual.index) >= 3:
        positivos.append("Tu semana ya tiene suficiente registro para recomendaciones más precisas.")
    if ahorro_actual > 0:
        positivos.append(f"Tienes un disponible actual de {money(ahorro_actual)}, lo que te da margen de maniobra.")

    top_categoria, top_monto, top_share = obtener_top_categoria(semana_actual)
    if top_categoria and top_share >= 0.40:
        alertas.append(f"{top_categoria} representa una parte muy alta de tu gasto semanal ({round(top_share * 100, 1)}%).")
    if gasto_anterior > 0 and gasto_actual > gasto_anterior * 1.15:
        alertas.append("Tus gastos subieron con fuerza frente a la semana pasada.")
    if meta_actual > 0 and ahorro_actual < meta_actual * 0.4:
        alertas.append("Tu meta aún va por debajo del ritmo esperado.")
    if ingreso_actual == 0 and gasto_actual > 0:
        alertas.append("Esta semana tienes salidas, pero no ingresos registrados.")

    if not positivos:
        positivos.append("Tu actividad semanal sigue siendo estable.")
    if not alertas:
        alertas.append("No se detectan alertas fuertes en esta semana.")

    if alertas and "subieron" in " ".join(alertas).lower():
        accion = "Reduce una sola categoría dominante esta semana para recuperar control sin sentir recorte extremo."
    elif meta_actual > 0 and ahorro_actual < meta_actual:
        accion = "Haz un ajuste pequeño en tu gasto variable para acercarte más rápido a tu meta."
    else:
        accion = "Mantén tu ritmo actual y sigue registrando para que Zentix afine mejor sus recomendaciones."

    return {
        "positivas": positivos[:3],
        "alertas": alertas[:2],
        "accion": accion
    }
def generar_alertas_proactivas(df_base, df_mes_actual, total_ingresos, total_gastos, saldo_disponible, meta_actual):
    alertas = []

    if total_ingresos > 0 and total_gastos >= total_ingresos * 0.9:
        alertas.append("Vas muy cerca del límite de tus ingresos este mes.")
    if saldo_disponible < 0:
        alertas.append("Tu disponible actual está en negativo.")
    top_categoria, _, top_share = obtener_top_categoria(df_mes_actual)
    if top_categoria and top_share >= 0.40:
        alertas.append(f"{top_categoria} domina tu gasto mensual.")
    if calcular_ratio_fin_semana(df_mes_actual) >= 0.45:
        alertas.append("Tus gastos se están concentrando en fines de semana.")
    if meta_actual > 0 and saldo_disponible < meta_actual:
        alertas.append("Todavía no alcanzas tu meta de ahorro actual.")

    if not alertas:
        alertas.append("Tu comportamiento actual no muestra alertas fuertes; mantén el ritmo.")

    return alertas[:3]


def generar_recomendacion_accionable(df_mes_actual, total_ingresos, total_gastos, ahorro_actual, meta_actual):
    top_categoria, top_monto, _ = obtener_top_categoria(df_mes_actual)

    if meta_actual > 0 and ahorro_actual < meta_actual:
        faltante = meta_actual - max(ahorro_actual, 0)
        if top_categoria and top_monto > 0:
            ajuste = min(faltante / 4, top_monto * 0.20)
            return f"Si recortas cerca de {money(max(ajuste, 0))} en {top_categoria} cada semana, te acercas mucho más rápido a tu meta."
        return f"Si reservas alrededor de {money(max(faltante / 4, 0))} por semana, avanzas con más control hacia tu meta."

    if total_ingresos > 0 and total_gastos > total_ingresos * 0.8 and top_categoria:
        return f"Tu mayor palanca ahora está en {top_categoria}. Un ajuste pequeño ahí puede devolverte margen sin tocar todo lo demás."

    return "Mantén el registro constante y usa las alertas para corregir solo una categoría a la vez."


def detectar_patrones_comportamiento(df_base):
    patrones = []

    if df_base is None or df_base.empty:
        return ["Aún no hay suficiente actividad para detectar patrones."]

    ratio_fin_semana = calcular_ratio_fin_semana(df_base)
    if ratio_fin_semana >= 0.45:
        patrones.append("Tus fines de semana cargan gran parte del gasto.")

    gastos = df_base[df_base["tipo"] == "Gasto"].copy()
    if not gastos.empty:
        gastos["dow"] = gastos["fecha"].dt.day_name()
        top_day = gastos.groupby("dow")["monto"].sum().sort_values(ascending=False)
        if not top_day.empty:
            patrones.append(f"Tu día con mayor presión de gasto suele ser {top_day.index[0]}.")

    if "emocion" in df_base.columns:
        emociones = df_base[df_base["emocion"].fillna("") != ""]
        if not emociones.empty:
            emocion_top = emociones["emocion"].value_counts().idxmax()
            patrones.append(f"La emoción más repetida en tus gastos es {emocion_top.lower()}.")

    if not patrones:
        patrones.append("Tu comportamiento luce estable, sin patrones dominantes todavía.")

    return patrones[:3]


def sugerir_categorias_inteligentes(df_base):
    sugerencias = []

    if df_base is None or df_base.empty:
        return ["Sigue registrando y Zentix podrá sugerirte mejores categorías."]

    gastos = df_base[df_base["tipo"] == "Gasto"].copy()
    if gastos.empty:
        return ["Aún no hay suficientes gastos para sugerir categorías inteligentes."]

    otros = gastos[gastos["categoria"].fillna("").str.lower() == "otros"]
    if not otros.empty and otros["monto"].sum() >= gastos["monto"].sum() * 0.15:
        sugerencias.append("Tus registros en 'Otros' ya pesan bastante. Te convendría dividirlos en categorías más específicas.")

    if gastos["descripcion"].fillna("").astype(str).str.strip().ne("").any():
        desc_tmp = gastos[gastos["descripcion"].fillna("").astype(str).str.strip() != ""].copy()
        desc_tmp["desc_norm"] = desc_tmp["descripcion"].astype(str).str.strip().str.lower()
        top_desc = desc_tmp["desc_norm"].value_counts()
        if not top_desc.empty and top_desc.iloc[0] >= 3:
            sugerencias.append(f"Registras con frecuencia '{top_desc.index[0]}'. Podría merecer una categoría propia.")

    top_categoria, _, top_share = obtener_top_categoria(gastos)
    if top_categoria and top_share >= 0.45:
        sugerencias.append(f"{top_categoria} domina tu gasto. Puedes crear subcategorías para tener mejor lectura.")

    if not sugerencias:
        sugerencias.append("Tus categorías actuales están bastante bien distribuidas.")

    return sugerencias[:3]


def construir_insight_personalizado(perfil_financiero, alertas, recomendacion, patrones):
    base_desc = perfil_financiero.get("descripcion", "Sin insight disponible.")
    alerta = alertas[0] if alertas else "Sin alertas críticas por ahora."
    patron = patrones[0] if patrones else "Sin patrones dominantes detectados."
    return f"{base_desc} Alerta principal: {alerta} Patrón clave: {patron} Recomendación: {recomendacion}"


def money_delta(value):
    prefix = "+" if value > 0 else ""
    return f"{prefix}{round(value, 1)}%"


def render_list_card(title, items, foot=""):
    items = items or ["Sin hallazgos todavía."]
    bullets = "".join([
        f"<li class='spotlight-item'>{html.escape(str(item))}</li>"
        for item in items
    ])
    st.markdown(
        f"""
        <div class="premium-list-card">
            <div class="premium-list-head">
                <div class="premium-list-title">{html.escape(str(title))}</div>
                <div class="premium-list-badge">{len(items)} señal{'es' if len(items) != 1 else ''}</div>
            </div>
            <div class="premium-list-copy">{html.escape(str(foot))}</div>
            <ul class="spotlight-list">{bullets}</ul>
        </div>
        """,
        unsafe_allow_html=True
    )




def movimiento_chip(label, kind="default"):
    return f"<span class='movement-chip movement-chip-{kind}'>{html.escape(str(label))}</span>"


def construir_chips_movimiento(row):
    chips = []
    tipo = str(row.get("tipo") or "").strip()
    monto = float(row.get("monto", 0) or 0)

    if tipo == "Ingreso":
        chips.append(movimiento_chip("Ingreso real", "income"))
    elif tipo == "Gasto":
        chips.append(movimiento_chip("Gasto", "expense"))
    elif tipo == "Ingreso (Deuda)":
        chips.append(movimiento_chip("Crédito solicitado", "debt"))
    elif tipo == "Pago de deuda":
        chips.append(movimiento_chip("Pago a crédito", "pay"))
    elif tipo == "Cuenta por cobrar":
        chips.append(movimiento_chip("Prestaste Dinero", "info"))
    elif tipo == "Cobro cuenta por cobrar":
        chips.append(movimiento_chip("Ya me pagaron", "income"))

    if bool(row.get("es_recurrente")):
        chips.append(movimiento_chip("Recurrente", "recurrent"))

    if str(row.get("deuda_nombre") or "").strip():
        chips.append(movimiento_chip("Con deuda", "info"))

    if tipo == "Gasto" and monto >= 500000:
        chips.append(movimiento_chip("Monto alto", "alert"))

    if tipo == "Pago de deuda" and monto > 0:
        chips.append(movimiento_chip("Reduce pendiente", "pay"))

    if tipo == "Cobro cuenta por cobrar" and monto > 0:
        chips.append(movimiento_chip("Entra a caja", "income"))

    return "".join(chips)


def obtener_movimiento_seleccionado_id(df_movs):
    if df_movs is None or df_movs.empty or "id" not in df_movs.columns:
        return None
    selected = st.session_state.get("zentix_selected_movimiento_id")
    ids = [str(x) for x in df_movs["id"].astype(str).tolist()]
    if selected and str(selected) in ids:
        return str(selected)
    return ids[0] if ids else None


def render_movimientos_action_hub(user_id, df_movs, df_deudas_local):
    st.markdown(
        """
        <div class="spotlight-side-card fade-up" style="margin-top:0.3rem;">
            <div class="spotlight-side-title">Acciones rápidas por movimiento</div>
            <div class="spotlight-side-sub">Selecciona, edita o elimina desde una ficha más visual. La edición avanzada sigue disponible más abajo.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if df_movs is None or df_movs.empty or "id" not in df_movs.columns:
        empty_state("Sin movimientos para gestionar", "Cuando registres movimientos, aquí aparecerán fichas premium con acciones directas.")
        return

    df_cards = df_movs.copy().sort_values("fecha", ascending=False).head(8)
    df_cards["fecha"] = pd.to_datetime(df_cards["fecha"], errors="coerce")
    df_cards["monto"] = pd.to_numeric(df_cards["monto"], errors="coerce").fillna(0)

    selected = obtener_movimiento_seleccionado_id(df_cards)
    rows = [df_cards.iloc[i:i+2] for i in range(0, len(df_cards), 2)]

    for pack_idx, pack in enumerate(rows):
        cols = st.columns(len(pack))
        for col_idx, (_, row) in zip(range(len(pack)), pack.iterrows()):
            with cols[col_idx]:
                fecha_txt = row["fecha"].strftime("%Y-%m-%d") if pd.notna(row["fecha"]) else "Sin fecha"
                descripcion = str(row.get("descripcion") or "Sin descripción").strip()
                if len(descripcion) > 70:
                    descripcion = descripcion[:70] + "..."
                deuda_txt = str(row.get("deuda_nombre") or "").strip()
                extra = deuda_txt if deuda_txt else (str(row.get("categoria") or "Sin categoría").strip())
                chips = construir_chips_movimiento(row)
                active_badge = "<span class='movement-chip movement-chip-info'>Seleccionado</span>" if str(row["id"]) == str(selected) else ""
                st.markdown(
                    f"""
                    <div class="movement-card fade-up">
                        <div class="movement-date">{fecha_txt}</div>
                        <div class="movement-title">{html.escape(str(row.get('tipo') or 'Sin tipo'))}</div>
                        <div class="movement-amount">{money(row.get('monto', 0))}</div>
                        <div class="movement-meta">{html.escape(extra)} · {html.escape(descripcion)}</div>
                        <div class="movement-chip-row">{chips}{active_badge}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                c1, c2, c3 = st.columns([1.15, 1.05, 0.95])
                with c1:
                    if st.button("Ver", key=f"mov_focus_{row['id']}", use_container_width=True, type="primary" if str(row["id"]) == str(selected) else "secondary"):
                        st.session_state["zentix_selected_movimiento_id"] = str(row["id"])
                        st.session_state["zentix_open_editor"] = True
                        st.session_state["zentix_editor_mode"] = "edit"
                        st.rerun()
                with c2:
                    if st.button("Editar", key=f"mov_edit_{row['id']}", use_container_width=True, type="secondary"):
                        st.session_state["zentix_selected_movimiento_id"] = str(row["id"])
                        st.session_state["zentix_open_editor"] = True
                        st.session_state["zentix_editor_mode"] = "edit"
                        st.rerun()
                with c3:
                    if st.button("Eliminar", key=f"mov_del_{row['id']}", use_container_width=True, type="secondary"):
                        st.session_state["zentix_selected_movimiento_id"] = str(row["id"])
                        st.session_state["zentix_open_editor"] = True
                        st.session_state["zentix_editor_mode"] = "delete"
                        st.rerun()


def render_movimiento_focus_panel(df_movs):
    selected = obtener_movimiento_seleccionado_id(df_movs if df_movs is not None else pd.DataFrame())
    if df_movs is None or df_movs.empty or not selected:
        st.markdown(
            """
            <div class="movement-side-shell fade-up">
                <div class="spotlight-side-title">Ficha rápida del movimiento</div>
                <div class="spotlight-side-sub">Selecciona un movimiento desde las fichas de la izquierda y verás aquí su resumen premium.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    row = df_movs[df_movs["id"].astype(str) == str(selected)]
    if row.empty:
        return
    row = row.iloc[0]
    fecha_val = pd.to_datetime(row.get("fecha"), errors="coerce")
    proxima_val = pd.to_datetime(row.get("proxima_fecha_recurrencia"), errors="coerce")
    limite_val = pd.to_datetime(row.get("fecha_limite_deuda"), errors="coerce")

    st.markdown(
        """
        <div class="movement-side-shell fade-up">
            <div class="spotlight-side-title">Ficha rápida del movimiento</div>
            <div class="spotlight-side-sub">Una lectura más editorial del registro seleccionado, con estados útiles y contexto de edición.</div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        f"""
        <div class="movement-side-kpi">
            <div class="movement-side-label">Tipo</div>
            <div class="movement-side-value">{html.escape(str(row.get('tipo') or 'Sin tipo'))}</div>
        </div>
        <div class="movement-side-kpi">
            <div class="movement-side-label">Monto</div>
            <div class="movement-side-value">{money(row.get('monto', 0))}</div>
        </div>
        <div class="movement-chip-row" style="margin-bottom:0.8rem;">{construir_chips_movimiento(row)}</div>
        <div class="movement-side-kpi">
            <div class="movement-side-label">Descripción</div>
            <div class="movement-side-value">{html.escape(str(row.get('descripcion') or 'Sin descripción'))}</div>
        </div>
        <div class="movement-side-kpi">
            <div class="movement-side-label">Fecha y categoría</div>
            <div class="movement-side-value">{fecha_val.strftime('%Y-%m-%d') if pd.notna(fecha_val) else 'Sin fecha'} · {html.escape(str(row.get('categoria') or 'Sin categoría'))}</div>
        </div>
        <div class="movement-side-kpi">
            <div class="movement-side-label">Deuda / prestamista</div>
            <div class="movement-side-value">{html.escape(str(row.get('deuda_nombre') or 'No aplica'))} · {html.escape(str(row.get('prestamista') or 'No aplica'))}</div>
        </div>
        <div class="movement-side-kpi">
            <div class="movement-side-label">Recurrencia</div>
            <div class="movement-side-value">{html.escape(str(row.get('frecuencia_recurrencia') or 'No recurrente'))}{' · próxima ' + proxima_val.strftime('%Y-%m-%d') if pd.notna(proxima_val) else ''}</div>
        </div>
        <div class="movement-side-kpi">
            <div class="movement-side-label">Fecha límite deuda</div>
            <div class="movement-side-value">{limite_val.strftime('%Y-%m-%d') if pd.notna(limite_val) else 'No aplica'}</div>
        </div>
        </div>
        """,
        unsafe_allow_html=True
    )



def obtener_estado_tutorial_usuario(user_id, df_base, meta_actual):
    total_mov = 0 if df_base is None else len(df_base.index)
    session_key = f"zentix_tutorial_state_{user_id}"
    if session_key not in st.session_state:
        st.session_state[session_key] = {
            "activo": bool(total_mov < 3 or float(meta_actual or 0) <= 0),
            "completado": False,
            "paso": "intro"
        }
    state = dict(st.session_state[session_key])
    try:
        result = (
            supabase.table("perfiles_usuario")
            .select("tutorial_completado, ultimo_paso_tutorial, tutorial_activo")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        if result.data:
            row = result.data[0]
            if row.get("tutorial_completado") is not None:
                state["completado"] = bool(row.get("tutorial_completado"))
            paso = str(row.get("ultimo_paso_tutorial") or state.get("paso") or "intro").strip().lower()
            if paso in {"intro", "registro", "analisis", "ahorro", "perfil"}:
                state["paso"] = paso
            if row.get("tutorial_activo") is not None:
                state["activo"] = bool(row.get("tutorial_activo"))
    except Exception:
        pass
    if state.get("completado"):
        state["activo"] = False
    st.session_state[session_key] = state
    return state


def guardar_estado_tutorial_usuario(user_id, paso=None, activo=None, completado=None):
    session_key = f"zentix_tutorial_state_{user_id}"
    current = dict(st.session_state.get(session_key, {"activo": True, "completado": False, "paso": "intro"}))
    if paso is not None:
        current["paso"] = str(paso).strip().lower()
    if activo is not None:
        current["activo"] = bool(activo)
    if completado is not None:
        current["completado"] = bool(completado)
        if completado:
            current["activo"] = False
    st.session_state[session_key] = current
    payload = {}
    if paso is not None:
        payload["ultimo_paso_tutorial"] = current["paso"]
    if activo is not None:
        payload["tutorial_activo"] = current["activo"]
    if completado is not None:
        payload["tutorial_completado"] = current["completado"]
    if not payload:
        return current
    candidatos = [
        dict(payload),
        {k: v for k, v in payload.items() if k != "tutorial_activo"}
    ]
    for candidate in candidatos:
        try:
            (
                supabase.table("perfiles_usuario")
                .update(candidate)
                .eq("id", user_id)
                .execute()
            )
            break
        except Exception:
            continue
    return current


def render_contexto_descubrimiento(pagina):
    mapa = {
        "Inicio": {
            "titulo": "Más inteligencia vive más abajo",
            "sub": "Sigue descendiendo y verás foco dinámico, gráficas mensuales, comparativas, patrones y el chat con IA sin salir de esta misma experiencia.",
            "chips": ["Spotlight inteligente", "Chat IA", "Comparativas", "Gráficas del mes", "Patrones"]
        },
        "Registrar": {
            "titulo": "Registro premium, no recargado",
            "sub": "El formulario se adapta a lo que elijas. Más abajo tienes vista previa, deuda, recurrentes y apoyo del avatar en el mismo flujo.",
            "chips": ["Ingreso", "Gasto", "Deuda", "Recurrentes", "Vista previa + IA"]
        },
        "Análisis": {
            "titulo": "Aquí hay lectura profunda",
            "sub": "Más abajo tienes tabla del mes, patrones, comparativas y visuales para detectar rápidamente qué está pasando con tu dinero.",
            "chips": ["Tabla viva", "Patrones", "Comparativas", "Timeline", "IA explicativa"]
        },
        "Ahorro": {
            "titulo": "Tu meta tiene más contexto",
            "sub": "Sigue bajando y verás proyección, progreso real, plan sugerido y lectura del avatar para convertir tu meta en algo accionable.",
            "chips": ["Meta con nombre", "Proyección", "Progreso", "Plan sugerido", "IA"]
        },
        "Perfil": {
            "titulo": "Tu experiencia se afina aquí",
            "sub": "Más abajo puedes ajustar recordatorios, ver diferencias entre Free y Pro y dejar lista una experiencia más premium sin invadir al usuario.",
            "chips": ["Plan", "IA diaria", "Recordatorios", "Preferencias", "Ruta Pro"]
        }
    }
    data = mapa.get(pagina, mapa["Inicio"])
    chips = "".join([f"<span class='feature-chip'>{chip}</span>" for chip in data["chips"]])
    st.markdown(
        f"""
        <div class="feature-signal">
            <div class="feature-signal-title">{data['titulo']}</div>
            <div class="feature-signal-sub">{data['sub']}</div>
            <div class="feature-signal-chips">{chips}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_spotlight_metric(label, value, foot=""):
    st.markdown(
        f"""
        <div class="spotlight-metric">
            <div class="spotlight-metric-label">{label}</div>
            <div class="spotlight-metric-value">{value}</div>
            <div class="spotlight-metric-foot">{foot}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def construir_flujo_semanal(df_base):
    if df_base is None or df_base.empty or "fecha" not in df_base.columns:
        return pd.DataFrame(columns=["semana", "tipo", "monto"])
    df_tmp = df_base.copy()
    df_tmp["fecha"] = pd.to_datetime(df_tmp["fecha"], errors="coerce")
    df_tmp = df_tmp.dropna(subset=["fecha"]).copy()
    if df_tmp.empty:
        return pd.DataFrame(columns=["semana", "tipo", "monto"])
    try:
        if getattr(df_tmp["fecha"].dt, "tz", None) is not None:
            df_tmp["fecha"] = df_tmp["fecha"].dt.tz_localize(None)
    except Exception:
        pass
    df_tmp["semana"] = df_tmp["fecha"].dt.to_period("W").apply(lambda r: r.start_time)
    resumen = (
        df_tmp[df_tmp["tipo"].isin(["Ingreso", "Gasto", "Ingreso (Deuda)", "Pago de deuda", "Cuenta por cobrar", "Cobro cuenta por cobrar"])]
        .groupby(["semana", "tipo"], dropna=False)["monto"]
        .sum()
        .reset_index()
        .sort_values("semana")
    )
    return resumen.tail(24).copy() if not resumen.empty else resumen


def construir_top_gastos_mes(df_mes_actual, limite=6):
    if df_mes_actual is None or df_mes_actual.empty:
        return pd.DataFrame(columns=["categoria", "monto"])
    gastos = df_mes_actual[df_mes_actual["tipo"] == "Gasto"].copy()
    if gastos.empty:
        return pd.DataFrame(columns=["categoria", "monto"])
    resumen = (
        gastos.groupby("categoria", dropna=False)["monto"]
        .sum()
        .reset_index()
        .sort_values("monto", ascending=False)
        .head(limite)
    )
    resumen["categoria"] = resumen["categoria"].fillna("Sin categoría")
    return resumen


def construir_meta_chart(meta_objetivo, ahorro_actual):
    objetivo = float(meta_objetivo or 0)
    disponible = float(max(ahorro_actual, 0))
    faltante = max(objetivo - disponible, 0)
    if objetivo <= 0:
        return pd.DataFrame({"concepto": ["Meta pendiente de definir"], "monto": [1.0]})
    return pd.DataFrame({"concepto": ["Disponible", "Faltante"], "monto": [disponible, faltante]})


def construir_deuda_chart(df_deudas_local, entradas_deuda, pagos_deuda, pendiente_total):
    if df_deudas_local is not None and not df_deudas_local.empty:
        activas = df_deudas_local[df_deudas_local["saldo_pendiente"] > 0].copy()
        if not activas.empty:
            return "activa", activas.sort_values("saldo_pendiente", ascending=False).head(6)
    return "flujo", pd.DataFrame({
        "concepto": ["Entradas por deuda", "Pagos de deuda", "Saldo pendiente"],
        "monto": [float(entradas_deuda or 0), float(pagos_deuda or 0), float(pendiente_total or 0)]
    })


def render_inicio_spotlight(df_base, df_mes_actual, df_deudas_local, total_ingresos_local, total_gastos_local,
                            entradas_deuda_local, pagos_deuda_local, saldo_pendiente_local, meta_objetivo,
                            ahorro_disponible, comparativa, resumen_semanal, alertas, sugerencias, proyeccion,
                            plan_actual, consultas_usadas, consultas_limite):
    section_header("Centro inteligente del mes", "Selecciona un foco y Zentix resalta una lectura útil con visuales, sin saturar la pantalla.")
    opciones = [("pulso", "Pulso del mes"), ("gastos", "Gasto dominante"), ("deuda", "Deuda y caja"), ("meta", "Meta viva")]
    state_key = "zentix_inicio_spotlight"
    if state_key not in st.session_state:
        st.session_state[state_key] = "pulso"
    cols = st.columns(len(opciones))
    for idx, (key, label) in enumerate(opciones):
        with cols[idx]:
            if st.button(label, key=f"spotlight_{key}", use_container_width=True, type="primary" if st.session_state[state_key] == key else "secondary"):
                st.session_state[state_key] = key
                st.rerun()
    foco = st.session_state[state_key]
    col_main, col_side = st.columns([1.35, 0.65])
    with col_main:
        if foco == "pulso":
            st.markdown("""
                <div class="spotlight-shell">
                    <div class="spotlight-badge">Pulso semanal</div>
                    <div class="spotlight-title">La vista rápida del ritmo financiero</div>
                    <div class="spotlight-copy">Aquí se combinan ingresos reales, gastos, deuda recibida y pagos para darte una lectura más completa de tu tracción reciente.</div>
                </div>
            """, unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            with m1:
                render_spotlight_metric("Ingreso semanal", money(total_ingresos_local / 4 if total_ingresos_local else 0), "Promedio estimado del mes")
            with m2:
                render_spotlight_metric("Cambio de gasto", money_delta(comparativa.get("gasto_semana_pct", 0.0)), "Semana actual vs pasada")
            with m3:
                render_spotlight_metric("Siguiente paso", resumen_semanal.get("accion", "Sigue registrando"), "Acción más útil ahora")
            flujo = construir_flujo_semanal(df_base)
            if not flujo.empty:
                fig = px.line(flujo, x="semana", y="monto", color="tipo", title="Pulso de las últimas semanas", markers=True,
                              color_discrete_map={"Ingreso": "#22C55E", "Gasto": "#EF4444", "Ingreso (Deuda)": "#3B82F6", "Pago de deuda": "#F59E0B"})
                aplicar_estilo_plotly(fig, height=360)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                empty_state("Aún no hay pulso semanal", "Cuando acumules algunos movimientos, Zentix resaltará aquí tu ritmo real con comparativas visuales.")
        elif foco == "gastos":
            top_categoria_local, top_monto_local, top_share_local = obtener_top_categoria(df_mes_actual[df_mes_actual["tipo"] == "Gasto"] if df_mes_actual is not None and not df_mes_actual.empty else pd.DataFrame())
            st.markdown("""
                <div class="spotlight-shell">
                    <div class="spotlight-badge">Gasto dominante</div>
                    <div class="spotlight-title">Tu punto de fuga más importante</div>
                    <div class="spotlight-copy">Zentix resalta la categoría que más pesa y te da contexto visual para decidir dónde ajustar con precisión.</div>
                </div>
            """, unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            with m1:
                render_spotlight_metric("Categoría top", top_categoria_local if top_categoria_local else "Sin datos", "La que más pesa este mes")
            with m2:
                render_spotlight_metric("Monto top", money(top_monto_local), "Presión principal del mes")
            with m3:
                render_spotlight_metric("Participación", f"{round((top_share_local or 0) * 100, 1)}%", "Dentro del gasto total")
            top_gastos = construir_top_gastos_mes(df_mes_actual)
            if not top_gastos.empty:
                fig = px.bar(top_gastos.sort_values("monto", ascending=True), x="monto", y="categoria", orientation="h", title="Top categorías de gasto del mes", text_auto=True,
                             color="monto", color_continuous_scale=["#1D4ED8", "#06B6D4", "#8B5CF6"])
                fig.update_coloraxes(showscale=False)
                aplicar_estilo_plotly(fig, height=360)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                empty_state("Todavía no hay gasto dominante", "Cuando registres gastos, aquí aparecerá una lectura visual clara de tus categorías más importantes.")
        elif foco == "deuda":
            st.markdown("""
                <div class="spotlight-shell">
                    <div class="spotlight-badge">Deuda y caja</div>
                    <div class="spotlight-title">Dinero que entra, pero no es ingreso real</div>
                    <div class="spotlight-copy">Zentix separa lo tuyo de lo prestado para que tu panel se vea elegante y financieramente honesto.</div>
                </div>
            """, unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            with m1:
                render_spotlight_metric("Entradas por deuda", money(entradas_deuda_local), "Sí entran a caja")
            with m2:
                render_spotlight_metric("Pagos de deuda", money(pagos_deuda_local), "Seguimiento de devolución")
            with m3:
                render_spotlight_metric("Pendiente", money(saldo_pendiente_local), "Saldo total por devolver")
            modo, deuda_chart = construir_deuda_chart(df_deudas_local, entradas_deuda_local, pagos_deuda_local, saldo_pendiente_local)
            if not deuda_chart.empty:
                if modo == "activa":
                    fig = px.pie(deuda_chart, values="saldo_pendiente", names="nombre", title="Deudas activas por saldo pendiente", hole=0.55, color_discrete_sequence=CHART_COLORS)
                else:
                    fig = px.bar(deuda_chart, x="concepto", y="monto", title="Flujo actual de deuda", text_auto=True, color="concepto",
                                 color_discrete_map={"Entradas por deuda": "#3B82F6", "Pagos de deuda": "#F59E0B", "Saldo pendiente": "#8B5CF6"})
                aplicar_estilo_plotly(fig, height=360)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                empty_state("Sin deuda activa", "Aquí verás de forma elegante tus entradas por deuda, devoluciones y saldo pendiente cuando existan registros.")
        else:
            st.markdown("""
                <div class="spotlight-shell">
                    <div class="spotlight-badge">Meta viva</div>
                    <div class="spotlight-title">Una meta que se siente alcanzable</div>
                    <div class="spotlight-copy">Tu objetivo deja de ser un número estático. Zentix lo convierte en ritmo, avance y una lectura accionable de cuánto falta.</div>
                </div>
            """, unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            with m1:
                render_spotlight_metric("Meta", money(meta_objetivo), "Objetivo principal")
            with m2:
                render_spotlight_metric("Disponible", money(ahorro_disponible), "Lo que hoy tienes a favor")
            with m3:
                render_spotlight_metric("Ritmo semanal", money(proyeccion.get("aporte_semanal", 0)), "Aporte estimado")
            meta_chart = construir_meta_chart(meta_objetivo, ahorro_disponible)
            fig = px.bar(meta_chart, x="concepto", y="monto", title="Progreso visual de la meta", text_auto=True, color="concepto",
                         color_discrete_map={"Disponible": "#22C55E", "Faltante": "#8B5CF6", "Meta pendiente de definir": "#334155"})
            aplicar_estilo_plotly(fig, height=360)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col_side:
        if foco == "pulso":
            items = resumen_semanal.get("positivas", [])[:2] + alertas[:1]
            subtitle = "Lo que ya está bien y lo que conviene vigilar sin mirar cinco paneles a la vez."
        elif foco == "gastos":
            items = sugerencias[:2] + [f"Cambio mensual de gasto: {money_delta(comparativa.get('gasto_mes_pct', 0.0))}"]
            subtitle = "Ideas concretas para limpiar categorías y reducir fuga sin saturar la experiencia."
        elif foco == "deuda":
            items = [f"Deudas activas: {int((df_deudas_local['saldo_pendiente'] > 0).sum()) if df_deudas_local is not None and not df_deudas_local.empty else 0}", f"Pendiente actual: {money(saldo_pendiente_local)}", "Tus KPIs de ingreso real ya no se contaminan con dinero prestado."]
            subtitle = "Una lectura limpia para distinguir caja disponible de obligación futura."
        else:
            items = [proyeccion.get("mensaje", "Sin proyección disponible"), globals().get("recomendacion_accionable", ""), f"Plan actual: {plan_actual.get('plan', 'free').upper()} · IA: {consultas_usadas}/{consultas_limite}"]
            items = [x for x in items if x]
            subtitle = "Meta, IA y siguiente paso concentrados en un solo lugar útil."
        st.markdown(f"""
            <div class="spotlight-side-card">
                <div class="spotlight-side-title">Resumen destacado</div>
                <div class="spotlight-side-sub">{subtitle}</div>
                <ul class="spotlight-list">{''.join([f'<li style="margin-bottom:0.4rem;">{item}</li>' for item in items])}</ul>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("""
            <div class="spotlight-side-card">
                <div class="spotlight-side-title">Sigue explorando en esta página</div>
                <div class="spotlight-side-sub">Más abajo encontrarás visualización mensual, lectura inteligente, comparativas y el avatar IA para profundizar sin cambiar de contexto.</div>
                <div class="feature-signal-chips">
                    <span class="feature-chip">Lectura del mes</span>
                    <span class="feature-chip">Avatar IA</span>
                    <span class="feature-chip">Gráficas premium</span>
                    <span class="feature-chip">Comparativas</span>
                </div>
            </div>
        """, unsafe_allow_html=True)


def render_registrar_spotlight(tipo, monto, categoria, deuda_nombre, prestamista, saldo_deuda_actual, es_recurrente, frecuencia_recurrencia, df_mes_actual):
    tipo_base = "Ingreso" if tipo == "Ingreso" else "Gasto" if tipo == "Gasto" else tipo
    promedio_tipo = 0.0
    if df_mes_actual is not None and not df_mes_actual.empty and "tipo" in df_mes_actual.columns:
        muestra = df_mes_actual[df_mes_actual["tipo"] == tipo_base] if tipo_base in ["Ingreso", "Gasto"] else pd.DataFrame()
        if not muestra.empty:
            promedio_tipo = float(muestra["monto"].mean() or 0)
    st.markdown("""
        <div class="spotlight-side-card">
            <div class="spotlight-side-title">Spotlight del registro</div>
            <div class="spotlight-side-sub">La interfaz se adapta al tipo que elijas y aquí te resume qué estás haciendo antes de guardar.</div>
        </div>
    """, unsafe_allow_html=True)
    with st.expander("✨ Enfoque dinámico del movimiento", expanded=True):
        info = {
            "Ingreso": "Estás registrando dinero propio que sí alimenta tus KPIs reales.",
            "Gasto": "Este gasto impacta tu caja operativa y puede afectar tus patrones del mes.",
            "Ingreso (Deuda)": "Corresponde a un crédito solicitado: entra a caja, pero Zentix lo separa del ingreso real para que tu lectura siga siendo honesta.",
            "Pago de deuda": "Este pago a crédito reduce tu obligación pendiente y mejora tu salud financiera, aunque salga de caja.",
            "Cuenta por cobrar": "Registras dinero que prestaste; aún no entra como ingreso real hasta que te paguen.",
            "Cobro cuenta por cobrar": "Este pago recibido sí entra a caja y mejora tu disponible sin inflar ventas no pagadas."
        }
        st.markdown(f"<div class='tiny-muted' style='margin-bottom:0.6rem;'>{info.get(tipo, 'Registro contextual.')}</div>", unsafe_allow_html=True)
        x1, x2 = st.columns(2)
        with x1:
            render_spotlight_metric("Tipo", tipo_display(tipo), "Naturaleza activa")
        with x2:
            render_spotlight_metric("Monto", money(monto or 0), "Lectura inmediata")
        if tipo == "Pago de deuda" and saldo_deuda_actual > 0:
            data = pd.DataFrame({"concepto": ["Pago a crédito", "Saldo actual", "Saldo luego"], "monto": [float(monto or 0), float(saldo_deuda_actual), float(max(saldo_deuda_actual - float(monto or 0), 0))]})
        elif tipo == "Ingreso (Deuda)":
            data = pd.DataFrame({"concepto": ["Crédito solicitado", "Pendiente total actual"], "monto": [float(monto or 0), float(globals().get('saldo_pendiente_deudas_global', 0) or 0)]})
        elif tipo == "Cuenta por cobrar":
            data = pd.DataFrame({"concepto": ["Prestaste Dinero", "Pendiente actual por recibir"], "monto": [float(monto or 0), float(globals().get('saldo_pendiente_cxc_global', 0) or 0)]})
        elif tipo == "Cobro cuenta por cobrar":
            data = pd.DataFrame({"concepto": ["Cobro actual", "Pendiente por cobrar"], "monto": [float(monto or 0), float(globals().get('saldo_pendiente_cxc_global', 0) or 0)]})
        else:
            data = pd.DataFrame({"concepto": ["Este movimiento", "Promedio del tipo"], "monto": [float(monto or 0), float(promedio_tipo or 0)]})
        fig = px.bar(data, x="concepto", y="monto", title="Lectura rápida del movimiento", text_auto=True, color="concepto", color_discrete_sequence=CHART_COLORS)
        aplicar_estilo_plotly(fig, height=300)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        chips = [categoria or "Contextual", deuda_nombre or "Sin deuda", prestamista or "Sin prestamista", frecuencia_recurrencia if es_recurrente and frecuencia_recurrencia else "No recurrente"]
        st.markdown(f"<div class='feature-signal-chips'>{''.join([f'<span class="feature-chip">{chip}</span>' for chip in chips])}</div>", unsafe_allow_html=True)


def render_perfil_spotlight(plan_actual, consultas_usadas, consultas_limite, preferencias, resumen_recordatorios, meta_nombre, meta_valor, saldo_pendiente, proyeccion):
    activos = sum([
        bool(preferencias.get("recordatorio_email")),
        bool(preferencias.get("recordatorio_sms")),
        bool(preferencias.get("recordatorio_registro")),
        bool(preferencias.get("recordatorio_meta")),
        bool(preferencias.get("resumen_semanal"))
    ])
    st.markdown("""
        <div class="spotlight-shell">
            <div class="spotlight-badge">Spotlight de experiencia</div>
            <div class="spotlight-title">Lo que hoy define tu versión de Zentix</div>
            <div class="spotlight-copy">Plan, IA, recordatorios y meta principal reunidos en una lectura más editorial y premium.</div>
        </div>
    """, unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1:
        render_spotlight_metric("Plan", plan_actual.get("plan", "free").upper(), "Nivel activo")
    with m2:
        render_spotlight_metric("IA restante", str(max(int(consultas_limite or 0) - int(consultas_usadas or 0), 0)), "Disponible hoy")
    with m3:
        render_spotlight_metric("Preferencias activas", str(activos), "Señales encendidas")
    with st.expander("✨ Panel inteligente de perfil", expanded=True):
        data = pd.DataFrame({
            "concepto": ["IA usada", "IA restante", "Preferencias activas"],
            "monto": [float(consultas_usadas or 0), float(max(int(consultas_limite or 0) - int(consultas_usadas or 0), 0)), float(activos)]
        })
        fig = px.bar(data, x="concepto", y="monto", title="Pulso de tu experiencia actual", text_auto=True, color="concepto", color_discrete_sequence=CHART_COLORS)
        aplicar_estilo_plotly(fig, height=300)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown(f"""
            <div class="mini-soft-card">
                <div class="tiny-muted">Meta principal</div>
                <div style="font-weight:800;line-height:1.5;">{meta_nombre if meta_nombre else 'Sin nombre'} · {money(meta_valor)}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Proyección</div>
                <div style="font-weight:700;line-height:1.5;">{proyeccion.get('mensaje', 'Sin proyección')}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Saldo pendiente de deudas</div>
                <div style="font-weight:700;line-height:1.5;">{money(saldo_pendiente)}</div>
            </div>
        """, unsafe_allow_html=True)
        st.info(resumen_recordatorios.get("sugerencia", "Sin evaluación de recordatorios por ahora."))



def render_automation_control_center():
    if not mostrar_paneles_internos():
        return

    cfg = obtener_automation_runtime_config()
    url_job = construir_url_job_recordatorios(limit=25)
    st.markdown(
        """
        <div class="soft-card fade-up">
            <div class="section-title">Centro de automatización</div>
            <div class="section-caption">Zentix queda listo para correr recordatorios en segundo plano con un cron externo seguro.</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    if cfg.get("enabled") and url_job:
        st.code(url_job, language="text")
        st.caption("Puedes usar esta URL desde un cron externo, GitHub Actions o un scheduler para disparar recordatorios sin que nadie abra la app.")
    else:
        st.info("Opcional: si algún día quieres recordatorios totalmente en segundo plano, agrega APP_BASE_URL y AUTOMATION_JOB_TOKEN en secrets y conecta un cron externo seguro.")

def render_tutorial_zentix(pagina, nombre, user_id, df_base, meta_actual, preferencias):
    state = obtener_estado_tutorial_usuario(user_id, df_base, meta_actual)
    total_mov = 0 if df_base is None else len(df_base.index)

    if state.get("completado"):
        return

    if state.get("paso") == "registro" and total_mov > 0:
        state = guardar_estado_tutorial_usuario(user_id, paso="analisis", activo=True)
    if state.get("paso") == "ahorro" and float(meta_actual or 0) > 0:
        state = guardar_estado_tutorial_usuario(user_id, paso="perfil", activo=True)

    if not state.get("activo"):
        if st.button("Activar mini tutorial premium", key=f"activar_tutorial_{pagina}", use_container_width=True, type="secondary"):
            guardar_estado_tutorial_usuario(user_id, activo=True)
            st.rerun()
        return

    pasos = [
        {"id": "intro", "page": "Inicio", "title": "Conoce el corazón del panel", "desc": "Aquí verás el pulso de tu dinero, el foco inteligente, gráficas y al avatar Zentix explicándote qué significa cada cosa."},
        {"id": "registro", "page": "Registrar", "title": "Haz tu primer registro guiado", "desc": "Registra un ingreso, un gasto o una deuda. El formulario ya se adapta solo según lo que elijas."},
        {"id": "analisis", "page": "Análisis", "title": "Lee patrones y comparativas", "desc": "Después de registrar, Zentix te mostrará patrones, comparativas semanales y lectura mensual con contexto."},
        {"id": "ahorro", "page": "Ahorro", "title": "Ponle nombre a tu meta", "desc": "Convierte tu ahorro en un objetivo real con nombre, progreso y una proyección premium de llegada."},
        {"id": "perfil", "page": "Perfil", "title": "Afina recordatorios y plan", "desc": "Deja tu experiencia lista: plan, IA diaria, recordatorios suaves y preferencias futuras."},
    ]
    paso_actual = state.get("paso", "intro")
    progreso_ids = ["intro"]
    if total_mov > 0:
        progreso_ids.append("registro")
    if paso_actual in {"ahorro", "perfil"}:
        progreso_ids.append("analisis")
    if float(meta_actual or 0) > 0:
        progreso_ids.append("ahorro")
    if paso_actual == "perfil":
        progreso_ids.append("perfil")
    pendiente = next((step for step in pasos if step["id"] == paso_actual), pasos[0])
    progress = min(sum(1 for step in pasos if step["id"] in set(progreso_ids)) / len(pasos), 1.0)
    chips_html = "".join([
        f"<span class='tutorial-step-chip {'is-done' if step['id'] in set(progreso_ids) and step['id'] != paso_actual else 'is-active' if step['id'] == paso_actual else ''}'>{'✓ ' if step['id'] in set(progreso_ids) and step['id'] != paso_actual else ''}{step['title']}</span>"
        for step in pasos
    ])
    st.markdown(
        f"""
        <div class="tutorial-card">
            <div class="tutorial-badge">Onboarding guiado por Zentix</div>
            <div class="tutorial-title">{nombre}, tu experiencia premium va paso a paso</div>
            <div class="tutorial-copy">Paso actual: <strong>{pendiente['title']}</strong>. {pendiente['desc']}</div>
            <div class="tutorial-step-row">{chips_html}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.progress(progress)
    c1, c2, c3 = st.columns([1.15, 1, 0.85])
    with c1:
        if pendiente["page"] != pagina:
            if st.button(f"Ir a {pendiente['page']}", key=f"tutorial_ir_{pagina}_{pendiente['id']}", use_container_width=True, type="primary"):
                st.session_state.pagina = pendiente["page"]
                st.rerun()
        else:
            if pendiente["id"] == "intro":
                if st.button("Entendido, continuar", key=f"tutorial_intro_ok_{pagina}", use_container_width=True, type="primary"):
                    guardar_estado_tutorial_usuario(user_id, paso="registro", activo=True)
                    st.session_state.pagina = "Registrar"
                    st.rerun()
            elif pendiente["id"] == "registro":
                if total_mov > 0:
                    st.success("Perfecto. Ya hiciste tu primer registro.")
                    if st.button("Siguiente: ver análisis", key=f"tutorial_registro_next_{pagina}", use_container_width=True, type="primary"):
                        guardar_estado_tutorial_usuario(user_id, paso="analisis", activo=True)
                        st.session_state.pagina = "Análisis"
                        st.rerun()
                else:
                    st.info("Haz tu primer movimiento en esta misma pantalla. Cuando lo guardes, el tutorial avanzará solo.")
            elif pendiente["id"] == "analisis":
                if st.button("Ya revisé esta sección", key=f"tutorial_analisis_ok_{pagina}", use_container_width=True, type="primary"):
                    guardar_estado_tutorial_usuario(user_id, paso="ahorro", activo=True)
                    st.session_state.pagina = "Ahorro"
                    st.rerun()
            elif pendiente["id"] == "ahorro":
                if float(meta_actual or 0) > 0:
                    st.success("Excelente. Tu meta ya tiene identidad.")
                    if st.button("Siguiente: abrir perfil", key=f"tutorial_ahorro_next_{pagina}", use_container_width=True, type="primary"):
                        guardar_estado_tutorial_usuario(user_id, paso="perfil", activo=True)
                        st.session_state.pagina = "Perfil"
                        st.rerun()
                else:
                    st.info("Ponle nombre y monto a tu primera meta. Cuando la guardes, Zentix continuará contigo.")
            elif pendiente["id"] == "perfil":
                if st.button("Finalizar guía", key=f"tutorial_perfil_ok_{pagina}", use_container_width=True, type="primary"):
                    guardar_estado_tutorial_usuario(user_id, completado=True, paso="perfil", activo=False)
                    st.success("Mini tutorial completado. Tu experiencia premium ya quedó presentada paso a paso.")
                    st.rerun()
    with c2:
        if st.button("Pausar tutorial", key=f"tutorial_pause_{pagina}", use_container_width=True, type="secondary"):
            guardar_estado_tutorial_usuario(user_id, activo=False)
            st.rerun()
    with c3:
        if st.button("Cerrar guía", key=f"tutorial_close_{pagina}", use_container_width=True, type="secondary"):
            guardar_estado_tutorial_usuario(user_id, completado=True, activo=False)
            st.rerun()


def obtener_movimientos_recientes_para_ia(df_mes_actual, limite=8):
    if df_mes_actual is None or df_mes_actual.empty:
        return "No hay movimientos registrados este mes."

    vista = df_mes_actual.copy().sort_values("fecha", ascending=False).head(limite)

    lineas = []
    for _, row in vista.iterrows():
        fecha_txt = row["fecha"].strftime("%Y-%m-%d") if pd.notna(row["fecha"]) else "Sin fecha"
        tipo = row.get("tipo", "Sin tipo")
        categoria = row.get("categoria", "Sin categoría") or "Sin categoría"
        monto = money(row.get("monto", 0))
        descripcion = row.get("descripcion", "") or "Sin descripción"
        deuda_txt = row.get("deuda_nombre", "") or ""
        prestamista_txt = row.get("prestamista", "") or ""

        extras = []
        if deuda_txt:
            extras.append(f"deuda: {deuda_txt}")
        if prestamista_txt:
            extras.append(f"prestamista: {prestamista_txt}")

        extra_texto = f" | {' | '.join(extras)}" if extras else ""
        lineas.append(f"- {fecha_txt} | {tipo} | {categoria} | {monto} | {descripcion}{extra_texto}")

    return "\n".join(lineas)


def construir_contexto_zentix(pagina, nombre, total_ingresos, total_gastos, ahorro_actual, ultimo_tipo):
    df_mes_actual = globals().get("df_mes", pd.DataFrame())
    meta_actual = float(globals().get("meta_guardada_global", 0.0) or 0.0)
    categoria_top_actual = globals().get("categoria_top", None)
    monto_top_actual = float(globals().get("monto_top", 0.0) or 0.0)
    insight_actual = globals().get("insight_personalizado", globals().get("insight_financiero", "Sin insight disponible."))
    perfil_actual = globals().get("perfil_financiero", {})
    alertas_actuales = globals().get("alertas_proactivas", [])
    resumen_semanal_actual = globals().get("resumen_semanal_premium", {})
    comparativa_actual = globals().get("comparativa_periodos", {})
    recomendacion_actual = globals().get("recomendacion_accionable", "")
    patrones_actuales = globals().get("patrones_comportamiento", [])
    sugerencias_actuales = globals().get("sugerencias_categoria", [])
    plan_actual = globals().get("plan_usuario_actual", {})
    consultas_restantes = globals().get("consultas_restantes_hoy", 0)
    nombre_meta = globals().get("nombre_meta_guardado", "")
    entradas_deuda = float(globals().get("total_entradas_deuda_mes", 0.0) or 0.0)
    pagos_deuda = float(globals().get("total_pagos_deuda_mes", 0.0) or 0.0)
    saldo_pendiente_deudas = float(globals().get("saldo_pendiente_deudas_global", 0.0) or 0.0)
    categorias_favoritas = globals().get("categorias_favoritas_global", [])
    proyeccion_meta = globals().get("proyeccion_meta_global", {})
    resumen_recordatorios = globals().get("resumen_recordatorios_global", {})
    preferencias_usuario = globals().get("preferencias_usuario_actual", {})

    movimientos_texto = obtener_movimientos_recientes_para_ia(df_mes_actual, limite=8)

    positivas = "\n".join([f"- {x}" for x in resumen_semanal_actual.get("positivas", [])]) or "- Sin positivas registradas."
    alertas = "\n".join([f"- {x}" for x in alertas_actuales]) or "- Sin alertas."
    patrones = "\n".join([f"- {x}" for x in patrones_actuales]) or "- Sin patrones."
    sugerencias = "\n".join([f"- {x}" for x in sugerencias_actuales]) or "- Sin sugerencias."
    favoritas = ", ".join(categorias_favoritas) if categorias_favoritas else "Sin favoritas todavía"
    comparativa_linea = (
        f"Gasto semana: {money_delta(comparativa_actual.get('gasto_semana_pct', 0.0))} | "
        f"Ingreso semana: {money_delta(comparativa_actual.get('ingreso_semana_pct', 0.0))} | "
        f"Gasto mes: {money_delta(comparativa_actual.get('gasto_mes_pct', 0.0))} | "
        f"Ingreso mes: {money_delta(comparativa_actual.get('ingreso_mes_pct', 0.0))}"
    )

    return f"""
CONTEXTO DE ZENTIX
- Página actual: {pagina}
- Usuario: {nombre}
- Plan actual: {plan_actual.get('plan', 'free')}
- Consultas IA restantes hoy: {consultas_restantes}
- Perfil financiero: {perfil_actual.get('titulo', 'Sin perfil')}
- Descripción del perfil: {perfil_actual.get('descripcion', 'Sin descripción')}
- Ingresos reales del mes: {money(total_ingresos)}
- Gastos operativos del mes: {money(total_gastos)}
- Entradas por deuda del mes: {money(entradas_deuda)}
- Pagos de deuda del mes: {money(pagos_deuda)}
- Saldo disponible actual: {money(ahorro_actual)}
- Saldo pendiente de deudas: {money(saldo_pendiente_deudas)}
- Meta de ahorro actual: {money(meta_actual)}
- Nombre de la meta: {nombre_meta if nombre_meta else 'Sin nombre definido'}
- Proyección de meta: {proyeccion_meta.get('mensaje', 'Sin proyección')}
- Categorías favoritas: {favoritas}
- Categoría con mayor peso: {categoria_top_actual if categoria_top_actual else 'Sin datos'}
- Monto de categoría top: {money(monto_top_actual)}
- Último tipo de movimiento: {ultimo_tipo if ultimo_tipo else 'Sin movimientos'}
- Insight financiero actual: {insight_actual}
- Recomendación accionable: {recomendacion_actual}
- Comparativas: {comparativa_linea}

PREFERENCIAS Y RECORDATORIOS
- Email activado: {preferencias_usuario.get('recordatorio_email', False)}
- SMS activado: {preferencias_usuario.get('recordatorio_sms', False)}
- Frecuencia recordatorios: {preferencias_usuario.get('frecuencia_recordatorios', 'suave')}
- Recordatorio de registro: {preferencias_usuario.get('recordatorio_registro', False)}
- Alertas de meta: {preferencias_usuario.get('recordatorio_meta', False)}
- Resumen semanal: {preferencias_usuario.get('resumen_semanal', False)}
- Resumen motor recordatorios: {resumen_recordatorios.get('sugerencia', 'Sin evaluación')}

RESUMEN SEMANAL PREMIUM
{positivas}
- Acción recomendada: {resumen_semanal_actual.get('accion', 'Sigue registrando movimientos.')}

ALERTAS PROACTIVAS
{alertas}

PATRONES DE COMPORTAMIENTO
{patrones}

SUGERENCIAS DE CATEGORÍAS
{sugerencias}

MOVIMIENTOS RECIENTES DEL MES
{movimientos_texto}
""".strip()


def extraer_valor_contexto_zentix(contexto, etiqueta, default=""):
    for linea in str(contexto or "").splitlines():
        linea_strip = linea.strip()
        if linea_strip.startswith(etiqueta):
            return linea_strip.split(":", 1)[1].strip() if ":" in linea_strip else linea_strip.replace(etiqueta, "").strip()
    return default


def extraer_bloque_contexto_zentix(contexto, titulo_inicio, titulo_fin=None, limite=2):
    lineas = str(contexto or "").splitlines()
    capturando = False
    items = []
    for linea in lineas:
        linea_strip = linea.strip()
        if linea_strip == titulo_inicio:
            capturando = True
            continue
        if capturando and titulo_fin and linea_strip == titulo_fin:
            break
        if capturando and linea_strip.startswith("-"):
            texto = linea_strip.lstrip("-").strip()
            if texto:
                items.append(texto)
    return items[:limite]


def generar_respuesta_zentix_local(pregunta, contexto):
    pregunta_txt = str(pregunta or "").strip()
    pregunta_norm = pregunta_txt.lower()

    ingresos = extraer_valor_contexto_zentix(contexto, "- Ingresos reales del mes", "Sin dato")
    gastos = extraer_valor_contexto_zentix(contexto, "- Gastos operativos del mes", "Sin dato")
    disponible = extraer_valor_contexto_zentix(contexto, "- Saldo disponible actual", "Sin dato")
    saldo_deuda = extraer_valor_contexto_zentix(contexto, "- Saldo pendiente de deudas", "Sin dato")
    meta = extraer_valor_contexto_zentix(contexto, "- Meta de ahorro actual", "Sin dato")
    proyeccion = extraer_valor_contexto_zentix(contexto, "- Proyección de meta", "Sin proyección")
    categoria_top = extraer_valor_contexto_zentix(contexto, "- Categoría con mayor peso", "Sin datos")
    recomendacion = extraer_valor_contexto_zentix(contexto, "- Recomendación accionable", "Sigue registrando para afinar la lectura.")

    alertas = extraer_bloque_contexto_zentix(contexto, "ALERTAS PROACTIVAS", "PATRONES DE COMPORTAMIENTO", limite=2)
    patrones = extraer_bloque_contexto_zentix(contexto, "PATRONES DE COMPORTAMIENTO", "SUGERENCIAS DE CATEGORÍAS", limite=2)

    bullets = []
    encabezado = "Te dejo una lectura rápida y accionable:"

    if any(token in pregunta_norm for token in ["deuda", "crédito", "credito", "préstamo", "prestamo"]):
        bullets.append(f"Saldo pendiente actual de deudas: {saldo_deuda}.")
        bullets.append(f"Disponible actual: {disponible}.")
        bullets.append(recomendacion)
    elif any(token in pregunta_norm for token in ["meta", "ahorro", "ahorrar"]):
        bullets.append(f"Meta actual: {meta}.")
        bullets.append(f"Disponible / ahorro actual: {disponible}.")
        bullets.append(proyeccion)
    elif any(token in pregunta_norm for token in ["gasto", "gastos", "categoría", "categoria"]):
        bullets.append(f"Gastos operativos del mes: {gastos}.")
        bullets.append(f"La categoría con mayor peso ahora es: {categoria_top}.")
        bullets.append(recomendacion)
    else:
        bullets.append(f"Ingresos reales del mes: {ingresos}.")
        bullets.append(f"Gastos operativos del mes: {gastos}.")
        bullets.append(f"Disponible actual: {disponible}.")
        bullets.append(recomendacion)

    if alertas:
        bullets.append(f"Alerta clave: {alertas[0]}")
    elif patrones:
        bullets.append(f"Patrón observado: {patrones[0]}")

    bullets = bullets[:4]
    return encabezado + "\n- " + "\n- ".join([b for b in bullets if b])


def consultar_ia_zentix(pregunta, contexto):
    if not openai_client:
        return "La IA todavía no está activa. Agrega GEMINI_API_KEY en los secrets de Streamlit Cloud para habilitar al avatar."

    contexto = str(contexto or "").strip()
    if len(contexto) > 9000:
        contexto = contexto[:9000]

    mensajes = [
        {
            "role": "system",
            "content": (
                "Eres Avatar Zentix, un coach financiero premium dentro de una app de finanzas personales. "
                "Hablas siempre en español. "
                "Tu tono es elegante, claro, cálido, útil y muy personalizado. "
                "No hablas como un banco; hablas como un asistente inteligente que entiende hábitos y comportamiento. "
                "Usa únicamente el contexto recibido. "
                "Nunca inventes cifras, categorías o movimientos. "
                "Si algo no está en el contexto, dilo con honestidad. "
                "No des asesoría financiera profesional, legal ni tributaria. "
                "Responde de forma breve pero valiosa, idealmente entre 4 y 8 líneas. "
                "Cuando convenga, usa viñetas cortas. "
                "Da recomendaciones aterrizadas, accionables y humanas. "
                "Si detectas oportunidad de mejora, exprésala con tacto. "
                "Adapta tu voz al perfil financiero del usuario."
            )
        },
        {
            "role": "user",
            "content": f"{contexto}\n\nPREGUNTA DEL USUARIO:\n{pregunta}"
        }
    ]

    ultimo_error = ""
    fragmentos_reintentables = [
        "503", "429", "500", "502", "504", "timeout", "timed out", "deadline",
        "unavailable", "high demand", "resource_exhausted", "temporarily unavailable",
        "overloaded", "rate limit"
    ]

    for model_name in GEMINI_MODEL_CANDIDATES:
        for intento in range(2):
            try:
                response = openai_client.chat.completions.create(
                    model=model_name,
                    messages=mensajes,
                    temperature=0.35,
                    max_tokens=380,
                )

                texto = response.choices[0].message.content if response and response.choices else ""

                if isinstance(texto, list):
                    partes = []
                    for item in texto:
                        if isinstance(item, dict) and item.get("type") == "text":
                            partes.append(item.get("text", ""))
                    texto = "".join(partes)

                texto = (texto or "").strip()
                if texto:
                    return texto

                ultimo_error = f"Respuesta vacía desde {model_name}"
            except Exception as e:
                ultimo_error = str(e)
                error_normalizado = ultimo_error.lower()
                es_reintentable = any(fragmento in error_normalizado for fragmento in fragmentos_reintentables)
                if es_reintentable and intento < 1:
                    time.sleep(0.8 + (0.7 * intento))
                    continue
                break

    return generar_respuesta_zentix_local(pregunta, contexto)


def obtener_mensajes_iniciales_zentix(nombre):
    return {
        "Inicio": f"Hola, {nombre}. Soy Zentix. Ya distingo tus ingresos reales de tus movimientos por deuda y puedo resumirte tu panorama.",
        "Registrar": f"Hola, {nombre}. Registra ingresos, gastos, deudas y recurrencias sin contaminar tus KPIs reales.",
        "Análisis": f"Hola, {nombre}. Pregúntame por patrones, alertas, comparativas, deuda pendiente o categorías dominantes.",
        "Ahorro": f"Hola, {nombre}. Puedo ayudarte a leer tu progreso, cuánto te falta y cuál sería un ritmo semanal razonable.",
        "Perfil": f"Hola, {nombre}. Aquí también puedo ayudarte a decidir qué recordatorios activar y cómo aprovechar mejor tu plan."
    }


def obtener_claves_chat_zentix(pagina):
    chat_key = f"zentix_chat_{pagina}"
    input_key = f"zentix_input_{pagina}"
    clear_key = f"zentix_clear_{pagina}"
    return chat_key, input_key, clear_key


def asegurar_estado_chat_zentix(pagina, nombre):
    chat_key, input_key, clear_key = obtener_claves_chat_zentix(pagina)
    mensajes_iniciales = obtener_mensajes_iniciales_zentix(nombre)

    if chat_key not in st.session_state:
        st.session_state[chat_key] = [
            {"role": "assistant", "content": mensajes_iniciales.get(pagina, "Hola. Soy tu avatar financiero de Zentix.")}
        ]

    if clear_key not in st.session_state:
        st.session_state[clear_key] = False

    if st.session_state.get(clear_key):
        st.session_state[input_key] = ""
        st.session_state[clear_key] = False

    return chat_key, input_key, clear_key, mensajes_iniciales


def obtener_data_uri_imagen(path_obj):
    try:
        if path_obj and Path(path_obj).exists():
            mime = "image/png"
            if str(path_obj).lower().endswith((".jpg", ".jpeg")):
                mime = "image/jpeg"
            b64 = base64.b64encode(Path(path_obj).read_bytes()).decode()
            return f"data:{mime};base64,{b64}"
    except Exception:
        pass
    return ""


def limpiar_query_params_zentix(preservar_chat=False):
    try:
        if preservar_chat:
            st.query_params["zchat"] = "open"
        else:
            try:
                del st.query_params["zchat"]
            except Exception:
                pass
        for clave in ["zq", "zclear", "zpage"]:
            try:
                del st.query_params[clave]
            except Exception:
                pass
    except Exception:
        pass


def procesar_chat_flotante_zentix(pagina, nombre, contexto_ia):
    chat_key, input_key, clear_key, mensajes_iniciales = asegurar_estado_chat_zentix(pagina, nombre)

    try:
        pregunta_url = st.query_params.get("zq")
        clear_url = st.query_params.get("zclear")
        pagina_url = st.query_params.get("zpage")
    except Exception:
        pregunta_url = None
        clear_url = None
        pagina_url = None

    if isinstance(pregunta_url, list):
        pregunta_url = pregunta_url[0] if pregunta_url else None
    if isinstance(clear_url, list):
        clear_url = clear_url[0] if clear_url else None
    if isinstance(pagina_url, list):
        pagina_url = pagina_url[0] if pagina_url else None

    if pagina_url and str(pagina_url) != str(pagina):
        return chat_key, input_key, clear_key, mensajes_iniciales

    if str(clear_url or "").strip().lower() in {"1", "true", "yes", "si", "sí"}:
        st.session_state[chat_key] = [
            {"role": "assistant", "content": mensajes_iniciales.get(pagina, "Hola. Soy tu avatar financiero de Zentix.")}
        ]
        st.session_state[clear_key] = True
        limpiar_query_params_zentix(preservar_chat=True)
        st.rerun()

    pregunta_final = str(pregunta_url or "").strip()
    if pregunta_final:
        st.session_state[chat_key].append({"role": "user", "content": pregunta_final})

        permitido, usadas, limite, _, plan = puede_usar_ia(st.session_state.user.id)

        if not permitido:
            respuesta = (
                f"Has alcanzado tu límite diario de IA ({limite} consultas) en el plan "
                f"{plan.get('plan', 'free')}. Pásate a Pro para tener más acceso y análisis más profundos."
            )
        else:
            with st.spinner("Zentix está analizando tu información..."):
                respuesta = consultar_ia_zentix(pregunta_final, contexto_ia)
            registrar_uso_ia(st.session_state.user.id)

        st.session_state[chat_key].append({"role": "assistant", "content": respuesta})
        st.session_state[clear_key] = True
        limpiar_query_params_zentix(preservar_chat=True)
        st.rerun()

    return chat_key, input_key, clear_key, mensajes_iniciales


def construir_html_historial_chat(historial):
    bloques = []
    for item in historial:
        contenido = html.escape(str(item.get("content") or "")).replace("\n", "<br>")
        rol = str(item.get("role") or "assistant")
        clase = "assistant" if rol == "assistant" else "user"
        etiqueta = "Zentix IA" if rol == "assistant" else "Tú"
        bloques.append(
            f"<div class='zentix-chat-msg {clase}'><div class='role'>{etiqueta}</div><div class='copy'>{contenido}</div></div>"
        )
    return "".join(bloques)


def render_widget_chat_flotante_zentix(pagina, nombre, total_ingresos, total_gastos, ahorro_actual, ultimo_tipo):
    asset_path = zentix_floating_path if zentix_floating_path.exists() else avatar_path
    asset_uri = obtener_data_uri_imagen(asset_path)

    st.markdown(f"""
    <style>
      .zentix-avatar-fab-static {{
        position: fixed;
        right: 18px;
        bottom: calc(82px + env(safe-area-inset-bottom));
        width: 112px;
        height: 128px;
        z-index: 1000001;
        pointer-events: none;
      }}
      .zentix-avatar-fab-static img {{
        width: 100%;
        height: 100%;
        object-fit: contain;
        display: block;
        filter: drop-shadow(0 18px 28px rgba(15,23,42,.22));
      }}
      @media (max-width: 900px) {{
        .zentix-avatar-fab-static {{
          right: 10px;
          bottom: calc(110px + env(safe-area-inset-bottom));
          width: 96px;
          height: 110px;
        }}
      }}
    </style>
    <div class="zentix-avatar-fab-static" aria-hidden="true">
      <img src="{asset_uri}" alt="Zentix IA" />
    </div>
    """, unsafe_allow_html=True)


def render_pagina_zentix_ia(nombre, total_ingresos, total_gastos, ahorro_actual, ultimo_tipo, pagina_origen=None):
    pagina_base = str(pagina_origen or "Inicio")
    if pagina_base == "Zentix IA":
        pagina_base = "Inicio"

    contexto_ia = construir_contexto_zentix(
        pagina=pagina_base,
        nombre=nombre,
        total_ingresos=total_ingresos,
        total_gastos=total_gastos,
        ahorro_actual=ahorro_actual,
        ultimo_tipo=ultimo_tipo
    )

    chat_key, input_key, clear_key, mensajes_iniciales = asegurar_estado_chat_zentix("Zentix IA", nombre)

    if clear_key not in st.session_state:
        st.session_state[clear_key] = False
    if st.session_state.get(clear_key):
        st.session_state[input_key] = ""
        st.session_state[clear_key] = False

    historial = st.session_state.get(chat_key, [])

    if not historial:
        historial = [{"role": "assistant", "content": mensajes_iniciales.get("Zentix IA", "Hola. Soy Zentix IA.")}]
        st.session_state[chat_key] = historial

    ultimo = tipo_display(ultimo_tipo) if ultimo_tipo else "Sin movimientos"
    plan_actual = globals().get("plan_usuario_actual", {})
    consultas_usadas = globals().get("consultas_usadas_hoy", 0)
    consultas_limite = globals().get("consultas_limite_hoy", 10)
    balance = float(total_ingresos or 0) - float(total_gastos or 0)
    balance_label = "Pulso positivo" if balance >= 0 else "Pulso ajustado"
    prompts_sugeridos = [
        "¿Cómo voy este mes y qué debería ajustar primero?",
        "Dame 3 patrones claros de mis gastos.",
        "¿Qué acción concreta me acerca más a mi meta?",
        "Resume mi panorama en lenguaje ejecutivo."
    ]

    st.markdown("""
    <style>
      .zentix-ia-shell { display:grid; gap:1rem; }
      .zentix-ia-hero {
        background:
          radial-gradient(circle at top left, rgba(255,255,255,0.18), transparent 30%),
          radial-gradient(circle at bottom right, rgba(255,255,255,0.08), transparent 24%),
          linear-gradient(135deg, #0F172A 0%, #172554 42%, #4F46E5 82%, #7C3AED 100%);
        border-radius: 30px;
        padding: 1.25rem;
        color: #FFFFFF;
        box-shadow: 0 28px 55px rgba(37,99,235,0.18);
        border: 1px solid rgba(255,255,255,0.08);
        overflow: hidden;
      }
      .zentix-ia-badge {
        display:inline-flex; align-items:center; gap:.45rem;
        padding:.42rem .8rem; border-radius:999px;
        background: rgba(255,255,255,0.14);
        border:1px solid rgba(255,255,255,0.18);
        font-size:.78rem; font-weight:800; margin-bottom:.9rem;
      }
      .zentix-ia-title { font-size:2.08rem; line-height:1.02; font-weight:900; letter-spacing:-.04em; margin:0 0 .35rem 0; color:#FFFFFF !important; }
      .zentix-ia-sub { font-size:1rem; line-height:1.62; color:rgba(255,255,255,.9) !important; margin:0; }
      .zentix-ia-pills { display:flex; flex-wrap:wrap; gap:.6rem; margin-top:1rem; }
      .zentix-ia-pill {
        padding:.48rem .84rem; border-radius:999px;
        background: rgba(255,255,255,0.14);
        border:1px solid rgba(255,255,255,0.16);
        color:#FFFFFF !important; font-size:.82rem; font-weight:700;
      }
      .zentix-ia-grid { display:grid; grid-template-columns: minmax(0, 1.4fr) minmax(320px, .8fr); gap:1rem; align-items:start; }
      .zentix-ia-card {
        background: linear-gradient(180deg, rgba(255,255,255,1), rgba(248,250,252,1));
        border:1px solid rgba(99,102,241,.10);
        box-shadow: 0 16px 30px rgba(15,23,42,.06);
        border-radius: 26px;
        padding: 1rem 1.05rem;
      }
      .zentix-ia-card-title { font-size:1.14rem; font-weight:900; color:#0F172A; letter-spacing:-.03em; margin-bottom:.2rem; }
      .zentix-ia-card-sub { color:#64748B !important; font-size:.92rem; line-height:1.55; margin-bottom:.9rem; }
      .zentix-ia-kpi-row { display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap:.75rem; margin-top:.95rem; }
      .zentix-ia-kpi {
        border-radius:20px; padding:.9rem;
        background: linear-gradient(180deg,#FFFFFF 0%,#F8FBFF 100%);
        border:1px solid rgba(148,163,184,.18);
      }
      .zentix-ia-kpi-label { font-size:.78rem; color:#64748B; font-weight:700; margin-bottom:.35rem; }
      .zentix-ia-kpi-value { font-size:1.25rem; font-weight:900; color:#0F172A; letter-spacing:-.03em; }
      .zentix-ia-prompt-grid { display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:.7rem; margin-top:.95rem; }
      .zentix-ia-prompt {
        border-radius:18px; padding:.82rem .9rem;
        background: linear-gradient(180deg, #EEF2FF 0%, #F8FAFF 100%);
        border:1px solid rgba(99,102,241,.14);
        color:#312E81; font-size:.88rem; line-height:1.45; font-weight:700;
      }
      .zentix-ia-chat-wrap {
        display:flex; flex-direction:column; gap:.9rem;
      }
      .zentix-ia-chat-history {
        background: linear-gradient(180deg,#F8FAFC 0%,#FFFFFF 100%);
        border:1px solid rgba(148,163,184,.18);
        border-radius:22px;
        padding:.85rem;
        min-height:320px;
        max-height:540px;
        overflow:auto;
      }
      .zentix-ia-chat-history .zentix-chat-msg {
        border-radius:18px; padding:12px 13px; margin-bottom:10px;
        line-height:1.55; font-size:.94rem; box-shadow:0 8px 18px rgba(15,23,42,.04);
      }
      .zentix-ia-chat-history .zentix-chat-msg.assistant {
        background:#FFFFFF; border:1px solid rgba(148,163,184,.22); color:#0F172A;
      }
      .zentix-ia-chat-history .zentix-chat-msg.user {
        background:#EEF2FF; border:1px solid rgba(129,140,248,.18); color:#0F172A;
      }
      .zentix-ia-chat-history .role {
        font-size:.72rem; font-weight:900; text-transform:uppercase; letter-spacing:.06em; margin-bottom:4px; color:#475569;
      }
      .zentix-ia-chat-history .zentix-chat-msg.user .role { color:#4338CA; }
      .zentix-ia-chat-history .copy { color:#0F172A !important; }
      .zentix-ia-side-stack { display:grid; gap:1rem; }
      .zentix-ia-mini-list { display:grid; gap:.65rem; }
      .zentix-ia-mini-item {
        border-radius:18px; padding:.84rem .9rem;
        background: linear-gradient(180deg,#FFFFFF 0%,#F8FAFC 100%);
        border:1px solid rgba(148,163,184,.18);
      }
      .zentix-ia-mini-label { font-size:.76rem; color:#64748B; font-weight:800; margin-bottom:.25rem; text-transform:uppercase; letter-spacing:.05em; }
      .zentix-ia-mini-value { font-size:1.04rem; color:#0F172A; font-weight:900; }
      .zentix-ia-mini-copy { font-size:.9rem; color:#475569 !important; line-height:1.5; }
      @media (max-width: 980px) {
        .zentix-ia-grid { grid-template-columns: 1fr; }
        .zentix-ia-kpi-row { grid-template-columns: 1fr; }
        .zentix-ia-prompt-grid { grid-template-columns: 1fr; }
      }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="zentix-ia-shell">
          <div class="zentix-ia-hero">
            <div class="zentix-ia-badge">🤖 Zentix IA · Premium advisor</div>
            <div class="zentix-ia-title">Tu copiloto financiero más claro y ejecutivo.</div>
            <p class="zentix-ia-sub">
              Aquí puedes conversar con Zentix IA con una vista dedicada, elegante y más útil.
              Entraste desde <strong>{pagina_base}</strong> y el contexto ya viene preparado para darte respuestas accionables.
            </p>
            <div class="zentix-ia-pills">
              <span class="zentix-ia-pill">Último movimiento: {ultimo}</span>
              <span class="zentix-ia-pill">Plan {plan_actual.get('plan', 'free').upper()}</span>
              <span class="zentix-ia-pill">IA hoy: {consultas_usadas}/{consultas_limite}</span>
              <span class="zentix-ia-pill">{balance_label}</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_chat, col_side = st.columns([1.42, 0.78], gap="large")

    with col_chat:
        st.markdown("<div class='zentix-ia-card'>", unsafe_allow_html=True)
        st.markdown("<div class='zentix-ia-card-title'>Conversación premium con Zentix</div>", unsafe_allow_html=True)
        st.markdown("<div class='zentix-ia-card-sub'>Haz preguntas seguidas sin overlays ni saltos raros. El chat te responde con el contexto del apartado desde el que entraste.</div>", unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="zentix-ia-kpi-row">
              <div class="zentix-ia-kpi">
                <div class="zentix-ia-kpi-label">Disponible / ahorro actual</div>
                <div class="zentix-ia-kpi-value">{money(ahorro_actual)}</div>
              </div>
              <div class="zentix-ia-kpi">
                <div class="zentix-ia-kpi-label">Ingresos visibles</div>
                <div class="zentix-ia-kpi-value">{money(total_ingresos)}</div>
              </div>
              <div class="zentix-ia-kpi">
                <div class="zentix-ia-kpi-label">Gastos visibles</div>
                <div class="zentix-ia-kpi-value">{money(total_gastos)}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        prompts_html = "".join([f"<div class='zentix-ia-prompt'>{html.escape(p)}</div>" for p in prompts_sugeridos])
        st.markdown(f"<div class='zentix-ia-prompt-grid'>{prompts_html}</div>", unsafe_allow_html=True)

        historial_html = construir_html_historial_chat(historial[-14:])
        st.markdown(f"<div class='zentix-ia-chat-wrap'><div class='zentix-ia-chat-history'>{historial_html}</div></div>", unsafe_allow_html=True)

        with st.form(key="zentix_ia_page_form", clear_on_submit=False):
            pregunta_manual = st.text_area(
                "Pregúntale a Zentix IA",
                key=input_key,
                label_visibility="collapsed",
                placeholder="Ej: Resume mi mes en lenguaje ejecutivo y dime la acción más importante para mejorar.",
                height=118,
            )
            c1, c2 = st.columns([1.2, 0.9])
            with c1:
                enviar = st.form_submit_button("Enviar a Zentix IA", use_container_width=True, type="primary")
            with c2:
                limpiar = st.form_submit_button("Limpiar conversación", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        if limpiar:
            st.session_state[chat_key] = [
                {"role": "assistant", "content": mensajes_iniciales.get("Zentix IA", "Hola. Soy Zentix IA.")}
            ]
            st.session_state[clear_key] = True
            st.rerun()

        if enviar:
            pregunta_final = (pregunta_manual or "").strip()
            if pregunta_final:
                st.session_state[chat_key].append({"role": "user", "content": pregunta_final})

                permitido, usadas, limite, _, plan = puede_usar_ia(st.session_state.user.id)
                if not permitido:
                    respuesta = (
                        f"Has alcanzado tu límite diario de IA ({limite} consultas) en el plan "
                        f"{plan.get('plan', 'free')}. Pásate a Pro para tener más acceso y análisis más profundos."
                    )
                else:
                    with st.spinner("Zentix está analizando tu panorama premium..."):
                        respuesta = consultar_ia_zentix(pregunta_final, contexto_ia)
                    registrar_uso_ia(st.session_state.user.id)

                st.session_state[chat_key].append({"role": "assistant", "content": respuesta})
                st.session_state[clear_key] = True
                st.rerun()

    with col_side:
        st.markdown("<div class='zentix-ia-side-stack'>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="zentix-ia-card">
              <div class="zentix-ia-card-title">Contexto que estoy leyendo</div>
              <div class="zentix-ia-card-sub">Zentix responde con el marco del apartado desde el que entraste, para no mezclar señales ni inventar panorama.</div>
              <div class="zentix-ia-mini-list">
                <div class="zentix-ia-mini-item">
                  <div class="zentix-ia-mini-label">Apartado origen</div>
                  <div class="zentix-ia-mini-value">{pagina_base}</div>
                </div>
                <div class="zentix-ia-mini-item">
                  <div class="zentix-ia-mini-label">Pulso del mes</div>
                  <div class="zentix-ia-mini-value">{balance_label}</div>
                  <div class="zentix-ia-mini-copy">Balance visible: {money(balance)} · Disponible actual: {money(ahorro_actual)}</div>
                </div>
                <div class="zentix-ia-mini-item">
                  <div class="zentix-ia-mini-label">Lectura rápida</div>
                  <div class="zentix-ia-mini-copy">Ingreso visible {money(total_ingresos)} frente a gasto visible {money(total_gastos)}. Zentix prioriza claridad, no ruido.</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="zentix-ia-card">
              <div class="zentix-ia-card-title">Cómo aprovechar mejor esta vista</div>
              <div class="zentix-ia-mini-list">
                <div class="zentix-ia-mini-item">
                  <div class="zentix-ia-mini-label">1 · Pide resumen ejecutivo</div>
                  <div class="zentix-ia-mini-copy">Te lo devuelve corto, claro y accionable.</div>
                </div>
                <div class="zentix-ia-mini-item">
                  <div class="zentix-ia-mini-label">2 · Pide patrones</div>
                  <div class="zentix-ia-mini-copy">Úsalo para descubrir qué categoría pesa más y dónde estás perdiendo margen.</div>
                </div>
                <div class="zentix-ia-mini-item">
                  <div class="zentix-ia-mini-label">3 · Pide siguiente paso</div>
                  <div class="zentix-ia-mini-copy">Zentix te aterriza la acción más útil según tu panorama actual.</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)



def render_avatar(pagina, nombre, total_ingresos, total_gastos, ahorro_actual, ultimo_tipo):
    # El bloque antiguo de Avatar Zentix IA se desactiva para evitar duplicidad.
    # Toda la conversación ahora vive en el apartado Zentix IA.
    return
def render_avatar(pagina, nombre, total_ingresos, total_gastos, ahorro_actual, ultimo_tipo):
    # El bloque antiguo de Avatar Zentix IA se desactiva para evitar duplicidad.
    # Toda la conversación ahora vive en el widget flotante premium.
    return


def obtener_insight_financiero(total_ingresos, total_gastos, saldo_disponible, df_mes):
    if df_mes.empty:
        return "Empieza registrando tus primeros movimientos. En cuanto tengas datos del mes, Zentix podrá mostrarte patrones y alertas útiles."

    if total_ingresos == 0 and total_gastos > 0:
        return "Este mes tienes gastos registrados, pero no ingresos. Revisa si te falta registrar entradas para ver un balance real."

    if total_ingresos > 0:
        ratio = total_gastos / total_ingresos
        if ratio >= 0.9:
            return "Tus gastos están muy cerca de tus ingresos. Conviene revisar la categoría más pesada del mes y contener salidas."
        if ratio >= 0.7:
            return "Tu nivel de gasto está controlado, aunque ya representa una parte importante de tus ingresos. Mantén vigilancia."
        return "Tu relación entre ingresos y gastos es saludable. Tienes margen para ahorro o colchón de seguridad."

    if saldo_disponible < 0:
        return "Tu saldo actual está en negativo. Prioriza recortar gasto variable antes de fijar metas más agresivas."
    return "Tu comportamiento del mes luce estable. Sigue registrando para confirmar la tendencia."


def obtener_categoria_top(df_mes):
    if df_mes.empty:
        return None, 0.0
    resumen = (
        df_mes.groupby("categoria", dropna=False)["monto"]
        .sum()
        .sort_values(ascending=False)
    )
    if resumen.empty:
        return None, 0.0
    return resumen.index[0], float(resumen.iloc[0])




def render_home_action_tiles():
    return


def render_recent_activity_feed(df_movs, limit=6):
    st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Actividad reciente</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-caption'>Tu último movimiento, como feed simple y limpio.</div>", unsafe_allow_html=True)
    if df_movs is None or df_movs.empty:
        st.markdown("<div class='tiny-muted'>Aún no hay movimientos registrados.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    vista = df_movs.copy().sort_values("fecha", ascending=False).head(limit)
    vista["fecha"] = pd.to_datetime(vista["fecha"], errors="coerce")
    vista["monto"] = pd.to_numeric(vista["monto"], errors="coerce").fillna(0)

    for _, row in vista.iterrows():
        tipo = str(row.get("tipo") or "Sin tipo")
        descripcion = str(row.get("descripcion") or row.get("categoria") or "Movimiento").strip()
        fecha_txt = row["fecha"].strftime("%d %b · %H:%M") if pd.notna(row["fecha"]) else "Sin fecha"
        amount_class = "amount-income" if tipo in {"Ingreso", "Cobro cuenta por cobrar"} else "amount-expense" if tipo == "Gasto" else "amount-debt" if tipo == "Ingreso (Deuda)" else "amount-pay" if tipo == "Pago de deuda" else "amount-debt"
        icono = "↑" if tipo in {"Ingreso", "Cobro cuenta por cobrar"} else "↓" if tipo == "Gasto" else "↔"
        st.markdown(
            f"""
            <div class='activity-feed-item'>
                <div class='activity-feed-left'>
                    <div class='activity-feed-bullet'>{icono}</div>
                    <div>
                        <div class='activity-feed-title'>{html.escape(descripcion)}</div>
                        <div class='activity-feed-sub'>{html.escape(tipo_display(tipo))} · {fecha_txt}</div>
                    </div>
                </div>
                <div class='activity-feed-amount {amount_class}'>{money(row.get('monto', 0))}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_resumen_general_chart(df_mes_actual):
    st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Evolución del mes</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-caption'>Una sola gráfica limpia para no saturarte al entrar.</div>", unsafe_allow_html=True)
    if df_mes_actual is None or df_mes_actual.empty:
        st.markdown("<div class='tiny-muted'>Registra movimientos y aquí aparecerá la evolución diaria.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    chart_df = df_mes_actual.copy()
    chart_df["fecha"] = pd.to_datetime(chart_df["fecha"], errors="coerce")
    chart_df = chart_df.dropna(subset=["fecha"]).copy()
    chart_df = chart_df[chart_df["tipo"].isin(["Ingreso", "Gasto", "Cobro cuenta por cobrar", "Pago de deuda"])]
    if chart_df.empty:
        st.markdown("<div class='tiny-muted'>No hay tipos suficientes para mostrar la evolución.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    chart_df["tipo_visual"] = chart_df["tipo"].replace({"Cobro cuenta por cobrar": "Ingreso", "Pago de deuda": "Gasto"})
    daily = chart_df.groupby([chart_df["fecha"].dt.date, "tipo_visual"], dropna=False)["monto"].sum().reset_index()
    daily.columns = ["fecha", "tipo", "monto"]
    fig = px.line(
        daily,
        x="fecha",
        y="monto",
        color="tipo",
        markers=True,
        title="",
        color_discrete_map={"Ingreso": "#22C55E", "Gasto": "#EF4444"}
    )
    aplicar_estilo_plotly(fig, height=340)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

def render_inicio_pie_charts(df_mes_actual, df_deudas_local, df_cxc_local):
    p1, p2, p3 = st.columns(3)

    with p1:
        st.markdown("<div class='home-pie-card'>", unsafe_allow_html=True)
        st.markdown("<div class='home-pie-title'>Gasto por categoría</div><div class='home-pie-sub'>Más visual para interpretar rápido dónde se está yendo tu dinero.</div>", unsafe_allow_html=True)
        if df_mes_actual is None or df_mes_actual.empty:
            st.markdown("<div class='tiny-muted'>Aún no hay datos del mes para esta lectura.</div>", unsafe_allow_html=True)
        else:
            gastos = df_mes_actual.copy()
            gastos = gastos[gastos["tipo"] == "Gasto"].copy()
            if gastos.empty:
                st.markdown("<div class='tiny-muted'>Todavía no tienes gastos en el periodo.</div>", unsafe_allow_html=True)
            else:
                data = gastos.groupby("categoria", dropna=False)["monto"].sum().reset_index()
                data["categoria"] = data["categoria"].fillna("Sin categoría")
                fig = px.pie(data, values="monto", names="categoria", hole=0.55, color_discrete_sequence=["#EF4444", "#F97316", "#F59E0B", "#FB7185", "#A855F7", "#38BDF8"])
                aplicar_estilo_plotly(fig, height=320)
                fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with p2:
        st.markdown("<div class='home-pie-card'>", unsafe_allow_html=True)
        st.markdown("<div class='home-pie-title'>Deudas activas</div><div class='home-pie-sub'>Distribución del pendiente para leer presión financiera de un vistazo.</div>", unsafe_allow_html=True)
        if df_deudas_local is None or df_deudas_local.empty:
            st.markdown("<div class='tiny-muted'>No tienes deudas activas registradas.</div>", unsafe_allow_html=True)
        else:
            deuda_chart = df_deudas_local.copy()
            deuda_chart["saldo_pendiente"] = pd.to_numeric(deuda_chart.get("saldo_pendiente"), errors="coerce").fillna(0)
            deuda_chart = deuda_chart[deuda_chart["saldo_pendiente"] > 0].copy()
            if deuda_chart.empty:
                st.markdown("<div class='tiny-muted'>No tienes saldo pendiente en deudas.</div>", unsafe_allow_html=True)
            else:
                fig = px.pie(deuda_chart, values="saldo_pendiente", names="nombre", hole=0.55, color_discrete_sequence=["#3B82F6", "#60A5FA", "#818CF8", "#22D3EE", "#A78BFA", "#93C5FD"])
                aplicar_estilo_plotly(fig, height=320)
                fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with p3:
        st.markdown("<div class='home-pie-card'>", unsafe_allow_html=True)
        st.markdown("<div class='home-pie-title'>Por cobrar</div><div class='home-pie-sub'>Quién te debe y cuánto concentra de tu cartera pendiente.</div>", unsafe_allow_html=True)
        if df_cxc_local is None or df_cxc_local.empty:
            st.markdown("<div class='tiny-muted'>No tienes cartera pendiente registrada.</div>", unsafe_allow_html=True)
        else:
            cxc_chart = df_cxc_local.copy()
            cxc_chart["saldo_pendiente"] = pd.to_numeric(cxc_chart.get("saldo_pendiente"), errors="coerce").fillna(0)
            cxc_chart = cxc_chart[cxc_chart["saldo_pendiente"] > 0].copy()
            if cxc_chart.empty:
                st.markdown("<div class='tiny-muted'>No tienes cuentas por cobrar pendientes.</div>", unsafe_allow_html=True)
            else:
                group_col = "cliente" if "cliente" in cxc_chart.columns else "nombre"
                data = cxc_chart.groupby(group_col, dropna=False)["saldo_pendiente"].sum().reset_index()
                data[group_col] = data[group_col].fillna("Sin cliente")
                fig = px.pie(data, values="saldo_pendiente", names=group_col, hole=0.55, color_discrete_sequence=["#06B6D4", "#22C55E", "#8B5CF6", "#4F46E5", "#38BDF8", "#2DD4BF"])
                aplicar_estilo_plotly(fig, height=320)
                fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)



def render_home_hub(nombre_usuario, user_id, df, df_mes, df_deudas, df_cxc, total_ingresos, total_gastos,
                    total_entradas_deuda_mes, total_pagos_deuda_mes, saldo_pendiente_deudas_global,
                    saldo_pendiente_cxc_global, deudas_activas_global, meta_guardada_global, nombre_meta_guardado,
                    ahorro_actual, saldo_disponible, perfil_financiero, insight_personalizado,
                    resumen_semanal_premium, alertas_proactivas, patrones_comportamiento,
                    sugerencias_categoria, recomendacion_accionable, proyeccion_meta_global,
                    plan_usuario_actual, consultas_usadas_hoy, consultas_limite_hoy,
                    preferencias_usuario_actual, ultimo_tipo):
    zentix_hero(nombre_usuario, saldo_disponible, total_ingresos, total_gastos)
    render_contexto_descubrimiento("Inicio")
    render_tutorial_zentix("Inicio", nombre_usuario, user_id, df, meta_guardada_global, preferencias_usuario_actual)
    render_home_action_tiles()

    tabs = st.tabs(["Resumen", "Actividad", "Planificación", "Modo Pro ✦"])

    with tabs[0]:
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            kpi_card("Ingresos reales", money(total_ingresos), "Flujo propio del mes", "income")
        with k2:
            kpi_card("Gastos", money(total_gastos), "Salidas operativas", "expense")
        with k3:
            kpi_card("Disponible", money(saldo_disponible), "Caja actual", "balance")
        with k4:
            kpi_card("Meta", money(meta_guardada_global), nombre_meta_guardado if nombre_meta_guardado else "Objetivo activo", "saving")

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            kpi_card("Deuda recibida", money(total_entradas_deuda_mes), "No cuenta como ingreso real", "debt")
        with d2:
            kpi_card("Pagos deuda", money(total_pagos_deuda_mes), "Seguimiento de devolución", "pay")
        with d3:
            kpi_card("Por cobrar", money(saldo_pendiente_cxc_global), "Pendiente de cobrar", "receivable")
        with d4:
            kpi_card("Pendiente", money(saldo_pendiente_deudas_global), f"{deudas_activas_global} deuda(s) activas", "debt")

        c1, c2 = st.columns([1.15, 0.85])
        with c1:
            render_resumen_general_chart(df_mes if df_mes is not None else pd.DataFrame())
        with c2:
            render_recent_activity_feed(df if df is not None else pd.DataFrame(), limit=6)

        render_inicio_pie_charts(
            df_mes if df_mes is not None else pd.DataFrame(),
            df_deudas if df_deudas is not None else pd.DataFrame(),
            df_cxc if df_cxc is not None else pd.DataFrame()
        )

        s1, s2, s3 = st.columns(3)
        with s1:
            render_list_card("Lo bueno del periodo", resumen_semanal_premium.get("positivas", []), "Zentix te resalta avances sin llenarte la pantalla de widgets.")
        with s2:
            render_list_card("Alertas suaves", alertas_proactivas, "Alertas accionables, no ruido.")
        with s3:
            render_list_card("Siguiente paso", [recomendacion_accionable, proyeccion_meta_global.get("mensaje", "")], "La mejor acción puntual para hoy.")

    with tabs[1]:
        c1, c2 = st.columns([1.2, 0.8])
        with c1:
            render_movimientos_action_hub(user_id, df if df is not None else pd.DataFrame(), df_deudas if df_deudas is not None else pd.DataFrame())
        with c2:
            render_movimiento_focus_panel(df if df is not None else pd.DataFrame())
        render_recent_activity_feed(df if df is not None else pd.DataFrame(), limit=10)

    with tabs[2]:
        c1, c2 = st.columns([1.15, 0.85])
        with c1:
            render_inicio_spotlight(
                df_base=df if df is not None else pd.DataFrame(),
                df_mes_actual=df_mes if df_mes is not None else pd.DataFrame(),
                df_deudas_local=df_deudas if df_deudas is not None else pd.DataFrame(),
                total_ingresos_local=total_ingresos,
                total_gastos_local=total_gastos,
                entradas_deuda_local=total_entradas_deuda_mes,
                pagos_deuda_local=total_pagos_deuda_mes,
                saldo_pendiente_local=saldo_pendiente_deudas_global,
                meta_objetivo=meta_guardada_global,
                ahorro_disponible=ahorro_actual,
                comparativa=globals().get("comparativa_periodos", {}),
                resumen_semanal=resumen_semanal_premium,
                alertas=alertas_proactivas,
                sugerencias=sugerencias_categoria,
                proyeccion=proyeccion_meta_global,
                plan_actual=plan_usuario_actual,
                consultas_usadas=consultas_usadas_hoy,
                consultas_limite=consultas_limite_hoy
            )
        with c2:
            render_list_card("Perfil e insights", [perfil_financiero.get("titulo", "Perfil en construcción"), insight_personalizado], "Una lectura editorial del momento financiero.")
            render_list_card("Categorías inteligentes", sugerencias_categoria if sugerencias_categoria else ["Sigue registrando para refinar sugerencias."], "Organización que reduce saturación visual y mental.")
            render_list_card("Patrones detectados", patrones_comportamiento + [f"Plan: {plan_usuario_actual.get('plan', 'free').upper()} · IA {consultas_usadas_hoy}/{consultas_limite_hoy}"], "Lo importante resumido, no repartido en diez cajas.")

    with tabs[3]:
        st.markdown("<div class='soft-card'><div class='section-title'>Modo Pro · Personal o Negocio</div><div class='section-caption'>Aquí eliges cómo quieres leer tu dinero: vida personal o tablero ejecutivo. Es tu capa más estratégica y premium.</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='tiny-muted' style='margin-top:0.55rem;'>Selecciona el enfoque que quieres activar: <strong>Personal</strong> para hábitos, metas y bienestar financiero, o <strong>Negocio</strong> para caja, utilidad y crecimiento.</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class='mini-soft-card' style='margin-top:0.85rem; margin-bottom:0.9rem; background:linear-gradient(135deg,#0F172A 0%, #172554 42%, #4F46E5 82%, #7C3AED 100%) !important; border:none !important; box-shadow:0 18px 34px rgba(15,23,42,0.18) !important;'>
                <div style='font-size:0.82rem;font-weight:900;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.75) !important;margin-bottom:.35rem;'>Zentix Pro Switch</div>
                <div style='font-size:1.18rem;font-weight:900;color:#FFFFFF !important;margin-bottom:.2rem;'>Activa el modo que mejor explica tu dinero.</div>
                <div style='font-size:.94rem;line-height:1.6;color:rgba(255,255,255,.88) !important;'>Personal te habla de estabilidad, metas y hábitos. Negocio te habla de caja, margen, rentabilidad y crecimiento.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        render_dashboard_pro(
            nombre=nombre_usuario,
            df_base=df if df is not None else pd.DataFrame(),
            df_mes_actual=df_mes if df_mes is not None else pd.DataFrame(),
            df_cxc_local=df_cxc if df_cxc is not None else pd.DataFrame(),
            total_ingresos_local=total_ingresos,
            total_gastos_local=total_gastos,
            entradas_deuda_local=total_entradas_deuda_mes,
            pagos_deuda_local=total_pagos_deuda_mes,
            saldo_deuda_pendiente=saldo_pendiente_deudas_global,
            meta_objetivo=meta_guardada_global,
            ahorro_actual=ahorro_actual,
        )
        render_avatar("Inicio", nombre_usuario, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)


aplicar_estilo_zentix()


@st.cache_data(ttl=25, show_spinner=False)
def obtener_movimientos(user_id):
    result = (
        supabase.table("movimientos")
        .select("*")
        .eq("usuario_id", user_id)
        .order("fecha", desc=True)
        .execute()
    )
    data = result.data if result.data else []
    df_local = pd.DataFrame(data)

    columnas_esperadas = [
        "id", "usuario_id", "fecha", "tipo", "categoria", "monto", "descripcion", "emocion",
        "deuda_id", "deuda_nombre", "prestamista", "fecha_limite_deuda",
        "es_recurrente", "frecuencia_recurrencia", "proxima_fecha_recurrencia",
        "fecha_fin_recurrencia", "recurrente_activo"
    ]
    for col in columnas_esperadas:
        if col not in df_local.columns:
            df_local[col] = None

    if not df_local.empty:
        df_local["fecha"] = pd.to_datetime(df_local["fecha"], errors="coerce")
        df_local["monto"] = pd.to_numeric(df_local["monto"], errors="coerce").fillna(0)

        for date_col in ["fecha_limite_deuda", "proxima_fecha_recurrencia", "fecha_fin_recurrencia"]:
            if date_col in df_local.columns:
                df_local[date_col] = pd.to_datetime(df_local[date_col], errors="coerce")

        for bool_col in ["es_recurrente", "recurrente_activo"]:
            if bool_col in df_local.columns:
                df_local[bool_col] = df_local[bool_col].fillna(False).astype(bool)

        for text_col in ["categoria", "descripcion", "emocion", "deuda_nombre", "prestamista", "frecuencia_recurrencia"]:
            if text_col in df_local.columns:
                df_local[text_col] = df_local[text_col].fillna("")

    return df_local


@st.cache_data(ttl=90, show_spinner=False)
def obtener_perfil(user_id):
    result = (
        supabase.table("perfiles_usuario")
        .select("*")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def guardar_onboarding(user_id, nombre_mostrado, categorias_gasto, categorias_ingreso):
    perfil = obtener_perfil(user_id)

    if perfil:
        supabase.table("perfiles_usuario").update({
            "nombre_mostrado": nombre_mostrado,
            "onboarding_completo": True
        }).eq("id", user_id).execute()
    else:
        supabase.table("perfiles_usuario").insert({
            "id": user_id,
            "nombre_mostrado": nombre_mostrado,
            "onboarding_completo": True
        }).execute()

    supabase.table("categorias_usuario").delete().eq("usuario_id", user_id).execute()

    registros = []
    for cat in categorias_gasto:
        registros.append({"usuario_id": user_id, "tipo": "Gasto", "nombre": cat})
    for cat in categorias_ingreso:
        registros.append({"usuario_id": user_id, "tipo": "Ingreso", "nombre": cat})

    if registros:
        supabase.table("categorias_usuario").insert(registros).execute()


def limpiar_cache_datos_usuario():
    for fn_name in [
        "obtener_perfil",
        "obtener_movimientos",
        "obtener_meta",
        "obtener_deudas_usuario",
        "obtener_cuentas_por_cobrar_usuario",
        "obtener_preferencias_usuario",
        "obtener_categorias_usuario",
    ]:
        try:
            globals()[fn_name].clear()
        except Exception:
            pass


def usuario_ya_tiene_historial(user_id):
    try:
        result = (
            supabase.table("movimientos")
            .select("id", count="exact")
            .eq("usuario_id", user_id)
            .limit(1)
            .execute()
        )
        return int(getattr(result, "count", 0) or 0) > 0
    except Exception:
        return False


@st.cache_data(ttl=90, show_spinner=False)
def obtener_categorias_usuario(user_id, tipo):
    result = (
        supabase.table("categorias_usuario")
        .select("*")
        .eq("usuario_id", user_id)
        .eq("tipo", tipo)
        .order("nombre")
        .execute()
    )
    data = result.data if result.data else []
    return [x["nombre"] for x in data]



def obtener_automation_runtime_config():
    def _read(key, default=""):
        try:
            value = st.secrets.get(key)
        except Exception:
            value = None
        if value in (None, ""):
            value = os.getenv(key, default)
        return value if value is not None else default

    return {
        "job_token": str(_read("AUTOMATION_JOB_TOKEN", "")).strip(),
        "app_base_url": str(_read("APP_BASE_URL", "")).strip().rstrip("/"),
        "enabled": bool(str(_read("AUTOMATION_JOB_TOKEN", "")).strip())
    }


def construir_url_job_recordatorios(limit=25):
    cfg = obtener_automation_runtime_config()
    if not cfg.get("enabled") or not cfg.get("app_base_url"):
        return ""
    return f"{cfg['app_base_url']}/?job=recordatorios&token={cfg['job_token']}&limit={int(limit)}"


def obtener_query_param(key, default=""):
    try:
        value = st.query_params.get(key, default)
        if isinstance(value, list):
            return value[0] if value else default
        return value
    except Exception:
        return default


def _obtener_nombre_para_batch(user_id, email_contacto=""):
    try:
        perfil = obtener_perfil(user_id)
        if perfil and perfil.get("nombre_mostrado"):
            return perfil.get("nombre_mostrado")
    except Exception:
        pass
    email_contacto = str(email_contacto or "").strip()
    return email_contacto.split("@")[0].replace(".", " ").title() if email_contacto else "Usuario Zentix"


def _filtrar_mes_actual(df_base):
    if df_base is None or df_base.empty or "fecha" not in df_base.columns:
        return pd.DataFrame(columns=getattr(df_base, "columns", []))
    df_tmp = df_base.copy()
    df_tmp["fecha"] = pd.to_datetime(df_tmp["fecha"], errors="coerce")
    df_tmp = df_tmp.dropna(subset=["fecha"]).copy()
    if df_tmp.empty:
        return df_tmp
    try:
        if getattr(df_tmp["fecha"].dt, "tz", None) is not None:
            df_tmp["fecha"] = df_tmp["fecha"].dt.tz_localize(None)
    except Exception:
        pass
    hoy = pd.Timestamp.now()
    return df_tmp[(df_tmp["fecha"].dt.month == hoy.month) & (df_tmp["fecha"].dt.year == hoy.year)].copy()


def ejecutar_lote_recordatorios(limit=25):
    summary = {"procesados": 0, "enviados": 0, "errores": 0, "detalles": []}
    try:
        result = (
            supabase.table("preferencias_usuario")
            .select("*")
            .eq("recordatorio_email", True)
            .limit(int(limit))
            .execute()
        )
        registros = result.data if result.data else []
    except Exception as e:
        summary["errores"] += 1
        summary["detalles"].append({"user_id": None, "detalle": f"No pude leer preferencias: {e}"})
        return summary

    for row in registros:
        user_id_local = row.get("usuario_id")
        if not user_id_local:
            continue
        try:
            df_user = obtener_movimientos(user_id_local)
            df_mes_user = _filtrar_mes_actual(df_user)
            total_gastos_user = float(df_mes_user[df_mes_user["tipo"] == "Gasto"]["monto"].sum()) if not df_mes_user.empty else 0.0
            total_ingresos_user = float(df_mes_user[df_mes_user["tipo"].isin(["Ingreso", "Cobro cuenta por cobrar"])]["monto"].sum()) if not df_mes_user.empty else 0.0
            total_entradas_deuda_user = float(df_mes_user[df_mes_user["tipo"] == "Ingreso (Deuda)"]["monto"].sum()) if not df_mes_user.empty else 0.0
            total_pagos_deuda_user = float(df_mes_user[df_mes_user["tipo"] == "Pago de deuda"]["monto"].sum()) if not df_mes_user.empty else 0.0
            saldo_disponible_user = total_ingresos_user + total_entradas_deuda_user - total_gastos_user - total_pagos_deuda_user

            meta_result_user = obtener_meta(user_id_local)
            meta_user = float(meta_result_user["meta"]) if meta_result_user and meta_result_user.get("meta") is not None else 0.0
            prefs_user = obtener_preferencias_usuario(user_id_local, row.get("email_contacto", ""))
            resumen_user = construir_resumen_recordatorios(df_user, prefs_user)
            proyeccion_user = calcular_proyeccion_meta(meta_user, saldo_disponible_user, estimar_aporte_semanal_meta(df_user if df_user is not None else pd.DataFrame()))
            alertas_user = generar_alertas_proactivas(df_user, df_mes_user if df_mes_user is not None else pd.DataFrame(), total_ingresos_user, total_gastos_user, saldo_disponible_user, meta_user)
            nombre_user = _obtener_nombre_para_batch(user_id_local, row.get("email_contacto", ""))

            status = disparar_recordatorio_automatico_si_aplica(
                user_id=user_id_local,
                nombre=nombre_user,
                preferencias=prefs_user,
                resumen_recordatorios=resumen_user,
                total_ingresos=total_ingresos_user,
                total_gastos=total_gastos_user,
                saldo_disponible=saldo_disponible_user,
                meta_actual=meta_user,
                proyeccion_meta=proyeccion_user,
                alertas=alertas_user,
                fallback_email=row.get("email_contacto", "")
            )
            summary["procesados"] += 1
            if bool(status.get("enviado")):
                summary["enviados"] += 1
            summary["detalles"].append({
                "user_id": user_id_local,
                "destino": status.get("destino", ""),
                "tipo": status.get("tipo"),
                "detalle": status.get("detalle")
            })
        except Exception as e:
            summary["procesados"] += 1
            summary["errores"] += 1
            summary["detalles"].append({"user_id": user_id_local, "detalle": f"Error procesando usuario: {e}"})
    return summary


def maybe_handle_public_automation_job():
    job = str(obtener_query_param("job", "") or "").strip().lower()
    if job != "recordatorios":
        return False

    cfg = obtener_automation_runtime_config()
    token = str(obtener_query_param("token", "") or "").strip()
    if not cfg.get("enabled") or token != cfg.get("job_token"):
        st.error("Token de automatización inválido o no configurado.")
        st.stop()

    try:
        limit = int(str(obtener_query_param("limit", "25")).strip())
    except Exception:
        limit = 25

    st.markdown("<div class='soft-card'><div class='section-title'>Ejecución automática de recordatorios</div><div class='section-caption'>Modo job seguro activado por token.</div></div>", unsafe_allow_html=True)
    resumen = ejecutar_lote_recordatorios(limit=max(1, min(limit, 250)))
    st.json(resumen)
    st.stop()
    return True


def construir_redirect_recuperacion_supabase():
    base_redirect = _leer_secret_texto("RESET_PASSWORD_REDIRECT", _leer_secret_texto("APP_BASE_URL", "")).strip()
    if not base_redirect:
        return None
    try:
        parsed = urllib.parse.urlparse(base_redirect)
        query = urllib.parse.parse_qs(parsed.query)
        query["recovery"] = ["1"]
        return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query, doseq=True), fragment=""))
    except Exception:
        separador = "&" if "?" in base_redirect else "?"
        return f"{base_redirect}{separador}recovery=1"


def inyectar_captura_callback_recuperacion():
    components.html(
        """
        <script>
        (function () {
          try {
            const parentWindow = window.parent;
            const currentUrl = new URL(parentWindow.location.href);
            const hash = (parentWindow.location.hash || '').replace(/^#/, '');
            if (!hash) return;
            const hashParams = new URLSearchParams(hash);
            const accessToken = hashParams.get('access_token');
            const refreshToken = hashParams.get('refresh_token');
            const recoveryType = hashParams.get('type') || hashParams.get('mode');
            if (!accessToken || !refreshToken) return;
            currentUrl.searchParams.set('__zentix_recovery', '1');
            currentUrl.searchParams.set('__zentix_access_token', accessToken);
            currentUrl.searchParams.set('__zentix_refresh_token', refreshToken);
            if (recoveryType) currentUrl.searchParams.set('__zentix_recovery_type', recoveryType);
            parentWindow.location.replace(currentUrl.toString().split('#')[0]);
          } catch (e) {
            console.error('Zentix recovery hash error', e);
          }
        })();
        </script>
        """,
        height=0,
    )


def limpiar_query_params_recuperacion():
    for clave in ["recovery", "__zentix_recovery", "__zentix_access_token", "__zentix_refresh_token", "__zentix_recovery_type"]:
        try:
            if clave in st.query_params:
                del st.query_params[clave]
        except Exception:
            pass


def maybe_handle_password_recovery_tokens():
    recovery_flag = str(obtener_query_param("recovery", "") or obtener_query_param("__zentix_recovery", "")).strip().lower() in {"1", "true", "yes", "si", "sí"}
    access_token = str(obtener_query_param("__zentix_access_token", "")).strip()
    refresh_token = str(obtener_query_param("__zentix_refresh_token", "")).strip()
    recovery_type = str(obtener_query_param("__zentix_recovery_type", "")).strip().lower()

    if not access_token or not refresh_token:
        return
    if not recovery_flag and recovery_type != "recovery":
        return

    if st.session_state.get("zentix_password_recovery_ready") and st.session_state.get("zentix_access_token") == access_token:
        limpiar_query_params_recuperacion()
        return

    try:
        supabase.auth.set_session(access_token, refresh_token)
        user_res = supabase.auth.get_user()
        if getattr(user_res, "user", None):
            st.session_state.user = user_res.user
            st.session_state["zentix_password_recovery_email"] = getattr(user_res.user, "email", "") or ""
        st.session_state["zentix_access_token"] = access_token
        st.session_state["zentix_refresh_token"] = refresh_token
        st.session_state["zentix_password_recovery_ready"] = True
        st.session_state["zentix_password_recovery_error"] = ""
    except Exception as e:
        st.session_state["zentix_password_recovery_ready"] = False
        st.session_state["zentix_password_recovery_error"] = str(e)
    finally:
        limpiar_query_params_recuperacion()


def render_pantalla_recuperacion_contrasena():
    correo = st.session_state.get("zentix_password_recovery_email") or getattr(st.session_state.get("user"), "email", "") or "tu cuenta"

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-badge">Recuperación segura</div>
            <div class="hero-title">Define tu nueva contraseña</div>
            <div class="hero-subtitle">
                Ya validamos tu enlace de recuperación para <strong>{html.escape(str(correo))}</strong>. Ahora solo falta guardar tu nueva clave.
            </div>
            <div class="hero-pills">
                <span class="hero-pill">Acceso validado</span>
                <span class="hero-pill">Cambio inmediato</span>
                <span class="hero-pill">Sin salir de Zentix</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
    section_header("Actualiza tu contraseña", "Pon una clave nueva y continúa normalmente dentro de la app.")
    nueva = st.text_input("Nueva contraseña", type="password", key="recovery_new_password")
    nueva_2 = st.text_input("Confirmar nueva contraseña", type="password", key="recovery_new_password_2")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Guardar nueva contraseña", key="btn_guardar_nueva_password", use_container_width=True, type="primary"):
            if len(str(nueva or "")) < 6:
                st.error("La nueva contraseña debe tener al menos 6 caracteres.")
            elif nueva != nueva_2:
                st.error("Las contraseñas no coinciden.")
            else:
                try:
                    supabase.auth.update_user({"password": nueva})
                    st.session_state["zentix_password_recovery_ready"] = False
                    st.session_state["zentix_password_recovery_error"] = ""
                    st.success("Contraseña actualizada correctamente. Ya puedes seguir usando Zentix.")
                    time.sleep(1.0)
                    st.rerun()
                except Exception as e:
                    st.error(f"No pude actualizar la contraseña: {e}")
    with c2:
        if st.button("Cancelar", key="btn_cancelar_recovery", use_container_width=True):
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            st.session_state["zentix_password_recovery_ready"] = False
            st.session_state["zentix_password_recovery_error"] = ""
            st.session_state["zentix_password_recovery_email"] = ""
            st.session_state.user = None
            st.session_state["zentix_access_token"] = None
            st.session_state["zentix_refresh_token"] = None
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def resetear_contrasena_supabase(email):
    email = str(email or "").strip()
    if not email:
        return False, "Escribe tu correo para enviarte el enlace de recuperación."
    try:
        redirect_to = construir_redirect_recuperacion_supabase()
        options = {"redirect_to": redirect_to} if redirect_to else None
        try:
            if options:
                supabase.auth.reset_password_for_email(email, options)
            else:
                supabase.auth.reset_password_for_email(email)
        except AttributeError:
            if options:
                supabase.auth.reset_password_email(email, options)
            else:
                supabase.auth.reset_password_email(email)
        return True, "Te enviamos un enlace para cambiar tu contraseña. Revisa tu correo y abre el link completo."
    except Exception as e:
        return False, f"No pude enviar el correo de recuperación: {e}"


def obtener_limites_categoria_usuario(user_id):
    columnas = ["id", "usuario_id", "categoria", "limite_mensual", "activo", "creado_en", "actualizado_en"]
    try:
        result = (
            supabase.table("limites_categoria")
            .select("*")
            .eq("usuario_id", user_id)
            .order("categoria")
            .execute()
        )
        data = result.data if result.data else []
    except Exception:
        data = []
    df_local = pd.DataFrame(data)
    for col in columnas:
        if col not in df_local.columns:
            df_local[col] = None
    if not df_local.empty:
        df_local["limite_mensual"] = pd.to_numeric(df_local["limite_mensual"], errors="coerce").fillna(0)
        df_local["activo"] = df_local["activo"].fillna(True).astype(bool)
    return df_local


def guardar_limite_categoria_seguro(user_id, categoria, limite_mensual, activo=True):
    payload = {
        "usuario_id": user_id,
        "categoria": str(categoria or "").strip(),
        "limite_mensual": float(limite_mensual or 0),
        "activo": bool(activo),
        "actualizado_en": datetime.now().isoformat()
    }
    if not payload["categoria"]:
        return None
    try:
        return supabase.table("limites_categoria").upsert(payload, on_conflict="usuario_id,categoria").execute()
    except Exception:
        try:
            existe = (
                supabase.table("limites_categoria")
                .select("id")
                .eq("usuario_id", user_id)
                .eq("categoria", payload["categoria"])
                .limit(1)
                .execute()
            )
            if existe.data:
                return (
                    supabase.table("limites_categoria")
                    .update(payload)
                    .eq("usuario_id", user_id)
                    .eq("categoria", payload["categoria"])
                    .execute()
                )
            payload["creado_en"] = datetime.now().isoformat()
            return supabase.table("limites_categoria").insert(payload).execute()
        except Exception:
            return None


def eliminar_limite_categoria_seguro(user_id, categoria):
    try:
        return (
            supabase.table("limites_categoria")
            .delete()
            .eq("usuario_id", user_id)
            .eq("categoria", str(categoria or "").strip())
            .execute()
        )
    except Exception:
        return None


def evaluar_limite_categoria(df_mes_actual, categoria, monto_nuevo=0.0):
    if df_mes_actual is None or df_mes_actual.empty:
        actual = 0.0
    else:
        actual = float(df_mes_actual[(df_mes_actual["tipo"] == "Gasto") & (df_mes_actual["categoria"] == categoria)]["monto"].sum())
    total = actual + float(monto_nuevo or 0)
    return actual, total


def render_limites_categoria(user_id, plan_actual, df_mes_actual):
    plan_name = str((plan_actual or {}).get("plan", "free") or "free").lower()
    premium = plan_name in {"pro", "premium", "paid", "plus"}
    st.markdown("<div class='limit-card-premium'><div class='section-title'>Límites por categoría</div><div class='section-caption'>Define techos por categoría para que Zentix te avise cuando estés por pasarte.</div></div>", unsafe_allow_html=True)
    if not premium:
        st.info("Esta opción queda perfecta para tu versión premium paga. La dejé preparada para activarse cuando el plan sea PRO/PREMIUM.")
        return

    categorias = sorted(set(obtener_categorias_usuario(user_id, "Gasto")))
    if not categorias:
        st.info("Primero configura o registra categorías de gasto.")
        return

    with st.expander("Configurar límites mensuales", expanded=False):
        col1, col2 = st.columns([1.1, 0.9])
        with col1:
            categoria_sel = st.selectbox("Categoría a limitar", categorias, key="limit_categoria_sel")
        with col2:
            limite_sel = st.number_input("Límite mensual", min_value=0.0, step=1000.0, key="limit_categoria_monto")
        activo_sel = st.checkbox("Límite activo", value=True, key="limit_categoria_activo")
        if st.button("Guardar límite", key="guardar_limite_categoria", use_container_width=True, type="primary"):
            resp = guardar_limite_categoria_seguro(user_id, categoria_sel, limite_sel, activo_sel)
            if resp is not None:
                st.success("Límite guardado correctamente.")
                st.rerun()
            st.error("No pude guardar el límite. Si la tabla aún no existe, créala en Supabase.")

    df_limites = obtener_limites_categoria_usuario(user_id)
    if df_limites.empty:
        st.caption("Todavía no has creado límites.")
        return

    for _, row in df_limites.iterrows():
        actual, proyectado = evaluar_limite_categoria(df_mes_actual if df_mes_actual is not None else pd.DataFrame(), row.get("categoria", ""), 0)
        ratio = (actual / float(row.get("limite_mensual", 0) or 1)) if float(row.get("limite_mensual", 0) or 0) > 0 else 0
        st.markdown(f"""
        <div class='mini-soft-card'>
            <div style='display:flex;justify-content:space-between;gap:0.8rem;align-items:center;'>
                <div>
                    <div style='font-weight:800;font-size:1rem;'>{row.get('categoria','Sin categoría')}</div>
                    <div class='tiny-muted'>Usado este mes: {money(actual)} de {money(row.get('limite_mensual',0))}</div>
                </div>
                <div class='tiny-muted'>{'Activo' if bool(row.get('activo', True)) else 'Pausado'}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(float(max(0.0, min(ratio, 1.0))))
        if ratio >= 1:
            st.error(f"Ya superaste el límite de {row.get('categoria')}.")
        elif ratio >= 0.8:
            st.warning(f"Vas en {ratio*100:.0f}% del límite de {row.get('categoria')}.")
        if st.button(f"Eliminar límite · {row.get('categoria')}", key=f"delete_limit_{row.get('categoria')}", use_container_width=True, type="secondary"):
            eliminar_limite_categoria_seguro(user_id, row.get('categoria'))
            st.rerun()


def obtener_mensajes_bienvenida(nombre):
    nombre = nombre or ""
    return [
        f"Hola {nombre}, soy Zentix. Aquí vas a controlar tu dinero con una vista más limpia y premium.",
        "En Inicio encuentras tus KPIs, tus alertas y una lectura rápida de tu mes.",
        "En Registrar puedes guardar ingresos, gastos, deudas y pagos sin enredarte.",
        "En Análisis ves reportes e indicadores solo cuando tú quieras abrirlos.",
        "En Ahorro y Perfil podrás afinar metas, recordatorios y límites premium por categoría."
    ]


def render_bienvenida_flotante(nombre, pagina_actual, total_ingresos, total_gastos, ahorro_actual, ultimo_tipo):
    render_widget_chat_flotante_zentix(
        pagina=pagina_actual,
        nombre=nombre,
        total_ingresos=total_ingresos,
        total_gastos=total_gastos,
        ahorro_actual=ahorro_actual,
        ultimo_tipo=ultimo_tipo
    )


def render_reporte_preview_modal(pdf_bytes, filename, titulo="Reporte premium Zentix"):

    if not pdf_bytes:
        return
    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    data_uri = f"data:application/pdf;base64,{b64}"
    texto_compartir = urllib.parse.quote(f"Te comparto mi reporte premium de Zentix: {filename}. Descárgalo desde la app.")
    mailto = f"mailto:?subject={urllib.parse.quote(titulo)}&body={texto_compartir}"
    whatsapp = f"https://wa.me/?text={texto_compartir}"
    html_block = f"""
    <div style='background:#0b1220;border:1px solid rgba(96,165,250,.18);border-radius:20px;padding:12px;'>
        <div style='display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px;'>
            <button onclick="window.open('{data_uri}','_blank')" style='background:#1d4ed8;color:white;border:none;border-radius:12px;padding:10px 14px;font-weight:700;cursor:pointer;'>Abrir en grande</button>
            <button onclick="var w=window.open('{data_uri}','_blank'); setTimeout(function(){{ try{{w.print();}}catch(e){{}} }}, 900);" style='background:#0f766e;color:white;border:none;border-radius:12px;padding:10px 14px;font-weight:700;cursor:pointer;'>Imprimir</button>
            <a href='{whatsapp}' target='_blank' style='background:#14532d;color:white;text-decoration:none;border-radius:12px;padding:10px 14px;font-weight:700;'>Compartir por WhatsApp</a>
            <a href='{mailto}' style='background:#7c3aed;color:white;text-decoration:none;border-radius:12px;padding:10px 14px;font-weight:700;'>Compartir por correo</a>
        </div>
        <iframe src='{data_uri}' width='100%' height='780' style='border:none;border-radius:16px;background:#fff;'></iframe>
    </div>
    """
    components.html(html_block, height=860, scrolling=True)


def render_reportes_compactos(nombre_usuario, plan_actual, df_base, user_id=None):
    section_header("Reportes premium", "Ábrelos solo cuando quieras para mantener la experiencia más limpia y menos saturada.")
    tabs = st.tabs(["Diario", "Semanal", "Mensual"])
    mapping = {"Diario": "Diario", "Semanal": "Semanal", "Mensual": "Mensual"}
    for tab_name, tab in zip(["Diario", "Semanal", "Mensual"], tabs):
        with tab:
            fecha_ref = st.date_input(f"Fecha de referencia · {tab_name}", value=date.today(), key=f"reporte_fecha_ref_{tab_name}")
            if tab_name == "Diario":
                inicio_rep = fecha_ref
                fin_rep = fecha_ref
                if df_base is None or df_base.empty:
                    df_periodo = pd.DataFrame()
                else:
                    df_periodo = df_base.copy()
                    df_periodo["fecha"] = pd.to_datetime(df_periodo["fecha"], errors="coerce").dt.date
                    df_periodo = df_periodo[df_periodo["fecha"] == fecha_ref].copy()
            else:
                df_periodo, inicio_rep, fin_rep = obtener_movimientos_periodo(df_base if df_base is not None else pd.DataFrame(), tab_name, fecha_ref)
            resumen_rep = resumir_periodo_movimientos(df_periodo)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                render_spotlight_metric("Movimientos", str(resumen_rep.get("conteo", 0)), "Incluidos")
            with c2:
                render_spotlight_metric("Ingresos", money(resumen_rep.get("ingresos", 0)), "Reales")
            with c3:
                render_spotlight_metric("Gastos", money(resumen_rep.get("gastos", 0)), "Operativos")
            with c4:
                render_spotlight_metric("Balance", money(resumen_rep.get("balance", 0)), "Neto")
            if df_periodo is None or df_periodo.empty:
                st.info(f"No hay movimientos para el reporte {tab_name.lower()}.")
                continue
            preview = df_periodo.copy().sort_values("fecha", ascending=False).head(10)
            if "fecha" in preview.columns:
                preview["fecha"] = pd.to_datetime(preview["fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
            cols = [c for c in ["fecha", "tipo", "categoria", "monto", "descripcion", "deuda_nombre", "prestamista"] if c in preview.columns]
            st.dataframe(preview[cols], use_container_width=True)
            png_bytes = generar_imagen_reporte_premium(nombre_usuario, plan_actual.get("plan", "free").upper(), tab_name, inicio_rep, fin_rep, resumen_rep, df_periodo)
            pdf_bytes = None
            if REPORTLAB_AVAILABLE:
                pdf_bytes = generar_pdf_reporte_premium(nombre_usuario, plan_actual.get("plan", "free").upper(), tab_name, inicio_rep, fin_rep, df_periodo, resumen_rep)
            filename_base = f"zentix_reporte_{tab_name.lower()}_{inicio_rep.strftime('%Y%m%d')}_{fin_rep.strftime('%Y%m%d')}"
            abrir = st.toggle(f"Abrir vista previa premium · {tab_name}", key=f"toggle_preview_{tab_name}")
            d1, d2 = st.columns(2)
            with d1:
                if pdf_bytes:
                    st.download_button(f"Descargar PDF · {tab_name}", data=pdf_bytes, file_name=f"{filename_base}.pdf", mime="application/pdf", use_container_width=True)
                else:
                    st.info("PDF premium no disponible todavía en este entorno. La imagen premium sí está lista para descargar o imprimir.")
            with d2:
                if png_bytes:
                    st.download_button(f"Descargar imagen · {tab_name}", data=png_bytes, file_name=f"{filename_base}.png", mime="image/png", use_container_width=True)
            if abrir:
                st.markdown("<div class='report-preview-shell'><div class='section-title'>Vista previa y acciones premium</div><div class='section-caption'>Puedes guardar una imagen premium del reporte y, cuando reportlab esté activo, descargar también el PDF listo para impresión física.</div></div>", unsafe_allow_html=True)
                if png_bytes:
                    st.markdown("<div class='report-image-shell'><div class='section-title'>Imagen premium del reporte</div><div class='report-image-note'>Esta versión queda lista para guardar, compartir o imprimir desde tu dispositivo sin perder el estilo visual de Zentix.</div></div>", unsafe_allow_html=True)
                    st.image(png_bytes, use_container_width=True)
                if pdf_bytes:
                    render_reporte_preview_modal(pdf_bytes, f"{filename_base}.pdf", titulo=f"Reporte {tab_name} Zentix")
                registrar_evento_producto("report_preview_open", user_id=user_id, pagina="Análisis", detalle=f"{tab_name} {inicio_rep} {fin_rep}")

@st.cache_data(ttl=60, show_spinner=False)
def obtener_meta(user_id):
    result = (
        supabase.table("ahorro_meta")
        .select("*")
        .eq("usuario_id", user_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


if "user" not in st.session_state:
    st.session_state.user = None
if "zentix_access_token" not in st.session_state:
    st.session_state["zentix_access_token"] = None
if "zentix_refresh_token" not in st.session_state:
    st.session_state["zentix_refresh_token"] = None
if "zentix_password_recovery_ready" not in st.session_state:
    st.session_state["zentix_password_recovery_ready"] = False
if "zentix_password_recovery_email" not in st.session_state:
    st.session_state["zentix_password_recovery_email"] = ""
if "zentix_password_recovery_error" not in st.session_state:
    st.session_state["zentix_password_recovery_error"] = ""

maybe_handle_public_automation_job()
launch_cfg = obtener_config_lanzamiento()

maybe_handle_special_nav_actions()
inyectar_captura_callback_recuperacion()
maybe_handle_password_recovery_tokens()

if st.session_state.user is None and st.session_state.get("zentix_access_token") and st.session_state.get("zentix_refresh_token"):
    try:
        supabase.auth.set_session(st.session_state["zentix_access_token"], st.session_state["zentix_refresh_token"])
        user_res = supabase.auth.get_user()
        if getattr(user_res, "user", None):
            st.session_state.user = user_res.user
    except Exception:
        st.session_state.user = None
        st.session_state["zentix_access_token"] = None
        st.session_state["zentix_refresh_token"] = None

if st.session_state.get("zentix_password_recovery_ready"):
    render_pantalla_recuperacion_contrasena()
    st.stop()

if st.session_state.user is None:
    with st.sidebar:
        col_sb_icon, col_sb_text = st.columns([1, 3])
        with col_sb_icon:
            if icono_path.exists():
                st.image(str(icono_path), width=58)
        with col_sb_text:
            st.markdown('<div class="sidebar-brand-title">ZENTIX</div>', unsafe_allow_html=True)
            st.markdown('<div class="sidebar-brand-sub">Registro primero · login después</div>', unsafe_allow_html=True)
        st.markdown("<div class='sidebar-nav-note'>Si eres nuevo, crea tu cuenta. Si ya tienes una, entra con login. Recuperación de contraseña disponible en la misma pantalla.</div>", unsafe_allow_html=True)

    if st.session_state.get("zentix_password_recovery_error"):
        st.error(f"No pude validar el enlace de recuperación: {st.session_state.get('zentix_password_recovery_error')}")

    col_hero, col_form = st.columns([1.1, 1.0])
    with col_hero:
        st.markdown("""
            <div class="hero-card">
                <div class="hero-badge">Experiencia premium · simple desde el primer segundo</div>
                <div class="hero-title">Primero regístrate. Luego entra a tu panel.</div>
                <div class="hero-subtitle">
                    Crea tu cuenta, entra a tu panel o recupera tu contraseña desde una sola vista clara y fácil de entender.
                </div>
                <div class="hero-pills">
                    <span class="hero-pill">Registro guiado</span>
                    <span class="hero-pill">Login claro</span>
                    <span class="hero-pill">Recuperación de contraseña</span>
                    <span class="hero-pill">Diseño mobile premium</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        if avatar_path.exists():
            st.image(str(avatar_path), width=220)
        st.markdown("<div class='auth-step-card'><div class='auth-step-title'>Acceso a tu cuenta</div><div class='auth-step-copy'>Registro, login y recuperación visibles todo el tiempo para que cualquier usuario entienda de inmediato dónde entrar.</div></div>", unsafe_allow_html=True)
        render_contexto_lanzamiento_acceso(launch_cfg)

    with col_form:
        st.markdown('<div class="auth-shell">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Acceso premium</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-caption">Dejé el flujo mucho más lógico y directo para que no se sienta pesado.</div>', unsafe_allow_html=True)
        render_auth_visibility_strip()
        tab_reg, tab_login, tab_reset = st.tabs(["Registro", "Login", "Recuperar contraseña"])

        with tab_reg:
            st.markdown("<div class='auth-step-card'><div class='auth-step-title'>Crear cuenta</div><div class='auth-step-copy'>Ingresa tu correo y una contraseña segura para empezar con Zentix.</div></div>", unsafe_allow_html=True)
            reg_email = st.text_input("Correo para registro", key="reg_email")
            reg_password = st.text_input("Contraseña para registro", type="password", key="reg_password")
            reg_password_2 = st.text_input("Confirma tu contraseña", type="password", key="reg_password_2")
            if st.button("Crear cuenta premium", key="btn_registro_premium", use_container_width=True, type="primary"):
                if not launch_cfg.get("allow_public_signup"):
                    st.warning("El registro público está cerrado en este momento.")
                elif not reg_email.strip():
                    st.error("Escribe tu correo.")
                elif len(reg_password or "") < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres.")
                elif reg_password != reg_password_2:
                    st.error("Las contraseñas no coinciden.")
                else:
                    try:
                        supabase.auth.sign_up({"email": reg_email.strip(), "password": reg_password})
                        registrar_evento_producto("signup_success", pagina="Acceso", detalle=reg_email.strip())
                        st.success("Cuenta creada. Ahora entra desde la pestaña Login.")
                    except Exception as e:
                        registrar_evento_producto("signup_error", pagina="Acceso", detalle=str(e))
                        st.error(f"Error al registrar: {e}")

        with tab_login:
            st.markdown("<div class='auth-step-card'><div class='auth-step-title'>Iniciar sesión</div><div class='auth-step-copy'>Entra con el mismo correo y la misma contraseña con los que creaste tu cuenta.</div></div>", unsafe_allow_html=True)
            login_email = st.text_input("Correo", key="login_email")
            login_password = st.text_input("Contraseña", type="password", key="login_password")
            if st.button("Entrar a Zentix", key="btn_login_premium", use_container_width=True, type="primary"):
                correo = str(login_email or "").strip()
                clave = str(login_password or "")
                if not correo:
                    st.error("Escribe tu correo para iniciar sesión.")
                elif "@" not in correo:
                    st.error("Debes iniciar sesión con el correo con el que te registraste.")
                elif not clave:
                    st.error("Escribe tu contraseña.")
                else:
                    try:
                        res = supabase.auth.sign_in_with_password({"email": correo, "password": clave})
                        st.session_state.user = res.user
                        if getattr(res, "session", None):
                            st.session_state["zentix_access_token"] = getattr(res.session, "access_token", None)
                            st.session_state["zentix_refresh_token"] = getattr(res.session, "refresh_token", None)
                        registrar_evento_producto("login_success", user_id=getattr(res.user, "id", None), pagina="Acceso", detalle=correo)
                        st.session_state["zentix_show_transition"] = False
                        st.rerun()
                    except Exception as e:
                        registrar_evento_producto("login_error", pagina="Acceso", detalle=str(e))
                        st.error("No pude iniciar sesión. Verifica que el correo y la contraseña sean los mismos con los que te registraste.")

        with tab_reset:
            st.markdown("<div class='auth-step-card'><div class='auth-step-title'>Recuperar contraseña</div><div class='auth-step-copy'>Escribe tu correo y te enviaremos el enlace para restablecer tu acceso.</div></div>", unsafe_allow_html=True)
            reset_email = st.text_input("Correo para recuperación", key="reset_email")
            if st.button("Enviar enlace de recuperación", key="btn_reset_password", use_container_width=True, type="secondary"):
                ok, detalle = resetear_contrasena_supabase(reset_email)
                if ok:
                    st.success(detalle)
                else:
                    st.error(detalle)

        st.markdown('</div>', unsafe_allow_html=True)
        render_footer_producto(launch_cfg)
    st.stop()



zentix_brand_header()

user_id = st.session_state.user.id
perfil = obtener_perfil(user_id)
nombre_usuario = perfil["nombre_mostrado"] if perfil and perfil.get("nombre_mostrado") else "usuario"

plan_usuario_actual = obtener_o_crear_plan_usuario(user_id)
_, consultas_usadas_hoy, consultas_limite_hoy, consultas_restantes_hoy, _ = puede_usar_ia(user_id)

paginas_disponibles = ["Inicio", "Registrar", "Análisis", "Ahorro", "Perfil", "Zentix IA"]

if "pagina" not in st.session_state or st.session_state.pagina not in paginas_disponibles:
    st.session_state.pagina = "Inicio"

aplicar_nav_desde_query(paginas_disponibles)
inyectar_sidebar_drawer(nombre_usuario, plan_usuario_actual, consultas_usadas_hoy, consultas_limite_hoy, st.session_state.pagina)

with st.sidebar:
    col_sb_icon, col_sb_text = st.columns([1, 3])
    with col_sb_icon:
        if icono_path.exists():
            st.image(str(icono_path), width=54)
    with col_sb_text:
        st.markdown('<div class="sidebar-brand-title">Zentix</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-brand-sub">Centro secundario</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="sidebar-user-card">
            <div class="sidebar-user-label">Sesión activa</div>
            <div class="sidebar-user-name">{nombre_usuario}</div>
            <div class="tiny-muted" style="margin-top:0.35rem;">Plan {plan_usuario_actual.get('plan', 'free').upper()} · IA {consultas_usadas_hoy}/{consultas_limite_hoy}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.caption("Atajos de navegación")
    sb1, sb2 = st.columns(2)
    with sb1:
        if st.button("🏠 Inicio", key="sidebar_inicio", use_container_width=True, type="primary" if st.session_state.pagina == "Inicio" else "secondary"):
            ir_a_pagina("Inicio")
    with sb2:
        if st.button("➕ Registrar", key="sidebar_registrar", use_container_width=True, type="primary" if st.session_state.pagina == "Registrar" else "secondary"):
            ir_a_pagina("Registrar")
    sb3, sb4 = st.columns(2)
    with sb3:
        if st.button("📈 Análisis", key="sidebar_analisis", use_container_width=True, type="primary" if st.session_state.pagina == "Análisis" else "secondary"):
            ir_a_pagina("Análisis")
    with sb4:
        if st.button("🎯 Ahorro", key="sidebar_ahorro", use_container_width=True, type="primary" if st.session_state.pagina == "Ahorro" else "secondary"):
            ir_a_pagina("Ahorro")
    sb5, sb6 = st.columns(2)
    with sb5:
        if st.button("⚙️ Perfil", key="sidebar_perfil", use_container_width=True, type="primary" if st.session_state.pagina == "Perfil" else "secondary"):
            ir_a_pagina("Perfil")
    with sb6:
        if st.button("🤖 Zentix IA", key="sidebar_zentix_ia", use_container_width=True, type="primary" if st.session_state.pagina == "Zentix IA" else "secondary"):
            ir_a_pagina("Zentix IA")

    st.markdown("<div class='sidebar-nav-note'>Este panel lateral puede mantenerse visible o plegarse con el botón superior izquierdo. La idea es que se sienta como un drawer premium de app móvil.</div>", unsafe_allow_html=True)

    if st.button("Cerrar sesión", use_container_width=True):
        st.session_state.user = None
        st.rerun()

# render_nav_rapida_premium()
render_transition_overlay()

pagina = st.session_state.pagina
track_page_view_once(user_id, pagina)


nombre_guardado = str((perfil or {}).get("nombre_mostrado") or "").strip()
categorias_gasto_guardadas = obtener_categorias_usuario(user_id, "Gasto")
categorias_ingreso_guardadas = obtener_categorias_usuario(user_id, "Ingreso")
tiene_historial = usuario_ya_tiene_historial(user_id)
onboarding_completo_flag = bool((perfil or {}).get("onboarding_completo", False))

onboarding_necesario = (
    not onboarding_completo_flag
    and not nombre_guardado
    and not categorias_gasto_guardadas
    and not categorias_ingreso_guardadas
    and not tiene_historial
)

if not onboarding_necesario and not onboarding_completo_flag:
    try:
        if perfil:
            supabase.table("perfiles_usuario").update({
                "onboarding_completo": True
            }).eq("id", user_id).execute()
        else:
            supabase.table("perfiles_usuario").insert({
                "id": user_id,
                "nombre_mostrado": nombre_guardado or nombre_usuario or "Usuario Zentix",
                "onboarding_completo": True
            }).execute()

        limpiar_cache_datos_usuario()
        perfil = obtener_perfil(user_id)
    except Exception:
        pass

if onboarding_necesario:
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-badge">Onboarding inicial</div>
            <div class="hero-title">Configura tu experiencia Zentix</div>
            <div class="hero-subtitle">
                Define cómo quieres que te llame Zentix y selecciona tus categorías principales para personalizar tu registro financiero. Desde aquí ya arranca una guía más clara y premium.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    section_header("Preferencias iniciales", "Esta configuración se guarda por usuario y luego puedes ampliarla en tu evolución de producto.")
    progreso_onboarding = 0.34
    st.progress(progreso_onboarding)

    nombre_mostrado = st.text_input("¿Cómo quieres que te llame Zentix?")
    categorias_gasto = st.multiselect(
        "Selecciona tus categorías de gasto",
        DEFAULT_GASTOS,
        default=["Comida", "Transporte", "Servicios"]
    )
    categorias_ingreso = st.multiselect(
        "Selecciona tus categorías de ingreso",
        DEFAULT_INGRESOS,
        default=["Salario"]
    )

    col_on_1, col_on_2 = st.columns([1.1, 0.9])

    with col_on_1:
        if st.button("Guardar configuración inicial", use_container_width=True):
            if not nombre_mostrado.strip():
                st.error("Escribe el nombre con el que quieres ser llamado.")
            elif not categorias_gasto:
                st.error("Selecciona al menos una categoría de gasto.")
            elif not categorias_ingreso:
                st.error("Selecciona al menos una categoría de ingreso.")
            else:
                try:
                    guardar_onboarding(
                        user_id,
                        nombre_mostrado.strip(),
                        categorias_gasto,
                        categorias_ingreso
                    )
                    limpiar_cache_datos_usuario()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error guardando onboarding: {e}")

    with col_on_2:
        st.markdown(
            """
            <div class="soft-card">
                <div class="section-title">Configura tu base financiera</div>
                <div class="section-caption">
                    Elige cómo quieres que Zentix te acompañe y define tus categorías principales para empezar con orden desde el primer día.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.stop()


try:
    df = obtener_movimientos(user_id)
except Exception as e:
    st.error(f"Error cargando movimientos: {e}")
    st.stop()

try:
    meta_result_global = obtener_meta(user_id)
    meta_guardada_global = float(meta_result_global["meta"]) if meta_result_global else 0.0
except Exception:
    meta_result_global = None
    meta_guardada_global = 0.0

if not df.empty:
    mes_actual = pd.Timestamp.now().month
    anio_actual = pd.Timestamp.now().year
    df_mes = df[(df["fecha"].dt.month == mes_actual) & (df["fecha"].dt.year == anio_actual)].copy()
    ultimo_tipo = df.iloc[0]["tipo"]
else:
    df_mes = pd.DataFrame(columns=["usuario_id", "fecha", "tipo", "categoria", "monto", "descripcion"])
    ultimo_tipo = None

if not df_mes.empty:
    total_gastos = float(df_mes[df_mes["tipo"] == "Gasto"]["monto"].sum())
    total_ingresos = float(df_mes[df_mes["tipo"].isin(["Ingreso", "Cobro cuenta por cobrar"])]["monto"].sum())
    total_entradas_deuda_mes = float(df_mes[df_mes["tipo"] == "Ingreso (Deuda)"]["monto"].sum())
    total_pagos_deuda_mes = float(df_mes[df_mes["tipo"] == "Pago de deuda"]["monto"].sum())
    total_cuentas_cobrar_mes = float(df_mes[df_mes["tipo"] == "Cuenta por cobrar"]["monto"].sum())
    total_cobros_cxc_mes = float(df_mes[df_mes["tipo"] == "Cobro cuenta por cobrar"]["monto"].sum())
else:
    total_gastos = 0.0
    total_ingresos = 0.0
    total_entradas_deuda_mes = 0.0
    total_pagos_deuda_mes = 0.0
    total_cuentas_cobrar_mes = 0.0
    total_cobros_cxc_mes = 0.0

df_deudas = obtener_deudas_usuario(user_id)
df_deudas = recalcular_deudas_usuario_desde_movimientos(user_id, df if not df.empty else pd.DataFrame(), df_deudas)
df_cxc = obtener_cuentas_por_cobrar_usuario(user_id)
df_cxc = recalcular_cuentas_por_cobrar_desde_movimientos(user_id, df if not df.empty else pd.DataFrame(), df_cxc)
if not df_deudas.empty:
    saldo_pendiente_deudas_global = float(df_deudas["saldo_pendiente"].sum())
    deudas_activas_global = int((df_deudas["saldo_pendiente"] > 0).sum())
else:
    saldo_pendiente_deudas_global = 0.0
    deudas_activas_global = 0

if not df_cxc.empty:
    saldo_pendiente_cxc_global = float(df_cxc["saldo_pendiente"].sum())
    cuentas_por_cobrar_activas_global = int((df_cxc["saldo_pendiente"] > 0).sum())
else:
    saldo_pendiente_cxc_global = 0.0
    cuentas_por_cobrar_activas_global = 0

saldo_disponible = total_ingresos + total_entradas_deuda_mes - total_gastos - total_pagos_deuda_mes
ahorro_actual = float(saldo_disponible)
insight_financiero = obtener_insight_financiero(total_ingresos, total_gastos, saldo_disponible, df_mes)
categoria_top, monto_top = obtener_categoria_top(df_mes[df_mes["tipo"] == "Gasto"].copy() if not df_mes.empty else pd.DataFrame())

nombre_meta_guardado = obtener_nombre_meta_guardado(user_id)
perfil_financiero = obtener_perfil_financiero(total_ingresos, total_gastos, saldo_disponible, df_mes)
comparativa_periodos = obtener_comparativa_periodos(df if not df.empty else pd.DataFrame())
resumen_semanal_premium = construir_resumen_semanal_premium(df if not df.empty else pd.DataFrame(), meta_guardada_global, ahorro_actual)
alertas_proactivas = generar_alertas_proactivas(df if not df.empty else pd.DataFrame(), df_mes, total_ingresos, total_gastos, saldo_disponible, meta_guardada_global)
recomendacion_accionable = generar_recomendacion_accionable(df_mes[df_mes["tipo"].isin(["Ingreso", "Gasto"])] if not df_mes.empty else pd.DataFrame(), total_ingresos, total_gastos, ahorro_actual, meta_guardada_global)
patrones_comportamiento = detectar_patrones_comportamiento(df if not df.empty else pd.DataFrame())
sugerencias_categoria = sugerir_categorias_inteligentes(df if not df.empty else pd.DataFrame())
insight_personalizado = construir_insight_personalizado(
    perfil_financiero,
    alertas_proactivas,
    recomendacion_accionable,
    patrones_comportamiento
)
categorias_favoritas_global = obtener_categorias_favoritas(df if not df.empty else pd.DataFrame())
preferencias_usuario_actual = obtener_preferencias_usuario(user_id, getattr(st.session_state.user, "email", ""))
resumen_recordatorios_global = construir_resumen_recordatorios(df if not df.empty else pd.DataFrame(), preferencias_usuario_actual)
aporte_semanal_estimado_global = estimar_aporte_semanal_meta(df if not df.empty else pd.DataFrame())
proyeccion_meta_global = calcular_proyeccion_meta(meta_guardada_global, ahorro_actual, aporte_semanal_estimado_global)
estado_recordatorios_automaticos_global = disparar_recordatorio_automatico_si_aplica(
    user_id=user_id,
    nombre=nombre_usuario,
    preferencias=preferencias_usuario_actual,
    resumen_recordatorios=resumen_recordatorios_global,
    total_ingresos=total_ingresos,
    total_gastos=total_gastos,
    saldo_disponible=saldo_disponible,
    meta_actual=meta_guardada_global,
    proyeccion_meta=proyeccion_meta_global,
    alertas=alertas_proactivas,
    fallback_email=getattr(st.session_state.user, "email", "")
)
_, consultas_usadas_hoy, consultas_limite_hoy, consultas_restantes_hoy, plan_usuario_actual = puede_usar_ia(user_id)

render_bienvenida_flotante(nombre_usuario, pagina, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)

if pagina == "Zentix IA":
    render_pagina_zentix_ia(
        nombre=nombre_usuario,
        total_ingresos=total_ingresos,
        total_gastos=total_gastos,
        ahorro_actual=saldo_disponible,
        ultimo_tipo=ultimo_tipo,
        pagina_origen=st.session_state.get("zentix_ia_return_page", "Inicio"),
    )
    render_footer_producto(launch_cfg)
    st.stop()

if pagina == "Inicio":
    render_home_hub(
        nombre_usuario=nombre_usuario,
        user_id=user_id,
        df=df if not df.empty else pd.DataFrame(),
        df_mes=df_mes if not df_mes.empty else pd.DataFrame(),
        df_deudas=df_deudas if not df_deudas.empty else pd.DataFrame(),
        df_cxc=df_cxc if not df_cxc.empty else pd.DataFrame(),
        total_ingresos=total_ingresos,
        total_gastos=total_gastos,
        total_entradas_deuda_mes=total_entradas_deuda_mes,
        total_pagos_deuda_mes=total_pagos_deuda_mes,
        saldo_pendiente_deudas_global=saldo_pendiente_deudas_global,
        saldo_pendiente_cxc_global=saldo_pendiente_cxc_global,
        deudas_activas_global=deudas_activas_global,
        meta_guardada_global=meta_guardada_global,
        nombre_meta_guardado=nombre_meta_guardado,
        ahorro_actual=ahorro_actual,
        saldo_disponible=saldo_disponible,
        perfil_financiero=perfil_financiero,
        insight_personalizado=insight_personalizado,
        resumen_semanal_premium=resumen_semanal_premium,
        alertas_proactivas=alertas_proactivas,
        patrones_comportamiento=patrones_comportamiento,
        sugerencias_categoria=sugerencias_categoria,
        recomendacion_accionable=recomendacion_accionable,
        proyeccion_meta_global=proyeccion_meta_global,
        plan_usuario_actual=plan_usuario_actual,
        consultas_usadas_hoy=consultas_usadas_hoy,
        consultas_limite_hoy=consultas_limite_hoy,
        preferencias_usuario_actual=preferencias_usuario_actual,
        ultimo_tipo=ultimo_tipo,
    )

if pagina == "Registrar":
    zentix_hero(nombre_usuario, saldo_disponible, total_ingresos, total_gastos)
    render_contexto_descubrimiento("Registrar")
    render_tutorial_zentix("Registrar", nombre_usuario, user_id, df, meta_guardada_global, preferencias_usuario_actual)
    section_header("Registrar movimiento", "Agrega ingresos, gastos, deuda, cuentas por cobrar y recurrencias desde un flujo claro y visual.")
    ejecutar_reset_registrar_si_aplica()

    col_form, col_side = st.columns([1.15, 0.85])

    with col_form:
        tipo_labels = {
            "Ingreso": "🟢 Ingreso",
            "Gasto": "🔴 Gasto",
            "Ingreso (Deuda)": "🔵 Crédito solicitado",
            "Pago de deuda": "🟡 Pago a crédito",
            "Cuenta por cobrar": "🟣 Prestaste Dinero",
            "Cobro cuenta por cobrar": "🟦 Ya me pagaron",
        }
        tipo = st.radio(
            "Tipo de movimiento",
            ["Ingreso", "Gasto", "Ingreso (Deuda)", "Pago de deuda", "Cuenta por cobrar", "Cobro cuenta por cobrar"],
            horizontal=True,
            format_func=lambda x: tipo_labels.get(x, x)
        )
        st.markdown("<div class='register-chip-note'>Selecciona el tipo de movimiento y el formulario se ajusta automáticamente.</div>", unsafe_allow_html=True)

        if tipo == "Ingreso":
            st.markdown('<div class="pill-ingreso">Ingreso real seleccionado</div>', unsafe_allow_html=True)
        elif tipo == "Gasto":
            st.markdown('<div class="pill-gasto">Gasto seleccionado</div>', unsafe_allow_html=True)
        elif tipo == "Ingreso (Deuda)":
            st.markdown('<div class="pill-debt">Crédito solicitado seleccionado</div>', unsafe_allow_html=True)
        elif tipo == "Pago de deuda":
            st.markdown('<div class="pill-pay">Pago a crédito seleccionado</div>', unsafe_allow_html=True)
        elif tipo == "Cuenta por cobrar":
            st.markdown('<div class="pill-debt" style="background:#F3E8FF;border-color:#D8B4FE;color:#7E22CE;">Prestaste Dinero seleccionado</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="pill-ingreso" style="background:#CCFBF1;border-color:#5EEAD4;color:#0F766E;">Ya me pagaron seleccionado</div>', unsafe_allow_html=True)

        fecha_mov = st.date_input("Fecha", value=date.today(), key="registrar_fecha_mov")
        descripcion = st.text_input("Descripción", key="registrar_descripcion")

        es_recurrente = st.checkbox("Hacer recurrente", key="registrar_recurrente")
        frecuencia_recurrencia = ""
        proxima_fecha_recurrencia = None
        fecha_fin_recurrencia = None
        recurrente_activo = False

        if es_recurrente:
            with st.expander("🔁 Configuración recurrente", expanded=True):
                frecuencia_recurrencia = st.selectbox(
                    "Frecuencia",
                    ["Semanal", "Quincenal", "Mensual"],
                    key="registrar_frecuencia"
                )
                delta_map = {"Semanal": 7, "Quincenal": 15, "Mensual": 30}
                proxima_fecha_recurrencia = st.date_input(
                    "Próxima fecha",
                    value=fecha_mov + timedelta(days=delta_map.get(frecuencia_recurrencia, 7)),
                    key="registrar_proxima_fecha"
                )
                activar_fecha_fin = st.checkbox("Definir fecha fin", key="registrar_fin_toggle")
                if activar_fecha_fin:
                    fecha_fin_recurrencia = st.date_input(
                        "Fecha fin",
                        value=proxima_fecha_recurrencia,
                        key="registrar_fecha_fin"
                    )
                recurrente_activo = st.checkbox("Mantener activa", value=True, key="registrar_recurrente_activo")

        categoria = ""
        monto = 0.0
        emocion = ""
        deuda_id = None
        deuda_nombre = ""
        prestamista = ""
        fecha_limite_deuda = None
        saldo_deuda_actual = 0.0
        cuenta_cobrar_id = None
        cuenta_cobrar_nombre = ""
        cliente_cxc = ""
        fecha_limite_cxc = None
        saldo_cxc_actual = 0.0

        if tipo == "Ingreso":
            categorias_disponibles = obtener_categorias_usuario(user_id, "Ingreso")
            if not categorias_disponibles:
                st.warning("No tienes categorías de ingreso configuradas. Completa tu onboarding o agrega categorías para registrar mejor.")
                categorias_disponibles = ["Sin categorías"]
            categoria = st.selectbox("Categoría", categorias_disponibles, key="registrar_categoria_ingreso")
            monto = st.number_input("Monto recibido", min_value=0.0, step=1000.0, key="registrar_monto_ingreso")

        elif tipo == "Gasto":
            categorias_disponibles = obtener_categorias_usuario(user_id, "Gasto")
            if not categorias_disponibles:
                st.warning("No tienes categorías de gasto configuradas. Completa tu onboarding o agrega categorías para registrar mejor.")
                categorias_disponibles = ["Sin categorías"]
            categoria = st.selectbox("Categoría", categorias_disponibles, key="registrar_categoria_gasto")
            monto = st.number_input("Monto gastado", min_value=0.0, step=1000.0, key="registrar_monto_gasto")

            with st.expander("Emoción asociada (opcional)", expanded=False):
                emocion = st.selectbox(
                    "¿Cómo te sentías al hacer este gasto?",
                    ["", "Tranquilidad", "Impulso", "Estrés", "Recompensa", "Urgencia", "Antojo"],
                    format_func=lambda x: "No registrar emoción" if x == "" else x,
                    key="registrar_emocion"
                )

        elif tipo == "Ingreso (Deuda)":
            categoria = "Deuda"
            with st.expander("💳 Bloque específico de crédito", expanded=True):
                deuda_nombre = st.text_input(
                    "Nombre del crédito",
                    placeholder="Ej: Crédito Banco, Crédito Juan",
                    key="registrar_deuda_nombre"
                )
                prestamista = st.text_input(
                    "Quién te prestó",
                    placeholder="Ej: Banco, mamá, Juan",
                    key="registrar_prestamista"
                )
                monto = st.number_input("Monto recibido", min_value=0.0, step=1000.0, key="registrar_monto_deuda")
                activar_fecha_limite = st.checkbox("Agregar fecha límite", key="registrar_deuda_limite_toggle")
                if activar_fecha_limite:
                    fecha_limite_deuda = st.date_input(
                        "Fecha límite",
                        value=fecha_mov + timedelta(days=30),
                        key="registrar_deuda_limite"
                    )
                st.caption("Este movimiento entra a caja como crédito solicitado, pero no contaminará tus KPIs de ingresos reales.")

        elif tipo == "Cuenta por cobrar":
            categoria = "Cuenta por cobrar"
            with st.expander("🧾 Bloque de dinero que prestaste", expanded=True):
                cuenta_cobrar_nombre = st.text_input(
                    "Nombre del dinero prestado",
                    placeholder="Ej: Préstamo a Juan, Dinero prestado a cliente",
                    key="registrar_cxc_nombre"
                )
                cliente_cxc = st.text_input(
                    "Quién te debe ese dinero",
                    placeholder="Ej: Cliente Juan, Vecino, Distribuidor",
                    key="registrar_cxc_cliente"
                )
                monto = st.number_input("Monto que te deben", min_value=0.0, step=1000.0, key="registrar_cxc_monto")
                activar_fecha_limite_cxc = st.checkbox("Agregar fecha estimada de pago", key="registrar_cxc_limite_toggle")
                if activar_fecha_limite_cxc:
                    fecha_limite_cxc = st.date_input(
                        "Fecha estimada de pago",
                        value=fecha_mov + timedelta(days=30),
                        key="registrar_cxc_limite"
                    )
                deuda_nombre = cuenta_cobrar_nombre
                prestamista = cliente_cxc
                fecha_limite_deuda = fecha_limite_cxc
                st.caption("Se registra como dinero que prestaste. No entra aún como ingreso real hasta que te paguen.")

        elif tipo == "Cobro cuenta por cobrar":
            categoria = "Cobro cuenta por cobrar"
            cxc_activas_df = df_cxc[df_cxc["saldo_pendiente"] > 0].copy() if not df_cxc.empty else pd.DataFrame()
            if cxc_activas_df.empty:
                st.info("Aún no tienes registros activos de 'Prestaste Dinero'. Primero crea uno.")
            else:
                cxc_activas_df["label"] = cxc_activas_df.apply(
                    lambda row: f"{row['nombre']} · {row['cliente']} · pendiente {money(row['saldo_pendiente'])}",
                    axis=1
                )
                cxc_label = st.selectbox(
                    "Selecciona un registro de dinero prestado",
                    cxc_activas_df["label"].tolist(),
                    key="registrar_cobro_cxc_select"
                )
                cxc_row = cxc_activas_df[cxc_activas_df["label"] == cxc_label].iloc[0]
                cuenta_cobrar_id = cxc_row["id"]
                cuenta_cobrar_nombre = cxc_row["nombre"]
                cliente_cxc = cxc_row["cliente"]
                saldo_cxc_actual = float(cxc_row["saldo_pendiente"] or 0)
                fecha_limite_cxc = cxc_row["fecha_limite"].date() if pd.notna(cxc_row["fecha_limite"]) else None
                monto = st.number_input(
                    "Monto que te pagaron",
                    min_value=0.0,
                    max_value=float(saldo_cxc_actual) if saldo_cxc_actual > 0 else None,
                    step=1000.0,
                    key="registrar_cobro_cxc_monto"
                )
                deuda_nombre = cuenta_cobrar_nombre
                prestamista = cliente_cxc
                fecha_limite_deuda = fecha_limite_cxc
                st.caption(f"Pendiente actual por recibir: {money(saldo_cxc_actual)}")

        else:
            categoria = "Pago de deuda"
            deudas_activas_df = df_deudas[df_deudas["saldo_pendiente"] > 0].copy() if not df_deudas.empty else pd.DataFrame()
            if deudas_activas_df.empty:
                st.info("Aún no tienes créditos activos registrados. Primero crea un 'Crédito solicitado'.")
            else:
                deudas_activas_df["label"] = deudas_activas_df.apply(
                    lambda row: f"{row['nombre']} · {row['prestamista']} · pendiente {money(row['saldo_pendiente'])}",
                    axis=1
                )
                deuda_label = st.selectbox(
                    "Selecciona un crédito",
                    deudas_activas_df["label"].tolist(),
                    key="registrar_pago_deuda_select"
                )
                deuda_row = deudas_activas_df[deudas_activas_df["label"] == deuda_label].iloc[0]
                deuda_id = deuda_row["id"]
                deuda_nombre = deuda_row["nombre"]
                prestamista = deuda_row["prestamista"]
                saldo_deuda_actual = float(deuda_row["saldo_pendiente"] or 0)
                fecha_limite_deuda = deuda_row["fecha_limite"].date() if pd.notna(deuda_row["fecha_limite"]) else None
                monto = st.number_input(
                    "Monto pagado al crédito",
                    min_value=0.0,
                    max_value=float(saldo_deuda_actual) if saldo_deuda_actual > 0 else None,
                    step=1000.0,
                    key="registrar_pago_deuda_monto"
                )
                st.caption(f"Pendiente actual del crédito: {money(saldo_deuda_actual)}")

        col_btn_1, col_btn_2 = st.columns(2)
        with col_btn_1:
            if st.button("Guardar movimiento", use_container_width=True):
                errores = []

                if tipo in ("Ingreso", "Gasto") and (not categoria or categoria.strip() == "Sin categorías"):
                    errores.append("Necesitas al menos una categoría válida para guardar el movimiento.")
                if monto <= 0:
                    errores.append("El monto debe ser mayor que 0.")
                if tipo == "Ingreso (Deuda)" and not deuda_nombre.strip():
                    errores.append("Escribe un nombre para el crédito.")
                if tipo == "Gasto":
                    try:
                        df_limites_eval = obtener_limites_categoria_usuario(user_id)
                        if not df_limites_eval.empty and str(plan_usuario_actual.get("plan", "free")).lower() in {"pro", "premium", "paid", "plus"}:
                            fila_lim = df_limites_eval[(df_limites_eval["categoria"] == categoria) & (df_limites_eval["activo"] == True)]
                            if not fila_lim.empty:
                                limite_val = float(fila_lim.iloc[0]["limite_mensual"] or 0)
                                _, proyectado = evaluar_limite_categoria(df_mes if not df_mes.empty else pd.DataFrame(), categoria, float(monto or 0))
                                if limite_val > 0 and proyectado > limite_val:
                                    errores.append(f"Este gasto dejaría {categoria} en {money(proyectado)}, por encima de tu límite premium de {money(limite_val)}.")
                    except Exception:
                        pass
                if tipo == "Ingreso (Deuda)" and not prestamista.strip():
                    errores.append("Indica quién te prestó.")
                if tipo == "Cuenta por cobrar" and not cuenta_cobrar_nombre.strip():
                    errores.append("Escribe un nombre para el dinero prestado.")
                if tipo == "Cuenta por cobrar" and not cliente_cxc.strip():
                    errores.append("Indica quién te debe ese dinero.")
                if tipo == "Cobro cuenta por cobrar" and not cuenta_cobrar_id:
                    errores.append("Selecciona un registro activo de dinero prestado para registrar el pago recibido.")
                if tipo == "Cobro cuenta por cobrar" and saldo_cxc_actual > 0 and monto > saldo_cxc_actual:
                    errores.append("Lo recibido no puede superar el saldo pendiente que te deben.")
                if tipo == "Pago de deuda" and not deuda_id:
                    errores.append("Selecciona un crédito activo para registrar el pago.")
                if tipo == "Pago de deuda" and saldo_deuda_actual > 0 and monto > saldo_deuda_actual:
                    errores.append("El pago no puede superar el saldo pendiente del crédito.")
                if es_recurrente and proxima_fecha_recurrencia and proxima_fecha_recurrencia < fecha_mov:
                    errores.append("La próxima fecha recurrente no puede ser anterior al movimiento.")
                if es_recurrente and fecha_fin_recurrencia and proxima_fecha_recurrencia and fecha_fin_recurrencia < proxima_fecha_recurrencia:
                    errores.append("La fecha fin recurrente no puede ser anterior a la próxima fecha.")

                if errores:
                    for err in errores:
                        st.error(err)
                else:
                    try:
                        deuda_creada = None
                        deuda_id_mov = deuda_id
                        cxc_creada = None
                        cuenta_cobrar_id_mov = cuenta_cobrar_id

                        if tipo == "Ingreso (Deuda)":
                            deuda_creada = crear_deuda_segura({
                                "usuario_id": user_id,
                                "nombre": deuda_nombre.strip(),
                                "prestamista": prestamista.strip(),
                                "monto_total": float(monto),
                                "saldo_pendiente": float(monto),
                                "fecha": datetime.combine(fecha_mov, datetime.min.time()).isoformat(),
                                "fecha_limite": datetime.combine(fecha_limite_deuda, datetime.min.time()).isoformat() if fecha_limite_deuda else None,
                                "descripcion": descripcion.strip(),
                                "estado": "activa",
                                "actualizado_en": datetime.now().isoformat()
                            })
                            if not deuda_creada or not isinstance(deuda_creada, dict) or not deuda_creada.get("id"):
                                st.error("La deuda no se pudo crear en la tabla base 'deudas'. El movimiento no se guardó para evitar inconsistencias.")
                                st.stop()
                            deuda_id_mov = deuda_creada.get("id")

                        if tipo == "Cuenta por cobrar":
                            cxc_creada = crear_cuenta_por_cobrar_segura({
                                "usuario_id": user_id,
                                "nombre": cuenta_cobrar_nombre.strip(),
                                "cliente": cliente_cxc.strip(),
                                "monto_total": float(monto),
                                "saldo_pendiente": float(monto),
                                "fecha": datetime.combine(fecha_mov, datetime.min.time()).isoformat(),
                                "fecha_limite": datetime.combine(fecha_limite_cxc, datetime.min.time()).isoformat() if fecha_limite_cxc else None,
                                "descripcion": descripcion.strip(),
                                "estado": "activa",
                                "actualizado_en": datetime.now().isoformat()
                            })
                            if not cxc_creada or not isinstance(cxc_creada, dict) or not cxc_creada.get("id"):
                                st.error("La cuenta por cobrar no se pudo crear en la tabla base 'cuentas_por_cobrar'. El movimiento no se guardó para evitar inconsistencias.")
                                st.stop()
                            cuenta_cobrar_id_mov = cxc_creada.get("id")

                        payload = {
                            "usuario_id": user_id,
                            "fecha": datetime.combine(fecha_mov, datetime.min.time()).isoformat(),
                            "tipo": tipo,
                            "categoria": categoria.strip() if categoria else None,
                            "monto": float(monto),
                            "descripcion": descripcion.strip(),
                            "emocion": emocion if tipo == "Gasto" else None,
                            "deuda_id": deuda_id_mov if tipo in ["Ingreso (Deuda)", "Pago de deuda"] else cuenta_cobrar_id_mov if tipo in ["Cuenta por cobrar", "Cobro cuenta por cobrar"] else None,
                            "deuda_nombre": deuda_nombre.strip() if deuda_nombre else None,
                            "prestamista": prestamista.strip() if prestamista else None,
                            "fecha_limite_deuda": datetime.combine(fecha_limite_deuda, datetime.min.time()).isoformat() if fecha_limite_deuda else None,
                            "cuenta_cobrar_id": cuenta_cobrar_id_mov if tipo in ["Cuenta por cobrar", "Cobro cuenta por cobrar"] else None,
                            "cuenta_cobrar_nombre": cuenta_cobrar_nombre.strip() if cuenta_cobrar_nombre else deuda_nombre.strip() if deuda_nombre else None,
                            "cliente_cxc": cliente_cxc.strip() if cliente_cxc else prestamista.strip() if prestamista else None,
                            "fecha_limite_cxc": datetime.combine(fecha_limite_cxc, datetime.min.time()).isoformat() if fecha_limite_cxc else None,
                            "es_recurrente": bool(es_recurrente),
                            "frecuencia_recurrencia": frecuencia_recurrencia if es_recurrente else None,
                            "proxima_fecha_recurrencia": datetime.combine(proxima_fecha_recurrencia, datetime.min.time()).isoformat() if es_recurrente and proxima_fecha_recurrencia else None,
                            "fecha_fin_recurrencia": datetime.combine(fecha_fin_recurrencia, datetime.min.time()).isoformat() if es_recurrente and fecha_fin_recurrencia else None,
                            "recurrente_activo": bool(recurrente_activo) if es_recurrente else False
                        }

                        insertar_movimiento_seguro(payload)

                        if tipo == "Pago de deuda" and deuda_id:
                            actualizar_deuda_pago_seguro(deuda_id, saldo_deuda_actual - float(monto))

                        registrar_evento_producto(
                            "movement_created",
                            user_id=user_id,
                            pagina="Registrar",
                            detalle=f"{tipo_display(tipo)} · {categoria}",
                            valor=float(monto)
                        )
                        st.session_state["reset_registrar_form"] = True
                        st.success("Movimiento guardado correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error guardando movimiento: {e}")

        with col_btn_2:
            if st.button("Resetear formulario", use_container_width=True):
                st.session_state["reset_registrar_form"] = True
                st.rerun()

    with col_side:
        render_registrar_spotlight(
            tipo=tipo,
            monto=monto,
            categoria=categoria,
            deuda_nombre=deuda_nombre,
            prestamista=prestamista,
            saldo_deuda_actual=saldo_deuda_actual,
            es_recurrente=es_recurrente,
            frecuencia_recurrencia=frecuencia_recurrencia,
            df_mes_actual=df_mes if not df_mes.empty else pd.DataFrame()
        )

        color_map = {
            "Ingreso": "#4ADE80",
            "Gasto": "#F87171",
            "Ingreso (Deuda)": "#93C5FD",
            "Pago de deuda": "#FCD34D"
        }
        color_valor = color_map.get(tipo, "#E2E8F0")
        deuda_preview = deuda_nombre if deuda_nombre else "Sin deuda asociada"
        frecuencia_preview = frecuencia_recurrencia if es_recurrente and frecuencia_recurrencia else "No recurrente"
        proxima_preview = proxima_fecha_recurrencia.strftime("%Y-%m-%d") if es_recurrente and proxima_fecha_recurrencia else "No aplica"
        fecha_limite_preview = fecha_limite_deuda.strftime("%Y-%m-%d") if isinstance(fecha_limite_deuda, date) else "No definida"

        st.markdown(
            f"""
            <div class="soft-card">
                <div class="section-title">Vista previa contextual</div>
                <div class="section-caption">Aparece solo lo necesario según el tipo de movimiento.</div>
                <div class="tiny-muted">Tipo</div>
                <div class="form-preview-value" style="color:{color_valor};">{tipo}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Categoría / naturaleza</div>
                <div style="font-weight:700;">{categoria if categoria else 'Contextual'}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Monto</div>
                <div style="font-weight:800;font-size:1.15rem;">{money(monto)}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Descripción</div>
                <div style="font-weight:600;">{descripcion if descripcion else 'Sin descripción'}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Deuda</div>
                <div style="font-weight:600;">{deuda_preview}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Prestamista</div>
                <div style="font-weight:600;">{prestamista if prestamista else 'No aplica'}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Fecha límite deuda</div>
                <div style="font-weight:600;">{fecha_limite_preview}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Emoción</div>
                <div style="font-weight:600;">{emocion if emocion else 'No registrada'}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Recurrencia</div>
                <div style="font-weight:600;">{frecuencia_preview} · próxima: {proxima_preview}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if tipo == "Pago de deuda" and saldo_deuda_actual > 0:
            st.markdown(
                f"""
                <div class="mini-soft-card">
                    <div class="tiny-muted">Saldo pendiente luego del pago</div>
                    <div style="font-weight:800;font-size:1.05rem;">{money(max(saldo_deuda_actual - float(monto or 0), 0))}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        render_avatar(pagina, nombre_usuario, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)

if pagina == "Análisis":
    zentix_hero(nombre_usuario, saldo_disponible, total_ingresos, total_gastos)
    render_contexto_descubrimiento("Análisis")
    render_tutorial_zentix("Análisis", nombre_usuario, user_id, df, meta_guardada_global, preferencias_usuario_actual)
    section_header("Análisis del mes", "Explora movimientos, deuda, recurrencias, concentración por categoría y evolución diaria.")

    col_a, col_b = st.columns([1.15, 0.85])
    with col_a:
        render_movimientos_action_hub(user_id, df if not df.empty else pd.DataFrame(), df_deudas if df_deudas is not None else pd.DataFrame())
        if not df_mes.empty:
            vista_df = df_mes.copy().sort_values("fecha", ascending=False)
            vista_df["fecha"] = vista_df["fecha"].dt.strftime("%Y-%m-%d")
            columnas = ["fecha", "tipo", "categoria", "monto", "descripcion"]

            for extra_col in ["deuda_nombre", "prestamista", "emocion", "frecuencia_recurrencia", "proxima_fecha_recurrencia"]:
                if extra_col in vista_df.columns:
                    columnas.append(extra_col)

            if "proxima_fecha_recurrencia" in vista_df.columns:
                vista_df["proxima_fecha_recurrencia"] = pd.to_datetime(vista_df["proxima_fecha_recurrencia"], errors="coerce").dt.strftime("%Y-%m-%d")

            st.dataframe(
                vista_df[columnas],
                use_container_width=True
            )
            render_editor_movimientos(user_id, df if not df.empty else pd.DataFrame(), df_deudas if df_deudas is not None else pd.DataFrame())
        else:
            empty_state("Todavía no hay datos", "Cuando registres movimientos este mes, aquí verás tablas y gráficos más útiles.")
            render_editor_movimientos(user_id, df if not df.empty else pd.DataFrame(), df_deudas if df_deudas is not None else pd.DataFrame())
    with col_b:
        render_movimiento_focus_panel(df if not df.empty else pd.DataFrame())
        st.markdown(
            f"""
            <div class="soft-card fade-up">
                <div class="section-title">Lectura de deuda y recurrencia</div>
                <div class="section-caption">Separando caja, ingresos reales y obligaciones pendientes.</div>
                <div class="tiny-muted">Entradas por deuda</div>
                <div class="form-preview-value">{money(total_entradas_deuda_mes)}</div>
                <div class="tiny-muted" style="margin-top:0.6rem;">Pagos de deuda</div>
                <div style="font-weight:800;font-size:1.1rem;">{money(total_pagos_deuda_mes)}</div>
                <div class="tiny-muted" style="margin-top:0.6rem;">Saldo pendiente total</div>
                <div style="font-weight:800;font-size:1.1rem;">{money(saldo_pendiente_deudas_global)}</div>
                <div class="tiny-muted" style="margin-top:0.6rem;">Pendiente por cobrar</div>
                <div style="font-weight:800;font-size:1.1rem;">{money(saldo_pendiente_cxc_global)}</div>
                <div class="tiny-muted" style="margin-top:0.6rem;">Recurrentes activos</div>
                <div style="font-weight:800;font-size:1.1rem;">{int(df[df["recurrente_activo"] == True].shape[0]) if not df.empty and "recurrente_activo" in df.columns else 0}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        render_avatar(pagina, nombre_usuario, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)

    render_reportes_compactos(nombre_usuario, plan_usuario_actual, df if not df.empty else pd.DataFrame(), user_id=user_id)

    with st.expander("Comparativas y patrones", expanded=False):
        section_header("Comparativas y patrones", "Así viene cambiando tu comportamiento financiero.")
        a1, a2, a3 = st.columns(3)
        with a1:
            render_list_card("Comparativa semanal", [f"Gasto: {money_delta(comparativa_periodos.get('gasto_semana_pct', 0.0))}", f"Ingreso: {money_delta(comparativa_periodos.get('ingreso_semana_pct', 0.0))}"], "Semana actual vs anterior.")
        with a2:
            render_list_card("Comparativa mensual", [f"Gasto: {money_delta(comparativa_periodos.get('gasto_mes_pct', 0.0))}", f"Ingreso: {money_delta(comparativa_periodos.get('ingreso_mes_pct', 0.0))}"], "Mes actual vs anterior.")
        with a3:
            render_list_card("Patrones detectados", patrones_comportamiento + [f"Deudas activas: {deudas_activas_global}"], "Zentix busca hábitos que explican tu comportamiento.")

    with st.expander("Insights personalizados", expanded=False):
        section_header("Insights personalizados", "Tu perfil, tus alertas y tus mejores mejoras.")
        b1, b2 = st.columns(2)
        with b1:
            render_list_card("Perfil financiero", [perfil_financiero.get("descripcion", "Sin perfil disponible."), perfil_financiero.get("microcopy", "")], "Identidad financiera detectada automáticamente.")
        with b2:
            render_list_card("Alertas + categorías", alertas_proactivas + sugerencias_categoria + [f"Saldo deuda pendiente: {money(saldo_pendiente_deudas_global)}"], recomendacion_accionable)

    if not df_mes.empty:
        resumen = (
            df_mes.groupby("categoria")["monto"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        resumen["categoria"] = resumen["categoria"].fillna("Sin categoría")

        timeline = (
            df_mes.groupby(["fecha", "tipo"])["monto"]
            .sum()
            .reset_index()
            .sort_values("fecha")
        )

        col_chart_1, col_chart_2 = st.columns(2)

        with col_chart_1:
            fig_bar = px.bar(
                resumen,
                x="categoria",
                y="monto",
                title="Movimientos por categoría",
                text_auto=True,
                color="monto",
                color_continuous_scale=["#1D4ED8", "#06B6D4", "#8B5CF6"]
            )
            fig_bar.update_coloraxes(showscale=False)
            aplicar_estilo_plotly(fig_bar, height=390)
            st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

        with col_chart_2:
            fig_line = px.line(
                timeline,
                x="fecha",
                y="monto",
                color="tipo",
                title="Evolución diaria",
                markers=True,
                color_discrete_map={
                    "Ingreso": "#22C55E",
                    "Gasto": "#EF4444",
                    "Ingreso (Deuda)": "#3B82F6",
                    "Pago de deuda": "#F59E0B"
                }
            )
            aplicar_estilo_plotly(fig_line, height=390)
            st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No hay datos este mes.")

if pagina == "Ahorro":
    zentix_hero(nombre_usuario, saldo_disponible, total_ingresos, total_gastos)
    render_contexto_descubrimiento("Ahorro")
    render_tutorial_zentix("Ahorro", nombre_usuario, user_id, df, meta_guardada_global, preferencias_usuario_actual)
    section_header("Plan de ahorro", "Conecta tu meta con tu saldo disponible actual y dale identidad.")

    try:
        meta_result = obtener_meta(user_id)
        meta_guardada = float(meta_result["meta"]) if meta_result else 0.0
    except Exception as e:
        st.error(f"Error cargando meta de ahorro: {e}")
        meta_result = None
        meta_guardada = 0.0

    nombre_meta_input = st.text_input(
        "Ponle nombre a tu meta",
        value=nombre_meta_guardado,
        placeholder="Ej: Viaje, Moto, Fondo de calma"
    )

    meta = st.number_input(
        "¿Cuánto quieres ahorrar?",
        min_value=0.0,
        step=1000.0,
        value=meta_guardada,
        key="meta_ahorro_input"
    )

    ahorro_actual = float(saldo_disponible)
    faltante = max(0.0, float(meta) - max(ahorro_actual, 0.0))
    progreso = max(0.0, ahorro_actual / float(meta)) if float(meta) > 0 else 0.0
    aporte_semanal_estimado = estimar_aporte_semanal_meta(df if not df.empty else pd.DataFrame())
    proyeccion_meta = calcular_proyeccion_meta(meta, ahorro_actual, aporte_semanal_estimado)

    col_k1, col_k2, col_k3 = st.columns(3)
    with col_k1:
        kpi_card("Disponible actual", money(ahorro_actual), "Lo que hoy puedes destinar", "balance")
    with col_k2:
        kpi_card("Meta definida", money(meta), nombre_meta_input if nombre_meta_input else "Objetivo configurado", "saving")
    with col_k3:
        kpi_card("Faltante", money(faltante), "Lo que resta por cubrir", "expense" if faltante > 0 else "income")

    col_meta1, col_meta2 = st.columns([1.1, 0.9])

    with col_meta1:
        col_btn_1, col_btn_2 = st.columns(2)

        with col_btn_1:
            if st.button("Guardar meta", use_container_width=True):
                try:
                    guardar_meta_segura(user_id, meta, nombre_meta_input, meta_result)
                    st.success("Meta guardada correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error guardando meta: {e}")

        with col_btn_2:
            if st.button("Limpiar meta", use_container_width=True):
                try:
                    eliminar_meta_segura(user_id)
                    st.warning("Meta eliminada correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error eliminando meta: {e}")

        if float(meta) > 0:
            st.progress(min(progreso, 1.0))
            if ahorro_actual >= float(meta):
                st.success("Vas excelente: con tu disponible actual ya alcanzas tu meta de ahorro.")
            else:
                st.info(f"Te faltan {money(faltante)} para cumplir tu meta.")
        else:
            st.info("Define una meta para comenzar.")

        st.markdown(
            f"""
            <div class="mini-soft-card">
                <div class="tiny-muted">Proyección estimada</div>
                <div style="font-weight:800;line-height:1.5;">{proyeccion_meta.get('mensaje', 'Sin proyección')}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_meta2:
        st.markdown(
            f"""
            <div class="soft-card">
                <div class="section-title">{nombre_meta_input if nombre_meta_input else 'Lectura de tu objetivo'}</div>
                <div class="section-caption">
                    {("Tu saldo ya cubre la meta actual. Puedes subir el objetivo o mantenerlo." if float(meta) > 0 and ahorro_actual >= float(meta)
                    else "Tu meta aún no está cubierta. Usa esta referencia para ajustar tu ritmo de gasto y ahorro." if float(meta) > 0
                    else "Todavía no has definido una meta. Zentix puede acompañarte mejor cuando fijes un objetivo claro.")}
                </div>
                <div class="tiny-muted">Progreso actual</div>
                <div class="form-preview-value">{round(min(progreso, 1.0) * 100, 1) if float(meta) > 0 else 0}%</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Aporte semanal estimado</div>
                <div style="font-weight:700;line-height:1.5;">{money(proyeccion_meta.get('aporte_semanal', 0))}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Plan sugerido</div>
                <div style="font-weight:700;line-height:1.5;">{recomendacion_accionable}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        render_avatar(pagina, nombre_usuario, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)

if pagina == "Perfil":
    zentix_hero(nombre_usuario, saldo_disponible, total_ingresos, total_gastos)
    render_contexto_descubrimiento("Perfil")
    render_tutorial_zentix("Perfil", nombre_usuario, user_id, df, meta_guardada_global, preferencias_usuario_actual)
    section_header("Centro de perfil y plan", "Gestiona identidad, IA, meta principal y recordatorios suaves desde un solo lugar.")

    plan_nombre = plan_usuario_actual.get("plan", "free").upper()
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        kpi_card("Plan actual", plan_nombre, "Experiencia activa", "balance")
    with col_k2:
        kpi_card("Límite IA diario", str(consultas_limite_hoy), "Consultas por día", "saving")
    with col_k3:
        kpi_card("IA usada hoy", str(consultas_usadas_hoy), "Consumo acumulado", "expense" if consultas_usadas_hoy >= consultas_limite_hoy else "income")
    with col_k4:
        kpi_card("Meta principal", nombre_meta_guardado if nombre_meta_guardado else "Sin nombre", money(meta_guardada_global), "saving")

    render_perfil_spotlight(
        plan_actual=plan_usuario_actual,
        consultas_usadas=consultas_usadas_hoy,
        consultas_limite=consultas_limite_hoy,
        preferencias=preferencias_usuario_actual,
        resumen_recordatorios=resumen_recordatorios_global,
        meta_nombre=nombre_meta_guardado,
        meta_valor=meta_guardada_global,
        saldo_pendiente=saldo_pendiente_deudas_global,
        proyeccion=proyeccion_meta_global
    )

    col_main, col_side = st.columns([1.15, 0.85])

    with col_main:
        st.markdown(
            f"""
            <div class="soft-card">
                <div class="section-title">Identidad financiera</div>
                <div class="section-caption">Tu perfil visible, tu meta principal y un vistazo elegante a tu estado actual.</div>
                <div class="tiny-muted">Nombre mostrado</div>
                <div class="form-preview-value" style="font-size:1.2rem;">{nombre_usuario}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Correo de acceso</div>
                <div style="font-weight:700;">{getattr(st.session_state.user, "email", "Sin correo")}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Meta principal</div>
                <div style="font-weight:700;">{nombre_meta_guardado if nombre_meta_guardado else 'Aún sin nombre'} · {money(meta_guardada_global)}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Categorías favoritas</div>
                <div style="font-weight:700;">{", ".join(categorias_favoritas_global) if categorias_favoritas_global else 'Se irán detectando con tu uso'}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.expander("🔔 Recordatorios y preferencias", expanded=True):
            pref_email = st.checkbox("Recibir recordatorios por correo", value=bool(preferencias_usuario_actual.get("recordatorio_email", True)))
            pref_sms = st.checkbox("Preparar SMS para futuro", value=bool(preferencias_usuario_actual.get("recordatorio_sms", False)))
            pref_frecuencia = st.selectbox(
                "Frecuencia",
                ["suave", "normal"],
                index=["suave", "normal"].index(preferencias_usuario_actual.get("frecuencia_recordatorios", "suave"))
                if preferencias_usuario_actual.get("frecuencia_recordatorios", "suave") in ["suave", "normal"] else 0
            )
            pref_registro = st.checkbox("Recordatorio por inactividad", value=bool(preferencias_usuario_actual.get("recordatorio_registro", True)))
            pref_meta = st.checkbox("Alertas de meta", value=bool(preferencias_usuario_actual.get("recordatorio_meta", False)))
            pref_resumen = st.checkbox("Resumen semanal", value=bool(preferencias_usuario_actual.get("resumen_semanal", False)))
            pref_silencio = st.checkbox("Activar horario silencioso", value=bool(preferencias_usuario_actual.get("silencio_activado", False)))

            col_h1, col_h2 = st.columns(2)
            with col_h1:
                silencio_inicio = st.text_input("Silencio desde", value=preferencias_usuario_actual.get("silencio_inicio", "21:00"))
            with col_h2:
                silencio_fin = st.text_input("Silencio hasta", value=preferencias_usuario_actual.get("silencio_fin", "07:00"))

            email_contacto = st.text_input(
                "Correo para avisos",
                value=preferencias_usuario_actual.get("email_contacto") or getattr(st.session_state.user, "email", "")
            )
            telefono_contacto = st.text_input(
                "Teléfono (opcional / futuro)",
                value=preferencias_usuario_actual.get("telefono", ""),
                placeholder="Déjalo listo para SMS más adelante"
            )

            smtp_status = obtener_config_smtp()
            estado_smtp = describir_config_smtp(smtp_status)
            estado_smtp_txt = estado_smtp.get("titulo", "SMTP pendiente")
            st.caption(f"Estado del canal de correo: {estado_smtp_txt}")
            st.caption(estado_smtp.get("detalle", ""))
            if smtp_status.get("provider_hint") == "gmail":
                st.caption("Tip Gmail: la app admite la contraseña de aplicación con o sin espacios; Zentix la normaliza sola.")

            btn_save, btn_test = st.columns(2)
            with btn_save:
                if st.button("Guardar preferencias", use_container_width=True):
                    guardar_preferencias_usuario(user_id, {
                        "recordatorio_email": pref_email,
                        "recordatorio_sms": pref_sms,
                        "frecuencia_recordatorios": pref_frecuencia,
                        "recordatorio_registro": pref_registro,
                        "recordatorio_meta": pref_meta,
                        "resumen_semanal": pref_resumen,
                        "silencio_activado": pref_silencio,
                        "silencio_inicio": silencio_inicio,
                        "silencio_fin": silencio_fin,
                        "email_contacto": email_contacto,
                        "telefono": telefono_contacto
                    })
                    st.success("Preferencias guardadas. Si SMTP está configurado, Zentix ya puede enviar recordatorios por correo.")

            with btn_test:
                if st.button("Enviar correo de prueba", use_container_width=True):
                    ok, detalle = enviar_correo_prueba_zentix(nombre_usuario, {
                        "email_contacto": email_contacto,
                        "recordatorio_email": pref_email
                    }, total_ingresos, total_gastos, saldo_disponible)
                    registrar_evento_producto("test_email_sent" if ok else "test_email_error", user_id=user_id, pagina="Perfil", detalle=detalle)
                    if ok:
                        st.success(detalle)
                    else:
                        st.warning(detalle)

            st.caption("Activa tus recordatorios, ajusta el horario silencioso y prueba tu correo cuando quieras. Zentix usará estas preferencias para acompañarte sin ser invasivo.")
            if mostrar_paneles_internos():
                render_automation_control_center()
                render_centro_lanzamiento(launch_cfg, plan_usuario_actual)

        if mostrar_plan_comercial():
            with st.expander("✨ Plan Free vs Pro", expanded=False):
                st.markdown(
                    """
                    <div class="mini-soft-card">
                        <div style="font-weight:800;margin-bottom:0.35rem;">Free</div>
                        <div class="tiny-muted">Límite diario de IA, recordatorios suaves, panel premium esencial.</div>
                    </div>
                    <div class="mini-soft-card">
                        <div style="font-weight:800;margin-bottom:0.35rem;">Pro</div>
                        <div class="tiny-muted">Más IA, lecturas más profundas, automatizaciones y una experiencia más potente sin ser invasiva.</div>
                    <div class="tiny-muted" style="margin-top:0.35rem;">La app actual ya queda lista para integrarse mejor a jobs externos y modularización futura sin romper el panel.</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with col_side:
        dias_inactividad_publico = resumen_recordatorios_global.get('dias_inactividad')
        dias_inactividad_txt = 'Aún no aplica' if dias_inactividad_publico is None else str(dias_inactividad_publico)
        ultimo_mov_publico = resumen_recordatorios_global.get('ultimo_movimiento', 'Sin movimientos') or 'Sin movimientos'
        sugerencia_publica = resumen_recordatorios_global.get('sugerencia', 'Sin evaluación') or 'Sin evaluación'
        canal_recordatorios_txt = 'Correo activo' if bool(preferencias_usuario_actual.get('recordatorio_email', False)) else 'Recordatorios pausados'
        st.markdown(
            f"""
            <div class="soft-card">
                <div class="section-title">Recordatorios inteligentes</div>
                <div class="section-caption">Zentix te acompaña con tacto, sin volverse invasivo.</div>
                <div class="tiny-muted">Último registro</div>
                <div style="font-weight:800;font-size:1.05rem;">{ultimo_mov_publico}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Días sin registrar</div>
                <div style="font-weight:800;font-size:1.05rem;">{dias_inactividad_txt}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Lectura actual</div>
                <div style="font-weight:700;line-height:1.5;">{sugerencia_publica}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Canal activo</div>
                <div style="font-weight:700;line-height:1.5;">{canal_recordatorios_txt}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="soft-card">
                <div class="section-title">Meta y deuda</div>
                <div class="section-caption">Dos palancas críticas, visibles sin recargar.</div>
                <div class="tiny-muted">Meta principal</div>
                <div style="font-weight:800;font-size:1.05rem;">{nombre_meta_guardado if nombre_meta_guardado else 'Sin nombre'} · {money(meta_guardada_global)}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Proyección</div>
                <div style="font-weight:700;line-height:1.5;">{proyeccion_meta_global.get('mensaje', 'Sin proyección')}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Saldo pendiente de deudas</div>
                <div style="font-weight:800;font-size:1.05rem;">{money(saldo_pendiente_deudas_global)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        render_avatar(pagina, nombre_usuario, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)


render_footer_producto(launch_cfg)
