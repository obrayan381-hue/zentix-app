import streamlit as st
from supabase import create_client, Client

url = st.secrets["SUPABASE"]["URL"]
key = st.secrets["SUPABASE"]["ANON_KEY"]

supabase: Client = create_client(url, key)