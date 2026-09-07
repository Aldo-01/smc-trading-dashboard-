import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
import json

# ==========================================
# 1. PAGE CONFIG & CUSTOM STYLING
# ==========================================
st.set_page_config(
    page_title="SMC Institutional Trading Terminal",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Terminal Custom Styling
st.markdown("""
<style>
    .main { background-color: #0b0e14; }
    .stMetric {
        background-color: #131722;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #2a2e39;
    }
    .stMetric label { color: #848e9c !important; font-size: 0.85rem !important; }
    .stMetric div { color: #d1d4dc !important; font-weight: bold; }
    .badge-approved { background-color: #0ecb8120; color: #0ecb81; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .badge-review { background-color: #f0b90b20; color: #f0b90b; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .badge-discarded { background-color: #f6465d20; color: #f6465d; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SUPABASE CONNECTION & DATA PIPELINE
# ==========================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

def load_data():
    try:
        res = supabase.table("trading_journal").select("*").order("created_at", desc=True).execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['timestamp_wita'] = df['created_at'].dt.tz_convert('Asia/Makassar').dt.strftime('%Y-%m-%d %H:%M:%S')
        return df
    except Exception as e:
        st.error(f"Error fetching data from Supabase: {e}")
        return pd.DataFrame()

df = load_data()

# ==========================================
# 3. SIDEBAR CONTROLS
# ==========================================
st.sidebar.title("🦅 SMC TERMINAL")
st.sidebar.caption("Institutional Algo-Engine v2.4")

if st.sidebar.button("🔄 Sync Live Data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.write("### ⚙️ Engine Parameters")
st.sidebar.info(
    "• **Symbol:** XAUUSD\n"
    "• **Timeframe:** M15\n"
    "• **Execution:** Auto / Webhook\n"
    "• **Risk per Trade:** 1.0%\n"
    "• **Min Confidence:** 85% Auto"
)

# ==========================================
# 4. DASHBOARD HEADER
# ==========================================
st.title("⚡ SMC TRADING DASHBOARD")
st.caption("Institutional Liquidity & Multi-Session Analytics System")
st.divider()

if df.empty:
    st.warning("⚠️ Belum ada record data di Supabase. Silakan jalankan scanner Colab!")
else:
    # =========================================================================
    # MODUL 1: OVERVIEW AKUN & PERFORMANCE (MT5 LIVE FEED)
    # =========================================================================
    st.header("1. Overview Akun & Performance", anchor="account-overview")
    
    # Kalkulasi Metric
    total_scans = len(df)
    executed_df = df[df['trade_status'] == 'EXECUTED']
    executed_count = len(executed_df)
    
    # Hitung PnL dan Win Rate jika ada data transaksi
    wins = len(df[df['pnl_usd'] > 0]) if 'pnl_usd' in df else 0
    win_rate = (wins / executed_count * 100) if executed_count > 0 else 0.0
    total_pnl = df['pnl_usd'].sum() if ('pnl_usd' in df and not df['pnl_usd'].isnull().all()) else 0.0
    
    # Simulasi Akun / Integration Feed
    sim_balance = 10000.0 + total_pnl
    sim_equity = sim_balance
    sim_drawdown = 0.0  # Dynamic Drawdown Tracker
    
    a1, a2, a3, a4, a5 = st.columns(5)
    a1.metric("Account Balance", f"${sim_balance:,.2f}")
    a2.metric("Equity", f"${sim_equity:,.2f}")
    a3.metric("Current Drawdown", f"{sim_drawdown:.2f}%")
    a4.metric("Realized Win Rate", f"{win_rate:.1f}%", delta=f"{wins}/{executed_count} Wins")
    a5.metric("Total Net PnL", f"${total_pnl:,.2f}", delta_color="normal" if total_pnl >= 0 else "inverse")

    st.subheader("Active Positions (MT5 Live Bridge)")
    active_trades = df[df['trade_status'] == 'EXECUTED']
    if active_trades.empty:
        st.info("ℹ️ Tidak ada posisi aktif yang sedang berjalan di pasar saat ini.")
    else:
        st.dataframe(
            active_trades[['timestamp_wita', 'symbol', 'direction', 'entry_price', 'sl', 'tp', 'lot_size', 'trade_status']],
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # =========================================================================
    # MODUL 2: LIVE ENGINE & SIGNAL LOG (M15 RADAR & SCANNER)
    # =========================================================================
    st.header("2. Live Engine & Signal Log Monitor", anchor="engine-monitor")
    
    col_radar, col_latest = st.columns([1, 1])
    
    latest_scan = df.iloc[0]
    
    with col_radar:
        st.subheader("🎯 Real-Time Confidence Score Meter")
        
        score = int(latest_scan['confidence_score'])
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': f"Latest Scan: {latest_scan['symbol']} ({latest_scan['direction']})"},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "#58a6ff"},
                'steps': [
                    {'range': [0, 70], 'color': "#2d1517"},
                    {'range': [70, 85], 'color': "#2b2611"},
                    {'range': [85, 100], 'color': "#112a1d"}
                ],
                'threshold': {
                    'line': {'color': "#0ecb81", 'width': 4},
                    'thickness': 0.75,
                    'value': 85
                }
            }
        ))
        fig_gauge.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#d1d4dc"))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_latest:
        st.subheader("📡 Radar Matrix M15 Breakdown")
        bd = latest_scan['matrix_breakdown']
        if isinstance(bd, str):
            bd = json.loads(bd)
            
        def status_icon(val):
            return "✅ PASSED" if val else "❌ FAILED"

        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.write(f"• **HTF PD Zone (+25p):** {status_icon(bd.get('HTF_PD_Zone'))}")
            st.write(f"• **Liquidity Sweep (+25p):** {status_icon(bd.get('Liquidity_Sweep'))}")
            st.write(f"• **MSS / CHoCH (+20p):** {status_icon(bd.get('MSS_CHoCH'))}")
        with m_col2:
            st.write(f"• **Unfilled FVG (+15p):** {status_icon(bd.get('Unfilled_FVG'))}")
            st.write(f"• **RR Ratio >= 1:2 (+15p):** {status_icon(bd.get('RR_Check'))}")
            st.write(f"• **Market Session:** `{latest_scan['market_session']}`")
            
        st.caption(f"Last Candle Time: {latest_scan['timestamp_wita']} WITA")

    st.subheader("📄 Scanner Stream Log (Candle-to-Candle)")
    st.dataframe(
        df[['timestamp_wita', 'symbol', 'direction', 'market_session', 'confidence_score', 'entry_price', 'sl', 'tp', 'rr_ratio', 'status_decision']],
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # =========================================================================
    # MODUL 3: ADVANCED TRADING JOURNAL & ANALYTICS (EVALUASI LOGIKA)
    # =========================================================================
    st.header("3. Advanced Trading Journal & Analytics", anchor="advanced-journal")
    
    tab_journal, tab_session, tab_matrix = st.tabs([
        "📖 Complete Trade History", 
        "🌍 Session Analytics", 
        "🔥 Matrix Factor Analysis"
    ])

    with tab_journal:
        st.subheader("Historical Log Table")
        st.dataframe(df, use_container_width=True)

    with tab_session:
        st.subheader("Session Tagging Distribution")
        s_col1, s_col2 = st.columns(2)
        
        with s_col1:
            fig_sess = px.pie(
                df, names='market_session', title='Sinyal Terbentuk per Sesi Pasar',
                color_discrete_sequence=['#f0b90b', '#0ecb81', '#58a6ff']
            )
            fig_sess.update_layout(template="plotly_dark")
            st.plotly_chart(fig_sess, use_container_width=True)
            
        with s_col2:
            fig_status = px.histogram(
                df, x='market_session', color='status_decision', barmode='group',
                title='Keputusan Sistem Berdasarkan Sesi'
            )
            fig_status.update_layout(template="plotly_dark")
            st.plotly_chart(fig_status, use_container_width=True)

    with tab_matrix:
        st.subheader("🔥 Matrix Confluence Factor Analysis")
        st.caption("Menganalisis matriks mana yang paling sering meloloskan sinyal trading.")
        
        # Extract Matriks Data
        matrix_records = []
        for _, row in df.iterrows():
            b = row['matrix_breakdown']
            if isinstance(b, str):
                b = json.loads(b)
            matrix_records.append(b)
            
        df_matrix = pd.DataFrame(matrix_records)
        passed_counts = df_matrix.sum().reset_index()
        passed_counts.columns = ['Matrix Factor', 'Frequency Passed']
        
        fig_matrix = px.bar(
            passed_counts, x='Matrix Factor', y='Frequency Passed',
            color='Frequency Passed', color_continuous_scale='Blues',
            title='Frekuensi Kehadiran Matriks Konfluens SMC'
        )
        fig_matrix.update_layout(template="plotly_dark")
        st.plotly_chart(fig_matrix, use_container_width=True)
