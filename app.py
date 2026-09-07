import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

# Konfigurasi Tampilan
st.set_page_config(page_title="SMC AI Trading Dashboard", page_icon="📈", layout="wide")

# Mengambil Kredensial dari Secrets Streamlit
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.title("🛡️ SMC/ICT Institutional Trading Dashboard")
st.caption("Real-Time Logic Scanner, Analytics, & Multi-Session Journaling")

# Load Data dari Supabase
def load_data():
    try:
        res = supabase.table("trading_journal").select("*").order("created_at", desc=True).execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'])
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.info("Belum ada data jurnal tersimpan di Supabase.")
else:
    # 1. Metric Top Cards
    c1, c2, c3, c4 = st.columns(4)
    total_scans = len(df)
    executed = len(df[df['trade_status'] == 'EXECUTED'])
    win_rate = 100.0 if executed == 0 else (len(df[df['pnl_usd'] > 0]) / executed) * 100
    total_pnl = df['pnl_usd'].sum() if 'pnl_usd' in df and not df['pnl_usd'].isnull().all() else 0.0

    c1.metric("Total M15 Scans", f"{total_scans} Log")
    c2.metric("Executed Trades", f"{executed}")
    c3.metric("Win Rate (%)", f"{win_rate:.1f}%")
    c4.metric("Total Realized PnL", f"${total_pnl:.2f}")

    st.divider()

    # 2. Main Tabs
    tab1, tab2 = st.tabs(["📋 Live Journal Logs", "🌍 Market Session Analytics"])

    with tab1:
        st.subheader("Data Riwayat Scanner & Decision Log")
        st.dataframe(
            df[['created_at', 'symbol', 'direction', 'market_session', 'confidence_score', 'entry_price', 'sl', 'tp', 'rr_ratio', 'status_decision', 'trade_status']],
            use_container_width=True
        )

    with tab2:
        st.subheader("Distribusi Sinyal per Sesi Pasar")
        fig = px.histogram(df, x="market_session", color="status_decision", barmode="group", title="Frekuensi Status Sinyal Berdasarkan Sesi Perdagangan")
        st.plotly_chart(fig, use_container_width=True)
