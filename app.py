import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
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

OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


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
        min-height: 56px;
        border-radius: 20px;
        border: 1px solid rgba(148, 163, 184, 0.20);
        background:
            radial-gradient(circle at top left, rgba(125, 211, 252, 0.18), transparent 34%),
            radial-gradient(circle at bottom right, rgba(139, 92, 246, 0.14), transparent 28%),
            linear-gradient(135deg, rgba(10,18,32,0.98), rgba(15,23,42,0.98));
        color: #F8FAFC;
        font-weight: 800;
        font-size: 1rem;
        letter-spacing: 0.01em;
        padding: 0.95rem 1.15rem;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.05),
            0 12px 28px rgba(0,0,0,0.30);
        backdrop-filter: blur(10px);
        transition:
            transform 0.18s ease,
            box-shadow 0.18s ease,
            border-color 0.18s ease,
            background 0.18s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        border-color: rgba(96, 165, 250, 0.42);
        background:
            radial-gradient(circle at top left, rgba(125, 211, 252, 0.24), transparent 34%),
            radial-gradient(circle at bottom right, rgba(167, 139, 250, 0.18), transparent 28%),
            linear-gradient(135deg, rgba(13,22,38,1), rgba(20,28,48,1));
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.06),
            0 16px 34px rgba(37,99,235,0.16);
    }

    .stButton > button:active {
        transform: translateY(0) scale(0.985);
    }

    .stButton > button:focus:not(:active) {
        border-color: rgba(125, 211, 252, 0.50);
        box-shadow:
            0 0 0 1px rgba(125, 211, 252, 0.22),
            0 14px 30px rgba(37,99,235,0.14);
    }

    .stButton > button[kind="secondary"] {
        background:
            radial-gradient(circle at top left, rgba(59,130,246,0.10), transparent 30%),
            linear-gradient(135deg, rgba(17,24,39,0.98), rgba(15,23,42,0.98));
        border: 1px solid rgba(148, 163, 184, 0.18);
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
    insight_actual = globals().get("insight_financiero", "Sin insight disponible.")

    movimientos_texto = obtener_movimientos_recientes_para_ia(df_mes_actual, limite=8)

    return f"""
CONTEXTO DE ZENTIX
- Página actual: {pagina}
- Usuario: {nombre}
- Ingresos del mes: {money(total_ingresos)}
- Gastos del mes: {money(total_gastos)}
- Saldo disponible actual: {money(ahorro_actual)}
- Meta de ahorro actual: {money(meta_actual)}
- Categoría con mayor peso: {categoria_top_actual if categoria_top_actual else 'Sin datos'}
- Monto de categoría top: {money(monto_top_actual)}
- Último tipo de movimiento: {ultimo_tipo if ultimo_tipo else 'Sin movimientos'}
- Insight financiero actual: {insight_actual}

MOVIMIENTOS RECIENTES DEL MES
{movimientos_texto}
""".strip()


def consultar_ia_zentix(pregunta, contexto):
    if not openai_client:
        return "La IA todavía no está activa. Agrega OPENAI_API_KEY en los secrets de Streamlit Cloud para habilitar al avatar."

    try:
        response = openai_client.responses.create(
            model="gpt-5.4",
            instructions=(
                "Eres Avatar Zentix, un copiloto financiero dentro de una app de finanzas personales. "
                "Hablas siempre en español. "
                "Tu tono es premium, claro, útil y cercano. "
                "Usa únicamente el contexto recibido. "
                "Nunca inventes cifras, categorías o movimientos. "
                "Si algo no está en el contexto, dilo con honestidad. "
                "No des asesoría financiera profesional, legal ni tributaria. "
                "Responde de forma breve pero valiosa, idealmente entre 4 y 8 líneas. "
                "Cuando corresponda, entrega viñetas cortas. "
                "Cierra con una recomendación concreta."
            ),
            input=f"{contexto}\n\nPREGUNTA DEL USUARIO:\n{pregunta}"
        )

        texto = (response.output_text or "").strip()

        if not texto:
            return "No pude generar una respuesta útil en este momento."

        return texto

    except Exception as e:
        return f"No pude responder ahora mismo. Error: {e}"


def render_avatar(pagina, nombre, total_ingresos, total_gastos, ahorro_actual, ultimo_tipo):
    if pagina == "Inicio":
        mensaje = f"{nombre}, tu panorama mensual ya está listo. Ahora también puedes preguntarme por tus números."
    elif pagina == "Registrar":
        mensaje = f"{nombre}, puedo ayudarte a interpretar lo que registras y darte contexto financiero al instante."
    elif pagina == "Análisis":
        mensaje = f"{nombre}, aquí puedo explicarte patrones, concentración por categoría y alertas simples."
    else:
        mensaje = f"{nombre}, también puedo ayudarte a leer tu meta de ahorro contra tu saldo actual."

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
        "Inicio": f"Hola, {nombre}. Puedo resumirte tu mes, detectar alertas y decirte en qué estás gastando más.",
        "Registrar": f"Hola, {nombre}. Puedo ayudarte a revisar el impacto de tus registros en tu panorama financiero.",
        "Análisis": f"Hola, {nombre}. Pregúntame por tendencias, categorías dominantes o señales de gasto.",
        "Ahorro": f"Hola, {nombre}. Puedo ayudarte a leer tu progreso de ahorro y qué te falta para tu meta."
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
            f'<div class="assistant-mini">Ingresos: {money(total_ingresos)} · Gastos: {money(total_gastos)} · Disponible: {money(ahorro_actual)}</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="quick-action-note">Acciones rápidas</div>', unsafe_allow_html=True)

    preguntas_rapidas = {
        "Inicio": [
            "Resúmeme mi mes en 3 puntos",
            "¿En qué estoy gastando más?",
            "¿Ves alguna alerta este mes?",
            "¿Cómo voy frente a mi ahorro?"
        ],
        "Registrar": [
            "¿Qué debería vigilar al registrar gastos?",
            "¿Cómo impactan mis gastos en mi balance?",
            "Dame una recomendación rápida para registrar mejor",
            "¿Qué categoría conviene vigilar más?"
        ],
        "Análisis": [
            "Interpreta mis patrones de gasto",
            "¿Cuál es mi categoría más pesada?",
            "¿Qué tendencia ves este mes?",
            "Dame 3 insights claros"
        ],
        "Ahorro": [
            "Explícame mi progreso de ahorro",
            "¿Cuánto me falta realmente?",
            "¿Qué ajuste simple me recomiendas?",
            "Dame un plan corto para acercarme a mi meta"
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
        placeholder="Ej: ¿Cómo voy este mes? ¿Dónde debería ajustar gastos?"
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

        with st.spinner("Zentix está analizando tu información..."):
            respuesta = consultar_ia_zentix(pregunta_final, contexto_ia)

        st.session_state[chat_key].append({"role": "assistant", "content": respuesta})
        st.session_state[clear_key] = True
        st.rerun()

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

nav1, nav2, nav3, nav4 = st.columns(4)

with nav1:
    if st.button("Inicio", key="nav_inicio_top", use_container_width=True):
        st.session_state.pagina = "Inicio"
        st.rerun()

with nav2:
    if st.button("Registrar", key="nav_registrar_top", use_container_width=True):
        st.session_state.pagina = "Registrar"
        st.rerun()

with nav3:
    if st.button("Análisis", key="nav_analisis_top", use_container_width=True):
        st.session_state.pagina = "Análisis"
        st.rerun()

with nav4:
    if st.button("Ahorro", key="nav_ahorro_top", use_container_width=True):
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
        kpi_card("Meta de ahorro", money(meta_guardada_global), "Objetivo configurado", "saving")

    col_info, col_avatar = st.columns([1.2, 0.8])
    with col_info:
        section_header("Lectura rápida del mes", "Una interpretación simple para tomar mejores decisiones.")
        st.markdown(
            f"""
            <div class="soft-card">
                <div class="section-title">Salud financiera</div>
                <div class="section-caption">{insight_financiero}</div>
                <div class="tiny-muted">Categoría más representativa: {categoria_top if categoria_top else 'Sin datos'} {f'· {money(monto_top)}' if categoria_top else ''}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_avatar:
        render_avatar(pagina, nombre_usuario, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)

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
            "Empieza en Registrar para construir tu dashboard. Apenas ingreses datos, aquí aparecerán tus indicadores y gráficos."
        )


if pagina == "Registrar":
    zentix_hero(nombre_usuario, saldo_disponible, total_ingresos, total_gastos)
    section_header("Registrar movimiento", "Agrega ingresos y gastos con una experiencia más clara y visual.")

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

        col_btn_1, col_btn_2 = st.columns(2)
        with col_btn_1:
            if st.button("Guardar movimiento", use_container_width=True):
                if categoria.strip() == "Sin categorías":
                    st.error("Necesitas al menos una categoría válida para guardar el movimiento.")
                elif monto <= 0:
                    st.error("El monto debe ser mayor que 0.")
                else:
                    try:
                        supabase.table("movimientos").insert({
                            "usuario_id": user_id,
                            "fecha": datetime.combine(fecha_mov, datetime.min.time()).isoformat(),
                            "tipo": tipo,
                            "categoria": categoria.strip(),
                            "monto": float(monto),
                            "descripcion": descripcion.strip()
                        }).execute()
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
            </div>
            """,
            unsafe_allow_html=True
        )
        render_avatar(pagina, nombre_usuario, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)


if pagina == "Análisis":
    zentix_hero(nombre_usuario, saldo_disponible, total_ingresos, total_gastos)
    section_header("Análisis del mes", "Explora movimientos, concentración por categoría y evolución diaria.")

    col_a, col_b = st.columns([1.15, 0.85])
    with col_a:
        if not df_mes.empty:
            vista_df = df_mes.copy().sort_values("fecha", ascending=False)
            vista_df["fecha"] = vista_df["fecha"].dt.strftime("%Y-%m-%d")
            st.dataframe(
                vista_df[["fecha", "tipo", "categoria", "monto", "descripcion"]],
                use_container_width=True
            )
        else:
            empty_state("Todavía no hay datos", "Cuando registres movimientos este mes, aquí verás tablas y gráficos más útiles.")
    with col_b:
        render_avatar(pagina, nombre_usuario, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)

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
    section_header("Plan de ahorro", "Conecta tu meta con tu saldo disponible actual.")

    try:
        meta_result = obtener_meta(user_id)
        meta_guardada = float(meta_result["meta"]) if meta_result else 0.0
    except Exception as e:
        st.error(f"Error cargando meta de ahorro: {e}")
        meta_result = None
        meta_guardada = 0.0

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
        kpi_card("Meta definida", money(meta), "Objetivo configurado", "saving")
    with col_k3:
        kpi_card("Faltante", money(faltante), "Lo que resta por cubrir", "expense" if faltante > 0 else "income")

    col_meta1, col_meta2 = st.columns([1.1, 0.9])

    with col_meta1:
        col_btn_1, col_btn_2 = st.columns(2)

        with col_btn_1:
            if st.button("Guardar meta", use_container_width=True):
                try:
                    if meta_result:
                        supabase.table("ahorro_meta").update({
                            "meta": float(meta),
                            "actualizado_en": datetime.now().isoformat()
                        }).eq("usuario_id", user_id).execute()
                    else:
                        supabase.table("ahorro_meta").insert({
                            "usuario_id": user_id,
                            "meta": float(meta),
                            "actualizado_en": datetime.now().isoformat()
                        }).execute()

                    st.success("Meta guardada correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error guardando meta: {e}")

        with col_btn_2:
            if st.button("Limpiar meta", use_container_width=True):
                try:
                    supabase.table("ahorro_meta").delete().eq("usuario_id", user_id).execute()
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
                <div class="section-title">Lectura de tu objetivo</div>
                <div class="section-caption">
                    {("Tu saldo ya cubre la meta actual. Puedes subir el objetivo o mantenerlo." if float(meta) > 0 and ahorro_actual >= float(meta)
                    else "Tu meta aún no está cubierta. Usa esta referencia para ajustar tu ritmo de gasto y ahorro." if float(meta) > 0
                    else "Todavía no has definido una meta. Zentix puede acompañarte mejor cuando fijes un objetivo claro.")}
                </div>
                <div class="tiny-muted">Progreso actual</div>
                <div class="form-preview-value">{round(min(progreso, 1.0) * 100, 1) if float(meta) > 0 else 0}%</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        render_avatar(pagina, nombre_usuario, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)

