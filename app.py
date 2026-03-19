import streamlit as st
import pandas as pd
from datetime import datetime
import pyrebase
from firebase_config import firebase_config
from firestore_config import db  # firestore_config.py con st.secrets

# ---------------- FIREBASE ----------------
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Zentix", layout="wide")

# ---------------- ESTILO FINTECH ----------------
st.markdown("""
    <style>
    body {
        background-color: #0D0D0D;
        color: white;
    }
    .stApp {
        background-color: #0D0D0D;
    }
    .stButton>button {
        background-color: #00C896;
        color: white;
        border-radius: 10px;
        font-weight: bold;
    }
    .stTextInput>div>div>input {
        background-color: #1A1A1A;
        color: white;
    }
    .stNumberInput input {
        background-color: #1A1A1A;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
from pathlib import Path
logo_path = Path("logo.png")
if logo_path.exists():
    st.image(str(logo_path), width=120)
else:
    st.warning("Logo no encontrado")

st.markdown("## ZENTIX")
st.caption("Control inteligente de tu dinero")

# ---------------- AUTENTICACIÓN ----------------
menu_auth = ["Login", "Registro"]
choice = st.sidebar.selectbox("Acceso", menu_auth)

email = st.text_input("Correo")
password = st.text_input("Contraseña", type="password")

if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- REGISTRO ----------------
if choice == "Registro":
    if st.button("Crear cuenta"):
        try:
            user = auth.create_user_with_email_and_password(email, password)
            st.success("Cuenta creada correctamente")
        except Exception as e:
            st.error(f"Error: {e}")

# ---------------- LOGIN ----------------
elif choice == "Login":
    if st.button("Ingresar"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state.user = user
            st.success("Bienvenido a Zentix")
        except Exception as e:
            st.error(f"Error: {e}")

if st.session_state.user is None:
    st.stop()

# ---------------- USER ID ----------------
user_id = st.session_state.user["localId"]

# ---------------- NAVEGACIÓN ----------------
menu = ["Inicio", "Registrar", "Análisis", "Ahorro"]
pagina = st.sidebar.selectbox("Menú", menu)

# ---------------- CARGAR DATOS DESDE FIRESTORE ----------------
movimientos_ref = db.collection("movimientos")
query = movimientos_ref.where("usuario", "==", user_id)
docs = query.stream()

data = [doc.to_dict() for doc in docs]
df = pd.DataFrame(data)

# ---------------- FILTRAR POR MES ACTUAL ----------------
if not df.empty:
    df["fecha"] = pd.to_datetime(df["fecha"])
    mes_actual = pd.Timestamp.now().month
    anio_actual = pd.Timestamp.now().year
    df_mes = df[(df["fecha"].dt.month == mes_actual) & (df["fecha"].dt.year == anio_actual)]
else:
    df_mes = pd.DataFrame(columns=["usuario","fecha","tipo","categoria","monto","descripcion"])

# ---------------- VARIABLES ----------------
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
        st.metric("💸 Gastos", total_gastos)
    with col2:
        st.metric("💰 Ingresos", total_ingresos)

# ---------------- REGISTRAR ----------------
if pagina == "Registrar":
    st.subheader("➕ Agregar movimiento")
    fecha = st.date_input("Fecha")
    tipo = st.selectbox("Tipo", ["Gasto", "Ingreso"])
    categoria = st.text_input("Categoría")
    monto = st.number_input("Monto", min_value=0)
    descripcion = st.text_input("Descripción")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Guardar"):
            doc_ref = db.collection("movimientos").document()
            doc_ref.set({
                "usuario": user_id,
                "fecha": datetime.strptime(str(fecha), "%Y-%m-%d"),
                "tipo": tipo,
                "categoria": categoria,
                "monto": monto,
                "descripcion": descripcion
            })
            st.success("Guardado correctamente")
            st.experimental_rerun()
    with col2:
        if st.button("🗑️ Reset"):
            st.warning("Formulario limpiado")
            st.experimental_rerun()

# ---------------- ANÁLISIS ----------------
if pagina == "Análisis":
    st.subheader("📈 Análisis")
    if not df_mes.empty:
        st.dataframe(df_mes)
        try:
            resumen = df_mes.groupby("categoria")["monto"].sum()
            st.bar_chart(resumen)
        except:
            st.info("Agrega datos para ver gráficos")
    else:
        st.info("No hay datos este mes")

# ---------------- AHORRO ----------------
if pagina == "Ahorro":
    st.subheader("🎯 Plan de ahorro")
    meta = st.number_input("¿Cuánto quieres ahorrar?", min_value=0)
    ahorro_actual = total_ingresos - total_gastos
    st.write(f"💰 Ahorro actual: {ahorro_actual}")
    st.write(f"🎯 Meta: {meta}")
    if meta > 0:
        progreso = ahorro_actual / meta if meta != 0 else 0
        if progreso >= 1:
            st.success("🎉 ¡Meta alcanzada!")
        else:
            st.progress(min(progreso, 1.0))
            restante = meta - ahorro_actual
            st.info(f"Te faltan {restante} para cumplir tu meta")
    else:
        st.info("Define una meta para comenzar")
            st.progress(min(progreso, 1.0))
            restante = meta - ahorro_actual
            st.info(f"Te faltan {restante} para cumplir tu meta")
    else:
        st.info("Define una meta para comenzar")
