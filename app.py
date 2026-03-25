import streamlit as st
import pandas as pd
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
    }
    .stTextInput>div>div>input,
    .stNumberInput input {
        background-color: #1A1A1A;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
logo_path = Path("logo.png")
if logo_path.exists():
    st.image(str(logo_path), width=120)
else:
    st.warning("Logo no encontrado")

st.markdown("## ZENTIX")
st.caption("Control inteligente de tu dinero")

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- AUTH ----------------
menu_auth = ["Login", "Registro"]
choice = st.sidebar.selectbox("Acceso", menu_auth)

email = st.text_input("Correo")
password = st.text_input("Contraseña", type="password")

if choice == "Registro":
    if st.button("Crear cuenta"):
        try:
            res = supabase.auth.sign_up({
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

if st.session_state.user is None:
    st.stop()

user_id = st.session_state.user.id

# ---------------- NAVEGACIÓN ----------------
menu = ["Inicio", "Registrar", "Análisis", "Ahorro"]
pagina = st.sidebar.selectbox("Menú", menu)

# ---------------- CARGA DATOS ----------------
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
except Exception as e:
    st.error(f"Error cargando movimientos: {e}")
    st.stop()

if not df.empty:
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["monto"] = pd.to_numeric(df["monto"], errors="coerce").fillna(0)
    mes_actual = pd.Timestamp.now().month
    anio_actual = pd.Timestamp.now().year
    df_mes = df[(df["fecha"].dt.month == mes_actual) & (df["fecha"].dt.year == anio_actual)].copy()
else:
    df_mes = pd.DataFrame(columns=["usuario_id", "fecha", "tipo", "categoria", "monto", "descripcion"])

# ---------------- MÉTRICAS ----------------
if not df_mes.empty:
    total_gastos = df_mes[df_mes["tipo"] == "Gasto"]["monto"].sum()
    total_ingresos = df_mes[df_mes["tipo"] == "Ingreso"]["monto"].sum()
else:
    total_gastos = 0
    total_ingresos = 0

# ---------------- INICIO ----------------
if pagina == "Inicio":
    st.subheader("📊 Resumen")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💸 Gastos", f"{total_gastos:,.2f}")
    with col2:
        st.metric("💰 Ingresos", f"{total_ingresos:,.2f}")

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

# ---------------- ANÁLISIS ----------------
if pagina == "Análisis":
    st.subheader("📈 Análisis")
    if not df_mes.empty:
        st.dataframe(df_mes, use_container_width=True)
        resumen = df_mes.groupby("categoria")["monto"].sum().sort_values(ascending=False)
        if not resumen.empty:
            st.bar_chart(resumen)
        else:
            st.info("Agrega datos para ver gráficos")
    else:
        st.info("No hay datos este mes")

# ---------------- AHORRO ----------------
if pagina == "Ahorro":
    st.subheader("🎯 Plan de ahorro")
    meta = st.number_input("¿Cuánto quieres ahorrar?", min_value=0.0, step=1000.0)

    ahorro_actual = float(total_ingresos - total_gastos)
    st.write(f"💰 Ahorro actual: {ahorro_actual:,.2f}")
    st.write(f"🎯 Meta: {meta:,.2f}")

    if meta > 0:
        progreso = max(0.0, ahorro_actual / meta)
        st.progress(min(progreso, 1.0))

        if progreso >= 1:
            st.success("🎉 ¡Meta alcanzada!")
        else:
            restante = max(0.0, meta - ahorro_actual)
            st.info(f"Te faltan {restante:,.2f} para cumplir tu meta")
    else:
        st.info("Define una meta para comenzar")
