import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from pathlib import Path
from supabase_config import supabase
from openai import OpenAI
import html
import io
import uuid
import smtplib
import ssl
from email.message import EmailMessage

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

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
openai_client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
) if GEMINI_API_KEY else None


def aplicar_estilo_zentix():
    st.markdown("""
    <style>
    :root {
        --bg: #06111f;
        --bg2: #0a1628;
        --panel: rgba(12, 20, 36, 0.88);
        --panel-2: rgba(14, 24, 42, 0.94);
        --line: rgba(148, 163, 184, 0.15);
        --line-strong: rgba(96, 165, 250, 0.20);
        --text: #F8FAFC;
        --muted: #94A3B8;
        --blue: #3B82F6;
        --cyan: #06B6D4;
        --purple: #8B5CF6;
        --green: #22C55E;
        --red: #EF4444;
        --amber: #F59E0B;
    }

    html, body, [class*="css"]  {
        color: var(--text);
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(59,130,246,0.16), transparent 28%),
            radial-gradient(circle at top right, rgba(139,92,246,0.10), transparent 24%),
            linear-gradient(180deg, #040b15 0%, #08111f 50%, #0b1627 100%);
    }

    [data-testid="stAppViewContainer"] {
        background: transparent;
    }

    .block-container {
        max-width: 100%;
        padding-top: 4rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
    }

    header[data-testid="stHeader"] {
        background: rgba(4, 11, 21, 0.85);
        backdrop-filter: blur(8px);
    }

    [data-testid="stToolbar"] {
        display: none;
    }

    [data-testid="stDecoration"] {
        display: none;
    }

    [data-testid="collapsedControl"] {
        position: fixed;
        top: 0.85rem;
        left: 0.85rem;
        z-index: 999999 !important;
        background: rgba(15,23,42,0.96);
        border: 1px solid rgba(96,165,250,0.28);
        border-radius: 14px;
        padding: 0.2rem 0.3rem;
        box-shadow: 0 10px 24px rgba(0,0,0,0.28);
    }

    [data-testid="collapsedControl"]:hover {
        border-color: rgba(125,211,252,0.40);
        box-shadow: 0 12px 28px rgba(37,99,235,0.22);
    }

    [data-testid="collapsedControl"] svg {
        fill: #F8FAFC !important;
        color: #F8FAFC !important;
    }

    [data-testid="stSidebarContent"] {
        padding-top: 0.5rem;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(7,12,22,0.98), rgba(10,18,32,0.98));
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebar"] * {
        color: var(--text);
    }

    h1, h2, h3 {
        color: var(--text) !important;
        letter-spacing: -0.02em;
    }

    p, label, .stMarkdown, .stCaption, span, div {
        color: inherit;
    }

    .stButton > button {
        width: 100%;
        min-height: 58px;
        border-radius: 22px;
        border: 1px solid rgba(148, 163, 184, 0.18);
        background:
            radial-gradient(circle at top left, rgba(125, 211, 252, 0.10), transparent 34%),
            radial-gradient(circle at bottom right, rgba(139, 92, 246, 0.08), transparent 28%),
            linear-gradient(135deg, rgba(10,18,32,0.98), rgba(15,23,42,0.98));
        color: #F8FAFC;
        font-weight: 800;
        font-size: 1rem;
        letter-spacing: 0.01em;
        padding: 0.95rem 1.15rem;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.04),
            0 10px 24px rgba(0,0,0,0.26);
        backdrop-filter: blur(10px);
        transition:
            transform 0.18s ease,
            box-shadow 0.18s ease,
            border-color 0.18s ease,
            background 0.18s ease,
            filter 0.18s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        border-color: rgba(125, 211, 252, 0.32);
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.05),
            0 14px 30px rgba(16,24,40,0.34);
        filter: brightness(1.03);
    }

    .stButton > button:active {
        transform: translateY(0) scale(0.985);
    }

    .stButton > button:focus:not(:active) {
        border-color: rgba(125, 211, 252, 0.48);
        box-shadow:
            0 0 0 1px rgba(125, 211, 252, 0.20),
            0 14px 30px rgba(37,99,235,0.14);
    }

    .stButton > button[kind="primary"] {
        background:
            radial-gradient(circle at top left, rgba(125, 211, 252, 0.26), transparent 34%),
            radial-gradient(circle at bottom right, rgba(167, 139, 250, 0.22), transparent 30%),
            linear-gradient(135deg, rgba(18,35,72,0.98), rgba(27,46,95,0.98));
        border: 1px solid rgba(96, 165, 250, 0.34);
        color: #FFFFFF;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.07),
            0 16px 34px rgba(29,78,216,0.20),
            0 0 0 1px rgba(125,211,252,0.08);
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        border-color: rgba(125, 211, 252, 0.52);
        background:
            radial-gradient(circle at top left, rgba(125, 211, 252, 0.32), transparent 34%),
            radial-gradient(circle at bottom right, rgba(192, 132, 252, 0.24), transparent 30%),
            linear-gradient(135deg, rgba(22,41,84,1), rgba(34,56,110,1));
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.08),
            0 20px 40px rgba(37,99,235,0.24);
    }

    .stButton > button[kind="secondary"] {
        background:
            radial-gradient(circle at top left, rgba(59,130,246,0.08), transparent 30%),
            linear-gradient(135deg, rgba(13,20,36,0.98), rgba(15,23,42,0.98));
        border: 1px solid rgba(148, 163, 184, 0.16);
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.04),
            0 10px 22px rgba(0,0,0,0.24);
    }

    .stTextInput > div > div > input,
    .stNumberInput input,
    .stDateInput input,
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        background: rgba(15,23,42,0.88) !important;
        color: var(--text) !important;
        border: 1px solid rgba(148,163,184,0.15) !important;
        border-radius: 15px !important;
    }

    .stRadio [role="radiogroup"] {
        gap: 0.6rem;
    }

    .stRadio label {
        background: rgba(15,23,42,0.72);
        padding: 0.35rem 0.8rem;
        border-radius: 999px;
        border: 1px solid rgba(148,163,184,0.14);
    }

    .stAlert {
        border-radius: 16px;
    }

    .zentix-brand-title {
        font-size: 2rem;
        font-weight: 900;
        line-height: 1;
        margin: 0;
        letter-spacing: 0.02em;
    }

    .zentix-brand-sub {
        color: var(--muted);
        margin-top: 4px;
        font-size: 0.95rem;
    }

    .hero-card {
        background:
            radial-gradient(circle at top left, rgba(59,130,246,0.16), transparent 30%),
            linear-gradient(135deg, rgba(15,23,42,0.96), rgba(8,15,28,0.98));
        border: 1px solid rgba(96,165,250,0.16);
        border-radius: 28px;
        padding: 1.35rem;
        box-shadow: 0 18px 40px rgba(0,0,0,0.32);
        backdrop-filter: blur(10px);
        margin-bottom: 1rem;
    }

    .hero-badge {
        display: inline-block;
        padding: 0.35rem 0.78rem;
        border-radius: 999px;
        background: rgba(59,130,246,0.12);
        border: 1px solid rgba(59,130,246,0.22);
        color: #BFDBFE;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 0.85rem;
    }

    .hero-title {
        font-size: 2rem;
        font-weight: 900;
        line-height: 1.05;
        margin: 0 0 0.35rem 0;
        color: var(--text);
        letter-spacing: -0.03em;
    }

    .hero-subtitle {
        color: var(--muted);
        font-size: 1rem;
        line-height: 1.55;
        margin: 0;
    }

    .hero-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 1rem;
    }

    .hero-pill {
        display: inline-block;
        padding: 0.42rem 0.8rem;
        border-radius: 999px;
        background: rgba(15,23,42,0.74);
        border: 1px solid rgba(148,163,184,0.16);
        color: #E2E8F0;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .section-title {
        font-size: 1.06rem;
        font-weight: 800;
        color: var(--text);
        margin-top: 0.35rem;
        margin-bottom: 0.12rem;
    }

    .section-caption {
        font-size: 0.9rem;
        color: var(--muted);
        margin-bottom: 0.85rem;
    }

    .kpi-card {
        background: linear-gradient(180deg, rgba(12,20,36,0.94), rgba(9,16,29,0.98));
        border: 1px solid var(--line);
        border-radius: 22px;
        padding: 1rem;
        min-height: 124px;
        box-shadow: 0 12px 28px rgba(0,0,0,0.22);
    }

    .kpi-income {
        border-color: rgba(34,197,94,0.24);
        box-shadow: 0 12px 28px rgba(34,197,94,0.07);
    }

    .kpi-expense {
        border-color: rgba(239,68,68,0.22);
        box-shadow: 0 12px 28px rgba(239,68,68,0.07);
    }

    .kpi-balance {
        border-color: rgba(59,130,246,0.24);
        box-shadow: 0 12px 28px rgba(59,130,246,0.08);
    }

    .kpi-saving {
        border-color: rgba(139,92,246,0.22);
        box-shadow: 0 12px 28px rgba(139,92,246,0.08);
    }

    .kpi-label {
        font-size: 0.82rem;
        color: var(--muted);
        margin-bottom: 0.55rem;
    }

    .kpi-value {
        font-size: 1.6rem;
        font-weight: 900;
        color: var(--text);
        line-height: 1.1;
        margin-bottom: 0.25rem;
    }

    .kpi-foot {
        font-size: 0.82rem;
        color: var(--muted);
    }

    .soft-card {
        background: linear-gradient(180deg, rgba(12,20,36,0.80), rgba(10,18,32,0.94));
        border: 1px solid var(--line);
        border-radius: 22px;
        padding: 1rem 1.05rem;
        box-shadow: 0 12px 30px rgba(0,0,0,0.22);
        margin-bottom: 1rem;
    }

    .assistant-card {
        background:
            radial-gradient(circle at top left, rgba(59,130,246,0.14), transparent 32%),
            linear-gradient(135deg, rgba(15,23,42,0.96), rgba(10,18,32,0.98));
        border: 1px solid rgba(96,165,250,0.16);
        border-radius: 24px;
        padding: 1rem;
        box-shadow: 0 16px 32px rgba(0,0,0,0.26);
    }

    .assistant-title {
        font-size: 1.05rem;
        font-weight: 800;
        color: #C4B5FD;
        margin-bottom: 0.2rem;
    }

    .assistant-text {
        color: #E2E8F0;
        font-size: 0.95rem;
        line-height: 1.55;
    }

    .assistant-mini {
        color: var(--muted);
        font-size: 0.82rem;
        margin-top: 0.4rem;
    }

    .pill-ingreso {
        display: inline-block;
        padding: 0.45rem 0.88rem;
        border-radius: 999px;
        background: rgba(34,197,94,0.14);
        border: 1px solid rgba(34,197,94,0.28);
        color: #4ADE80;
        font-weight: 800;
        margin-bottom: 0.8rem;
    }

    .pill-gasto {
        display: inline-block;
        padding: 0.45rem 0.88rem;
        border-radius: 999px;
        background: rgba(239,68,68,0.14);
        border: 1px solid rgba(239,68,68,0.28);
        color: #F87171;
        font-weight: 800;
        margin-bottom: 0.8rem;
    }

    .empty-card {
        background: linear-gradient(180deg, rgba(12,20,36,0.82), rgba(10,18,32,0.94));
        border: 1px dashed rgba(148,163,184,0.18);
        border-radius: 22px;
        padding: 1.2rem;
        text-align: center;
        color: var(--muted);
    }

    .login-box {
        background: linear-gradient(180deg, rgba(10,14,24,0.92), rgba(10,18,32,0.98));
        border: 1px solid var(--line);
        border-radius: 24px;
        padding: 1.25rem;
        box-shadow: 0 18px 36px rgba(0,0,0,0.28);
    }

    .sidebar-brand-title {
        font-size: 1.05rem;
        font-weight: 900;
        color: var(--text);
        margin: 0;
        line-height: 1.1;
    }

    .sidebar-brand-sub {
        color: var(--muted);
        font-size: 0.78rem;
        margin-top: 2px;
    }

    .sidebar-user-card {
        background: rgba(15,23,42,0.72);
        border: 1px solid rgba(148,163,184,0.14);
        border-radius: 18px;
        padding: 0.85rem 0.9rem;
        margin: 0.6rem 0 0.9rem 0;
    }

    .sidebar-user-label {
        color: var(--muted);
        font-size: 0.76rem;
    }

    .sidebar-user-name {
        font-size: 0.96rem;
        font-weight: 800;
        color: var(--text);
        margin-top: 0.12rem;
    }

    .form-preview-value {
        font-size: 1.45rem;
        font-weight: 900;
        margin-top: 0.2rem;
        color: var(--text);
    }

    .tiny-muted {
        color: var(--muted);
        font-size: 0.82rem;
    }

    .stDataFrame {
        border: 1px solid var(--line);
        border-radius: 18px;
        overflow: hidden;
    }

    div[data-testid="stProgressBar"] > div > div {
        background: linear-gradient(90deg, #2563EB, #8B5CF6);
    }

    .chat-wrap {
        margin-top: 0.9rem;
    }

    .chat-bubble-ai {
        background: rgba(59,130,246,0.10);
        border: 1px solid rgba(96,165,250,0.18);
        border-radius: 16px;
        padding: 0.8rem 0.9rem;
        margin-bottom: 0.55rem;
        color: #E2E8F0;
        line-height: 1.5;
        font-size: 0.92rem;
    }

    .chat-bubble-user {
        background: rgba(139,92,246,0.10);
        border: 1px solid rgba(139,92,246,0.18);
        border-radius: 16px;
        padding: 0.8rem 0.9rem;
        margin-bottom: 0.55rem;
        color: #F8FAFC;
        line-height: 1.5;
        font-size: 0.92rem;
    }

    .chat-label {
        font-size: 0.78rem;
        color: var(--muted);
        margin: 0.55rem 0 0.45rem 0;
        font-weight: 700;
    }

    .chat-input-label {
        font-size: 0.8rem;
        color: var(--muted);
        margin-top: 0.8rem;
        margin-bottom: 0.35rem;
    }

    .quick-action-note {
        font-size: 0.78rem;
        color: var(--muted);
        margin-top: 0.55rem;
        margin-bottom: 0.45rem;
    }


    .pill-debt {
        display: inline-block;
        padding: 0.45rem 0.88rem;
        border-radius: 999px;
        background: rgba(59,130,246,0.14);
        border: 1px solid rgba(59,130,246,0.28);
        color: #93C5FD;
        font-weight: 800;
        margin-bottom: 0.8rem;
    }

    .pill-pay {
        display: inline-block;
        padding: 0.45rem 0.88rem;
        border-radius: 999px;
        background: rgba(245,158,11,0.14);
        border: 1px solid rgba(245,158,11,0.28);
        color: #FCD34D;
        font-weight: 800;
        margin-bottom: 0.8rem;
    }

    .mini-soft-card {
        background: linear-gradient(180deg, rgba(12,20,36,0.74), rgba(10,18,32,0.90));
        border: 1px solid rgba(148,163,184,0.12);
        border-radius: 18px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.8rem;
    }


    .zentix-brand-title {
        font-size: 2.25rem;
    }
    .sidebar-brand-title {
        font-size: 1.18rem;
    }
    .hero-card,
    .soft-card,
    .assistant-card,
    .mini-soft-card,
    .premium-list-card,
    .feature-signal,
    .tutorial-card,
    .spotlight-shell,
    .spotlight-side-card,
    .kpi-card {
        transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease, filter 0.22s ease;
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
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.26);
        border-color: rgba(125,211,252,0.18);
        filter: brightness(1.01);
    }
    .assistant-card {
        background:
            radial-gradient(circle at top left, rgba(59,130,246,0.16), transparent 32%),
            radial-gradient(circle at bottom right, rgba(139,92,246,0.10), transparent 28%),
            linear-gradient(135deg, rgba(15,23,42,0.98), rgba(10,18,32,0.98));
        border: 1px solid rgba(96,165,250,0.18);
        border-radius: 26px;
        padding: 1.08rem;
    }
    .assistant-title {
        font-size: 1.16rem;
        letter-spacing: -0.02em;
    }
    .assistant-text {
        font-size: 1rem;
    }
    .assistant-mini {
        font-size: 0.84rem;
    }
    .feature-signal {
        background:
            radial-gradient(circle at top left, rgba(59,130,246,0.12), transparent 28%),
            linear-gradient(135deg, rgba(10,18,32,0.96), rgba(11,23,41,0.98));
        border: 1px solid rgba(96,165,250,0.16);
        border-radius: 22px;
        padding: 1rem 1.05rem;
        margin-bottom: 1rem;
        box-shadow: 0 12px 28px rgba(0,0,0,0.22);
    }
    .feature-signal-title {
        font-size: 0.98rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 0.2rem;
    }
    .feature-signal-sub {
        font-size: 0.87rem;
        color: var(--muted);
        line-height: 1.58;
    }
    .feature-signal-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin-top: 0.85rem;
    }
    .feature-chip {
        display: inline-block;
        padding: 0.38rem 0.78rem;
        border-radius: 999px;
        background: rgba(15,23,42,0.78);
        border: 1px solid rgba(148,163,184,0.14);
        color: #E2E8F0;
        font-size: 0.79rem;
        font-weight: 700;
    }
    .tutorial-card {
        background:
            radial-gradient(circle at top left, rgba(125,211,252,0.14), transparent 26%),
            radial-gradient(circle at bottom right, rgba(139,92,246,0.12), transparent 24%),
            linear-gradient(135deg, rgba(14,24,42,0.98), rgba(9,17,30,0.98));
        border: 1px solid rgba(125,211,252,0.16);
        border-radius: 26px;
        padding: 1.1rem;
        box-shadow: 0 18px 34px rgba(0,0,0,0.24);
        margin-bottom: 1rem;
    }
    .tutorial-badge {
        display: inline-block;
        padding: 0.32rem 0.72rem;
        border-radius: 999px;
        background: rgba(59,130,246,0.14);
        border: 1px solid rgba(96,165,250,0.18);
        color: #BFDBFE;
        font-size: 0.77rem;
        font-weight: 800;
        margin-bottom: 0.7rem;
    }
    .tutorial-title {
        font-size: 1.14rem;
        font-weight: 900;
        color: #F8FAFC;
        margin-bottom: 0.25rem;
    }
    .tutorial-copy {
        color: #CBD5E1;
        font-size: 0.93rem;
        line-height: 1.62;
    }
    .tutorial-step-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin-top: 0.95rem;
    }
    .tutorial-step-chip {
        display: inline-block;
        padding: 0.34rem 0.72rem;
        border-radius: 999px;
        font-size: 0.76rem;
        font-weight: 800;
        border: 1px solid rgba(148,163,184,0.14);
        background: rgba(15,23,42,0.72);
        color: #CBD5E1;
    }
    .tutorial-step-chip.is-active {
        background: rgba(59,130,246,0.18);
        border-color: rgba(96,165,250,0.28);
        color: #DBEAFE;
    }
    .tutorial-step-chip.is-done {
        background: rgba(34,197,94,0.16);
        border-color: rgba(34,197,94,0.22);
        color: #BBF7D0;
    }
    .spotlight-shell {
        background:
            radial-gradient(circle at top left, rgba(59,130,246,0.14), transparent 32%),
            radial-gradient(circle at bottom right, rgba(139,92,246,0.10), transparent 26%),
            linear-gradient(135deg, rgba(14,24,42,0.98), rgba(8,15,28,0.98));
        border: 1px solid rgba(96,165,250,0.16);
        border-radius: 26px;
        padding: 1.1rem;
        box-shadow: 0 18px 34px rgba(0,0,0,0.24);
        margin-bottom: 1rem;
    }
    .spotlight-badge {
        display: inline-block;
        padding: 0.3rem 0.72rem;
        border-radius: 999px;
        background: rgba(59,130,246,0.12);
        border: 1px solid rgba(96,165,250,0.18);
        color: #BFDBFE;
        font-size: 0.76rem;
        font-weight: 800;
        margin-bottom: 0.72rem;
    }
    .spotlight-title {
        font-size: 1.2rem;
        font-weight: 900;
        color: #F8FAFC;
        margin-bottom: 0.25rem;
    }
    .spotlight-copy {
        color: #CBD5E1;
        font-size: 0.93rem;
        line-height: 1.6;
        margin-bottom: 0.95rem;
    }
    .spotlight-metric {
        background: rgba(15,23,42,0.72);
        border: 1px solid rgba(148,163,184,0.14);
        border-radius: 18px;
        padding: 0.82rem 0.9rem;
        min-height: 104px;
    }
    .spotlight-metric-label {
        color: #94A3B8;
        font-size: 0.78rem;
        margin-bottom: 0.38rem;
    }
    .spotlight-metric-value {
        color: #F8FAFC;
        font-size: 1.18rem;
        font-weight: 900;
        line-height: 1.1;
        margin-bottom: 0.22rem;
    }
    .spotlight-metric-foot {
        color: #CBD5E1;
        font-size: 0.8rem;
        line-height: 1.45;
    }
    .spotlight-side-card {
        background: linear-gradient(180deg, rgba(12,20,36,0.82), rgba(10,18,32,0.96));
        border: 1px solid rgba(148,163,184,0.14);
        border-radius: 22px;
        padding: 1rem 1.05rem;
        box-shadow: 0 14px 30px rgba(0,0,0,0.22);
        margin-bottom: 1rem;
    }
    .spotlight-side-title {
        font-size: 0.98rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 0.25rem;
    }
    .spotlight-side-sub {
        color: #94A3B8;
        font-size: 0.84rem;
        line-height: 1.55;
        margin-bottom: 0.65rem;
    }
    .spotlight-list {
        padding-left: 1rem;
        margin: 0;
        color: #E2E8F0;
        line-height: 1.55;
    }
    .premium-list-card {
        background:
            radial-gradient(circle at top left, rgba(59,130,246,0.10), transparent 30%),
            linear-gradient(180deg, rgba(12,20,36,0.84), rgba(10,18,32,0.96));
        border: 1px solid rgba(148,163,184,0.14);
        border-radius: 22px;
        padding: 1rem 1.05rem;
        box-shadow: 0 14px 30px rgba(0,0,0,0.22);
        margin-bottom: 1rem;
        min-height: 100%;
    }
    .premium-list-head {
        display: flex;
        justify-content: space-between;
        gap: 0.8rem;
        align-items: flex-start;
        margin-bottom: 0.6rem;
    }
    .premium-list-title {
        font-size: 1rem;
        font-weight: 800;
        color: #F8FAFC;
    }
    .premium-list-badge {
        padding: 0.3rem 0.62rem;
        border-radius: 999px;
        background: rgba(15,23,42,0.76);
        border: 1px solid rgba(148,163,184,0.14);
        color: #CBD5E1;
        font-size: 0.74rem;
        font-weight: 800;
        white-space: nowrap;
    }
    .premium-list-copy {
        color: #94A3B8;
        font-size: 0.84rem;
        line-height: 1.55;
        margin-bottom: 0.55rem;
    }

    .sticky-top-shell {
        position: sticky;
        top: 0.55rem;
        z-index: 40;
        background: linear-gradient(180deg, rgba(7,12,22,0.92), rgba(7,12,22,0.82));
        border: 1px solid rgba(96,165,250,0.14);
        border-radius: 24px;
        padding: 0.95rem 1rem 0.85rem 1rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(12px);
        box-shadow: 0 18px 34px rgba(0,0,0,0.22);
    }
    .sticky-top-shell .section-caption {
        margin-bottom: 0.65rem;
    }
    .fade-up {
        animation: zentixFadeUp 0.42s ease both;
    }
    @keyframes zentixFadeUp {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .movement-card {
        background:
            radial-gradient(circle at top left, rgba(59,130,246,0.12), transparent 28%),
            linear-gradient(180deg, rgba(12,20,36,0.90), rgba(10,18,32,0.98));
        border: 1px solid rgba(148,163,184,0.14);
        border-radius: 22px;
        padding: 0.95rem 1rem;
        min-height: 168px;
        box-shadow: 0 14px 28px rgba(0,0,0,0.22);
        margin-bottom: 0.8rem;
    }
    .movement-date {
        font-size: 0.76rem;
        color: #94A3B8;
        margin-bottom: 0.3rem;
        font-weight: 700;
    }
    .movement-title {
        font-size: 0.98rem;
        font-weight: 800;
        color: #F8FAFC;
        line-height: 1.35;
        margin-bottom: 0.35rem;
    }
    .movement-amount {
        font-size: 1.16rem;
        font-weight: 900;
        color: #F8FAFC;
        line-height: 1.1;
        margin-bottom: 0.45rem;
    }
    .movement-meta {
        font-size: 0.82rem;
        color: #CBD5E1;
        line-height: 1.55;
        margin-bottom: 0.7rem;
    }
    .movement-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin-top: 0.35rem;
        margin-bottom: 0.35rem;
    }
    .movement-chip {
        display: inline-block;
        padding: 0.28rem 0.66rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 800;
        border: 1px solid rgba(148,163,184,0.16);
        background: rgba(15,23,42,0.76);
        color: #E2E8F0;
    }
    .movement-chip-income {
        background: rgba(34,197,94,0.16);
        border-color: rgba(34,197,94,0.22);
        color: #BBF7D0;
    }
    .movement-chip-expense {
        background: rgba(239,68,68,0.16);
        border-color: rgba(239,68,68,0.22);
        color: #FECACA;
    }
    .movement-chip-debt {
        background: rgba(59,130,246,0.18);
        border-color: rgba(96,165,250,0.24);
        color: #DBEAFE;
    }
    .movement-chip-pay {
        background: rgba(245,158,11,0.18);
        border-color: rgba(245,158,11,0.24);
        color: #FDE68A;
    }
    .movement-chip-recurrent {
        background: rgba(139,92,246,0.18);
        border-color: rgba(139,92,246,0.24);
        color: #E9D5FF;
    }
    .movement-chip-alert {
        background: rgba(244,63,94,0.16);
        border-color: rgba(244,63,94,0.24);
        color: #FFE4E6;
    }
    .movement-chip-info {
        background: rgba(6,182,212,0.16);
        border-color: rgba(6,182,212,0.22);
        color: #CFFAFE;
    }
    .movement-side-shell {
        background:
            radial-gradient(circle at top left, rgba(59,130,246,0.14), transparent 28%),
            linear-gradient(180deg, rgba(12,20,36,0.88), rgba(10,18,32,0.98));
        border: 1px solid rgba(96,165,250,0.16);
        border-radius: 24px;
        padding: 1rem 1.05rem;
        box-shadow: 0 16px 32px rgba(0,0,0,0.24);
        margin-bottom: 1rem;
    }
    .movement-side-kpi {
        background: rgba(15,23,42,0.72);
        border: 1px solid rgba(148,163,184,0.14);
        border-radius: 16px;
        padding: 0.8rem 0.9rem;
        margin-bottom: 0.7rem;
    }
    .movement-side-label {
        color: #94A3B8;
        font-size: 0.75rem;
        margin-bottom: 0.25rem;
    }
    .movement-side-value {
        color: #F8FAFC;
        font-size: 1rem;
        font-weight: 800;
        line-height: 1.45;
    }
    .empty-card strong {
        color: #F8FAFC;
    }

    .launch-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin-top: 0.65rem;
    }
    .launch-chip-ok, .launch-chip-warn, .launch-chip-soft {
        display: inline-block;
        padding: 0.34rem 0.72rem;
        border-radius: 999px;
        font-size: 0.74rem;
        font-weight: 800;
        border: 1px solid rgba(148,163,184,0.14);
    }
    .launch-chip-ok {
        background: rgba(34,197,94,0.16);
        border-color: rgba(34,197,94,0.22);
        color: #BBF7D0;
    }
    .launch-chip-warn {
        background: rgba(245,158,11,0.16);
        border-color: rgba(245,158,11,0.22);
        color: #FDE68A;
    }
    .launch-chip-soft {
        background: rgba(59,130,246,0.14);
        border-color: rgba(96,165,250,0.18);
        color: #DBEAFE;
    }
    .launch-grid-card {
        background: linear-gradient(180deg, rgba(12,20,36,0.84), rgba(10,18,32,0.96));
        border: 1px solid rgba(148,163,184,0.14);
        border-radius: 22px;
        padding: 1rem 1.05rem;
        box-shadow: 0 14px 30px rgba(0,0,0,0.22);
        margin-bottom: 0.9rem;
        min-height: 100%;
    }
    .launch-grid-title {
        font-size: 0.98rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 0.2rem;
    }
    .launch-grid-copy {
        color: #94A3B8;
        font-size: 0.84rem;
        line-height: 1.55;
        margin-bottom: 0.55rem;
    }
    .legal-footer {
        margin-top: 1.25rem;
        padding: 0.95rem 1rem;
        border-radius: 18px;
        background: linear-gradient(180deg, rgba(12,20,36,0.78), rgba(10,18,32,0.94));
        border: 1px solid rgba(148,163,184,0.12);
        color: #CBD5E1;
        font-size: 0.84rem;
        line-height: 1.65;
    }
    .legal-footer a {
        color: #93C5FD;
        text-decoration: none;
        font-weight: 700;
    }
    .legal-footer a:hover {
        text-decoration: underline;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)


def forzar_sidebar_abierto():
    st.markdown("""
    <style>
    @media (min-width: 769px) {
        [data-testid="collapsedControl"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }

        button[kind="header"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }

        [data-testid="stSidebar"] {
            min-width: 320px !important;
            width: 320px !important;
            max-width: 320px !important;
        }

        section[data-testid="stSidebar"] {
            transform: translateX(0%) !important;
            margin-left: 0 !important;
        }

        section[data-testid="stSidebar"][aria-expanded="false"] {
            transform: translateX(0%) !important;
            min-width: 320px !important;
            width: 320px !important;
            max-width: 320px !important;
            margin-left: 0 !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    components.html(
        """
        <script>
        (function () {
            const SIDEBAR_WIDTH = "320px";

            function forceSidebarOpen() {
                const doc = window.parent.document;
                const sidebar = doc.querySelector('section[data-testid="stSidebar"]');
                if (!sidebar) return;

                const collapsedControl = doc.querySelector('[data-testid="collapsedControl"]');
                const headerButton = doc.querySelector('button[kind="header"]');
                const isMobile = window.parent.innerWidth < 769;

                const expanded = sidebar.getAttribute("aria-expanded");
                const isClosed = expanded === "false" || sidebar.offsetWidth < 180;

                if (isClosed && collapsedControl) {
                    try { collapsedControl.click(); } catch (e) {}
                }

                if (isClosed && headerButton) {
                    try { headerButton.click(); } catch (e) {}
                }

                if (!isMobile) {
                    sidebar.style.transform = "translateX(0)";
                    sidebar.style.minWidth = SIDEBAR_WIDTH;
                    sidebar.style.width = SIDEBAR_WIDTH;
                    sidebar.style.maxWidth = SIDEBAR_WIDTH;
                    sidebar.setAttribute("aria-expanded", "true");
                }
            }

            forceSidebarOpen();
            setTimeout(forceSidebarOpen, 250);
            setTimeout(forceSidebarOpen, 900);
            setTimeout(forceSidebarOpen, 1800);

            const observer = new MutationObserver(() => forceSidebarOpen());
            if (window.parent.document.body) {
                observer.observe(window.parent.document.body, {
                    childList: true,
                    subtree: true,
                    attributes: true
                });
            }
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def money(value):
    return f"${float(value):,.0f}"


def aplicar_estilo_plotly(fig, height=360):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E5E7EB",
        title_font_size=18,
        title_x=0.03,
        margin=dict(l=20, r=20, t=60, b=20),
        height=height,
        legend_title_text=""
    )
    return fig


def zentix_brand_header():
    col_logo, col_title = st.columns([1.15, 8])
    with col_logo:
        if icono_path.exists():
            st.image(str(icono_path), width=116)
    with col_title:
        st.markdown('<div class="zentix-brand-title">ZENTIX</div>', unsafe_allow_html=True)
        st.markdown('<div class="zentix-brand-sub">Finanzas inteligentes con estilo fintech premium</div>', unsafe_allow_html=True)


def zentix_hero(nombre, saldo_disponible, total_ingresos, total_gastos):
    balance_label = "Balance positivo" if saldo_disponible >= 0 else "Atención al balance"

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-badge">Zentix · tu espacio financiero personal</div>
            <div class="hero-title">Hola, {nombre}</div>
            <div class="hero-subtitle">
                Controla tus ingresos, ordena tus gastos y avanza hacia tus metas con una experiencia clara, rápida y elegante.
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
        return f"{fecha_txt} · {row.get('tipo', 'Sin tipo')} · {money(row.get('monto', 0))} · {descripcion_txt or 'Sin descripción'}{deuda_txt}"

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
            ["Ingreso", "Gasto", "Ingreso (Deuda)", "Pago de deuda"],
            index=["Ingreso", "Gasto", "Ingreso (Deuda)", "Pago de deuda"].index(tipo_actual if tipo_actual in ["Ingreso", "Gasto", "Ingreso (Deuda)", "Pago de deuda"] else "Gasto"),
            key=f"edit_tipo_{selected_id}"
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
            deuda_nombre_edit = st.text_input("Nombre de la deuda", value=deuda_nombre_actual or descripcion_actual, key=f"edit_deuda_nombre_{selected_id}")
            prestamista_edit = st.text_input("Prestamista", value=prestamista_actual, key=f"edit_prestamista_{selected_id}")
            usar_fecha_limite = st.checkbox("Tiene fecha límite", value=pd.notna(fecha_limite_actual), key=f"edit_deuda_lim_toggle_{selected_id}")
            if usar_fecha_limite:
                fecha_limite_edit = st.date_input("Fecha límite", value=fecha_limite_actual.date() if pd.notna(fecha_limite_actual) else fecha_edit + timedelta(days=30), key=f"edit_fecha_lim_{selected_id}")
            else:
                fecha_limite_edit = None
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
            deuda_nombre_edit = st.text_input("Nombre de la deuda", value=deuda_nombre_edit, key=f"edit_pago_deuda_nombre_{selected_id}")
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
                    errores.append("Escribe un nombre para la deuda.")
                if tipo_edit == "Ingreso (Deuda)" and not str(prestamista_edit or "").strip():
                    errores.append("Indica quién prestó.")
                if tipo_edit == "Pago de deuda" and not str(deuda_nombre_edit or "").strip():
                    errores.append("Define la deuda a la que corresponde este pago.")
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
                        "deuda_id": deuda_id_edit if tipo_edit in ("Ingreso (Deuda)", "Pago de deuda") else None,
                        "deuda_nombre": str(deuda_nombre_edit or "").strip() if tipo_edit in ("Ingreso (Deuda)", "Pago de deuda") else None,
                        "prestamista": str(prestamista_edit or "").strip() if tipo_edit in ("Ingreso (Deuda)", "Pago de deuda") else None,
                        "fecha_limite_deuda": datetime.combine(fecha_limite_edit, datetime.min.time()).isoformat() if fecha_limite_edit and tipo_edit in ("Ingreso (Deuda)", "Pago de deuda") else None,
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

    ingresos_reales = reciente.loc[reciente["tipo"] == "Ingreso", "monto"].sum()
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

    ingresos = float(df_periodo[df_periodo["tipo"] == "Ingreso"]["monto"].sum())
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
    left_cell.append(Paragraph("Finanzas inteligentes con estilo fintech premium", styles["ZentixHeroLight"]))

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
            semana_actual[semana_actual["tipo"] == "Ingreso"]["monto"].sum(),
            semana_anterior[semana_anterior["tipo"] == "Ingreso"]["monto"].sum()
        ),
        "gasto_mes_pct": cambio_pct(
            mes_actual[mes_actual["tipo"] == "Gasto"]["monto"].sum(),
            mes_anterior[mes_anterior["tipo"] == "Gasto"]["monto"].sum()
        ),
        "ingreso_mes_pct": cambio_pct(
            mes_actual[mes_actual["tipo"] == "Ingreso"]["monto"].sum(),
            mes_anterior[mes_anterior["tipo"] == "Ingreso"]["monto"].sum()
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
    ingreso_actual = float(semana_actual[semana_actual["tipo"] == "Ingreso"]["monto"].sum() or 0)

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
    bullets = "".join([f"<li style='margin-bottom:0.38rem;'>{item}</li>" for item in items])
    st.markdown(
        f"""
        <div class="premium-list-card">
            <div class="premium-list-head">
                <div class="premium-list-title">{title}</div>
                <div class="premium-list-badge">{len(items)} señal{'es' if len(items) != 1 else ''}</div>
            </div>
            <div class="premium-list-copy">{foot}</div>
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
        chips.append(movimiento_chip("Deuda recibida", "debt"))
    elif tipo == "Pago de deuda":
        chips.append(movimiento_chip("Pago deuda", "pay"))

    if bool(row.get("es_recurrente")):
        chips.append(movimiento_chip("Recurrente", "recurrent"))

    if str(row.get("deuda_nombre") or "").strip():
        chips.append(movimiento_chip("Con deuda", "info"))

    if tipo == "Gasto" and monto >= 500000:
        chips.append(movimiento_chip("Monto alto", "alert"))

    if tipo == "Pago de deuda" and monto > 0:
        chips.append(movimiento_chip("Reduce pendiente", "pay"))

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
        df_tmp[df_tmp["tipo"].isin(["Ingreso", "Gasto", "Ingreso (Deuda)", "Pago de deuda"])]
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
            "Ingreso (Deuda)": "Entra a caja, pero Zentix lo separa del ingreso real para que tu lectura siga siendo honesta.",
            "Pago de deuda": "Este pago reduce obligación pendiente y mejora tu salud financiera, aunque salga de caja."
        }
        st.markdown(f"<div class='tiny-muted' style='margin-bottom:0.6rem;'>{info.get(tipo, 'Registro contextual.')}</div>", unsafe_allow_html=True)
        x1, x2 = st.columns(2)
        with x1:
            render_spotlight_metric("Tipo", tipo, "Naturaleza activa")
        with x2:
            render_spotlight_metric("Monto", money(monto or 0), "Lectura inmediata")
        if tipo == "Pago de deuda" and saldo_deuda_actual > 0:
            data = pd.DataFrame({"concepto": ["Pago actual", "Saldo actual", "Saldo luego"], "monto": [float(monto or 0), float(saldo_deuda_actual), float(max(saldo_deuda_actual - float(monto or 0), 0))]})
        elif tipo == "Ingreso (Deuda)":
            data = pd.DataFrame({"concepto": ["Ingreso por deuda", "Pendiente total actual"], "monto": [float(monto or 0), float(globals().get('saldo_pendiente_deudas_global', 0) or 0)]})
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


def consultar_ia_zentix(pregunta, contexto):
    if not openai_client:
        return "La IA todavía no está activa. Agrega GEMINI_API_KEY en los secrets de Streamlit Cloud para habilitar al avatar."

    try:
        response = openai_client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
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
        )

        texto = response.choices[0].message.content

        if isinstance(texto, list):
            partes = []
            for item in texto:
                if isinstance(item, dict) and item.get("type") == "text":
                    partes.append(item.get("text", ""))
            texto = "".join(partes)

        texto = (texto or "").strip()

        if not texto:
            return "No pude generar una respuesta útil en este momento."

        return texto

    except Exception as e:
        return f"No pude responder ahora mismo. Error: {e}"



def render_avatar(pagina, nombre, total_ingresos, total_gastos, ahorro_actual, ultimo_tipo):
    perfil_actual = globals().get("perfil_financiero", {})
    plan_actual = globals().get("plan_usuario_actual", {})
    consultas_usadas = globals().get("consultas_usadas_hoy", 0)
    consultas_limite = globals().get("consultas_limite_hoy", 10)
    alertas_actuales = globals().get("alertas_proactivas", [])
    recomendacion_actual = globals().get("recomendacion_accionable", "Sigue registrando para obtener una recomendación más precisa.")
    entradas_deuda = float(globals().get("total_entradas_deuda_mes", 0.0) or 0.0)
    pagos_deuda = float(globals().get("total_pagos_deuda_mes", 0.0) or 0.0)
    saldo_pendiente_deudas = float(globals().get("saldo_pendiente_deudas_global", 0.0) or 0.0)

    tono_base = perfil_actual.get("titulo", "Perfil en construcción")

    if pagina == "Inicio":
        mensaje = f"{nombre}, ya entendí mejor tu panorama. Hoy te leo como: {tono_base.lower()}."
    elif pagina == "Registrar":
        mensaje = f"{nombre}, cada nuevo movimiento me ayuda a entender mejor tu comportamiento financiero, incluidas tus deudas y recurrencias."
    elif pagina == "Análisis":
        mensaje = f"{nombre}, aquí puedo explicarte patrones, comparar periodos y leer con claridad tus ingresos reales versus tus flujos por deuda."
    elif pagina == "Perfil":
        mensaje = f"{nombre}, desde aquí afinamos tu experiencia: plan, IA, recordatorios y preferencias sin recargar la interfaz."
    else:
        mensaje = f"{nombre}, tu meta no es solo un número. También puedo decirte qué ajuste te acercaría más rápido a ella."

    estado = {
        "Ingreso": "🟢 Último movimiento: ingreso",
        "Gasto": "🔴 Último movimiento: gasto",
        "Ingreso (Deuda)": "🔵 Último movimiento: ingreso por deuda",
        "Pago de deuda": "🟠 Último movimiento: pago de deuda"
    }.get(ultimo_tipo, "⚪ Aún no hay movimientos")

    contexto_ia = construir_contexto_zentix(
        pagina=pagina,
        nombre=nombre,
        total_ingresos=total_ingresos,
        total_gastos=total_gastos,
        ahorro_actual=ahorro_actual,
        ultimo_tipo=ultimo_tipo
    )

    chat_key = f"zentix_chat_{pagina}"
    input_key = f"zentix_input_{pagina}"
    clear_key = f"zentix_clear_{pagina}"

    mensajes_iniciales = {
        "Inicio": f"Hola, {nombre}. Soy Zentix. Ya distingo tus ingresos reales de tus movimientos por deuda y puedo resumirte tu panorama.",
        "Registrar": f"Hola, {nombre}. Registra ingresos, gastos, deudas y recurrencias sin contaminar tus KPIs reales.",
        "Análisis": f"Hola, {nombre}. Pregúntame por patrones, alertas, comparativas, deuda pendiente o categorías dominantes.",
        "Ahorro": f"Hola, {nombre}. Puedo ayudarte a leer tu progreso, cuánto te falta y cuál sería un ritmo semanal razonable.",
        "Perfil": f"Hola, {nombre}. Aquí también puedo ayudarte a decidir qué recordatorios activar y cómo aprovechar mejor tu plan."
    }

    if chat_key not in st.session_state:
        st.session_state[chat_key] = [
            {"role": "assistant", "content": mensajes_iniciales.get(pagina, "Hola. Soy tu avatar financiero de Zentix.")}
        ]

    if clear_key not in st.session_state:
        st.session_state[clear_key] = False

    if st.session_state.get(clear_key):
        st.session_state[input_key] = ""
        st.session_state[clear_key] = False

    st.markdown('<div class="assistant-card">', unsafe_allow_html=True)

    col1, col2 = st.columns([1.15, 4])

    with col1:
        if avatar_path.exists():
            st.image(str(avatar_path), width=124)

    with col2:
        st.markdown('<div class="assistant-title">Avatar Zentix IA</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="assistant-text">{mensaje}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="assistant-mini">{estado}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="assistant-mini">{texto_plan_avatar(plan_actual, consultas_usadas, consultas_limite)}</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="assistant-mini">Perfil: {perfil_actual.get("titulo", "Sin perfil")} · Disponible: {money(ahorro_actual)}</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="assistant-mini">Deuda recibida: {money(entradas_deuda)} · Pagos deuda: {money(pagos_deuda)} · Pendiente: {money(saldo_pendiente_deudas)}</div>',
            unsafe_allow_html=True
        )

    if alertas_actuales:
        st.markdown(
            f'<div class="assistant-mini">Alerta actual: {alertas_actuales[0]}</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="quick-action-note">Acciones rápidas</div>', unsafe_allow_html=True)

    preguntas_rapidas = {
        "Inicio": [
            "Resúmeme mi semana premium",
            "¿Cuál es mi perfil financiero?",
            "¿Qué alerta debería vigilar hoy?",
            "Dame una acción concreta para mejorar"
        ],
        "Registrar": [
            "¿Cómo registrar bien una deuda?",
            "¿Qué impacto tienen mis pagos de deuda?",
            "Dame una recomendación para registrar mejor",
            "¿Cómo usar recurrentes sin desorden?"
        ],
        "Análisis": [
            "Interpreta mis patrones de gasto",
            "Compárame esta semana con la pasada",
            "¿Cómo van mis deudas?",
            "Dame 3 insights personalizados"
        ],
        "Ahorro": [
            "Explícame mi progreso de ahorro",
            "¿Cuánto me falta realmente?",
            "¿Qué ajuste me acerca más rápido?",
            "Convierte mi meta en un plan corto"
        ],
        "Perfil": [
            "¿Cómo aprovechar mejor mi plan actual?",
            "Resume mis recordatorios activos",
            "¿Qué diferencia elegante hay entre Free y Pro?",
            "¿Qué debería configurar primero?"
        ]
    }

    pregunta_final = None
    qa = preguntas_rapidas.get(pagina, preguntas_rapidas["Inicio"])

    q1, q2 = st.columns(2)
    with q1:
        if st.button(qa[0], key=f"qa1_{pagina}", use_container_width=True):
            pregunta_final = qa[0]
        if st.button(qa[2], key=f"qa3_{pagina}", use_container_width=True):
            pregunta_final = qa[2]
    with q2:
        if st.button(qa[1], key=f"qa2_{pagina}", use_container_width=True):
            pregunta_final = qa[1]
        if st.button(qa[3], key=f"qa4_{pagina}", use_container_width=True):
            pregunta_final = qa[3]

    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="chat-label">Conversación</div>', unsafe_allow_html=True)

    historial = st.session_state[chat_key][-6:]
    for item in historial:
        contenido = html.escape(item["content"]).replace("\n", "<br>")
        if item["role"] == "assistant":
            st.markdown(f'<div class="chat-bubble-ai"><strong>Zentix:</strong><br>{contenido}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble-user"><strong>Tú:</strong><br>{contenido}</div>', unsafe_allow_html=True)

    st.markdown('<div class="chat-input-label">Pregúntale a Zentix</div>', unsafe_allow_html=True)
    pregunta_manual = st.text_input(
        "Pregúntale a Zentix",
        key=input_key,
        label_visibility="collapsed",
        placeholder="Ej: ¿Cómo voy este mes? ¿Qué patrón estás viendo? ¿Qué debería activar primero?"
    )

    c1, c2 = st.columns([3, 1])

    with c1:
        if st.button("Enviar pregunta", key=f"enviar_{pagina}", use_container_width=True):
            if pregunta_manual.strip():
                pregunta_final = pregunta_manual.strip()

    with c2:
        if st.button("Limpiar", key=f"limpiar_chat_{pagina}", use_container_width=True):
            st.session_state[chat_key] = [
                {"role": "assistant", "content": mensajes_iniciales.get(pagina, "Hola. Soy tu avatar financiero de Zentix.")}
            ]
            st.session_state[clear_key] = True
            st.rerun()

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
        st.rerun()

    if recomendacion_actual:
        st.markdown(
            f'<div class="assistant-mini" style="margin-top:0.65rem;">Siguiente mejor paso: {recomendacion_actual}</div>',
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


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


aplicar_estilo_zentix()
forzar_sidebar_abierto()


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
            total_ingresos_user = float(df_mes_user[df_mes_user["tipo"] == "Ingreso"]["monto"].sum()) if not df_mes_user.empty else 0.0
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

maybe_handle_public_automation_job()
launch_cfg = obtener_config_lanzamiento()

if st.session_state.user is None:
    with st.sidebar:
        col_sb_icon, col_sb_text = st.columns([1, 3])
        with col_sb_icon:
            if icono_path.exists():
                st.image(str(icono_path), width=58)
        with col_sb_text:
            st.markdown('<div class="sidebar-brand-title">ZENTIX</div>', unsafe_allow_html=True)
            st.markdown('<div class="sidebar-brand-sub">Acceso seguro</div>', unsafe_allow_html=True)

    col_hero, col_form = st.columns([1.2, 0.95])

    with col_hero:
        st.markdown(
            """
            <div class="hero-card">
                <div class="hero-badge">Finanzas personales · claridad total</div>
                <div class="hero-title">Toma el control de tu dinero</div>
                <div class="hero-subtitle">
                    Registra movimientos, analiza tus hábitos y construye un ahorro más sólido desde un solo lugar.
                </div>
                <div class="hero-pills">
                    <span class="hero-pill">Control diario</span>
                    <span class="hero-pill">Análisis visual</span>
                    <span class="hero-pill">Metas de ahorro</span>
                    <span class="hero-pill">Todo en un panel</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if avatar_path.exists():
            st.image(str(avatar_path), width=210)

        st.caption("Zentix te acompaña a entender mejor tu panorama financiero.")
        render_contexto_lanzamiento_acceso(launch_cfg)

    with col_form:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Accede a tu cuenta</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-caption">Ingresa o crea tu cuenta para continuar en tu panel personal.</div>', unsafe_allow_html=True)

        if mostrar_paneles_internos():
            if launch_cfg.get("app_stage") == "beta":
                st.info("Zentix está en beta controlada. Puedes abrir o cerrar el registro público desde secrets sin tocar el resto de la app.")
            elif launch_cfg.get("app_stage") == "public":
                st.success("La app ya está en modo público. Mantén soporte y textos legales visibles para un lanzamiento más serio.")
        else:
            st.caption("Ingresa para continuar en tu espacio financiero personal.")

        opciones_acceso = ["Login", "Registro"] if launch_cfg.get("allow_public_signup") else ["Login"]
        choice = st.selectbox("Acceso", opciones_acceso)
        email = st.text_input("Correo")
        password = st.text_input("Contraseña", type="password")

        if choice == "Registro":
            if st.button("Crear cuenta", use_container_width=True):
                if not launch_cfg.get("allow_public_signup"):
                    st.warning("El registro público está cerrado en este momento. Escríbenos para pedir acceso.")
                else:
                    try:
                        supabase.auth.sign_up({"email": email, "password": password})
                        registrar_evento_producto("signup_success", pagina="Acceso", detalle=email)
                        st.success("Cuenta creada correctamente. Ahora inicia sesión.")
                    except Exception as e:
                        registrar_evento_producto("signup_error", pagina="Acceso", detalle=str(e))
                        st.error(f"Error al registrar: {e}")

        if choice == "Login":
            if st.button("Ingresar", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = res.user
                    registrar_evento_producto("login_success", user_id=getattr(res.user, "id", None), pagina="Acceso", detalle=email)
                    st.success("Bienvenido a Zentix")
                    st.rerun()
                except Exception as e:
                    registrar_evento_producto("login_error", pagina="Acceso", detalle=str(e))
                    st.error(f"Error al iniciar sesión: {e}")

        st.markdown('</div>', unsafe_allow_html=True)
        render_footer_producto(launch_cfg)
    st.stop()



zentix_brand_header()

user_id = st.session_state.user.id
perfil = obtener_perfil(user_id)
nombre_usuario = perfil["nombre_mostrado"] if perfil and perfil.get("nombre_mostrado") else "usuario"

plan_usuario_actual = obtener_o_crear_plan_usuario(user_id)
_, consultas_usadas_hoy, consultas_limite_hoy, consultas_restantes_hoy, _ = puede_usar_ia(user_id)

paginas_disponibles = ["Inicio", "Registrar", "Análisis", "Ahorro", "Perfil"]

if "pagina" not in st.session_state or st.session_state.pagina not in paginas_disponibles:
    st.session_state.pagina = "Inicio"

with st.sidebar:
    col_sb_icon, col_sb_text = st.columns([1, 3])
    with col_sb_icon:
        if icono_path.exists():
            st.image(str(icono_path), width=58)
    with col_sb_text:
        st.markdown('<div class="sidebar-brand-title">ZENTIX</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-brand-sub">Panel personal</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="sidebar-user-card">
            <div class="sidebar-user-label">Sesión activa</div>
            <div class="sidebar-user-name">{nombre_usuario}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="sidebar-user-card">
            <div class="sidebar-user-label">Plan actual</div>
            <div class="sidebar-user-name">{plan_usuario_actual.get('plan', 'free').upper()}</div>
            <div class="tiny-muted" style="margin-top:0.35rem;">IA hoy: {consultas_usadas_hoy}/{consultas_limite_hoy}</div>
            <div class="tiny-muted">Restantes: {consultas_restantes_hoy}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Navegación")
    pagina_sidebar = st.radio(
        "Ir a",
        paginas_disponibles,
        index=paginas_disponibles.index(st.session_state.pagina),
        label_visibility="collapsed"
    )
    st.session_state.pagina = pagina_sidebar

    if st.button("Cerrar sesión", use_container_width=True):
        st.session_state.user = None
        st.rerun()

st.markdown(
    """
    <div class="sticky-top-shell fade-up">
        <div class="section-title" style="margin-top:0.05rem;">Navegación rápida</div>
        <div class="section-caption">
            Si el panel lateral se colapsa en Streamlit Cloud, usa estos accesos rápidos.
        </div>
    """,
    unsafe_allow_html=True
)

tipo_inicio = "primary" if st.session_state.pagina == "Inicio" else "secondary"
tipo_registrar = "primary" if st.session_state.pagina == "Registrar" else "secondary"
tipo_analisis = "primary" if st.session_state.pagina == "Análisis" else "secondary"
tipo_ahorro = "primary" if st.session_state.pagina == "Ahorro" else "secondary"
tipo_perfil = "primary" if st.session_state.pagina == "Perfil" else "secondary"

nav1, nav2, nav3, nav4, nav5 = st.columns(5)

with nav1:
    if st.button("Inicio", key="nav_inicio_top", use_container_width=True, type=tipo_inicio):
        st.session_state.pagina = "Inicio"
        st.rerun()

with nav2:
    if st.button("Registrar", key="nav_registrar_top", use_container_width=True, type=tipo_registrar):
        st.session_state.pagina = "Registrar"
        st.rerun()

with nav3:
    if st.button("Análisis", key="nav_analisis_top", use_container_width=True, type=tipo_analisis):
        st.session_state.pagina = "Análisis"
        st.rerun()

with nav4:
    if st.button("Ahorro", key="nav_ahorro_top", use_container_width=True, type=tipo_ahorro):
        st.session_state.pagina = "Ahorro"
        st.rerun()

with nav5:
    if st.button("Perfil", key="nav_perfil_top", use_container_width=True, type=tipo_perfil):
        st.session_state.pagina = "Perfil"
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

pagina = st.session_state.pagina
track_page_view_once(user_id, pagina)


if not perfil or not perfil.get("onboarding_completo", False):
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-badge">Onboarding inicial</div>
            <div class="hero-title">Configura tu experiencia Zentix</div>
            <div class="hero-subtitle">
                Define cómo quieres que te llame Zentix y selecciona tus categorías principales para personalizar tu registro financiero.
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
                    st.success("Tu configuración inicial quedó guardada.")
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
    total_ingresos = float(df_mes[df_mes["tipo"] == "Ingreso"]["monto"].sum())
    total_entradas_deuda_mes = float(df_mes[df_mes["tipo"] == "Ingreso (Deuda)"]["monto"].sum())
    total_pagos_deuda_mes = float(df_mes[df_mes["tipo"] == "Pago de deuda"]["monto"].sum())
else:
    total_gastos = 0.0
    total_ingresos = 0.0
    total_entradas_deuda_mes = 0.0
    total_pagos_deuda_mes = 0.0

df_deudas = obtener_deudas_usuario(user_id)
df_deudas = recalcular_deudas_usuario_desde_movimientos(user_id, df if not df.empty else pd.DataFrame(), df_deudas)
if not df_deudas.empty:
    saldo_pendiente_deudas_global = float(df_deudas["saldo_pendiente"].sum())
    deudas_activas_global = int((df_deudas["saldo_pendiente"] > 0).sum())
else:
    saldo_pendiente_deudas_global = 0.0
    deudas_activas_global = 0

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

if pagina == "Inicio":
    zentix_hero(nombre_usuario, saldo_disponible, total_ingresos, total_gastos)
    render_contexto_descubrimiento("Inicio")
    render_tutorial_zentix("Inicio", nombre_usuario, user_id, df, meta_guardada_global, preferencias_usuario_actual)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Ingresos reales", money(total_ingresos), "Sin préstamos ni deuda", "income")
    with col2:
        kpi_card("Gastos del mes", money(total_gastos), "Salidas operativas", "expense")
    with col3:
        kpi_card("Disponible", money(saldo_disponible), "Caja real incluyendo deuda", "balance")
    with col4:
        kpi_card("Meta de ahorro", money(meta_guardada_global), nombre_meta_guardado if nombre_meta_guardado else "Objetivo configurado", "saving")

    d1, d2, d3 = st.columns(3)
    with d1:
        kpi_card("Entradas por deuda", money(total_entradas_deuda_mes), "No cuentan como ingreso real", "balance")
    with d2:
        kpi_card("Pagos de deuda", money(total_pagos_deuda_mes), "Seguimiento de devolución", "expense")
    with d3:
        kpi_card("Saldo pendiente", money(saldo_pendiente_deudas_global), f"Deudas activas: {deudas_activas_global}", "saving")

    render_inicio_spotlight(
        df_base=df if not df.empty else pd.DataFrame(),
        df_mes_actual=df_mes if not df_mes.empty else pd.DataFrame(),
        df_deudas_local=df_deudas if not df_deudas.empty else pd.DataFrame(),
        total_ingresos_local=total_ingresos,
        total_gastos_local=total_gastos,
        entradas_deuda_local=total_entradas_deuda_mes,
        pagos_deuda_local=total_pagos_deuda_mes,
        saldo_pendiente_local=saldo_pendiente_deudas_global,
        meta_objetivo=meta_guardada_global,
        ahorro_disponible=ahorro_actual,
        comparativa=comparativa_periodos,
        resumen_semanal=resumen_semanal_premium,
        alertas=alertas_proactivas,
        sugerencias=sugerencias_categoria,
        proyeccion=proyeccion_meta_global,
        plan_actual=plan_usuario_actual,
        consultas_usadas=consultas_usadas_hoy,
        consultas_limite=consultas_limite_hoy
    )

    col_info, col_avatar = st.columns([1.15, 0.85])
    with col_info:
        section_header("Lectura inteligente del mes", "Zentix interpreta tu comportamiento, no solo tus cifras.")
        st.markdown(
            f"""
            <div class="soft-card">
                <div class="section-title">{perfil_financiero.get('titulo', 'Perfil en construcción')}</div>
                <div class="section-caption">{insight_personalizado}</div>
                <div class="tiny-muted">Microlectura: {perfil_financiero.get('microcopy', 'Sigue registrando para personalizar más.')}</div>
                <div class="tiny-muted" style="margin-top:0.55rem;">Deuda pendiente actual: {money(saldo_pendiente_deudas_global)} · Proyección meta: {proyeccion_meta_global.get("mensaje", "Sin proyección")}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_avatar:
        render_avatar(pagina, nombre_usuario, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)

    section_header("Resumen premium de tu comportamiento", "Lo bueno, lo que debes vigilar y tu mejor siguiente paso.")
    s1, s2, s3 = st.columns(3)
    with s1:
        render_list_card("Lo que hiciste bien", resumen_semanal_premium.get("positivas", []), "Zentix detecta avances para reforzar hábitos sanos.")
    with s2:
        render_list_card("Alertas proactivas", alertas_proactivas, "Alertas simples para actuar antes de que el mes se complique.")
    with s3:
        render_list_card("Patrones + acción", patrones_comportamiento + [f"Saldo pendiente de deudas: {money(saldo_pendiente_deudas_global)}"], recomendacion_accionable)

    section_header("Experiencia personalizada", "Comparativas inteligentes y sugerencias de organización.")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_list_card("Semana vs pasada", [f"Gasto: {money_delta(comparativa_periodos.get('gasto_semana_pct', 0.0))}", f"Ingreso: {money_delta(comparativa_periodos.get('ingreso_semana_pct', 0.0))}"], "Comparativa semanal.")
    with c2:
        render_list_card("Mes vs anterior", [f"Gasto: {money_delta(comparativa_periodos.get('gasto_mes_pct', 0.0))}", f"Ingreso: {money_delta(comparativa_periodos.get('ingreso_mes_pct', 0.0))}"], "Comparativa mensual.")
    with c3:
        render_list_card("Categorías inteligentes", sugerencias_categoria if sugerencias_categoria else ["Sigue registrando para refinar tus categorías."], "Ideas para que tus categorías te den más claridad.")
    with c4:
        render_list_card(
            "Plan, IA y recordatorios",
            [
                f"Plan actual: {plan_usuario_actual.get('plan', 'free').upper()}",
                f"IA hoy: {consultas_usadas_hoy}/{consultas_limite_hoy}",
                f"Recordatorios: {'email activo' if preferencias_usuario_actual.get('recordatorio_email') else 'email apagado'}"
            ],
            "El plan Pro tendrá más IA, alertas y profundidad."
        )

    if not df_mes.empty:
        section_header("Visualización mensual", "Distribuciones del mes actual para ver ingresos reales, deuda y pagos con claridad.")
        col_a, col_b = st.columns(2)

        with col_a:
            resumen_tipos = pd.DataFrame({
                "Tipo": ["Ingreso", "Gasto", "Ingreso (Deuda)", "Pago de deuda"],
                "Monto": [
                    float(total_ingresos),
                    float(total_gastos),
                    float(total_entradas_deuda_mes),
                    float(total_pagos_deuda_mes)
                ]
            })
            resumen_tipos = resumen_tipos[resumen_tipos["Monto"] > 0]
            if resumen_tipos.empty:
                resumen_tipos = pd.DataFrame({"Tipo": ["Sin datos"], "Monto": [1]})
            fig_tipos = px.pie(
                resumen_tipos,
                values="Monto",
                names="Tipo",
                title="Flujo mensual por naturaleza",
                hole=0.58,
                color="Tipo",
                color_discrete_map={
                    "Ingreso": "#22C55E",
                    "Gasto": "#EF4444",
                    "Ingreso (Deuda)": "#3B82F6",
                    "Pago de deuda": "#F59E0B",
                    "Sin datos": "#334155"
                }
            )
            fig_tipos.update_traces(textinfo="percent+label")
            aplicar_estilo_plotly(fig_tipos, height=380)
            st.plotly_chart(fig_tipos, use_container_width=True, config={"displayModeBar": False})

        with col_b:
            resumen_categoria = (
                df_mes.groupby("categoria", dropna=False)["monto"]
                .sum()
                .reset_index()
                .sort_values("monto", ascending=False)
            )
            resumen_categoria["categoria"] = resumen_categoria["categoria"].fillna("Sin categoría")
            fig_cat = px.pie(
                resumen_categoria,
                values="monto",
                names="categoria",
                title="Categorías del mes",
                color_discrete_sequence=CHART_COLORS
            )
            fig_cat.update_traces(textinfo="percent+label")
            aplicar_estilo_plotly(fig_cat, height=380)
            st.plotly_chart(fig_cat, use_container_width=True, config={"displayModeBar": False})
    else:
        empty_state(
            "Aún no hay movimientos este mes",
            "Empieza en Registrar para construir tu dashboard. Apenas ingreses datos, aquí aparecerán tus indicadores, perfil y análisis personalizados."
        )

if pagina == "Registrar":
    zentix_hero(nombre_usuario, saldo_disponible, total_ingresos, total_gastos)
    render_contexto_descubrimiento("Registrar")
    render_tutorial_zentix("Registrar", nombre_usuario, user_id, df, meta_guardada_global, preferencias_usuario_actual)
    section_header("Registrar movimiento", "Agrega ingresos, gastos, deuda y recurrencias con una experiencia dinámica, limpia y premium.")

    col_form, col_side = st.columns([1.15, 0.85])

    with col_form:
        tipo = st.radio(
            "Tipo de movimiento",
            ["Ingreso", "Gasto", "Ingreso (Deuda)", "Pago de deuda"],
            horizontal=True
        )

        if tipo == "Ingreso":
            st.markdown('<div class="pill-ingreso">Ingreso real seleccionado</div>', unsafe_allow_html=True)
        elif tipo == "Gasto":
            st.markdown('<div class="pill-gasto">Gasto seleccionado</div>', unsafe_allow_html=True)
        elif tipo == "Ingreso (Deuda)":
            st.markdown('<div class="pill-debt">Ingreso por deuda seleccionado</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="pill-pay">Pago de deuda seleccionado</div>', unsafe_allow_html=True)

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
            with st.expander("💳 Bloque específico de deuda", expanded=True):
                deuda_nombre = st.text_input(
                    "Nombre de la deuda",
                    placeholder="Ej: Préstamo de emergencia, Préstamo Juan",
                    key="registrar_deuda_nombre"
                )
                prestamista = st.text_input(
                    "Quién prestó",
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
                st.caption("Este movimiento entra a caja, pero no contaminará tus KPIs de ingresos reales.")

        else:
            categoria = "Pago de deuda"
            deudas_activas_df = df_deudas[df_deudas["saldo_pendiente"] > 0].copy() if not df_deudas.empty else pd.DataFrame()
            if deudas_activas_df.empty:
                st.info("Aún no tienes deudas activas registradas. Primero crea un 'Ingreso (Deuda)'.")
            else:
                deudas_activas_df["label"] = deudas_activas_df.apply(
                    lambda row: f"{row['nombre']} · {row['prestamista']} · pendiente {money(row['saldo_pendiente'])}",
                    axis=1
                )
                deuda_label = st.selectbox(
                    "Selecciona una deuda",
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
                    "Monto a pagar",
                    min_value=0.0,
                    max_value=float(saldo_deuda_actual) if saldo_deuda_actual > 0 else None,
                    step=1000.0,
                    key="registrar_pago_deuda_monto"
                )
                st.caption(f"Pendiente actual: {money(saldo_deuda_actual)}")

        col_btn_1, col_btn_2 = st.columns(2)
        with col_btn_1:
            if st.button("Guardar movimiento", use_container_width=True):
                errores = []

                if tipo in ("Ingreso", "Gasto") and (not categoria or categoria.strip() == "Sin categorías"):
                    errores.append("Necesitas al menos una categoría válida para guardar el movimiento.")
                if monto <= 0:
                    errores.append("El monto debe ser mayor que 0.")
                if tipo == "Ingreso (Deuda)" and not deuda_nombre.strip():
                    errores.append("Escribe un nombre para la deuda.")
                if tipo == "Ingreso (Deuda)" and not prestamista.strip():
                    errores.append("Indica quién prestó.")
                if tipo == "Pago de deuda" and not deuda_id:
                    errores.append("Selecciona una deuda activa para registrar el pago.")
                if tipo == "Pago de deuda" and saldo_deuda_actual > 0 and monto > saldo_deuda_actual:
                    errores.append("El pago no puede superar el saldo pendiente de la deuda.")
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

                        payload = {
                            "usuario_id": user_id,
                            "fecha": datetime.combine(fecha_mov, datetime.min.time()).isoformat(),
                            "tipo": tipo,
                            "categoria": categoria.strip() if categoria else None,
                            "monto": float(monto),
                            "descripcion": descripcion.strip(),
                            "emocion": emocion if tipo == "Gasto" else None,
                            "deuda_id": deuda_id_mov,
                            "deuda_nombre": deuda_nombre.strip() if deuda_nombre else None,
                            "prestamista": prestamista.strip() if prestamista else None,
                            "fecha_limite_deuda": datetime.combine(fecha_limite_deuda, datetime.min.time()).isoformat() if fecha_limite_deuda else None,
                            "es_recurrente": bool(es_recurrente),
                            "frecuencia_recurrencia": frecuencia_recurrencia if es_recurrente else None,
                            "proxima_fecha_recurrencia": datetime.combine(proxima_fecha_recurrencia, datetime.min.time()).isoformat() if es_recurrente and proxima_fecha_recurrencia else None,
                            "fecha_fin_recurrencia": datetime.combine(fecha_fin_recurrencia, datetime.min.time()).isoformat() if es_recurrente and fecha_fin_recurrencia else None,
                            "recurrente_activo": bool(recurrente_activo) if es_recurrente else False
                        }

                        insertar_movimiento_seguro(payload)

                        if tipo == "Pago de deuda" and deuda_id:
                            actualizar_deuda_pago_seguro(deuda_id, saldo_deuda_actual - float(monto))

                        registrar_evento_producto("movement_created", user_id=user_id, pagina="Registrar", detalle=f"{tipo} · {categoria}", valor=float(monto))
                        st.success("Movimiento guardado correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error guardando movimiento: {e}")

        with col_btn_2:
            if st.button("Resetear formulario", use_container_width=True):
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
                <div class="tiny-muted" style="margin-top:0.6rem;">Recurrentes activos</div>
                <div style="font-weight:800;font-size:1.1rem;">{int(df[df["recurrente_activo"] == True].shape[0]) if not df.empty and "recurrente_activo" in df.columns else 0}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        render_avatar(pagina, nombre_usuario, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)

    render_reporte_descargable(nombre_usuario, plan_usuario_actual, df if not df.empty else pd.DataFrame(), user_id=user_id)

    section_header("Comparativas y patrones", "Así viene cambiando tu comportamiento financiero.")
    a1, a2, a3 = st.columns(3)
    with a1:
        render_list_card("Comparativa semanal", [f"Gasto: {money_delta(comparativa_periodos.get('gasto_semana_pct', 0.0))}", f"Ingreso: {money_delta(comparativa_periodos.get('ingreso_semana_pct', 0.0))}"], "Semana actual vs anterior.")
    with a2:
        render_list_card("Comparativa mensual", [f"Gasto: {money_delta(comparativa_periodos.get('gasto_mes_pct', 0.0))}", f"Ingreso: {money_delta(comparativa_periodos.get('ingreso_mes_pct', 0.0))}"], "Mes actual vs anterior.")
    with a3:
        render_list_card("Patrones detectados", patrones_comportamiento + [f"Deudas activas: {deudas_activas_global}"], "Zentix busca hábitos que explican tu comportamiento.")

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
