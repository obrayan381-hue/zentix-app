import streamlit as st
from supabase import create_client, Client


def _leer_secret():
    try:
        url = st.secrets["SUPABASE"]["URL"]
        key = st.secrets["SUPABASE"]["ANON_KEY"]
    except Exception:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]

    url = str(url).strip()
    key = str(key).strip()

    return url, key


url, key = _leer_secret()
supabase: Client = create_client(url, key)
