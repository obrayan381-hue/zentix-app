import streamlit as st
import pandas as pd
import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_config import firebase_config

# ---------------- FIREBASE AUTH ----------------
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# ---------------- FIRESTORE ----------------
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["FIREBASE_CREDENTIALS"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ---------------- CONFIG ----------------
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
    .stTextInput input, .stNumberInput input {
        background-color: #1A1A1A;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- LOGO ----------------
st.image("logo.png", width=120)
st.markdown("## ZENTIX")
st.caption("Control inteligente de tu dinero")

# ---------------- AUTH ----------------
menu_auth = ["Login", "Registro"]
choice = st.sidebar.selectbox("Acceso", menu_auth)

email = st.text_input("Correo")
password = st.text_input("Contraseña", type="password")

if "user" not in st.session_state:
    st.session_state.user = None

if choice == "Registro":
    if st.button("Crear cuenta"):
        try:
            auth.create_user_with_email_and_password(email, password)
            st.success("Cuenta creada correctamente")
        except:
            st.error("Error al crear cuenta")

elif choice == "Login":
    if st.button("Ingresar"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state.user = user
            st.success("Bienvenido a Zentix")
        except:
            st.error("Credenciales incorrectas")

if st.session_state.user is None:
    st.stop()

# ---------------- USER ID ----------------
user_id = st.session_state.user["localId"]

# ---------------- NAV ----------------
menu = ["Inicio", "Registrar", "Análisis", "Ahorro"]
pagina = st.sidebar.selectbox("Menú", menu)

# ---------------- CARGAR DATOS FIRESTORE ----------------
docs = db.collection("usuarios").document(user_id).collection("movimientos").stream()

data = []
for doc in docs:
    item = doc.to_dict()
    data.append({
        "Fecha": item.get("fecha"),
        "Tipo": item.get("tipo"),
        "Categoría": item.get("categoria"),
        "Monto": item.get("monto"),
        "Descripción": item.get("descripcion")
    })

df = pd.DataFrame(data)

# ---------------- FILTRO MES ----------------
if not df.empty:
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

    mes_actual = pd.Timestamp.now().month
    anio_actual = pd.Timestamp.now().year

    df_mes = df[
        (df["Fecha"].dt.month == mes_actual) &
        (df["Fecha"].dt.year == anio_actual)
    ]
else:
    df_mes = df

# ---------------- VARIABLES ----------------
total_gastos = df_mes[df_mes["Tipo"] == "Gasto"]["Monto"].sum() if not df_mes.empty else 0
total_ingresos = df_mes[df_mes["Tipo"] == "Ingreso"]["Monto"].sum() if not df_mes.empty else 0

# ---------------- INICIO ----------------
if pagina == "Inicio":
    st.subheader("📊 Resumen")
    col1, col2 = st.columns(2)

    col1.metric("💸 Gastos", total_gastos)
    col2.metric("💰 Ingresos", total_ingresos)

# ---------------- REGISTRAR ----------------
if pagina == "Registrar":
    st.subheader("➕ Agregar movimiento")

    fecha = st.date_input("Fecha")
    tipo = st.selectbox("Tipo", ["Gasto", "Ingreso"])
    categoria = st.text_input("Categoría")
    monto = st.number_input("Monto", min_value=0)
    descripcion = st.text_input("Descripción")

    if st.button("💾 Guardar"):
        db.collection("usuarios").document(user_id).collection("movimientos").add({
            "fecha": str(fecha),
            "tipo": tipo,
            "categoria": categoria,
            "monto": monto,
            "descripcion": descripcion
        })
        st.success("Guardado correctamente")
        st.rerun()

# ---------------- ANÁLISIS ----------------
if pagina == "Análisis":
    st.subheader("📈 Análisis")

    if not df_mes.empty:
        st.dataframe(df_mes)
        resumen = df_mes.groupby("Categoría")["Monto"].sum()
        st.bar_chart(resumen)
    else:
        st.info("No hay datos este mes")

# ---------------- AHORRO ----------------
if pagina == "Ahorro":
    st.subheader("🎯 Plan de ahorro")

    meta = st.number_input("Meta", min_value=0)
    ahorro_actual = total_ingresos - total_gastos

    st.write(f"Ahorro actual: {ahorro_actual}")

    if meta > 0:
        progreso = ahorro_actual / meta

        if progreso >= 1:
            st.success("🎉 Meta alcanzada")
        else:
            st.progress(min(progreso, 1.0))
            st.info(f"Te faltan {meta - ahorro_actual}")
