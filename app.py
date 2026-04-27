import os
import re
import io
import html
from datetime import datetime, date, timedelta
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI
from supabase_config import supabase

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False


# ============================================================
# ZENTIX PERSONAL · APP SIMPLE DE FINANZAS PERSONALES
# Versión limpia para Streamlit + Supabase
# ============================================================

st.set_page_config(
    page_title="Zentix",
    page_icon="icono_zentix_v2.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_NAME = "Zentix"
APP_TAGLINE = "La forma más simple de saber cuánto entra, cuánto sale y cuánto queda."
PRESUPUESTO_TOTAL_KEY = "__PRESUPUESTO_TOTAL__"

DEFAULT_GASTOS = [
    "Comida", "Transporte", "Arriendo", "Servicios", "Salud",
    "Educación", "Compras", "Ocio", "Deudas", "Ahorro", "Otros"
]
DEFAULT_INGRESOS = ["Salario", "Freelance", "Ventas", "Regalos", "Otros"]
EMOCIONES = ["", "Tranquilidad", "Impulso", "Estrés", "Recompensa", "Urgencia", "Antojo"]

ICON_PATHS = [Path("icono_zentix_v2.png"), Path("icono_zentix.png")]
ICON_PATH = next((p for p in ICON_PATHS if p.exists()), None)


# ============================================================
# CONFIGURACIÓN IA
# ============================================================

def leer_config(clave, default=""):
    try:
        valor = st.secrets.get(clave)
    except Exception:
        valor = None
    if valor in (None, ""):
        valor = os.getenv(clave, default)
    return valor if valor is not None else default


def leer_float(clave, default):
    try:
        return float(str(leer_config(clave, default)).strip())
    except Exception:
        return float(default)


GEMINI_API_KEY = leer_config("GEMINI_API_KEY", "")
ZENTIX_IA_TIMEOUT = leer_float("ZENTIX_IA_TIMEOUT", 18)
GEMINI_MODEL_CANDIDATES = [
    str(leer_config("GEMINI_MODEL_PRIMARY", "gemini-2.5-flash")).strip(),
    str(leer_config("GEMINI_MODEL_FALLBACK_1", "gemini-2.0-flash")).strip(),
    str(leer_config("GEMINI_MODEL_FALLBACK_2", "gemini-1.5-flash")).strip(),
]
GEMINI_MODEL_CANDIDATES = [m for m in GEMINI_MODEL_CANDIDATES if m]

openai_client = None
if GEMINI_API_KEY:
    try:
        openai_client = OpenAI(
            api_key=GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            timeout=ZENTIX_IA_TIMEOUT,
            max_retries=0,
        )
    except Exception:
        openai_client = None


# ============================================================
# ESTILO
# ============================================================

def aplicar_estilo_zentix():
    st.markdown(
        """
        <style>
        :root {
            --bg: #F3F6FB;
            --surface: #FFFFFF;
            --surface-soft: #F8FBFF;
            --text: #0F172A;
            --muted: #475569;
            --line: rgba(15,23,42,.08);
            --brand: #4F46E5;
            --brand2: #2563EB;
            --brand3: #7C3AED;
            --green: #16A34A;
            --red: #DC2626;
            --amber: #D97706;
            --cyan: #0891B2;
            --shadow: 0 18px 40px rgba(15,23,42,.08);
            --radius: 24px;
        }

        html, body, [class*="css"] {
            color: var(--text) !important;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(79,70,229,.10), transparent 25%),
                radial-gradient(circle at top right, rgba(14,165,233,.10), transparent 22%),
                linear-gradient(180deg, #F4F7FC 0%, #EEF3FA 100%);
        }

        header[data-testid="stHeader"] {
            background: rgba(255,255,255,.82);
            backdrop-filter: blur(14px);
            border-bottom: 1px solid rgba(15,23,42,.04);
        }

        .block-container {
            max-width: 1320px;
            padding-top: 1rem;
            padding-bottom: 4rem;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #F8FAFF 0%, #EEF2FF 100%);
            border-right: 1px solid rgba(15,23,42,.06);
            box-shadow: 10px 0 28px rgba(15,23,42,.05);
        }

        /* Boton nativo para abrir/cerrar el panel lateral */
        [data-testid="collapsedControl"] {
            position: fixed !important;
            top: 0.85rem !important;
            left: 0.85rem !important;
            z-index: 999999 !important;
            background: linear-gradient(135deg, #0F172A 0%, #312E81 55%, #4F46E5 100%) !important;
            border-radius: 16px !important;
            padding: 0.18rem !important;
            box-shadow: 0 14px 26px rgba(15,23,42,.22) !important;
            border: 1px solid rgba(255,255,255,.18) !important;
        }

        [data-testid="collapsedControl"] button {
            min-width: 46px !important;
            min-height: 46px !important;
            color: #FFFFFF !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        [data-testid="collapsedControl"] svg,
        [data-testid="collapsedControl"] path {
            fill: #FFFFFF !important;
            color: #FFFFFF !important;
        }

        section[data-testid="stSidebar"] button[kind="header"],
        section[data-testid="stSidebar"] button[title="Close sidebar"] {
            color: #0F172A !important;
            background: #EEF2FF !important;
            border-radius: 14px !important;
        }

        section[data-testid="stSidebar"] button[kind="header"] svg,
        section[data-testid="stSidebar"] button[title="Close sidebar"] svg {
            fill: #0F172A !important;
            color: #0F172A !important;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #0F172A !important;
            letter-spacing: -.04em;
        }

        p, span, div, label, small {
            color: #0F172A !important;
        }

        .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div {
            color: #0F172A !important;
        }

        label,
        .stSelectbox label,
        .stTextInput label,
        .stNumberInput label,
        .stDateInput label,
        .stTextArea label,
        .stRadio label,
        .stCheckbox label,
        .stMultiSelect label {
            color: #0F172A !important;
            font-weight: 850 !important;
        }

        .stCaption,
        .stCaption p,
        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p {
            color: #475569 !important;
        }

        [data-testid="stForm"] h1,
        [data-testid="stForm"] h2,
        [data-testid="stForm"] h3,
        [data-testid="stForm"] p,
        [data-testid="stForm"] div,
        [data-testid="stForm"] label,
        [data-testid="stForm"] span {
            color: #0F172A !important;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: .5rem;
            background: #EAF0FA !important;
            padding: .45rem !important;
            border-radius: 18px !important;
            border: 1px solid rgba(148,163,184,.20) !important;
        }

        .stTabs [data-baseweb="tab"] {
            background: #FFFFFF !important;
            color: #0F172A !important;
            border-radius: 14px !important;
            padding: .65rem 1rem !important;
            font-weight: 900 !important;
            border: 1px solid rgba(148,163,184,.18) !important;
            box-shadow: 0 8px 16px rgba(15,23,42,.04) !important;
        }

        .stTabs [data-baseweb="tab"] p,
        .stTabs [data-baseweb="tab"] span {
            color: #0F172A !important;
            font-weight: 900 !important;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #4F46E5, #7C3AED) !important;
            color: #FFFFFF !important;
            border-color: transparent !important;
        }

        .stTabs [aria-selected="true"] p,
        .stTabs [aria-selected="true"] span {
            color: #FFFFFF !important;
        }

        a {
            color: var(--brand) !important;
        }

        .hero-card {
            background:
                radial-gradient(circle at top left, rgba(255,255,255,.22), transparent 30%),
                linear-gradient(135deg, #0F172A 0%, #1E3A8A 40%, #4F46E5 75%, #7C3AED 100%);
            color: #FFFFFF !important;
            border-radius: 30px;
            padding: 1.35rem 1.45rem;
            box-shadow: 0 28px 50px rgba(15,23,42,.24);
            margin-bottom: 1rem;
        }

        .hero-card * {
            color: #FFFFFF !important;
        }

        .hero-badge {
            display: inline-block;
            padding: .38rem .76rem;
            border-radius: 999px;
            background: rgba(255,255,255,.18);
            border: 1px solid rgba(255,255,255,.20);
            color: #F8FAFC !important;
            font-size: .78rem;
            font-weight: 850;
            margin-bottom: .85rem;
        }

        .hero-title {
            color: #FFFFFF !important;
            font-size: 2.15rem;
            font-weight: 950;
            margin: 0 0 .3rem 0;
        }

        .hero-sub {
            color: rgba(255,255,255,.92) !important;
            font-size: 1rem;
            line-height: 1.55;
            max-width: 760px;
        }

        .hero-pills {
            display: flex;
            flex-wrap: wrap;
            gap: .55rem;
            margin-top: 1rem;
        }

        .hero-pill {
            display: inline-block;
            padding: .42rem .82rem;
            border-radius: 999px;
            background: rgba(255,255,255,.16);
            border: 1px solid rgba(255,255,255,.20);
            color: #FFFFFF !important;
            font-weight: 850;
            font-size: .85rem;
        }

        .soft-card, .kpi-card, .simple-card, .movement-card {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FBFF 100%);
            border: 1px solid rgba(15,23,42,.07);
            border-radius: var(--radius);
            box-shadow: 0 14px 28px rgba(15,23,42,.055);
            padding: 1rem 1.05rem;
            margin-bottom: .9rem;
        }

        .soft-card *, .kpi-card *, .simple-card *, .movement-card * {
            color: #0F172A !important;
        }

        .section-title {
            font-size: 1.2rem;
            font-weight: 950;
            letter-spacing: -.03em;
            margin-bottom: .15rem;
            color: #0F172A !important;
        }

        .section-caption, .muted {
            color: #475569 !important;
            font-size: .94rem;
            line-height: 1.55;
        }

        .kpi-card {
            min-height: 128px;
        }

        .kpi-label {
            color: #334155 !important;
            font-size: .84rem;
            font-weight: 850;
            margin-bottom: .55rem;
        }

        .kpi-value {
            color: #0F172A !important;
            font-size: 1.7rem;
            line-height: 1.05;
            font-weight: 950;
            letter-spacing: -.04em;
        }

        .kpi-foot {
            color: #475569 !important;
            font-size: .83rem;
            margin-top: .3rem;
        }

        .kpi-income {
            background: linear-gradient(180deg, #ECFDF5, #F0FDF4);
            border-color: rgba(34,197,94,.20);
        }

        .kpi-expense {
            background: linear-gradient(180deg, #FEF2F2, #FFF1F2);
            border-color: rgba(239,68,68,.20);
        }

        .kpi-balance {
            background: linear-gradient(180deg, #EFF6FF, #EEF2FF);
            border-color: rgba(37,99,235,.20);
        }

        .kpi-saving {
            background: linear-gradient(180deg, #F5F3FF, #FAF5FF);
            border-color: rgba(124,58,237,.20);
        }

        .pill {
            display:inline-flex;
            align-items:center;
            gap:.35rem;
            padding:.48rem .82rem;
            border-radius:999px;
            font-size:.84rem;
            font-weight:850;
            border:1px solid rgba(148,163,184,.22);
            background:#FFFFFF;
            color:#0F172A !important;
        }

        .pill-income {
            background:#DCFCE7;
            border-color:#86EFAC;
            color:#166534 !important;
        }

        .pill-expense {
            background:#FEE2E2;
            border-color:#FCA5A5;
            color:#991B1B !important;
        }

        .pill-info {
            background:#EEF2FF;
            border-color:#C7D2FE;
            color:#3730A3 !important;
        }

        .movement-row {
            display:flex;
            justify-content:space-between;
            gap:.9rem;
            align-items:flex-start;
            padding:.78rem 0;
            border-bottom:1px solid rgba(15,23,42,.06);
        }

        .movement-row:last-child {
            border-bottom:none;
        }

        .movement-title {
            font-weight:900;
            color:#0F172A !important;
        }

        .movement-sub {
            color:#64748B !important;
            font-size:.84rem;
            margin-top:.15rem;
        }

        .amount-income {
            color:#16A34A !important;
            font-weight:950;
            white-space:nowrap;
        }

        .amount-expense {
            color:#DC2626 !important;
            font-weight:950;
            white-space:nowrap;
        }

        .stButton > button {
            border-radius: 18px;
            min-height: 50px;
            font-weight: 900;
            font-size: 1rem;
            border: 1px solid rgba(15,23,42,.08);
            box-shadow: 0 10px 20px rgba(15,23,42,.05);
            transition: all .2s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 14px 24px rgba(15,23,42,.08);
        }

        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #0F172A 0%, #1D4ED8 45%, #4F46E5 100%);
            color: #FFFFFF !important;
            border: none;
        }

        .stButton > button[kind="primary"] p,
        .stButton > button[kind="primary"] span,
        .stButton > button[kind="primary"] div {
            color: #FFFFFF !important;
        }

        .stTextInput input,
        .stNumberInput input,
        .stDateInput input,
        textarea,
        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div {
            border-radius: 16px !important;
            min-height: 48px !important;
            background: #FFFFFF !important;
            color: #0F172A !important;
            border: 1px solid #CBD5E1 !important;
        }

        .stSelectbox div[data-baseweb="select"] span,
        .stMultiSelect div[data-baseweb="select"] span {
            color: #0F172A !important;
        }

        textarea::placeholder,
        input::placeholder {
            color: #64748B !important;
            opacity: 1 !important;
        }

        .stRadio label p,
        .stRadio div[role="radiogroup"] label,
        .stRadio div[role="radiogroup"] span {
            color: #0F172A !important;
            font-weight: 850 !important;
        }

        div[data-testid="stProgressBar"] > div > div {
            background: linear-gradient(90deg, #4F46E5, #06B6D4);
        }

        .chat-bubble {
            border-radius:18px;
            padding:.85rem .95rem;
            margin-bottom:.65rem;
            line-height:1.55;
            color:#0F172A !important;
        }

        .chat-ai {
            background:#FFFFFF;
            border:1px solid rgba(148,163,184,.22);
        }

        .chat-user {
            background:#EEF2FF;
            border:1px solid #C7D2FE;
        }

        .footer-note {
            color:#475569 !important;
            font-size:.84rem;
            margin-top:1rem;
            text-align:center;
        }

        section[data-testid="stSidebar"] .stButton > button {
            background: linear-gradient(135deg, #0F172A 0%, #312E81 55%, #4F46E5 100%);
            color: #FFFFFF !important;
            border: none !important;
            font-weight: 900;
        }

        section[data-testid="stSidebar"] .stButton > button p,
        section[data-testid="stSidebar"] .stButton > button span {
            color: #FFFFFF !important;
        }

        section[data-testid="stSidebar"] .stButton > button:hover {
            filter: brightness(1.05);
        }

        .home-action-card * {
            color:#0F172A !important;
        }

        .home-color-title,
        .home-color-title span,
        .home-caption,
        .home-alert-box,
        .home-alert-box strong,
        .home-insight-label,
        .home-insight-value,
        .home-movement-name,
        .home-movement-meta {
            color:#0F172A !important;
        }

        .home-caption,
        .home-insight-label,
        .home-movement-meta {
            color:#475569 !important;
        }

        .home-register-shell * {
            color:#FFFFFF !important;
        }

        .home-register-shell input,
        .home-register-shell textarea,
        .home-register-shell div[data-baseweb="select"] > div,
        .home-register-shell div[data-baseweb="select"] span {
            color:#0F172A !important;
            background:#FFFFFF !important;
        }

        .home-register-shell .stRadio label p,
        .home-register-shell .stRadio div[role="radiogroup"] span,
        .home-register-shell label {
            color:#F8FAFC !important;
        }

        .stForm .section-title,
        .stForm .section-caption,
        .stForm .home-color-title,
        .stForm .home-caption {
            color:#0F172A !important;
        }

        #MainMenu { visibility:hidden; }
        footer { visibility:hidden; }

        @media (max-width: 900px) {
            .hero-title { font-size:1.72rem; }
            .block-container { padding-left:.8rem; padding-right:.8rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def money(value):
    try:
        return f"${float(value):,.0f}".replace(",", ".")
    except Exception:
        return "$0"


def fmt_pct(value):
    try:
        return f"{float(value) * 100:.0f}%"
    except Exception:
        return "0%"


def safe_text(value):
    return html.escape(str(value or ""))


def clear_cached_data():
    for name in [
        "obtener_perfil", "obtener_categorias_usuario", "obtener_movimientos",
        "obtener_meta", "obtener_limites_categoria_usuario", "obtener_plan_usuario",
        "obtener_uso_ia_hoy",
    ]:
        try:
            globals()[name].clear()
        except Exception:
            pass


def section_header(title, subtitle=""):
    st.markdown(f"<div class='section-title'>{safe_text(title)}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='section-caption'>{safe_text(subtitle)}</div>", unsafe_allow_html=True)


def kpi_card(label, value, foot="", variant="balance"):
    class_map = {
        "income": "kpi-card kpi-income",
        "expense": "kpi-card kpi-expense",
        "balance": "kpi-card kpi-balance",
        "saving": "kpi-card kpi-saving",
    }
    st.markdown(
        f"""
        <div class="{class_map.get(variant, 'kpi-card')}">
            <div class="kpi-label">{safe_text(label)}</div>
            <div class="kpi-value">{safe_text(value)}</div>
            <div class="kpi-foot">{safe_text(foot)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(nombre, total_ingresos, total_gastos, saldo, meta=0):
    estado = "Vas con saldo positivo" if saldo >= 0 else "Tu saldo está en negativo"
    meta_txt = f"Meta: {money(meta)}" if meta else "Meta pendiente"
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-badge">Zentix personal · simple y rápido</div>
            <div class="hero-title">Hola, {safe_text(nombre)} 👋</div>
            <div class="hero-sub">{APP_TAGLINE}</div>
            <div class="hero-pills">
                <span class="hero-pill">Entra: {money(total_ingresos)}</span>
                <span class="hero-pill">Sale: {money(total_gastos)}</span>
                <span class="hero-pill">Queda: {money(saldo)}</span>
                <span class="hero-pill">{safe_text(estado)}</span>
                <span class="hero-pill">{safe_text(meta_txt)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def df_vacio_movimientos():
    return pd.DataFrame(columns=["id", "usuario_id", "fecha", "tipo", "categoria", "monto", "descripcion", "emocion", "creado_en"])


def normalizar_fecha_col(df):
    if df is None or df.empty or "fecha" not in df.columns:
        return df_vacio_movimientos()
    df = df.copy()

    # Supabase puede devolver fechas con zona horaria. Pandas no permite comparar
    # datetime64[ns, UTC] con Timestamp sin zona horaria, por eso normalizamos todo
    # a fechas naive locales antes de filtrar por semana o mes.
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce", utc=True)
    try:
        df["fecha"] = df["fecha"].dt.tz_convert(None)
    except Exception:
        try:
            df["fecha"] = df["fecha"].dt.tz_localize(None)
        except Exception:
            pass

    df["monto"] = pd.to_numeric(df.get("monto", 0), errors="coerce").fillna(0)
    for col in ["tipo", "categoria", "descripcion", "emocion"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)
    return df


def filtrar_personal(df):
    df = normalizar_fecha_col(df)
    if df.empty:
        return df
    return df[df["tipo"].isin(["Ingreso", "Gasto"])].copy()


def filtrar_mes(df, ref=None):
    ref = pd.Timestamp(ref or date.today())
    df = filtrar_personal(df)
    if df.empty:
        return df
    return df[(df["fecha"].dt.year == ref.year) & (df["fecha"].dt.month == ref.month)].copy()


def filtrar_semana_actual(df):
    df = filtrar_personal(df)
    if df.empty:
        return df
    hoy = pd.Timestamp.now(tz=None).normalize()
    inicio = hoy - pd.Timedelta(days=hoy.weekday())
    fin = inicio + pd.Timedelta(days=7)
    return df[(df["fecha"] >= inicio) & (df["fecha"] < fin)].copy()


def filtrar_semana_anterior(df):
    df = filtrar_personal(df)
    if df.empty:
        return df
    hoy = pd.Timestamp.now(tz=None).normalize()
    inicio_actual = hoy - pd.Timedelta(days=hoy.weekday())
    inicio_ant = inicio_actual - pd.Timedelta(days=7)
    return df[(df["fecha"] >= inicio_ant) & (df["fecha"] < inicio_actual)].copy()


def resumen_movimientos(df):
    df = filtrar_personal(df)
    ingresos = float(df[df["tipo"] == "Ingreso"]["monto"].sum()) if not df.empty else 0.0
    gastos = float(df[df["tipo"] == "Gasto"]["monto"].sum()) if not df.empty else 0.0
    saldo = ingresos - gastos
    return ingresos, gastos, saldo


def top_categoria_gasto(df):
    df = filtrar_personal(df)
    gastos = df[df["tipo"] == "Gasto"].copy() if not df.empty else pd.DataFrame()
    if gastos.empty:
        return "", 0.0, 0.0
    resumen = gastos.groupby("categoria", dropna=False)["monto"].sum().sort_values(ascending=False)
    if resumen.empty:
        return "", 0.0, 0.0
    categoria = str(resumen.index[0] or "Otros")
    monto = float(resumen.iloc[0])
    total = float(resumen.sum())
    share = monto / total if total else 0.0
    return categoria, monto, share


# ============================================================
# SUPABASE · PERFIL, CATEGORÍAS, PLANES
# ============================================================

@st.cache_data(ttl=90, show_spinner=False)
def obtener_perfil(user_id):
    try:
        result = supabase.table("perfiles_usuario").select("*").eq("id", user_id).limit(1).execute()
        return result.data[0] if result.data else None
    except Exception:
        return None


@st.cache_data(ttl=90, show_spinner=False)
def obtener_categorias_usuario(user_id, tipo):
    try:
        result = (
            supabase.table("categorias_usuario")
            .select("*")
            .eq("usuario_id", user_id)
            .eq("tipo", tipo)
            .order("nombre")
            .execute()
        )
        data = result.data if result.data else []
        categorias = [str(x.get("nombre", "")).strip() for x in data if str(x.get("nombre", "")).strip()]
        if categorias:
            return categorias
    except Exception:
        pass
    return DEFAULT_INGRESOS if tipo == "Ingreso" else DEFAULT_GASTOS


def guardar_onboarding(user_id, nombre_mostrado, categorias_gasto, categorias_ingreso):
    nombre_mostrado = str(nombre_mostrado or "Usuario Zentix").strip() or "Usuario Zentix"
    try:
        perfil = obtener_perfil(user_id)
        payload = {"nombre_mostrado": nombre_mostrado, "onboarding_completo": True}
        if perfil:
            supabase.table("perfiles_usuario").update(payload).eq("id", user_id).execute()
        else:
            payload_insert = {"id": user_id, **payload}
            supabase.table("perfiles_usuario").insert(payload_insert).execute()
    except Exception:
        pass

    try:
        supabase.table("categorias_usuario").delete().eq("usuario_id", user_id).execute()
        registros = []
        for cat in categorias_gasto:
            registros.append({"usuario_id": user_id, "tipo": "Gasto", "nombre": str(cat).strip()})
        for cat in categorias_ingreso:
            registros.append({"usuario_id": user_id, "tipo": "Ingreso", "nombre": str(cat).strip()})
        registros = [r for r in registros if r["nombre"]]
        if registros:
            supabase.table("categorias_usuario").insert(registros).execute()
    except Exception:
        pass
    clear_cached_data()


def agregar_categoria(user_id, tipo, nombre):
    nombre = str(nombre or "").strip()
    if not nombre:
        return False, "Escribe una categoría."
    try:
        supabase.table("categorias_usuario").insert({"usuario_id": user_id, "tipo": tipo, "nombre": nombre}).execute()
        clear_cached_data()
        return True, "Categoría agregada."
    except Exception as e:
        return False, f"No pude agregar la categoría: {e}"


@st.cache_data(ttl=90, show_spinner=False)
def obtener_plan_usuario(user_id):
    default = {"plan": "free", "estado": "active", "consultas_ia_dia": 10, "categorias_extra": 10}
    try:
        result = supabase.table("planes_usuario").select("*").eq("usuario_id", user_id).limit(1).execute()
        if result.data:
            row = result.data[0]
            return {
                "plan": row.get("plan", "free"),
                "estado": row.get("estado", "active"),
                "consultas_ia_dia": int(row.get("consultas_ia_dia", 10) or 10),
                "categorias_extra": int(row.get("categorias_extra", 10) or 10),
            }
        supabase.table("planes_usuario").insert({
            "usuario_id": user_id,
            "plan": "free",
            "estado": "active",
            "consultas_ia_dia": 10,
            "categorias_extra": 10,
            "actualizado_en": datetime.now().isoformat(),
        }).execute()
    except Exception:
        pass
    return default


# ============================================================
# SUPABASE · MOVIMIENTOS
# ============================================================

@st.cache_data(ttl=25, show_spinner=False)
def obtener_movimientos(user_id):
    try:
        result = (
            supabase.table("movimientos")
            .select("*")
            .eq("usuario_id", user_id)
            .order("fecha", desc=True)
            .execute()
        )
        data = result.data if result.data else []
        df = pd.DataFrame(data)
    except Exception:
        df = df_vacio_movimientos()

    for col in ["id", "usuario_id", "fecha", "tipo", "categoria", "monto", "descripcion", "emocion", "creado_en"]:
        if col not in df.columns:
            df[col] = None
    df = normalizar_fecha_col(df)
    return filtrar_personal(df)


def insertar_movimiento(user_id, tipo, categoria, monto, descripcion="", fecha_mov=None, emocion=""):
    fecha_mov = fecha_mov or date.today()
    payload = {
        "usuario_id": user_id,
        "fecha": fecha_mov.isoformat() if hasattr(fecha_mov, "isoformat") else str(fecha_mov),
        "tipo": str(tipo),
        "categoria": str(categoria or "Otros").strip() or "Otros",
        "monto": float(monto or 0),
        "descripcion": str(descripcion or "").strip(),
        "emocion": str(emocion or "").strip(),
        "creado_en": datetime.now().isoformat(),
    }
    candidatos = [
        dict(payload),
        {k: v for k, v in payload.items() if k not in {"creado_en"}},
        {k: v for k, v in payload.items() if k not in {"creado_en", "emocion"}},
    ]
    last_error = None
    for candidate in candidatos:
        try:
            result = supabase.table("movimientos").insert(candidate).execute()
            clear_cached_data()
            return True, result
        except Exception as e:
            last_error = e
    return False, last_error


def actualizar_movimiento(movimiento_id, payload):
    candidatos = [
        dict(payload),
        {k: v for k, v in payload.items() if k not in {"emocion", "actualizado_en"}},
    ]
    last_error = None
    for candidate in candidatos:
        try:
            result = supabase.table("movimientos").update(candidate).eq("id", movimiento_id).execute()
            clear_cached_data()
            return True, result
        except Exception as e:
            last_error = e
    return False, last_error


def eliminar_movimiento(movimiento_id):
    try:
        result = supabase.table("movimientos").delete().eq("id", movimiento_id).execute()
        clear_cached_data()
        return True, result
    except Exception as e:
        return False, e


# ============================================================
# SUPABASE · METAS Y PRESUPUESTOS
# ============================================================

@st.cache_data(ttl=60, show_spinner=False)
def obtener_meta(user_id):
    try:
        result = supabase.table("ahorro_meta").select("*").eq("usuario_id", user_id).limit(1).execute()
        return result.data[0] if result.data else None
    except Exception:
        return None


def guardar_meta(user_id, meta_valor, nombre_meta):
    payload = {
        "meta": float(meta_valor or 0),
        "nombre_meta": str(nombre_meta or "").strip() or None,
        "actualizado_en": datetime.now().isoformat(),
    }
    try:
        actual = obtener_meta(user_id)
        if actual:
            result = supabase.table("ahorro_meta").update(payload).eq("usuario_id", user_id).execute()
        else:
            result = supabase.table("ahorro_meta").insert({"usuario_id": user_id, **payload}).execute()
        clear_cached_data()
        return True, result
    except Exception:
        try:
            payload_simple = {"meta": float(meta_valor or 0), "actualizado_en": datetime.now().isoformat()}
            actual = obtener_meta(user_id)
            if actual:
                result = supabase.table("ahorro_meta").update(payload_simple).eq("usuario_id", user_id).execute()
            else:
                result = supabase.table("ahorro_meta").insert({"usuario_id": user_id, **payload_simple}).execute()
            clear_cached_data()
            return True, result
        except Exception as e:
            return False, e


@st.cache_data(ttl=60, show_spinner=False)
def obtener_limites_categoria_usuario(user_id):
    columnas = ["id", "usuario_id", "categoria", "limite_mensual", "activo", "creado_en", "actualizado_en"]
    try:
        result = supabase.table("limites_categoria").select("*").eq("usuario_id", user_id).order("categoria").execute()
        data = result.data if result.data else []
    except Exception:
        data = []
    df = pd.DataFrame(data)
    for col in columnas:
        if col not in df.columns:
            df[col] = None
    if not df.empty:
        df["limite_mensual"] = pd.to_numeric(df["limite_mensual"], errors="coerce").fillna(0)
        df["activo"] = df["activo"].fillna(True).astype(bool)
    return df


def guardar_limite_categoria(user_id, categoria, limite_mensual, activo=True):
    categoria = str(categoria or "").strip()
    if not categoria:
        return False, "Categoría vacía."
    payload = {
        "usuario_id": user_id,
        "categoria": categoria,
        "limite_mensual": float(limite_mensual or 0),
        "activo": bool(activo),
        "actualizado_en": datetime.now().isoformat(),
    }
    try:
        result = supabase.table("limites_categoria").upsert(payload, on_conflict="usuario_id,categoria").execute()
        clear_cached_data()
        return True, result
    except Exception:
        try:
            existe = (
                supabase.table("limites_categoria")
                .select("id")
                .eq("usuario_id", user_id)
                .eq("categoria", categoria)
                .limit(1)
                .execute()
            )
            if existe.data:
                result = (
                    supabase.table("limites_categoria")
                    .update(payload)
                    .eq("usuario_id", user_id)
                    .eq("categoria", categoria)
                    .execute()
                )
            else:
                result = supabase.table("limites_categoria").insert({**payload, "creado_en": datetime.now().isoformat()}).execute()
            clear_cached_data()
            return True, result
        except Exception as e:
            return False, e


def eliminar_limite_categoria(user_id, categoria):
    try:
        result = supabase.table("limites_categoria").delete().eq("usuario_id", user_id).eq("categoria", categoria).execute()
        clear_cached_data()
        return True, result
    except Exception as e:
        return False, e


def obtener_presupuesto_total(df_limites):
    if df_limites is None or df_limites.empty:
        return 0.0
    row = df_limites[df_limites["categoria"] == PRESUPUESTO_TOTAL_KEY]
    if row.empty:
        return 0.0
    return float(row.iloc[0].get("limite_mensual", 0) or 0)


def obtener_limites_visibles(df_limites):
    if df_limites is None or df_limites.empty:
        return pd.DataFrame(columns=["categoria", "limite_mensual", "activo"])
    return df_limites[(df_limites["categoria"] != PRESUPUESTO_TOTAL_KEY) & (df_limites["activo"] == True)].copy()


# ============================================================
# IA, CATEGORIZACIÓN Y REGISTRO POR TEXTO
# ============================================================

def extraer_monto(texto):
    texto = str(texto or "")
    matches = re.findall(r"\d+(?:[\.,]\d{3})*(?:[\.,]\d+)?|\d+", texto)
    if not matches:
        return 0.0
    raw = matches[0].strip()
    if "." in raw and "," in raw:
        if raw.rfind(",") > raw.rfind("."):
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", "")
    elif "," in raw:
        parts = raw.split(",")
        raw = "".join(parts) if len(parts[-1]) == 3 else raw.replace(",", ".")
    elif "." in raw:
        parts = raw.split(".")
        raw = "".join(parts) if len(parts[-1]) == 3 else raw
    try:
        return float(raw)
    except Exception:
        return 0.0


def detectar_tipo_por_texto(texto):
    t = str(texto or "").lower()
    palabras_ingreso = ["recib", "me pagaron", "salario", "sueldo", "ingreso", "cobré", "cobre", "venta", "freelance", "gané", "gane"]
    palabras_gasto = ["gast", "pagué", "pague", "compr", "salió", "salio", "arriendo", "mercado", "transporte", "servicio"]
    score_ing = sum(1 for p in palabras_ingreso if p in t)
    score_gas = sum(1 for p in palabras_gasto if p in t)
    return "Ingreso" if score_ing > score_gas else "Gasto"


def sugerir_categoria(texto, tipo, categorias_disponibles):
    t = str(texto or "").lower()
    reglas_gasto = {
        "Comida": ["comida", "almuerzo", "desayuno", "cena", "restaurante", "domicilio", "mercado", "super", "pan", "café", "cafe"],
        "Transporte": ["uber", "taxi", "bus", "metro", "gasolina", "peaje", "transporte", "moto"],
        "Arriendo": ["arriendo", "renta", "alquiler"],
        "Servicios": ["luz", "agua", "internet", "gas", "celular", "servicio", "servicios"],
        "Salud": ["médico", "medico", "farmacia", "medicina", "salud", "odont", "clínica", "clinica"],
        "Educación": ["curso", "estudio", "universidad", "colegio", "libro", "educación", "educacion"],
        "Compras": ["ropa", "zapatos", "compra", "compré", "compre", "tienda", "amazon"],
        "Ocio": ["cine", "fiesta", "bar", "juego", "netflix", "spotify", "salida"],
        "Deudas": ["deuda", "cuota", "crédito", "credito", "tarjeta"],
        "Ahorro": ["ahorro", "guardé", "guarde", "invertí", "inverti"],
    }
    reglas_ingreso = {
        "Salario": ["salario", "sueldo", "nómina", "nomina", "quincena"],
        "Freelance": ["freelance", "proyecto", "cliente", "servicio"],
        "Ventas": ["venta", "vendí", "vendi", "producto"],
        "Regalos": ["regalo", "me dieron"],
    }
    reglas = reglas_ingreso if tipo == "Ingreso" else reglas_gasto
    disponibles_lower = {c.lower(): c for c in categorias_disponibles}
    for categoria, palabras in reglas.items():
        if any(p in t for p in palabras):
            for disp in categorias_disponibles:
                if disp.lower() == categoria.lower():
                    return disp
    return categorias_disponibles[0] if categorias_disponibles else "Otros"


def parsear_movimiento_texto(texto, categorias_ingreso, categorias_gasto):
    tipo = detectar_tipo_por_texto(texto)
    monto = extraer_monto(texto)
    categorias = categorias_ingreso if tipo == "Ingreso" else categorias_gasto
    categoria = sugerir_categoria(texto, tipo, categorias)
    descripcion = re.sub(r"\$?\s*\d+(?:[\.,]\d+)*", "", str(texto or "")).strip(" -.,")
    descripcion = descripcion or ("Ingreso rápido" if tipo == "Ingreso" else "Gasto rápido")
    return {"tipo": tipo, "monto": monto, "categoria": categoria, "descripcion": descripcion}


def construir_contexto_ia(nombre, df, meta_row, presupuesto_total, limites_df):
    df_mes = filtrar_mes(df)
    ingresos, gastos, saldo = resumen_movimientos(df_mes)
    semana = filtrar_semana_actual(df)
    semana_ant = filtrar_semana_anterior(df)
    gasto_sem, _, _saldo_sem = resumen_movimientos(semana)
    # Corrección: resumen_movimientos devuelve ingresos, gastos, saldo.
    ing_sem, gas_sem, sal_sem = resumen_movimientos(semana)
    ing_ant, gas_ant, sal_ant = resumen_movimientos(semana_ant)
    top_cat, top_monto, top_share = top_categoria_gasto(df_mes)
    meta = float((meta_row or {}).get("meta", 0) or 0)
    nombre_meta = str((meta_row or {}).get("nombre_meta", "") or "")
    movimientos_txt = "Sin movimientos recientes."
    if not df_mes.empty:
        rec = df_mes.sort_values("fecha", ascending=False).head(10)
        movimientos_txt = "\n".join(
            f"- {r.fecha.date()} | {r.tipo} | {r.categoria} | {money(r.monto)} | {r.descripcion}"
            for r in rec.itertuples()
        )
    limites_txt = "Sin límites por categoría."
    if limites_df is not None and not limites_df.empty:
        limites_txt = ", ".join(f"{r.categoria}: {money(r.limite_mensual)}" for r in limites_df.itertuples())
    return f"""
CONTEXTO ZENTIX PERSONAL
Usuario: {nombre}
Ingresos del mes: {money(ingresos)}
Gastos del mes: {money(gastos)}
Disponible del mes: {money(saldo)}
Presupuesto mensual: {money(presupuesto_total)}
Gasto semana actual: {money(gas_sem)}
Gasto semana anterior: {money(gas_ant)}
Categoría más alta: {top_cat or 'Sin datos'} ({money(top_monto)}, {fmt_pct(top_share)})
Meta: {nombre_meta or 'Sin nombre'} · {money(meta)}
Límites: {limites_txt}
Movimientos recientes:
{movimientos_txt}
""".strip()


def respuesta_local_zentix(pregunta, contexto, df):
    df_mes = filtrar_mes(df)
    ingresos, gastos, saldo = resumen_movimientos(df_mes)
    top_cat, top_monto, top_share = top_categoria_gasto(df_mes)
    if df_mes.empty:
        return "Aún no tengo suficientes movimientos. Empieza registrando tus ingresos y gastos principales; con 5 a 10 datos ya puedo darte una lectura más útil."
    accion = "Sigue registrando a diario."
    if saldo < 0:
        accion = "Tu primer paso debe ser frenar gastos variables hasta recuperar saldo positivo."
    elif top_cat and top_share >= 0.40:
        accion = f"Tu mejor ajuste está en {top_cat}. Intenta reducir esa categoría un 10% esta semana."
    elif gastos > ingresos * 0.8 and ingresos > 0:
        accion = "Estás usando más del 80% de tus ingresos. Define un techo de gasto semanal para no cerrar el mes justo."
    return (
        f"Resumen rápido: este mes entraron {money(ingresos)}, salieron {money(gastos)} y te quedan {money(saldo)}. "
        f"Tu categoría más pesada es {top_cat or 'sin datos'} con {money(top_monto)}. {accion}"
    )


def consultar_ia_zentix(pregunta, contexto, df):
    if not openai_client:
        return respuesta_local_zentix(pregunta, contexto, df)
    system = """
Eres Zentix IA, un asistente de finanzas personales simple, claro y responsable.
No eres contador, abogado ni asesor financiero regulado. No prometas rendimientos.
Tu estilo: corto, práctico, cálido y accionable. Habla en español colombiano neutro.
Prioriza: cuánto entra, cuánto sale, cuánto queda, hábito, presupuesto, meta y alertas simples.
No menciones funciones empresariales, inventario, caja de negocio, cartera ni contabilidad; eso será BradaFin.
Si el usuario pide registrar un movimiento, extrae tipo, monto, categoría sugerida y una descripción breve.
""".strip()
    user = f"{contexto}\n\nPregunta del usuario:\n{pregunta}"
    last_error = None
    for model in GEMINI_MODEL_CANDIDATES:
        try:
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.35,
                max_tokens=700,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            last_error = e
            continue
    return respuesta_local_zentix(pregunta, contexto, df) + f"\n\nNota: no pude conectar con la IA externa en este momento ({last_error})."


@st.cache_data(ttl=60, show_spinner=False)
def obtener_uso_ia_hoy(user_id):
    hoy = date.today().isoformat()
    session_key = f"uso_ia_local_{user_id}_{hoy}"
    try:
        result = supabase.table("uso_ia_diario").select("*").eq("usuario_id", user_id).eq("fecha", hoy).limit(1).execute()
        if result.data:
            return result.data[0]
        nuevo = {"usuario_id": user_id, "fecha": hoy, "consultas_usadas": 0, "actualizado_en": datetime.now().isoformat()}
        inserted = supabase.table("uso_ia_diario").insert(nuevo).execute()
        if inserted.data:
            return inserted.data[0]
    except Exception:
        pass
    if session_key not in st.session_state:
        st.session_state[session_key] = 0
    return {"id": None, "usuario_id": user_id, "fecha": hoy, "consultas_usadas": st.session_state[session_key]}


def puede_usar_ia(user_id):
    plan = obtener_plan_usuario(user_id)
    uso = obtener_uso_ia_hoy(user_id)
    limite = int(plan.get("consultas_ia_dia", 10) or 10)
    usadas = int(uso.get("consultas_usadas", 0) or 0)
    return usadas < limite, usadas, limite, max(0, limite - usadas), plan


def registrar_uso_ia(user_id):
    hoy = date.today().isoformat()
    session_key = f"uso_ia_local_{user_id}_{hoy}"
    uso = obtener_uso_ia_hoy(user_id)
    nuevas = int(uso.get("consultas_usadas", 0) or 0) + 1
    try:
        if uso.get("id"):
            supabase.table("uso_ia_diario").update({"consultas_usadas": nuevas, "actualizado_en": datetime.now().isoformat()}).eq("id", uso["id"]).execute()
        else:
            st.session_state[session_key] = nuevas
        clear_cached_data()
    except Exception:
        st.session_state[session_key] = nuevas


# ============================================================
# ALERTAS Y REPORTES
# ============================================================

def generar_alertas(df, meta_row=None, presupuesto_total=0, limites_df=None):
    alertas = []
    df_mes = filtrar_mes(df)
    ingresos, gastos, saldo = resumen_movimientos(df_mes)
    semana = filtrar_semana_actual(df)
    semana_ant = filtrar_semana_anterior(df)
    _, gasto_sem, _ = resumen_movimientos(semana)
    _, gasto_ant, _ = resumen_movimientos(semana_ant)
    top_cat, top_monto, top_share = top_categoria_gasto(df_mes)
    meta = float((meta_row or {}).get("meta", 0) or 0)

    if ingresos > 0 and gastos >= ingresos * 0.9:
        alertas.append("Tus gastos están muy cerca de tus ingresos este mes.")
    if saldo < 0:
        alertas.append("Tu disponible del mes está en negativo.")
    if gasto_ant > 0 and gasto_sem > gasto_ant * 1.15:
        alertas.append("Gastaste más que la semana pasada.")
    if top_cat and top_share >= 0.40:
        alertas.append(f"{top_cat} concentra {fmt_pct(top_share)} de tus gastos del mes.")
    if presupuesto_total > 0 and gastos >= presupuesto_total * 0.85:
        alertas.append("Ya estás cerca de consumir tu presupuesto mensual.")
    if meta > 0 and saldo < meta * 0.30:
        alertas.append("Tu saldo actual aún está lejos de tu meta de ahorro.")

    if limites_df is not None and not limites_df.empty and not df_mes.empty:
        for row in limites_df.itertuples():
            usado = float(df_mes[(df_mes["tipo"] == "Gasto") & (df_mes["categoria"] == row.categoria)]["monto"].sum())
            limite = float(row.limite_mensual or 0)
            if limite > 0 and usado >= limite:
                alertas.append(f"Ya superaste el límite de {row.categoria}.")
            elif limite > 0 and usado >= limite * 0.8:
                alertas.append(f"Vas en más del 80% del límite de {row.categoria}.")

    if not alertas:
        alertas.append("No hay alertas fuertes. Mantén el registro constante.")
    return alertas[:5]


def construir_reporte_semanal(df, meta_row=None):
    semana = filtrar_semana_actual(df)
    semana_ant = filtrar_semana_anterior(df)
    ing, gas, saldo = resumen_movimientos(semana)
    _, gas_ant, _ = resumen_movimientos(semana_ant)
    top_cat, top_monto, top_share = top_categoria_gasto(semana)
    meta = float((meta_row or {}).get("meta", 0) or 0)
    puntos = []
    puntos.append(f"Ingresos de la semana: {money(ing)}.")
    puntos.append(f"Gastos de la semana: {money(gas)}.")
    puntos.append(f"Disponible semanal: {money(saldo)}.")
    if gas_ant > 0:
        delta = gas - gas_ant
        if delta > 0:
            puntos.append(f"Gastaste {money(delta)} más que la semana pasada.")
        else:
            puntos.append(f"Gastaste {money(abs(delta))} menos que la semana pasada.")
    if top_cat:
        puntos.append(f"La categoría más alta fue {top_cat} con {money(top_monto)}.")
    if meta > 0:
        puntos.append(f"Tu meta activa es {money(meta)}. Disponible actual del mes: {money(resumen_movimientos(filtrar_mes(df))[2])}.")
    if not semana.empty:
        puntos.append("Siguiente paso: corrige una sola categoría, no todo al tiempo.")
    else:
        puntos.append("Siguiente paso: registra al menos 3 movimientos esta semana para activar mejores alertas.")
    return puntos


def generar_pdf_reporte(nombre, df, meta_row=None):
    if not REPORTLAB_AVAILABLE:
        return None
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=38, bottomMargin=36)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ZentixTitle", parent=styles["Title"], textColor=colors.HexColor("#0F172A"), fontSize=22, leading=26)
    h_style = ParagraphStyle("ZentixH", parent=styles["Heading2"], textColor=colors.HexColor("#172554"), fontSize=14, leading=18)
    p_style = ParagraphStyle("ZentixP", parent=styles["BodyText"], fontSize=10, leading=15)
    story = []
    story.append(Paragraph("Zentix · Reporte semanal sencillo", title_style))
    story.append(Paragraph(f"Usuario: {safe_text(nombre)} · Fecha: {date.today().isoformat()}", p_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Resumen", h_style))
    for punto in construir_reporte_semanal(df, meta_row):
        story.append(Paragraph(f"• {safe_text(punto)}", p_style))
    story.append(Spacer(1, 12))
    df_rep = filtrar_semana_actual(df).sort_values("fecha", ascending=False).head(20)
    if not df_rep.empty:
        story.append(Paragraph("Movimientos recientes", h_style))
        data = [["Fecha", "Tipo", "Categoría", "Monto", "Descripción"]]
        for r in df_rep.itertuples():
            data.append([str(r.fecha.date()), r.tipo, r.categoria, money(r.monto), str(r.descripcion)[:34]])
        table = Table(data, colWidths=[62, 58, 84, 74, 190])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172554")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), .25, colors.HexColor("#CBD5E1")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("Aún no hay movimientos esta semana.", p_style))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def exportar_excel(df):
    buffer = io.BytesIO()
    out = df.copy()
    if "fecha" in out.columns:
        out["fecha"] = pd.to_datetime(out["fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
    cols = [c for c in ["fecha", "tipo", "categoria", "monto", "descripcion", "emocion"] if c in out.columns]
    out = out[cols]
    try:
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            out.to_excel(writer, index=False, sheet_name="movimientos")
        buffer.seek(0)
        return buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"
    except Exception:
        csv = out.to_csv(index=False).encode("utf-8-sig")
        return csv, "text/csv", "csv"


# ============================================================
# AUTENTICACIÓN
# ============================================================

def render_auth():
    col_left, col_right = st.columns([1.05, .95], gap="large")

    with col_left:
        if ICON_PATH:
            st.image(str(ICON_PATH), width=110)

        st.markdown(
            f"""
            <div class="hero-card">
                <div class="hero-badge">Zentix personal</div>
                <div class="hero-title">Tu dinero claro en segundos.</div>
                <div class="hero-sub">{APP_TAGLINE}</div>
                <div class="hero-pills">
                    <span class="hero-pill">Registro rápido</span>
                    <span class="hero-pill">Metas de ahorro</span>
                    <span class="hero-pill">Presupuesto mensual</span>
                    <span class="hero-pill">IA simple</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="soft-card">
                <div class="section-title">Promesa de Zentix</div>
                <div class="section-caption">Saber cuánto entra, cuánto sale y cuánto queda sin sentirse en una hoja de cálculo.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        section_header("Acceso", "Primero crea tu cuenta. Si ya la tienes, entra desde Login.")

        tab_reg, tab_login, tab_reset = st.tabs(["Registro", "Login", "Recuperar"])

        with tab_reg:
            st.markdown(
                "<div class='muted' style='margin-bottom:.75rem;'>Si eres nuevo, empieza aquí.</div>",
                unsafe_allow_html=True,
            )
            reg_email = st.text_input("Correo para registro", key="reg_email")
            reg_password = st.text_input("Contraseña", type="password", key="reg_password")
            reg_password_2 = st.text_input("Confirma contraseña", type="password", key="reg_password_2")

            if st.button("Crear cuenta", type="primary", use_container_width=True):
                if not reg_email or "@" not in reg_email:
                    st.error("Escribe un correo válido.")
                elif len(reg_password or "") < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres.")
                elif reg_password != reg_password_2:
                    st.error("Las contraseñas no coinciden.")
                else:
                    try:
                        supabase.auth.sign_up({"email": reg_email.strip(), "password": reg_password})
                        st.success("Cuenta creada. Ahora entra desde Login. Si Supabase exige confirmación, revisa tu correo.")
                    except Exception as e:
                        st.error(f"No pude crear la cuenta: {e}")

        with tab_login:
            st.markdown(
                "<div class='muted' style='margin-bottom:.75rem;'>Si ya estás registrado, entra aquí.</div>",
                unsafe_allow_html=True,
            )
            email = st.text_input("Correo", key="login_email")
            password = st.text_input("Contraseña", type="password", key="login_password")

            if st.button("Entrar a Zentix", type="primary", use_container_width=True):
                if not email or not password:
                    st.error("Escribe correo y contraseña.")
                else:
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email.strip(), "password": password})
                        st.session_state.user = res.user
                        if getattr(res, "session", None):
                            st.session_state["zentix_access_token"] = getattr(res.session, "access_token", None)
                            st.session_state["zentix_refresh_token"] = getattr(res.session, "refresh_token", None)
                        st.success("Entraste correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"No pude iniciar sesión: {e}")

        with tab_reset:
            st.markdown(
                "<div class='muted' style='margin-bottom:.75rem;'>Si olvidaste tu contraseña, recupérala aquí.</div>",
                unsafe_allow_html=True,
            )
            reset_email = st.text_input("Correo de recuperación", key="reset_email")

            if st.button("Enviar enlace de recuperación", use_container_width=True):
                if not reset_email:
                    st.error("Escribe tu correo.")
                else:
                    try:
                        supabase.auth.reset_password_for_email(reset_email.strip())
                        st.success("Si el correo existe, Supabase enviará el enlace de recuperación.")
                    except Exception as e:
                        st.error(f"No pude enviar la recuperación: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

def render_onboarding(user_id, email):
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-badge">Primer paso</div>
            <div class="hero-title">Configura Zentix en un minuto.</div>
            <div class="hero-sub">Elige tus categorías principales. Luego podrás cambiarlas desde Perfil.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    nombre_default = str(email or "Usuario").split("@")[0].replace(".", " ").title()
    with st.form("onboarding_form"):
        nombre = st.text_input("¿Cómo quieres que te llame Zentix?", value=nombre_default)
        gastos = st.multiselect("Categorías de gasto", DEFAULT_GASTOS, default=["Comida", "Transporte", "Servicios", "Otros"])
        ingresos = st.multiselect("Categorías de ingreso", DEFAULT_INGRESOS, default=["Salario", "Otros"])
        submitted = st.form_submit_button("Guardar y empezar", type="primary", use_container_width=True)
    if submitted:
        if not nombre.strip():
            st.error("Escribe tu nombre.")
        elif not gastos or not ingresos:
            st.error("Selecciona al menos una categoría de ingreso y una de gasto.")
        else:
            guardar_onboarding(user_id, nombre, gastos, ingresos)
            st.success("Listo. Zentix ya quedó configurado.")
            st.rerun()


# ============================================================
# COMPONENTES DE MOVIMIENTOS
# ============================================================

def render_movimiento_row(row):
    tipo = str(row.get("tipo", ""))
    clase = "amount-income" if tipo == "Ingreso" else "amount-expense"
    signo = "+" if tipo == "Ingreso" else "-"
    fecha = pd.to_datetime(row.get("fecha"), errors="coerce")
    fecha_txt = fecha.strftime("%d %b") if pd.notna(fecha) else "Sin fecha"
    st.markdown(
        f"""
        <div class="movement-row">
            <div>
                <div class="movement-title">{safe_text(row.get('descripcion') or row.get('categoria') or tipo)}</div>
                <div class="movement-sub">{safe_text(fecha_txt)} · {safe_text(tipo)} · {safe_text(row.get('categoria'))}</div>
            </div>
            <div class="{clase}">{signo}{money(row.get('monto', 0))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_form_registro(user_id, categorias_ingreso, categorias_gasto, key_prefix="main"):
    with st.form(f"form_registro_{key_prefix}", clear_on_submit=True):
        col1, col2, col3 = st.columns([.85, 1.1, 1.1])
        with col1:
            tipo = st.radio("Tipo", ["Ingreso", "Gasto"], horizontal=True, key=f"{key_prefix}_tipo")
        with col2:
            fecha_mov = st.date_input("Fecha", value=date.today(), key=f"{key_prefix}_fecha")
        with col3:
            monto = st.number_input("Monto", min_value=0.0, step=1000.0, key=f"{key_prefix}_monto")
        descripcion = st.text_input("Descripción", placeholder="Ej: Almuerzo, salario, transporte...", key=f"{key_prefix}_descripcion")
        categorias = categorias_ingreso if tipo == "Ingreso" else categorias_gasto
        categoria_sugerida = sugerir_categoria(descripcion, tipo, categorias)
        default_index = categorias.index(categoria_sugerida) if categoria_sugerida in categorias else 0
        col4, col5 = st.columns([1.1, .9])
        with col4:
            categoria = st.selectbox("Categoría", categorias, index=default_index, key=f"{key_prefix}_categoria")
        with col5:
            emocion = ""
            if tipo == "Gasto":
                emocion = st.selectbox("Emoción opcional", EMOCIONES, format_func=lambda x: "No registrar" if x == "" else x, key=f"{key_prefix}_emocion")
        submitted = st.form_submit_button("Guardar movimiento", type="primary", use_container_width=True)
    if submitted:
        if monto <= 0:
            st.error("El monto debe ser mayor a cero.")
        else:
            ok, resp = insertar_movimiento(user_id, tipo, categoria, monto, descripcion, fecha_mov, emocion)
            if ok:
                st.success("Movimiento guardado.")
                st.rerun()
            else:
                st.error(f"No pude guardar el movimiento: {resp}")


def render_registro_por_texto(user_id, categorias_ingreso, categorias_gasto):
    st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="home-color-title">
            <span class="home-color-icon">⚡</span>
            <span style="color:#0F172A !important;">Registro por texto</span>
        </div>
        <div class="home-caption" style="color:#475569 !important;">
            Escribe como hablarías: "Gasté 12000 en almuerzo" o "Recibí 250000 de freelance".
        </div>
        """,
        unsafe_allow_html=True,
    )

    texto = st.text_input(
        "Movimiento rápido",
        placeholder="Ej: gasté 18000 en transporte",
        key="quick_text_register",
    )

    if texto:
        parsed = parsear_movimiento_texto(texto, categorias_ingreso, categorias_gasto)
        if parsed["monto"] > 0:
            st.info(f"Zentix entendió: {parsed['tipo']} · {parsed['categoria']} · {money(parsed['monto'])}")
        else:
            st.warning("No detecté monto todavía. Incluye un número para registrar.")

    col_a, col_b = st.columns([1, 1])

    with col_a:
        if st.button("Registrar desde texto", type="primary", use_container_width=True):
            parsed = parsear_movimiento_texto(texto, categorias_ingreso, categorias_gasto)
            if not texto.strip():
                st.error("Escribe el movimiento.")
            elif parsed["monto"] <= 0:
                st.error("No detecté un monto válido.")
            else:
                ok, resp = insertar_movimiento(
                    user_id=user_id,
                    tipo=parsed["tipo"],
                    categoria=parsed["categoria"],
                    monto=parsed["monto"],
                    descripcion=parsed["descripcion"],
                    fecha_mov=date.today(),
                    emocion="",
                )
                if ok:
                    st.success("Movimiento registrado desde texto.")
                    st.rerun()
                else:
                    st.error(f"No pude guardar: {resp}")

    with col_b:
        st.markdown(
            "<div class='muted' style='padding-top:.35rem; color:#475569 !important;'>La categorización automática usa reglas simples y tus categorías configuradas.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

def pagina_inicio(user_id, nombre, df, meta_row, presupuesto_total, limites_visibles):
    df_mes = filtrar_mes(df)
    ingresos, gastos, saldo = resumen_movimientos(df_mes)
    meta = float((meta_row or {}).get("meta", 0) or 0)
    top_cat, top_monto, top_share = top_categoria_gasto(df_mes)
    alertas = generar_alertas(df, meta_row, presupuesto_total, limites_visibles)
    semana = filtrar_semana_actual(df)
    semana_ant = filtrar_semana_anterior(df)
    _, gasto_semana, _ = resumen_movimientos(semana)
    _, gasto_semana_ant, _ = resumen_movimientos(semana_ant)

    estado = "Vas bien" if saldo >= 0 else "Revisar gastos"
    estado_sub = "Saldo positivo este mes" if saldo >= 0 else "Tu mes está en negativo"
    presupuesto_restante = presupuesto_total - gastos if presupuesto_total > 0 else 0
    progreso_presupuesto = gastos / presupuesto_total if presupuesto_total > 0 else 0
    progreso_meta = saldo / meta if meta > 0 else 0

    st.markdown(
        f"""
        <style>
        .home-premium-hero {{
            position: relative;
            overflow: hidden;
            border-radius: 34px;
            padding: 1.45rem 1.55rem;
            margin-bottom: 1rem;
            color: #FFFFFF;
            background:
                radial-gradient(circle at 10% 10%, rgba(255,255,255,.25), transparent 22%),
                radial-gradient(circle at 90% 20%, rgba(6,182,212,.22), transparent 26%),
                linear-gradient(135deg, #0F172A 0%, #1D4ED8 45%, #4F46E5 74%, #7C3AED 100%);
            box-shadow: 0 28px 60px rgba(30,64,175,.25);
        }}
        .home-premium-hero * {{ color: #FFFFFF !important; }}
        .home-premium-badge {{
            display:inline-flex;
            align-items:center;
            gap:.45rem;
            padding:.42rem .82rem;
            border-radius:999px;
            background:rgba(255,255,255,.18);
            border:1px solid rgba(255,255,255,.24);
            font-weight:900;
            font-size:.82rem;
        }}
        .home-premium-title {{
            font-size:2.28rem;
            line-height:1.02;
            font-weight:950;
            letter-spacing:-.05em;
            margin:.95rem 0 .35rem 0;
        }}
        .home-premium-sub {{
            max-width:820px;
            font-size:1.02rem;
            line-height:1.58;
            color:rgba(255,255,255,.92) !important;
        }}
        .home-premium-strip {{
            display:grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap:.7rem;
            margin-top:1.05rem;
        }}
        .home-premium-mini {{
            padding:.85rem .9rem;
            border-radius:22px;
            background:rgba(255,255,255,.16);
            border:1px solid rgba(255,255,255,.20);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.12);
        }}
        .home-premium-mini-label {{
            font-size:.74rem;
            font-weight:800;
            opacity:.85;
            margin-bottom:.24rem;
        }}
        .home-premium-mini-value {{
            font-size:1.08rem;
            font-weight:950;
            letter-spacing:-.03em;
        }}
        .home-action-card {{
            border-radius:28px;
            padding:1.05rem;
            margin-bottom:.9rem;
            background:linear-gradient(180deg, #FFFFFF 0%, #F8FBFF 100%);
            border:1px solid rgba(79,70,229,.12);
            box-shadow:0 16px 32px rgba(15,23,42,.06);
        }}
        .home-action-card * {{ color:#0F172A !important; }}
        .home-color-title {{
            display:flex;
            align-items:center;
            gap:.6rem;
            font-weight:950;
            font-size:1.14rem;
            letter-spacing:-.03em;
            margin-bottom:.18rem;
            color:#0F172A !important;
        }}
        .home-color-icon {{
            width:42px;
            height:42px;
            display:inline-flex;
            align-items:center;
            justify-content:center;
            border-radius:16px;
            color:#FFFFFF !important;
            font-weight:950;
            background:linear-gradient(135deg, #4F46E5, #7C3AED);
            box-shadow:0 12px 22px rgba(79,70,229,.22);
        }}
        .home-caption {{ color:#475569 !important; font-size:.92rem; line-height:1.55; margin-bottom:.75rem; }}
        .home-alert-box {{
            padding:.8rem .9rem;
            margin-bottom:.65rem;
            border-radius:20px;
            background:linear-gradient(135deg, #EEF2FF 0%, #ECFEFF 100%);
            border:1px solid rgba(99,102,241,.18);
            color:#1E293B !important;
            font-weight:850;
        }}
        .home-alert-box strong {{ color:#3730A3 !important; }}
        .home-register-shell {{
            border-radius:30px;
            padding:1.05rem;
            background:linear-gradient(180deg, #111827 0%, #172554 58%, #312E81 100%);
            box-shadow:0 24px 46px rgba(30,41,59,.18);
            border:1px solid rgba(129,140,248,.24);
        }}
        .home-register-shell .home-color-title,
        .home-register-shell .home-caption,
        .home-register-shell .home-color-title span {{
            color:#FFFFFF !important;
        }}
        .home-register-shell .home-caption {{ color:rgba(255,255,255,.82) !important; }}
        .home-register-shell label,
        .home-register-shell .stRadio label p,
        .home-register-shell .stMarkdown,
        .home-register-shell .stMarkdown p {{
            color:#F8FAFC !important;
            font-weight:800 !important;
        }}
        .home-register-shell input,
        .home-register-shell textarea,
        .home-register-shell div[data-baseweb="select"] > div {{
            background:#FFFFFF !important;
            color:#0F172A !important;
            border:1px solid rgba(255,255,255,.28) !important;
        }}
        .home-register-shell .stButton > button[kind="primary"] {{
            background:linear-gradient(135deg, #EF4444 0%, #F97316 100%) !important;
            color:#FFFFFF !important;
            border:none !important;
            box-shadow:0 16px 28px rgba(239,68,68,.28);
        }}
        .home-movement-card {{
            display:flex;
            justify-content:space-between;
            gap:.9rem;
            align-items:center;
            padding:.82rem 0;
            border-bottom:1px solid rgba(15,23,42,.06);
        }}
        .home-movement-card:last-child {{ border-bottom:none; }}
        .home-movement-left {{ display:flex; align-items:center; gap:.72rem; min-width:0; }}
        .home-movement-dot {{
            width:40px;
            height:40px;
            flex:0 0 40px;
            border-radius:15px;
            display:flex;
            align-items:center;
            justify-content:center;
            font-weight:950;
        }}
        .home-movement-dot-income {{ background:#DCFCE7; color:#166534 !important; }}
        .home-movement-dot-expense {{ background:#FEE2E2; color:#991B1B !important; }}
        .home-movement-name {{
            color:#0F172A !important;
            font-size:.98rem;
            font-weight:950;
            line-height:1.2;
            overflow:hidden;
            text-overflow:ellipsis;
            white-space:nowrap;
            max-width:360px;
        }}
        .home-movement-meta {{ color:#64748B !important; font-size:.83rem; margin-top:.18rem; }}
        .home-movement-amount-income {{ color:#16A34A !important; font-weight:950; white-space:nowrap; }}
        .home-movement-amount-expense {{ color:#DC2626 !important; font-weight:950; white-space:nowrap; }}
        .home-insight-grid {{
            display:grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap:.75rem;
            margin-top:.75rem;
        }}
        .home-insight-tile {{
            padding:.85rem;
            border-radius:22px;
            background:linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
            border:1px solid rgba(148,163,184,.20);
        }}
        .home-insight-label {{ color:#64748B !important; font-size:.78rem; font-weight:850; margin-bottom:.25rem; }}
        .home-insight-value {{ color:#0F172A !important; font-size:1.05rem; font-weight:950; }}
        @media (max-width: 900px) {{
            .home-premium-strip {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
            .home-premium-title {{ font-size:1.8rem; }}
            .home-movement-name {{ max-width:210px; }}
        }}
        </style>

        <div class="home-premium-hero">
            <div class="home-premium-badge">✨ Zentix personal · inicio inteligente</div>
            <div class="home-premium-title">Hola, {safe_text(nombre)}. Tu dinero ya está más claro.</div>
            <div class="home-premium-sub">Registra rápido, mira lo esencial y toma una decisión simple para esta semana. Zentix no te llena de módulos: te muestra lo que entra, lo que sale y lo que queda.</div>
            <div class="home-premium-strip">
                <div class="home-premium-mini">
                    <div class="home-premium-mini-label">ENTRÓ ESTE MES</div>
                    <div class="home-premium-mini-value">{money(ingresos)}</div>
                </div>
                <div class="home-premium-mini">
                    <div class="home-premium-mini-label">SALIÓ ESTE MES</div>
                    <div class="home-premium-mini-value">{money(gastos)}</div>
                </div>
                <div class="home-premium-mini">
                    <div class="home-premium-mini-label">TE QUEDA</div>
                    <div class="home-premium-mini-value">{money(saldo)}</div>
                </div>
                <div class="home-premium-mini">
                    <div class="home-premium-mini-label">ESTADO</div>
                    <div class="home-premium-mini-value">{safe_text(estado)}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Entró", money(ingresos), "Ingresos del mes", "income")
    with c2:
        kpi_card("Salió", money(gastos), "Gastos del mes", "expense")
    with c3:
        kpi_card("Queda", money(saldo), estado_sub, "balance")
    with c4:
        if meta > 0:
            kpi_card("Meta", fmt_pct(max(0, min(progreso_meta, 1))), f"Objetivo: {money(meta)}", "saving")
        else:
            kpi_card("Meta", "Pendiente", "Crea una meta de ahorro", "saving")

    col_left, col_right = st.columns([1.05, .95], gap="large")

    with col_right:
        st.markdown("<div class='home-register-shell'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="home-color-title"><span class="home-color-icon">＋</span><span>Registro rápido</span></div>
            <div class="home-caption">Guarda ingresos o gastos sin salir del inicio.</div>
            """,
            unsafe_allow_html=True,
        )
        categorias_ingreso = obtener_categorias_usuario(user_id, "Ingreso")
        categorias_gasto = obtener_categorias_usuario(user_id, "Gasto")
        render_form_registro(user_id, categorias_ingreso, categorias_gasto, key_prefix="home")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='home-action-card'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="home-color-title"><span class="home-color-icon">🎯</span><span>Progreso simple</span></div>
            <div class="home-caption">Dos barras para saber si vas bien sin llenarte de gráficas.</div>
            """,
            unsafe_allow_html=True,
        )
        if presupuesto_total > 0:
            st.markdown(f"**Presupuesto usado:** {money(gastos)} de {money(presupuesto_total)}")
            st.progress(float(max(0, min(progreso_presupuesto, 1))))
        else:
            st.info("Crea un presupuesto mensual para activar esta barra.")
        if meta > 0:
            st.markdown(f"**Meta de ahorro:** avance estimado {fmt_pct(max(0, min(progreso_meta, 1)))}")
            st.progress(float(max(0, min(progreso_meta, 1))))
        else:
            st.info("Crea una meta para medir tu avance.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_left:
        st.markdown("<div class='home-action-card'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="home-color-title"><span class="home-color-icon">⚡</span><span>Alerta principal</span></div>
            <div class="home-caption">Una señal clara para decidir mejor esta semana.</div>
            """,
            unsafe_allow_html=True,
        )
        for alerta in alertas[:3]:
            st.markdown(f"<div class='home-alert-box'><strong>•</strong> {safe_text(alerta)}</div>", unsafe_allow_html=True)

        st.markdown("<div class='home-insight-grid'>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="home-insight-tile">
                <div class="home-insight-label">MAYOR CATEGORÍA</div>
                <div class="home-insight-value">{safe_text(top_cat or 'Sin datos')}</div>
            </div>
            <div class="home-insight-tile">
                <div class="home-insight-label">MONTO DESTACADO</div>
                <div class="home-insight-value">{money(top_monto)}</div>
            </div>
            <div class="home-insight-tile">
                <div class="home-insight-label">GASTO ESTA SEMANA</div>
                <div class="home-insight-value">{money(gasto_semana)}</div>
            </div>
            <div class="home-insight-tile">
                <div class="home-insight-label">SEMANA ANTERIOR</div>
                <div class="home-insight-value">{money(gasto_semana_ant)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='home-action-card'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="home-color-title"><span class="home-color-icon">🧾</span><span>Últimos movimientos</span></div>
            <div class="home-caption">Lo más reciente primero, con mejor lectura visual.</div>
            """,
            unsafe_allow_html=True,
        )
        if df.empty:
            st.info("Aún no hay movimientos. Registra el primero desde el panel derecho.")
        else:
            for _, row in df.sort_values("fecha", ascending=False).head(8).iterrows():
                tipo = str(row.get("tipo", ""))
                is_income = tipo == "Ingreso"
                dot_cls = "home-movement-dot-income" if is_income else "home-movement-dot-expense"
                amount_cls = "home-movement-amount-income" if is_income else "home-movement-amount-expense"
                signo = "+" if is_income else "-"
                icon = "↑" if is_income else "↓"
                fecha = pd.to_datetime(row.get("fecha"), errors="coerce")
                fecha_txt = fecha.strftime("%d %b") if pd.notna(fecha) else "Sin fecha"
                titulo = row.get("descripcion") or row.get("categoria") or tipo
                st.markdown(
                    f"""
                    <div class="home-movement-card">
                        <div class="home-movement-left">
                            <div class="home-movement-dot {dot_cls}">{icon}</div>
                            <div>
                                <div class="home-movement-name">{safe_text(titulo)}</div>
                                <div class="home-movement-meta">{safe_text(fecha_txt)} · {safe_text(tipo)} · {safe_text(row.get('categoria'))}</div>
                            </div>
                        </div>
                        <div class="{amount_cls}">{signo}{money(row.get('monto', 0))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    if not df_mes.empty:
        g = df_mes[df_mes["tipo"] == "Gasto"].copy()
        if not g.empty:
            resumen = g.groupby("categoria", dropna=False)["monto"].sum().reset_index().sort_values("monto", ascending=False)
            fig = px.bar(resumen, x="categoria", y="monto", title="Gastos por categoría")
            fig.update_layout(
                height=360,
                margin=dict(l=20, r=20, t=55, b=40),
                paper_bgcolor="white",
                plot_bgcolor="white",
                font=dict(color="#0F172A"),
                title_font=dict(color="#0F172A", size=20),
            )
            fig.update_xaxes(tickfont=dict(color="#334155"), title_font=dict(color="#334155"))
            fig.update_yaxes(tickfont=dict(color="#334155"), title_font=dict(color="#334155"), gridcolor="rgba(148,163,184,.25)")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def pagina_registrar(user_id, df):
    categorias_ingreso = obtener_categorias_usuario(user_id, "Ingreso")
    categorias_gasto = obtener_categorias_usuario(user_id, "Gasto")
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-badge">Registrar</div>
            <div class="hero-title">Guarda tu movimiento sin enredarte.</div>
            <div class="hero-sub">Zentix personal solo registra ingresos y gastos. Lo empresarial queda para BradaFin.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1.05, .95], gap="large")

    with col1:
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="home-color-title">
                <span class="home-color-icon">📝</span>
                <span style="color:#0F172A !important;">Formulario simple</span>
            </div>
            <div class="home-caption" style="color:#475569 !important;">
                Ingreso o gasto, monto, categoría y listo.
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_form_registro(user_id, categorias_ingreso, categorias_gasto, key_prefix="register")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        render_registro_por_texto(user_id, categorias_ingreso, categorias_gasto)

    st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
    section_header("Movimientos recientes", "Puedes revisar lo que acabas de guardar.")
    if df.empty:
        st.info("Todavía no hay movimientos.")
    else:
        show = df.sort_values("fecha", ascending=False).head(10).copy()
        show["fecha"] = show["fecha"].dt.strftime("%Y-%m-%d")
        st.dataframe(
            show[["fecha", "tipo", "categoria", "monto", "descripcion", "emocion"]],
            use_container_width=True,
            hide_index=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

def pagina_presupuesto(user_id, df, df_limites):
    df_mes = filtrar_mes(df)
    ingresos, gastos, saldo = resumen_movimientos(df_mes)
    presupuesto_total = obtener_presupuesto_total(df_limites)
    limites_visibles = obtener_limites_visibles(df_limites)
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-badge">Presupuesto</div>
            <div class="hero-title">Ponle techo al mes.</div>
            <div class="hero-sub">Un presupuesto simple evita que Zentix se vuelva complicado.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Presupuesto", money(presupuesto_total), "Límite mensual", "balance")
    with c2:
        kpi_card("Gastado", money(gastos), "Gasto del mes", "expense")
    with c3:
        restante = presupuesto_total - gastos if presupuesto_total > 0 else 0
        kpi_card("Disponible del presupuesto", money(restante), "Restante estimado", "saving" if restante >= 0 else "expense")

    if presupuesto_total > 0:
        st.progress(float(max(0, min(gastos / presupuesto_total, 1))))

    col1, col2 = st.columns([.95, 1.05], gap="large")
    with col1:
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        section_header("Presupuesto mensual", "Un solo número para controlar el mes.")
        nuevo_presupuesto = st.number_input("¿Cuánto quieres gastar máximo este mes?", min_value=0.0, step=10000.0, value=float(presupuesto_total or 0))
        if st.button("Guardar presupuesto", type="primary", use_container_width=True):
            ok, resp = guardar_limite_categoria(user_id, PRESUPUESTO_TOTAL_KEY, nuevo_presupuesto, True)
            if ok:
                st.success("Presupuesto guardado.")
                st.rerun()
            else:
                st.error(f"No pude guardar el presupuesto. Revisa que exista la tabla limites_categoria. Detalle: {resp}")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        section_header("Límites por categoría", "Opcional para tu plan pagado: más control sin más ruido.")
        cats = obtener_categorias_usuario(user_id, "Gasto")
        cat = st.selectbox("Categoría", cats)
        limite = st.number_input("Límite mensual para esa categoría", min_value=0.0, step=5000.0, key="limite_cat_input")
        if st.button("Guardar límite por categoría", type="primary", use_container_width=True):
            ok, resp = guardar_limite_categoria(user_id, cat, limite, True)
            if ok:
                st.success("Límite guardado.")
                st.rerun()
            else:
                st.error(f"No pude guardar el límite. Detalle: {resp}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
    section_header("Estado de límites", "Vas viendo cuánto llevas usado.")
    if limites_visibles.empty:
        st.info("Todavía no has creado límites por categoría.")
    else:
        for r in limites_visibles.itertuples():
            usado = float(df_mes[(df_mes["tipo"] == "Gasto") & (df_mes["categoria"] == r.categoria)]["monto"].sum()) if not df_mes.empty else 0.0
            ratio = usado / float(r.limite_mensual or 1) if float(r.limite_mensual or 0) > 0 else 0.0
            st.markdown(f"**{safe_text(r.categoria)}** · usado {money(usado)} de {money(r.limite_mensual)}")
            st.progress(float(max(0, min(ratio, 1))))
            if st.button(f"Eliminar límite · {r.categoria}", key=f"delete_limit_{r.categoria}"):
                eliminar_limite_categoria(user_id, r.categoria)
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def pagina_metas(user_id, df, meta_row):
    df_mes = filtrar_mes(df)
    ingresos, gastos, saldo = resumen_movimientos(df_mes)
    meta_actual = float((meta_row or {}).get("meta", 0) or 0)
    nombre_meta = str((meta_row or {}).get("nombre_meta", "") or "")
    progreso = saldo / meta_actual if meta_actual > 0 else 0
    faltante = max(0, meta_actual - max(saldo, 0))
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-badge">Metas</div>
            <div class="hero-title">Dale propósito a lo que queda.</div>
            <div class="hero-sub">Una meta sencilla ayuda a crear hábito, claridad y confianza.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Meta", money(meta_actual), nombre_meta or "Sin nombre", "saving")
    with c2:
        kpi_card("Disponible", money(saldo), "Saldo del mes", "balance")
    with c3:
        kpi_card("Faltante", money(faltante), fmt_pct(max(0, min(progreso, 1))) + " logrado", "expense" if faltante > 0 else "income")
    if meta_actual > 0:
        st.progress(float(max(0, min(progreso, 1))))

    col1, col2 = st.columns([.95, 1.05], gap="large")
    with col1:
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        section_header("Configurar meta", "Ejemplo: viaje, fondo de calma, computador, moto.")
        nombre = st.text_input("Nombre de la meta", value=nombre_meta, placeholder="Ej: Fondo de emergencia")
        valor = st.number_input("Valor objetivo", min_value=0.0, step=10000.0, value=float(meta_actual or 0))
        if st.button("Guardar meta", type="primary", use_container_width=True):
            ok, resp = guardar_meta(user_id, valor, nombre)
            if ok:
                st.success("Meta guardada.")
                st.rerun()
            else:
                st.error(f"No pude guardar la meta. Revisa la tabla ahorro_meta. Detalle: {resp}")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        section_header("Plan sugerido", "Una guía simple, no una obligación.")
        if meta_actual <= 0:
            st.info("Define una meta para que Zentix calcule avance y faltante.")
        elif faltante <= 0:
            st.success("Ya alcanzaste tu meta con el saldo visible del mes. Puedes subir la meta o crear una nueva.")
        else:
            aporte_4 = faltante / 4
            aporte_8 = faltante / 8
            st.markdown(f"- Si quieres acercarte en 4 semanas, reserva cerca de **{money(aporte_4)}** por semana.")
            st.markdown(f"- Si quieres hacerlo más suave en 8 semanas, reserva cerca de **{money(aporte_8)}** por semana.")
            top_cat, top_monto, _ = top_categoria_gasto(df_mes)
            if top_cat:
                st.markdown(f"- Tu mayor oportunidad puede estar en **{safe_text(top_cat)}**, donde llevas {money(top_monto)} este mes.")
        st.markdown("</div>", unsafe_allow_html=True)


def pagina_reporte(user_id, nombre, df, meta_row):
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-badge">Reporte</div>
            <div class="hero-title">Tu semana en limpio.</div>
            <div class="hero-sub">Pocas conclusiones, movimientos exportables y respaldo de datos.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    puntos = construir_reporte_semanal(df, meta_row)
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        section_header("Resumen semanal", "Lo importante sin muchas gráficas.")
        for p in puntos:
            st.markdown(f"<span class='pill pill-info'>• {safe_text(p)}</span><br><br>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        section_header("Exportar movimientos", "Respaldo para ti.")
        if df.empty:
            st.info("No hay movimientos para exportar.")
        else:
            archivo, mime, ext = exportar_excel(df)
            st.download_button(
                "Descargar movimientos",
                data=archivo,
                file_name=f"zentix_movimientos_{date.today().isoformat()}.{ext}",
                mime=mime,
                use_container_width=True,
            )
        if REPORTLAB_AVAILABLE:
            pdf = generar_pdf_reporte(nombre, df, meta_row)
            if pdf:
                st.download_button(
                    "Descargar reporte PDF",
                    data=pdf,
                    file_name=f"zentix_reporte_{date.today().isoformat()}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
        else:
            st.caption("Para PDF instala reportlab. El Excel/CSV funciona sin problema.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
    section_header("Editar movimientos", "Solo ingreso/gasto para mantener Zentix simple.")
    if df.empty:
        st.info("Todavía no hay movimientos.")
    else:
        df_sorted = df.sort_values("fecha", ascending=False).copy()
        labels = {}
        for _, r in df_sorted.iterrows():
            labels[str(r["id"])] = f"{pd.to_datetime(r['fecha']).date()} · {r['tipo']} · {r['categoria']} · {money(r['monto'])} · {r.get('descripcion','')}"
        selected = st.selectbox("Selecciona un movimiento", list(labels.keys()), format_func=lambda x: labels.get(str(x), str(x)))
        row = df_sorted[df_sorted["id"].astype(str) == str(selected)].iloc[0]
        with st.form("editar_movimiento_form"):
            col_a, col_b, col_c = st.columns([.8, .8, 1])
            with col_a:
                tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"], index=0 if row["tipo"] == "Ingreso" else 1)
            with col_b:
                fecha_edit = st.date_input("Fecha", value=pd.to_datetime(row["fecha"]).date())
            with col_c:
                monto = st.number_input("Monto", min_value=0.0, step=1000.0, value=float(row["monto"] or 0))
            cats = obtener_categorias_usuario(user_id, tipo)
            cat_actual = row["categoria"] if row["categoria"] in cats else (cats[0] if cats else "Otros")
            categoria = st.selectbox("Categoría", cats, index=cats.index(cat_actual) if cat_actual in cats else 0)
            descripcion = st.text_input("Descripción", value=str(row.get("descripcion", "") or ""))
            emocion = ""
            if tipo == "Gasto":
                emocion = st.selectbox("Emoción", EMOCIONES, index=EMOCIONES.index(row.get("emocion", "")) if row.get("emocion", "") in EMOCIONES else 0, format_func=lambda x: "No registrar" if x == "" else x)
            col_save, col_delete = st.columns(2)
            with col_save:
                save = st.form_submit_button("Guardar cambios", type="primary", use_container_width=True)
            with col_delete:
                delete = st.form_submit_button("Eliminar movimiento", use_container_width=True)
        if save:
            payload = {
                "tipo": tipo,
                "fecha": fecha_edit.isoformat(),
                "monto": float(monto or 0),
                "categoria": categoria,
                "descripcion": descripcion,
                "emocion": emocion,
                "actualizado_en": datetime.now().isoformat(),
            }
            ok, resp = actualizar_movimiento(selected, payload)
            if ok:
                st.success("Movimiento actualizado.")
                st.rerun()
            else:
                st.error(f"No pude actualizar: {resp}")
        if delete:
            ok, resp = eliminar_movimiento(selected)
            if ok:
                st.success("Movimiento eliminado.")
                st.rerun()
            else:
                st.error(f"No pude eliminar: {resp}")
    st.markdown("</div>", unsafe_allow_html=True)


def pagina_ia(user_id, nombre, df, meta_row, presupuesto_total, limites_visibles):
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-badge">Zentix IA</div>
            <div class="hero-title">Pregunta en lenguaje natural.</div>
            <div class="hero-sub">La IA aquí es sencilla: te ayuda a entender tu mes y registrar más fácil.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    permitido, usadas, limite, restantes, plan = puede_usar_ia(user_id)
    contexto = construir_contexto_ia(nombre, df, meta_row, presupuesto_total, limites_visibles)
    if "zentix_chat" not in st.session_state:
        st.session_state.zentix_chat = [{"role": "assistant", "content": "Hola. Soy Zentix IA. Puedo resumir tu mes, detectar alertas simples o ayudarte a registrar un movimiento."}]

    col_chat, col_side = st.columns([1.25, .75], gap="large")
    with col_chat:
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        section_header("Conversación", f"IA usada hoy: {usadas}/{limite}")
        for msg in st.session_state.zentix_chat[-12:]:
            cls = "chat-ai" if msg["role"] == "assistant" else "chat-user"
            role = "Zentix IA" if msg["role"] == "assistant" else "Tú"
            st.markdown(f"<div class='chat-bubble {cls}'><strong>{safe_text(role)}</strong><br>{safe_text(msg['content']).replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
        with st.form("ia_form"):
            pregunta = st.text_area("Pregunta", placeholder="Ej: Resume mi semana y dime qué debo corregir primero.", height=120)
            c1, c2 = st.columns([1, .7])
            with c1:
                send = st.form_submit_button("Enviar", type="primary", use_container_width=True)
            with c2:
                clean = st.form_submit_button("Limpiar", use_container_width=True)
        if clean:
            st.session_state.zentix_chat = [{"role": "assistant", "content": "Conversación limpiada. ¿Qué quieres revisar ahora?"}]
            st.rerun()
        if send and pregunta.strip():
            st.session_state.zentix_chat.append({"role": "user", "content": pregunta.strip()})
            if not permitido:
                respuesta = f"Ya usaste tu límite diario de IA ({limite}). Puedes seguir registrando movimientos y volver mañana."
            else:
                with st.spinner("Zentix está leyendo tu panorama..."):
                    respuesta = consultar_ia_zentix(pregunta.strip(), contexto, df)
                registrar_uso_ia(user_id)
            st.session_state.zentix_chat.append({"role": "assistant", "content": respuesta})
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_side:
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        section_header("Prompts útiles", "Copia uno o escríbelo a tu forma.")
        prompts = [
            "Resume mi mes en 3 frases.",
            "¿En qué categoría estoy gastando más?",
            "Dime una acción para ahorrar esta semana.",
            "Gasté 15000 en almuerzo, ¿cómo lo registro?",
            "¿Voy bien con mi presupuesto?",
        ]
        for p in prompts:
            st.markdown(f"<span class='pill pill-info'>{safe_text(p)}</span><br><br>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        section_header("Registro asistido", "Si quieres, registra desde texto aquí mismo.")
        texto = st.text_input("Ej: gasté 12000 en bus", key="ia_quick_register")
        if st.button("Registrar movimiento detectado", use_container_width=True):
            parsed = parsear_movimiento_texto(texto, obtener_categorias_usuario(user_id, "Ingreso"), obtener_categorias_usuario(user_id, "Gasto"))
            if parsed["monto"] <= 0:
                st.error("No detecté monto válido.")
            else:
                ok, resp = insertar_movimiento(user_id, parsed["tipo"], parsed["categoria"], parsed["monto"], parsed["descripcion"], date.today(), "")
                if ok:
                    st.success("Movimiento registrado.")
                    st.rerun()
                else:
                    st.error(f"No pude registrar: {resp}")
        st.markdown("</div>", unsafe_allow_html=True)


def pagina_perfil(user_id, user, nombre, df, meta_row):
    plan = obtener_plan_usuario(user_id)
    permitido, usadas, limite, restantes, _ = puede_usar_ia(user_id)
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-badge">Perfil</div>
            <div class="hero-title">Tu configuración personal.</div>
            <div class="hero-sub">Categorías, privacidad, plan y salida de sesión.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Plan", str(plan.get("plan", "free")).upper(), "Estado: " + str(plan.get("estado", "active")), "balance")
    with c2:
        kpi_card("IA hoy", f"{usadas}/{limite}", f"Restantes: {restantes}", "saving" if restantes > 0 else "expense")
    with c3:
        kpi_card("Movimientos", str(len(df.index)), "Solo ingresos y gastos", "income")

    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        section_header("Identidad", "Nombre visible dentro de Zentix.")
        nuevo_nombre = st.text_input("Nombre mostrado", value=nombre)
        if st.button("Guardar nombre", type="primary", use_container_width=True):
            try:
                perfil = obtener_perfil(user_id)
                if perfil:
                    supabase.table("perfiles_usuario").update({"nombre_mostrado": nuevo_nombre, "onboarding_completo": True}).eq("id", user_id).execute()
                else:
                    supabase.table("perfiles_usuario").insert({"id": user_id, "nombre_mostrado": nuevo_nombre, "onboarding_completo": True}).execute()
                clear_cached_data()
                st.success("Nombre actualizado.")
                st.rerun()
            except Exception as e:
                st.error(f"No pude actualizar: {e}")
        st.markdown(f"<div class='muted'>Correo: {safe_text(getattr(user, 'email', 'Sin correo'))}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        section_header("Privacidad y respaldo", "Zentix debe darte confianza.")
        st.markdown("- Tus datos se guardan por usuario en Supabase.")
        st.markdown("- Exporta tus movimientos desde Reporte.")
        st.markdown("- No conectamos bancos en esta versión simple.")
        st.markdown("- No se muestran funciones de negocio; eso queda para BradaFin.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        section_header("Categorías", "Personaliza ingresos y gastos.")
        tab_g, tab_i = st.tabs(["Gastos", "Ingresos"])
        with tab_g:
            st.write(", ".join(obtener_categorias_usuario(user_id, "Gasto")))
            nueva_g = st.text_input("Nueva categoría de gasto", key="nueva_cat_gasto")
            if st.button("Agregar gasto", use_container_width=True):
                ok, msg = agregar_categoria(user_id, "Gasto", nueva_g)
                st.success(msg) if ok else st.error(msg)
                if ok:
                    st.rerun()
        with tab_i:
            st.write(", ".join(obtener_categorias_usuario(user_id, "Ingreso")))
            nueva_i = st.text_input("Nueva categoría de ingreso", key="nueva_cat_ingreso")
            if st.button("Agregar ingreso", use_container_width=True):
                ok, msg = agregar_categoria(user_id, "Ingreso", nueva_i)
                st.success(msg) if ok else st.error(msg)
                if ok:
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        section_header("Sesión", "Cerrar sesión de forma segura.")
        if st.button("Cerrar sesión", use_container_width=True):
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            st.session_state.user = None
            st.session_state.pop("zentix_access_token", None)
            st.session_state.pop("zentix_refresh_token", None)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# APP PRINCIPAL
# ============================================================

def main():
    if "user" not in st.session_state:
        st.session_state.user = None
    if "pagina" not in st.session_state:
        st.session_state.pagina = "Inicio"

    if st.session_state.user is None:
        render_auth()
        st.stop()

    user = st.session_state.user
    user_id = getattr(user, "id", None)
    email = getattr(user, "email", "")
    if not user_id:
        st.error("No pude identificar el usuario activo. Cierra sesión y vuelve a entrar.")
        st.stop()

    perfil = obtener_perfil(user_id)
    categorias_gasto = obtener_categorias_usuario(user_id, "Gasto")
    categorias_ingreso = obtener_categorias_usuario(user_id, "Ingreso")
    onboarding_ok = bool((perfil or {}).get("onboarding_completo", False)) and categorias_gasto and categorias_ingreso
    if not onboarding_ok:
        render_onboarding(user_id, email)
        st.stop()

    nombre = str((perfil or {}).get("nombre_mostrado") or email.split("@")[0] or "Usuario Zentix").strip()
    df = obtener_movimientos(user_id)
    meta_row = obtener_meta(user_id)
    df_limites = obtener_limites_categoria_usuario(user_id)
    presupuesto_total = obtener_presupuesto_total(df_limites)
    limites_visibles = obtener_limites_visibles(df_limites)

    with st.sidebar:
        if ICON_PATH:
            st.image(str(ICON_PATH), width=86)
        st.markdown(f"### Zentix")
        st.caption(APP_TAGLINE)
        st.markdown(f"**{safe_text(nombre)}**")
        st.caption(email)
        st.divider()
        paginas = ["Inicio", "Registrar", "Presupuesto", "Metas", "Reporte", "Zentix IA", "Perfil"]
        for p in paginas:
            icon = {
                "Inicio": "🏠", "Registrar": "➕", "Presupuesto": "🧭", "Metas": "🎯",
                "Reporte": "📄", "Zentix IA": "🤖", "Perfil": "⚙️"
            }.get(p, "•")
            if st.button(f"{icon} {p}", key=f"nav_{p}", use_container_width=True, type="primary" if st.session_state.pagina == p else "secondary"):
                st.session_state.pagina = p
                st.rerun()
        st.divider()
        st.caption("Zentix personal · BradaFin queda para negocio.")

    pagina = st.session_state.pagina
    if pagina == "Inicio":
        pagina_inicio(user_id, nombre, df, meta_row, presupuesto_total, limites_visibles)
    elif pagina == "Registrar":
        pagina_registrar(user_id, df)
    elif pagina == "Presupuesto":
        pagina_presupuesto(user_id, df, df_limites)
    elif pagina == "Metas":
        pagina_metas(user_id, df, meta_row)
    elif pagina == "Reporte":
        pagina_reporte(user_id, nombre, df, meta_row)
    elif pagina == "Zentix IA":
        pagina_ia(user_id, nombre, df, meta_row, presupuesto_total, limites_visibles)
    elif pagina == "Perfil":
        pagina_perfil(user_id, user, nombre, df, meta_row)

    st.markdown("<div class='footer-note'>Zentix · finanzas personales simples. Control, hábito y claridad.</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
