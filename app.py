import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from pathlib import Path
from supabase_config import supabase

st.set_page_config(page_title="Zentix", layout="wide")

# ---------------- ESTILO ----------------
st.markdown("""
    <style>
    body { background-color: #0D0D0D; color: white; }
    .stApp { background-color: #0D0D0D; }
    .stButton>button {
        background-color: #00C896;
        color: white;
        border-radius: 10px;
        font-weight: bold;
        border: none;
    }
    .stTextInput>div>div>input,
    .stNumberInput input,
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #1A1A1A !important;
        color: white !important;
    }
    .metric-card {
        background: #151515;
        padding: 18px;
        border-radius: 16px;
        border: 1px solid #2a2a2a;
        margin-bottom: 10px;
    }
    .saldo-verde {
        color: #00C896;
        font-weight: bold;
        font-size: 24px;
    }
    .saldo-rojo {
        color: #FF4B4B;
        font-weight: bold;
        font-size: 24px;
    }
    .bot-card {
        background: linear-gradient(135deg, #0f172a, #111827);
        border: 1px solid #1f2937;
        border-radius: 18px;
        padding: 16px;
        margin-top: 8px;
    }
    .bot-title {
        color: #00C896;
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
logo_path = Path("logo.png")

col_logo, col_title = st.columns([1, 5])
with col_logo:
    if logo_path.exists():
        st.image(str(logo_path), width=110)
    else:
        st.warning("Logo no encontrado")

with col_title:
    st.markdown("## ZENTIX")
    st.caption("Control inteligente de tu dinero")

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- FUNCIONES ----------------
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

def obtener_mensaje_ahorro(meta, ingresos, gastos):
    disponible = ingresos - gastos
    faltante = meta - max(disponible, 0)

    if meta <= 0:
        return "Define una meta clara para empezar a medir tu avance.", "info"

    if disponible <= 0:
        return "Tus gastos ya consumieron todo tu ingreso disponible. Conviene frenar un poco antes de seguir con tu meta.", "error"

    if disponible >= meta:
        return "Vas muy bien. Con lo que te queda disponible ya puedes cumplir tu meta de ahorro.", "success"

    porcentaje = disponible / meta

    if porcentaje >= 0.75:
        return "Estás cerca de lograr tu meta. Mantén controlados tus gastos para no perder el ritmo.", "info"
    elif porcentaje >= 0.4:
        return "Vas avanzando, pero tus gastos todavía se están comiendo una parte importante de tus ingresos.", "warning"
    else:
        return "Tu meta todavía está lejos. Conviene reducir gastos para que el ahorro no se te escape.", "warning"

def render_bot(pagina, total_ingresos, total_gastos, ahorro_actual, ultimo_tipo):
    if pagina == "Inicio":
        mensaje = "Estoy revisando tu panorama financiero. Mira tus métricas clave y detecta si tus gastos ya están presionando demasiado tu ingreso."
    elif pagina == "Registrar":
        mensaje = "Registra cada movimiento apenas ocurra. Mientras más completo esté tu historial, mejores decisiones vas a tomar."
    elif pagina == "Análisis":
        mensaje = "Aquí puedes identificar en qué categoría se te está yendo más dinero. Esa es la clave para mejorar."
    else:
        mensaje = "El ahorro no es solo lo que quieres guardar, sino lo que realmente logras conservar después de gastar."

    estado = "🟢 Último movimiento: ingreso" if ultimo_tipo == "Ingreso" else "🔴 Último movimiento: gasto" if ultimo_tipo == "Gasto" else "⚪ Aún no hay movimientos"
    resumen = f"Ingresos: {total_ingresos:,.0f} | Gastos: {total_gastos:,.0f} | Disponible: {ahorro_actual:,.0f}"

    st.markdown(f"""
        <div class="bot-card">
            <div class="bot-title">🤖 Zentix Bot</div>
            <div style="margin-bottom:8px;">{mensaje}</div>
            <div style="margin-bottom:4px;">{estado}</div>
            <div style="color:#cbd5e1;">{resumen}</div>
        </div>
    """, unsafe_allow_html=True)

# ---------------- AUTH ----------------
if st.session_state.user is None:
    menu_auth = ["Login", "Registro"]
    choice = st.sidebar.selectbox("Acceso", menu_auth)

    email = st.text_input("Correo")
    password = st.text_input("Contraseña", type="password")

    if choice == "Registro":
        if st.button("Crear cuenta"):
            try:
                supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })
                st.success("Cuenta creada correctamente")
            except Exception as e:
                st.error(f"Error al registrar: {e}")

    elif choice == "Login":
        if st.button("Ingresar"):
            try:
                res = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.session_state.user = res.user
                st.success("Bienvenido a Zentix")
                st.rerun()
            except Exception as e:
                st.error(f"Error al iniciar sesión: {e}")

    st.stop()

# ---------------- SESIÓN INICIADA ----------------
user_id = st.session_state.user.id

with st.sidebar:
    st.success("Sesión iniciada")
    if st.button("Cerrar sesión"):
        st.session_state.user = None
        st.rerun()

menu = ["Inicio", "Registrar", "Análisis", "Ahorro"]
pagina = st.sidebar.selectbox("Menú", menu)

# ---------------- CARGAR DATOS ----------------
try:
    df = obtener_movimientos(user_id)
except Exception as e:
    st.error(f"Error cargando movimientos: {e}")
    st.stop()

if not df.empty:
    mes_actual = pd.Timestamp.now().month
    anio_actual = pd.Timestamp.now().year
    df_mes = df[(df["fecha"].dt.month == mes_actual) & (df["fecha"].dt.year == anio_actual)].copy()
    ultimo_movimiento = df.iloc[0]
    ultimo_tipo = ultimo_movimiento["tipo"]
else:
    df_mes = pd.DataFrame(columns=["usuario_id", "fecha", "tipo", "categoria", "monto", "descripcion"])
    ultimo_tipo = None

# ---------------- MÉTRICAS ----------------
if not df_mes.empty:
    total_gastos = df_mes[df_mes["tipo"] == "Gasto"]["monto"].sum()
    total_ingresos = df_mes[df_mes["tipo"] == "Ingreso"]["monto"].sum()
else:
    total_gastos = 0
    total_ingresos = 0

saldo_disponible = total_ingresos - total_gastos

# ---------------- INICIO ----------------
if pagina == "Inicio":
    st.subheader("📊 Resumen")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💸 Gastos", f"{total_gastos:,.0f}")
    with col2:
        st.metric("💰 Ingresos", f"{total_ingresos:,.0f}")
    with col3:
        color_class = "saldo-verde" if ultimo_tipo == "Ingreso" else "saldo-rojo" if ultimo_tipo == "Gasto" else "saldo-verde"
        st.markdown(f"""
            <div class="metric-card">
                <div style="font-size:14px;color:#9ca3af;">Disponible</div>
                <div class="{color_class}">{saldo_disponible:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    render_bot(pagina, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)

    if not df_mes.empty:
        col_a, col_b = st.columns([1, 1])

        with col_a:
            resumen_tipos = pd.DataFrame({
                "Tipo": ["Ingresos", "Gastos"],
                "Monto": [float(total_ingresos), float(total_gastos)]
            })
            fig_tipos = px.pie(
                resumen_tipos,
                values="Monto",
                names="Tipo",
                title="Distribución de ingresos vs gastos",
                hole=0.45
            )
            fig_tipos.update_layout(
                paper_bgcolor="#0D0D0D",
                plot_bgcolor="#0D0D0D",
                font_color="white"
            )
            st.plotly_chart(fig_tipos, use_container_width=True)

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
                title="Gastos e ingresos por categoría"
            )
            fig_cat.update_layout(
                paper_bgcolor="#0D0D0D",
                plot_bgcolor="#0D0D0D",
                font_color="white"
            )
            st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info("Aún no hay movimientos este mes.")

# ---------------- REGISTRAR ----------------
if pagina == "Registrar":
    st.subheader("➕ Agregar movimiento")

    fecha = st.date_input("Fecha", value=date.today())
    tipo = st.selectbox("Tipo", ["Gasto", "Ingreso"])
    categoria = st.text_input("Categoría")
    monto = st.number_input("Monto", min_value=0.0, step=1000.0)
    descripcion = st.text_input("Descripción")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Guardar"):
            if not categoria.strip():
                st.error("La categoría es obligatoria")
            elif monto <= 0:
                st.error("El monto debe ser mayor que 0")
            else:
                try:
                    supabase.table("movimientos").insert({
                        "usuario_id": user_id,
                        "fecha": datetime.combine(fecha, datetime.min.time()).isoformat(),
                        "tipo": tipo,
                        "categoria": categoria.strip(),
                        "monto": float(monto),
                        "descripcion": descripcion.strip()
                    }).execute()
                    st.success("Guardado correctamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error guardando movimiento: {e}")

    with col2:
        if st.button("🗑️ Reset"):
            st.rerun()

    render_bot(pagina, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)

# ---------------- ANÁLISIS ----------------
if pagina == "Análisis":
    st.subheader("📈 Análisis")

    render_bot(pagina, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)

    if not df_mes.empty:
        st.dataframe(df_mes, use_container_width=True)

        resumen = (
            df_mes.groupby("categoria")["monto"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )

        fig_bar = px.bar(
            resumen,
            x="categoria",
            y="monto",
            title="Movimientos por categoría",
            text_auto=True
        )
        fig_bar.update_layout(
            paper_bgcolor="#0D0D0D",
            plot_bgcolor="#0D0D0D",
            font_color="white"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No hay datos este mes")

# ---------------- AHORRO ----------------
if pagina == "Ahorro":
    st.subheader("🎯 Plan de ahorro")

    meta = st.number_input("¿Cuánto quieres ahorrar?", min_value=0.0, step=1000.0)

    ahorro_actual = float(saldo_disponible)
    faltante = max(0.0, meta - max(ahorro_actual, 0))

    st.write(f"💰 Dinero disponible actual: {ahorro_actual:,.0f}")
    st.write(f"🎯 Meta de ahorro: {meta:,.0f}")

    if meta > 0:
        progreso = max(0.0, ahorro_actual / meta) if meta > 0 else 0
        st.progress(min(progreso, 1.0))

        if ahorro_actual >= meta:
            st.success("Vas excelente: con tu disponible actual ya alcanzas la meta de ahorro.")
        else:
            st.info(f"Te faltan {faltante:,.0f} para cumplir tu meta.")

        mensaje, tipo_msg = obtener_mensaje_ahorro(meta, total_ingresos, total_gastos)

        if tipo_msg == "success":
            st.success(mensaje)
        elif tipo_msg == "warning":
            st.warning(mensaje)
        elif tipo_msg == "error":
            st.error(mensaje)
        else:
            st.info(mensaje)

    else:
        st.info("Define una meta para comenzar")

    render_bot(pagina, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)
