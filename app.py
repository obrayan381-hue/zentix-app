import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from pathlib import Path
from supabase_config import supabase
from openai import OpenAI
import html

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

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)


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
    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        if icono_path.exists():
            st.image(str(icono_path), width=72)
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
    try:
        return supabase.table("movimientos").insert(payload).execute()
    except Exception:
        payload_fallback = dict(payload)
        payload_fallback.pop("emocion", None)
        return supabase.table("movimientos").insert(payload_fallback).execute()


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
    if df_base is None or df_base.empty:
        return {
            "gasto_semana_pct": 0.0,
            "ingreso_semana_pct": 0.0,
            "gasto_mes_pct": 0.0,
            "ingreso_mes_pct": 0.0
        }

    hoy = pd.Timestamp.now().normalize()
    inicio_semana = hoy - pd.Timedelta(days=hoy.weekday())
    inicio_semana_anterior = inicio_semana - pd.Timedelta(days=7)

    inicio_mes = hoy.replace(day=1)
    inicio_mes_anterior = (inicio_mes - pd.Timedelta(days=1)).replace(day=1)

    semana_actual = df_base[(df_base["fecha"] >= inicio_semana) & (df_base["fecha"] < inicio_semana + pd.Timedelta(days=7))]
    semana_anterior = df_base[(df_base["fecha"] >= inicio_semana_anterior) & (df_base["fecha"] < inicio_semana)]

    siguiente_mes = inicio_mes + pd.offsets.MonthBegin(1)
    mes_actual = df_base[(df_base["fecha"] >= inicio_mes) & (df_base["fecha"] < siguiente_mes)]
    mes_anterior = df_base[(df_base["fecha"] >= inicio_mes_anterior) & (df_base["fecha"] < inicio_mes)]

    def cambio_pct(actual, anterior):
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
    if df_base is None or df_base.empty:
        return {
            "positivas": ["Aún no hay semana suficiente para resumir."],
            "alertas": ["Registra algunos movimientos y Zentix activará tu resumen premium."],
            "accion": "Empieza por registrar tus gastos e ingresos principales de esta semana."
        }

    hoy = pd.Timestamp.now().normalize()
    inicio_semana = hoy - pd.Timedelta(days=hoy.weekday())
    inicio_semana_anterior = inicio_semana - pd.Timedelta(days=7)

    semana_actual = df_base[(df_base["fecha"] >= inicio_semana) & (df_base["fecha"] < inicio_semana + pd.Timedelta(days=7))]
    semana_anterior = df_base[(df_base["fecha"] >= inicio_semana_anterior) & (df_base["fecha"] < inicio_semana)]

    positivos = []
    alertas = []

    gasto_actual = semana_actual[semana_actual["tipo"] == "Gasto"]["monto"].sum()
    gasto_anterior = semana_anterior[semana_anterior["tipo"] == "Gasto"]["monto"].sum()
    ingreso_actual = semana_actual[semana_actual["tipo"] == "Ingreso"]["monto"].sum()

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
        alertas.append(f"Tus gastos subieron frente a la semana pasada en aproximadamente {money(gasto_actual - gasto_anterior)}.")
    if calcular_ratio_fin_semana(semana_actual) >= 0.45:
        alertas.append("Tus fines de semana concentran una gran parte de los gastos.")
    if meta_actual > 0 and ahorro_actual < meta_actual:
        alertas.append(f"Aún te faltan {money(meta_actual - max(ahorro_actual, 0))} para llegar a tu meta actual.")

    if not positivos:
        positivos = ["Tu panorama semanal está estable, pero aún necesita más datos para destacar avances claros."]
    if not alertas:
        alertas = ["No se detectan alertas críticas esta semana. Mantén consistencia en el registro."]

    if top_categoria and top_monto > 0:
        accion = f"Tu mejor siguiente paso es vigilar {top_categoria}. Si recortas alrededor de {money(top_monto * 0.15)}, notarás rápido el impacto."
    elif meta_actual > 0 and ahorro_actual < meta_actual:
        accion = f"Para acercarte a tu meta, prioriza conservar al menos {money((meta_actual - max(ahorro_actual, 0)) / 4)} por semana."
    else:
        accion = "Tu siguiente mejor acción es sostener el registro diario para que Zentix detecte tendencias más finas."

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
    bullets = "".join([f"<li style='margin-bottom:0.35rem;'>{item}</li>" for item in items])
    st.markdown(
        f"""
        <div class="soft-card">
            <div class="section-title">{title}</div>
            <div class="section-caption" style="margin-bottom:0.45rem;">
                <ul style="padding-left:1.05rem;margin:0;">{bullets}</ul>
            </div>
            <div class="tiny-muted">{foot}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def obtener_movimientos_recientes_para_ia(df_mes_actual, limite=8):
    if df_mes_actual is None or df_mes_actual.empty:
        return "No hay movimientos registrados este mes."

    vista = df_mes_actual.copy().sort_values("fecha", ascending=False).head(limite)

    lineas = []
    for _, row in vista.iterrows():
        fecha_txt = row["fecha"].strftime("%Y-%m-%d") if pd.notna(row["fecha"]) else "Sin fecha"
        tipo = row.get("tipo", "Sin tipo")
        categoria = row.get("categoria", "Sin categoría")
        monto = money(row.get("monto", 0))
        descripcion = row.get("descripcion", "") or "Sin descripción"
        lineas.append(f"- {fecha_txt} | {tipo} | {categoria} | {monto} | {descripcion}")

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

    movimientos_texto = obtener_movimientos_recientes_para_ia(df_mes_actual, limite=8)

    positivas = "\n".join([f"- {x}" for x in resumen_semanal_actual.get("positivas", [])]) or "- Sin positivas registradas."
    alertas = "\n".join([f"- {x}" for x in alertas_actuales]) or "- Sin alertas."
    patrones = "\n".join([f"- {x}" for x in patrones_actuales]) or "- Sin patrones."
    sugerencias = "\n".join([f"- {x}" for x in sugerencias_actuales]) or "- Sin sugerencias."
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
- Ingresos del mes: {money(total_ingresos)}
- Gastos del mes: {money(total_gastos)}
- Saldo disponible actual: {money(ahorro_actual)}
- Meta de ahorro actual: {money(meta_actual)}
- Nombre de la meta: {nombre_meta if nombre_meta else 'Sin nombre definido'}
- Categoría con mayor peso: {categoria_top_actual if categoria_top_actual else 'Sin datos'}
- Monto de categoría top: {money(monto_top_actual)}
- Último tipo de movimiento: {ultimo_tipo if ultimo_tipo else 'Sin movimientos'}
- Insight financiero actual: {insight_actual}
- Recomendación accionable: {recomendacion_actual}
- Comparativas: {comparativa_linea}

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

    tono_base = perfil_actual.get("titulo", "Perfil en construcción")

    if pagina == "Inicio":
        mensaje = f"{nombre}, ya entendí mejor tu panorama. Hoy te leo como: {tono_base.lower()}."
    elif pagina == "Registrar":
        mensaje = f"{nombre}, cada nuevo movimiento me ayuda a entender mejor tu comportamiento financiero y a personalizar tus recomendaciones."
    elif pagina == "Análisis":
        mensaje = f"{nombre}, aquí puedo explicarte patrones, comparar periodos y detectar señales que a simple vista se escapan."
    else:
        mensaje = f"{nombre}, tu meta no es solo un número. También puedo decirte qué ajuste te acercaría más rápido a ella."

    estado = (
        "🟢 Último movimiento: ingreso" if ultimo_tipo == "Ingreso"
        else "🔴 Último movimiento: gasto" if ultimo_tipo == "Gasto"
        else "⚪ Aún no hay movimientos"
    )

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
        "Inicio": f"Hola, {nombre}. Soy Zentix. Detecté un perfil tipo '{tono_base}' y puedo resumirte tu mes, tus alertas y tu mejor siguiente paso.",
        "Registrar": f"Hola, {nombre}. Si registras con constancia, puedo volverte recomendaciones mucho más personales.",
        "Análisis": f"Hola, {nombre}. Pregúntame por patrones, alertas, comparativas o categorías dominantes.",
        "Ahorro": f"Hola, {nombre}. Puedo ayudarte a leer tu progreso, cuánto te falta y qué ajuste haría más diferencia."
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

    col1, col2 = st.columns([1, 4])

    with col1:
        if avatar_path.exists():
            st.image(str(avatar_path), width=88)

    with col2:
        st.markdown('<div class="assistant-title">Avatar Zentix IA</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="assistant-text">{mensaje}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="assistant-mini">{estado}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="assistant-mini">Plan: {plan_actual.get("plan", "free").upper()} · IA hoy: {consultas_usadas}/{consultas_limite}</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="assistant-mini">Perfil: {perfil_actual.get("titulo", "Sin perfil")} · Disponible: {money(ahorro_actual)}</div>',
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
            "¿Qué emoción conviene vigilar en mis gastos?",
            "¿Cómo impacta este hábito en mi balance?",
            "Dame una recomendación para registrar mejor",
            "¿Qué categoría debería separar más?"
        ],
        "Análisis": [
            "Interpreta mis patrones de gasto",
            "Compárame esta semana con la pasada",
            "¿Qué categoría domina mi mes?",
            "Dame 3 insights personalizados"
        ],
        "Ahorro": [
            "Explícame mi progreso de ahorro",
            "¿Cuánto me falta realmente?",
            "¿Qué ajuste me acerca más rápido?",
            "Convierte mi meta en un plan corto"
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
        contenido = html.escape(item["content"]).replace("\\n", "<br>").replace("\n", "<br>")
        if item["role"] == "assistant":
            st.markdown(f'<div class="chat-bubble-ai"><strong>Zentix:</strong><br>{contenido}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble-user"><strong>Tú:</strong><br>{contenido}</div>', unsafe_allow_html=True)

    st.markdown('<div class="chat-input-label">Pregúntale a Zentix</div>', unsafe_allow_html=True)
    pregunta_manual = st.text_input(
        "Pregúntale a Zentix",
        key=input_key,
        label_visibility="collapsed",
        placeholder="Ej: ¿Cómo voy este mes? ¿Qué patrón estás viendo? ¿Cuál es mi siguiente mejor paso?"
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

    if not df_local.empty:
        df_local["fecha"] = pd.to_datetime(df_local["fecha"], errors="coerce")
        df_local["monto"] = pd.to_numeric(df_local["monto"], errors="coerce").fillna(0)

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


if st.session_state.user is None:
    with st.sidebar:
        col_sb_icon, col_sb_text = st.columns([1, 3])
        with col_sb_icon:
            if icono_path.exists():
                st.image(str(icono_path), width=40)
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
            st.image(str(avatar_path), width=170)

        st.caption("Zentix te acompaña a entender mejor tu panorama financiero.")

    with col_form:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Accede a tu cuenta</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-caption">Ingresa o crea tu cuenta para continuar en tu panel personal.</div>', unsafe_allow_html=True)

        choice = st.selectbox("Acceso", ["Login", "Registro"])
        email = st.text_input("Correo")
        password = st.text_input("Contraseña", type="password")

        if choice == "Registro":
            if st.button("Crear cuenta", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.success("Cuenta creada correctamente. Ahora inicia sesión.")
                except Exception as e:
                    st.error(f"Error al registrar: {e}")

        if choice == "Login":
            if st.button("Ingresar", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = res.user
                    st.success("Bienvenido a Zentix")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al iniciar sesión: {e}")

        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()



zentix_brand_header()

user_id = st.session_state.user.id
perfil = obtener_perfil(user_id)
nombre_usuario = perfil["nombre_mostrado"] if perfil and perfil.get("nombre_mostrado") else "usuario"

plan_usuario_actual = obtener_o_crear_plan_usuario(user_id)
_, consultas_usadas_hoy, consultas_limite_hoy, consultas_restantes_hoy, _ = puede_usar_ia(user_id)

paginas_disponibles = ["Inicio", "Registrar", "Análisis", "Ahorro"]

if "pagina" not in st.session_state or st.session_state.pagina not in paginas_disponibles:
    st.session_state.pagina = "Inicio"

with st.sidebar:
    col_sb_icon, col_sb_text = st.columns([1, 3])
    with col_sb_icon:
        if icono_path.exists():
            st.image(str(icono_path), width=40)
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
    <div class="section-title" style="margin-top:0.2rem;">Navegación rápida</div>
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

nav1, nav2, nav3, nav4 = st.columns(4)

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

pagina = st.session_state.pagina


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
    total_gastos = df_mes[df_mes["tipo"] == "Gasto"]["monto"].sum()
    total_ingresos = df_mes[df_mes["tipo"] == "Ingreso"]["monto"].sum()
else:
    total_gastos = 0
    total_ingresos = 0

saldo_disponible = total_ingresos - total_gastos
ahorro_actual = float(saldo_disponible)
insight_financiero = obtener_insight_financiero(total_ingresos, total_gastos, saldo_disponible, df_mes)
categoria_top, monto_top = obtener_categoria_top(df_mes)

nombre_meta_guardado = obtener_nombre_meta_guardado(user_id)
perfil_financiero = obtener_perfil_financiero(total_ingresos, total_gastos, saldo_disponible, df_mes)
comparativa_periodos = obtener_comparativa_periodos(df if not df.empty else pd.DataFrame())
resumen_semanal_premium = construir_resumen_semanal_premium(df if not df.empty else pd.DataFrame(), meta_guardada_global, ahorro_actual)
alertas_proactivas = generar_alertas_proactivas(df if not df.empty else pd.DataFrame(), df_mes, total_ingresos, total_gastos, saldo_disponible, meta_guardada_global)
recomendacion_accionable = generar_recomendacion_accionable(df_mes, total_ingresos, total_gastos, ahorro_actual, meta_guardada_global)
patrones_comportamiento = detectar_patrones_comportamiento(df if not df.empty else pd.DataFrame())
sugerencias_categoria = sugerir_categorias_inteligentes(df if not df.empty else pd.DataFrame())
insight_personalizado = construir_insight_personalizado(
    perfil_financiero,
    alertas_proactivas,
    recomendacion_accionable,
    patrones_comportamiento
)
_, consultas_usadas_hoy, consultas_limite_hoy, consultas_restantes_hoy, plan_usuario_actual = puede_usar_ia(user_id)


if pagina == "Inicio":
    zentix_hero(nombre_usuario, saldo_disponible, total_ingresos, total_gastos)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Ingresos del mes", money(total_ingresos), "Entradas registradas", "income")
    with col2:
        kpi_card("Gastos del mes", money(total_gastos), "Salidas registradas", "expense")
    with col3:
        kpi_card("Disponible", money(saldo_disponible), "Resultado neto actual", "balance")
    with col4:
        kpi_card("Meta de ahorro", money(meta_guardada_global), nombre_meta_guardado if nombre_meta_guardado else "Objetivo configurado", "saving")

    col_info, col_avatar = st.columns([1.15, 0.85])
    with col_info:
        section_header("Lectura inteligente del mes", "Zentix interpreta tu comportamiento, no solo tus cifras.")
        st.markdown(
            f"""
            <div class="soft-card">
                <div class="section-title">{perfil_financiero.get('titulo', 'Perfil en construcción')}</div>
                <div class="section-caption">{insight_personalizado}</div>
                <div class="tiny-muted">Microlectura: {perfil_financiero.get('microcopy', 'Sigue registrando para personalizar más.')}</div>
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
        render_list_card("Patrones + acción", patrones_comportamiento, recomendacion_accionable)

    section_header("Experiencia personalizada", "Comparativas inteligentes y sugerencias de organización.")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_list_card("Semana vs pasada", [f"Gasto: {money_delta(comparativa_periodos.get('gasto_semana_pct', 0.0))}", f"Ingreso: {money_delta(comparativa_periodos.get('ingreso_semana_pct', 0.0))}"], "Comparativa semanal.")
    with c2:
        render_list_card("Mes vs anterior", [f"Gasto: {money_delta(comparativa_periodos.get('gasto_mes_pct', 0.0))}", f"Ingreso: {money_delta(comparativa_periodos.get('ingreso_mes_pct', 0.0))}"], "Comparativa mensual.")
    with c3:
        render_list_card("Categorías inteligentes", sugerencias_categoria, "Ideas para que tus categorías te den más claridad.")
    with c4:
        render_list_card("Plan y IA", [f"Plan actual: {plan_usuario_actual.get('plan', 'free').upper()}", f"IA hoy: {consultas_usadas_hoy}/{consultas_limite_hoy}", f"Restantes: {consultas_restantes_hoy}"], "El plan Pro tendrá más IA, alertas y profundidad.")

    if not df_mes.empty:
        section_header("Visualización mensual", "Distribuciones del mes actual para ver proporciones y foco de gasto.")
        col_a, col_b = st.columns(2)

        with col_a:
            resumen_tipos = pd.DataFrame({
                "Tipo": ["Ingresos", "Gastos"],
                "Monto": [float(total_ingresos), float(total_gastos)]
            })
            fig_tipos = px.pie(
                resumen_tipos,
                values="Monto",
                names="Tipo",
                title="Ingresos vs gastos",
                hole=0.58,
                color="Tipo",
                color_discrete_map={"Ingresos": "#22C55E", "Gastos": "#EF4444"}
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
    section_header("Registrar movimiento", "Agrega ingresos y gastos con una experiencia más clara, emocional y visual.")

    col_form, col_side = st.columns([1.15, 0.85])

    with col_form:
        tipo = st.radio("Tipo de movimiento", ["Ingreso", "Gasto"], horizontal=True)

        if tipo == "Ingreso":
            st.markdown('<div class="pill-ingreso">Ingreso seleccionado</div>', unsafe_allow_html=True)
            categorias_disponibles = obtener_categorias_usuario(user_id, "Ingreso")
        else:
            st.markdown('<div class="pill-gasto">Gasto seleccionado</div>', unsafe_allow_html=True)
            categorias_disponibles = obtener_categorias_usuario(user_id, "Gasto")

        if not categorias_disponibles:
            st.warning(f"No tienes categorías de {tipo.lower()} configuradas. Completa tu onboarding o agrega categorías para registrar mejor.")
            categorias_disponibles = ["Sin categorías"]

        fecha_mov = st.date_input("Fecha", value=date.today())
        categoria = st.selectbox("Categoría", categorias_disponibles)
        monto = st.number_input("Monto", min_value=0.0, step=1000.0)
        descripcion = st.text_input("Descripción")

        emocion = ""
        if tipo == "Gasto":
            emocion = st.selectbox(
                "¿Cómo te sentías al hacer este gasto?",
                ["", "Tranquilidad", "Impulso", "Estrés", "Recompensa", "Urgencia", "Antojo"],
                format_func=lambda x: "No registrar emoción" if x == "" else x
            )

        col_btn_1, col_btn_2 = st.columns(2)
        with col_btn_1:
            if st.button("Guardar movimiento", use_container_width=True):
                if categoria.strip() == "Sin categorías":
                    st.error("Necesitas al menos una categoría válida para guardar el movimiento.")
                elif monto <= 0:
                    st.error("El monto debe ser mayor que 0.")
                else:
                    try:
                        payload = {
                            "usuario_id": user_id,
                            "fecha": datetime.combine(fecha_mov, datetime.min.time()).isoformat(),
                            "tipo": tipo,
                            "categoria": categoria.strip(),
                            "monto": float(monto),
                            "descripcion": descripcion.strip(),
                            "emocion": emocion if tipo == "Gasto" else None
                        }
                        insertar_movimiento_seguro(payload)
                        st.success("Movimiento guardado correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error guardando movimiento: {e}")

        with col_btn_2:
            if st.button("Resetear formulario", use_container_width=True):
                st.rerun()

    with col_side:
        color_valor = "#4ADE80" if tipo == "Ingreso" else "#F87171"
        st.markdown(
            f"""
            <div class="soft-card">
                <div class="section-title">Vista previa</div>
                <div class="section-caption">Así se interpreta el movimiento antes de guardar.</div>
                <div class="tiny-muted">Tipo</div>
                <div class="form-preview-value" style="color:{color_valor};">{tipo}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Categoría</div>
                <div style="font-weight:700;">{categoria}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Monto</div>
                <div style="font-weight:800;font-size:1.15rem;">{money(monto)}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Descripción</div>
                <div style="font-weight:600;">{descripcion if descripcion else 'Sin descripción'}</div>
                <div class="tiny-muted" style="margin-top:0.7rem;">Emoción</div>
                <div style="font-weight:600;">{emocion if emocion else 'No registrada'}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        render_avatar(pagina, nombre_usuario, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)

if pagina == "Análisis":
    zentix_hero(nombre_usuario, saldo_disponible, total_ingresos, total_gastos)
    section_header("Análisis del mes", "Explora movimientos, concentración por categoría, evolución diaria y lectura personalizada.")

    col_a, col_b = st.columns([1.15, 0.85])
    with col_a:
        if not df_mes.empty:
            vista_df = df_mes.copy().sort_values("fecha", ascending=False)
            vista_df["fecha"] = vista_df["fecha"].dt.strftime("%Y-%m-%d")
            columnas = ["fecha", "tipo", "categoria", "monto", "descripcion"]
            if "emocion" in vista_df.columns:
                columnas.append("emocion")
            st.dataframe(
                vista_df[columnas],
                use_container_width=True
            )
        else:
            empty_state("Todavía no hay datos", "Cuando registres movimientos este mes, aquí verás tablas y gráficos más útiles.")
    with col_b:
        render_avatar(pagina, nombre_usuario, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)

    section_header("Comparativas y patrones", "Así viene cambiando tu comportamiento financiero.")
    a1, a2, a3 = st.columns(3)
    with a1:
        render_list_card("Comparativa semanal", [f"Gasto: {money_delta(comparativa_periodos.get('gasto_semana_pct', 0.0))}", f"Ingreso: {money_delta(comparativa_periodos.get('ingreso_semana_pct', 0.0))}"], "Semana actual vs anterior.")
    with a2:
        render_list_card("Comparativa mensual", [f"Gasto: {money_delta(comparativa_periodos.get('gasto_mes_pct', 0.0))}", f"Ingreso: {money_delta(comparativa_periodos.get('ingreso_mes_pct', 0.0))}"], "Mes actual vs anterior.")
    with a3:
        render_list_card("Patrones detectados", patrones_comportamiento, "Zentix busca hábitos que explican tu comportamiento.")

    section_header("Insights personalizados", "Tu perfil, tus alertas y tus mejores mejoras.")
    b1, b2 = st.columns(2)
    with b1:
        render_list_card("Perfil financiero", [perfil_financiero.get("descripcion", "Sin perfil disponible."), perfil_financiero.get("microcopy", "")], "Identidad financiera detectada automáticamente.")
    with b2:
        render_list_card("Alertas + categorías", alertas_proactivas + sugerencias_categoria, recomendacion_accionable)

    if not df_mes.empty:
        resumen = (
            df_mes.groupby("categoria")["monto"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )

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
                color_discrete_map={"Ingreso": "#22C55E", "Gasto": "#EF4444"}
            )
            aplicar_estilo_plotly(fig_line, height=390)
            st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No hay datos este mes.")

if pagina == "Ahorro":
    zentix_hero(nombre_usuario, saldo_disponible, total_ingresos, total_gastos)
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
        placeholder="Ej: Viaje a Medellín, Fondo de calma, Moto"
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
                <div class="tiny-muted" style="margin-top:0.7rem;">Plan sugerido</div>
                <div style="font-weight:700;line-height:1.5;">{recomendacion_accionable}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        render_avatar(pagina, nombre_usuario, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)
