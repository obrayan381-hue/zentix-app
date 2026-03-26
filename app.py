import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from pathlib import Path
from supabase_config import supabase

st.set_page_config(page_title="Zentix", layout="wide")

# ---------------- CONFIG BASE ----------------
DEFAULT_GASTOS = [
    "Comida", "Transporte", "Arriendo", "Servicios", "Salud",
    "Educación", "Compras", "Ocio", "Deudas", "Otros"
]

DEFAULT_INGRESOS = [
    "Salario", "Freelance", "Ventas", "Inversiones", "Regalos", "Otros"
]

icono_path = Path("icono_zentix.png")
avatar_path = Path("avatar_zentix.png")

# ---------------- ESTILO ----------------
st.markdown("""
    <style>
    body { background-color: #0D0D0D; color: white; }
    .stApp { background-color: #0D0D0D; }

    .stButton>button {
        background: linear-gradient(90deg, #2563EB, #7C3AED);
        color: white;
        border-radius: 12px;
        font-weight: 700;
        border: none;
    }

    .stTextInput>div>div>input,
    .stNumberInput input,
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        background-color: #151515 !important;
        color: white !important;
        border-radius: 12px !important;
    }

    .brand-wrap {
        display: flex;
        align-items: center;
        gap: 18px;
        margin-bottom: 18px;
    }

    .brand-title {
        font-size: 34px;
        font-weight: 800;
        color: white;
        margin: 0;
        letter-spacing: 1px;
    }

    .brand-subtitle {
        color: #94A3B8;
        margin-top: 4px;
        font-size: 14px;
    }

    .metric-card {
        background: #151515;
        padding: 18px;
        border-radius: 16px;
        border: 1px solid #2a2a2a;
        margin-bottom: 10px;
    }

    .saldo-verde {
        color: #22C55E;
        font-weight: bold;
        font-size: 24px;
    }

    .saldo-rojo {
        color: #EF4444;
        font-weight: bold;
        font-size: 24px;
    }

    .avatar-card {
        background: linear-gradient(135deg, rgba(37,99,235,0.16), rgba(124,58,237,0.18));
        border: 1px solid rgba(124,58,237,0.28);
        border-radius: 24px;
        padding: 18px;
        margin-top: 12px;
        box-shadow: 0 12px 35px rgba(37,99,235,0.16);
        backdrop-filter: blur(10px);
    }

    .avatar-title {
        font-size: 20px;
        font-weight: 800;
        color: #C4B5FD;
        margin-bottom: 6px;
    }

    .avatar-text {
        color: #E5E7EB;
        font-size: 15px;
        line-height: 1.5;
    }

    .avatar-mini {
        color: #94A3B8;
        font-size: 13px;
        margin-top: 8px;
    }

    .pill-ingreso {
        display: inline-block;
        padding: 8px 14px;
        border-radius: 999px;
        background: rgba(34,197,94,0.15);
        border: 1px solid rgba(34,197,94,0.35);
        color: #22C55E;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .pill-gasto {
        display: inline-block;
        padding: 8px 14px;
        border-radius: 999px;
        background: rgba(239,68,68,0.15);
        border: 1px solid rgba(239,68,68,0.35);
        color: #EF4444;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .section-card {
        background: #101010;
        border: 1px solid #222;
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
col_logo, col_title = st.columns([1, 6])

with col_logo:
    if icono_path.exists():
        st.image(str(icono_path), width=82)

with col_title:
    st.markdown("## ZENTIX")
    st.caption("Finanzas inteligentes con estilo fintech")

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

def render_avatar(pagina, nombre, total_ingresos, total_gastos, ahorro_actual, ultimo_tipo):
    if pagina == "Inicio":
        mensaje = f"{nombre}, este es tu panorama financiero actual. Vigila si tus gastos están subiendo demasiado."
    elif pagina == "Registrar":
        mensaje = f"{nombre}, registra bien cada movimiento. Así Zentix podrá ayudarte mejor."
    elif pagina == "Análisis":
        mensaje = f"{nombre}, aquí podrás detectar patrones y entender en qué se te va más dinero."
    else:
        mensaje = f"{nombre}, ahorrar es conservar lo que queda después de gastar, no solo proponértelo."

    estado = "🟢 Último movimiento: ingreso" if ultimo_tipo == "Ingreso" else "🔴 Último movimiento: gasto" if ultimo_tipo == "Gasto" else "⚪ Aún no hay movimientos"

    st.markdown('<div class="avatar-card">', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 5])

    with col1:
        if avatar_path.exists():
            st.image(str(avatar_path), width=95)

    with col2:
        st.markdown('<div class="avatar-title">Avatar Zentix</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="avatar-text">{mensaje}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="avatar-mini">{estado}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="avatar-mini">Ingresos: {total_ingresos:,.0f} | Gastos: {total_gastos:,.0f} | Disponible: {ahorro_actual:,.0f}</div>',
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- AUTH ----------------
if st.session_state.user is None:
    menu_auth = ["Login", "Registro"]
    choice = st.sidebar.selectbox("Acceso", menu_auth)

    email = st.text_input("Correo")
    password = st.text_input("Contraseña", type="password")

    if choice == "Registro":
        if st.button("Crear cuenta"):
            try:
                supabase.auth.sign_up({"email": email, "password": password})
                st.success("Cuenta creada correctamente. Ahora inicia sesión.")
            except Exception as e:
                st.error(f"Error al registrar: {e}")

    elif choice == "Login":
        if st.button("Ingresar"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.success("Bienvenido a Zentix")
                st.rerun()
            except Exception as e:
                st.error(f"Error al iniciar sesión: {e}")

    st.stop()

# ---------------- SESIÓN INICIADA ----------------
user_id = st.session_state.user.id
perfil = obtener_perfil(user_id)

with st.sidebar:
    if icono_path.exists():
        st.image(str(icono_path), width=70)

    st.markdown("### ZENTIX")
    st.caption("Panel personal")

    st.success("Sesión iniciada")

    if st.button("Cerrar sesión"):
        st.session_state.user = None
        st.rerun()

# ---------------- ONBOARDING ----------------
if not perfil or not perfil.get("onboarding_completo", False):
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("👋 Configura tu experiencia Zentix")

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

    if st.button("Guardar configuración inicial"):
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
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

nombre_usuario = perfil["nombre_mostrado"] if perfil and perfil.get("nombre_mostrado") else "usuario"

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

# ---------------- INICIO ----------------
if pagina == "Inicio":
    st.subheader(f"📊 Resumen de {nombre_usuario}")

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

    render_avatar(pagina, nombre_usuario, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)

    if not df_mes.empty:
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
                title="Distribución de ingresos vs gastos",
                hole=0.52
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
                title="Categorías del mes"
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

    tipo = st.radio("Tipo de movimiento", ["Ingreso", "Gasto"], horizontal=True)

    if tipo == "Ingreso":
        st.markdown('<div class="pill-ingreso">Ingreso seleccionado</div>', unsafe_allow_html=True)
        categorias_disponibles = obtener_categorias_usuario(user_id, "Ingreso")
    else:
        st.markdown('<div class="pill-gasto">Gasto seleccionado</div>', unsafe_allow_html=True)
        categorias_disponibles = obtener_categorias_usuario(user_id, "Gasto")

    fecha = st.date_input("Fecha", value=date.today())
    categoria = st.selectbox("Categoría", categorias_disponibles if categorias_disponibles else ["Sin categorías"])
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

    render_avatar(pagina, nombre_usuario, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)

# ---------------- ANÁLISIS ----------------
if pagina == "Análisis":
    st.subheader("📈 Análisis")
    render_avatar(pagina, nombre_usuario, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)

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

    col_meta1, col_meta2 = st.columns(2)

    with col_meta1:
        if st.button("💾 Guardar meta", use_container_width=True):
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

                st.success("Meta guardada correctamente")
                st.rerun()
            except Exception as e:
                st.error(f"Error guardando meta: {e}")

    with col_meta2:
        if st.button("🗑️ Limpiar meta", use_container_width=True):
            try:
                supabase.table("ahorro_meta").delete().eq("usuario_id", user_id).execute()
                st.warning("Meta eliminada correctamente")
                st.rerun()
            except Exception as e:
                st.error(f"Error eliminando meta: {e}")

    ahorro_actual = float(saldo_disponible)
    faltante = max(0.0, float(meta) - max(ahorro_actual, 0.0))

    st.write(f"💰 Dinero disponible actual: {ahorro_actual:,.0f}")
    st.write(f"🎯 Meta de ahorro: {float(meta):,.0f}")

    if float(meta) > 0:
        progreso = max(0.0, ahorro_actual / float(meta))
        st.progress(min(progreso, 1.0))

        if ahorro_actual >= float(meta):
            st.success("Vas excelente: con tu disponible actual ya alcanzas tu meta de ahorro.")
        else:
            st.info(f"Te faltan {faltante:,.0f} para cumplir tu meta.")
    else:
        st.info("Define una meta para comenzar.")

    render_avatar(pagina, nombre_usuario, total_ingresos, total_gastos, saldo_disponible, ultimo_tipo)
