import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
import json

# 1. Page Configuration
st.set_page_config(
    page_title="SMC AI Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Dashboard Professional Dark Theme
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stMetric {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    .stMetric label { color: #8b949e !important; font-size: 0.9rem !important; }
    .stMetric div { color: #58a6ff !important; font-weight: bold; }
    .status-executed { color: #3fb950; font-weight: bold; }
    .status-review { color: #d29922; font-weight: bold; }
    .status-discarded { color: #f85149; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 2. Supabase Connection
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# 3. Load Data
def load_data():
    try:
        res = supabase.table("trading_journal").select("*").order("created_at", desc=True).execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'])
            # Convert timezone ke Local (WIB/WITA)
            df['created_at_local'] = df['created_at'].dt.tz_convert('Asia/Makassar').dt.strftime('%Y-%m-%d %H:%M:%S')
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

df = load_data()

# Sidebar
st.sidebar.title("⚡ SMC Scanner Controls")
if st.sidebar.button("🔄 Refresh Data Manual"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.info("🤖 **SMC Engine Status:** Active\n\n- Interval: M15\n- Symbol: XAUUSD\n- Risk/Trade: 1%")

# Header
st.title("⚡ SMC/ICT Institutional Trading Dashboard")
st.caption("Real-Time Algo-Scanner Log & Multi-Session Analytics Terminal")

if df.empty:
    st.warning("Belum ada data jurnal tersimpan di Supabase.")
else:
    # --- METRICS ROW ---
    m1, m2, m3, m4, m5 = st.columns(5)
    total_scans = len(df)
    executed_trades = df[df['trade_status'] == 'EXECUTED']
    executed_count = len(executed_trades)
    pending_count = len(df[df['trade_status'] == 'PENDING_REVIEW'])
    discarded_count = len(df[df['trade_status'] == 'DISCARDED'])
    
    win_rate = 0.0 if executed_count == 0 else (len(executed_trades[executed_trades['pnl_usd'] > 0]) / executed_count) * 100
    total_pnl = df['pnl_usd'].sum() if 'pnl_usd' in df and not df['pnl_usd'].isnull().all() else 0.0

    m1.metric("Total M15 Scans", f"{total_scans}")
    m2.metric("Auto Executed", f"{executed_count}", delta=f"{(executed_count/total_scans)*100:.1f}% Rate")
    m3.metric("Pending Review", f"{pending_count}")
    m4.metric("Discarded", f"{discarded_count}")
    m5.metric("Win Rate", f"{win_rate:.1f}%")

    st.divider()

    # --- FILTER SECTION ---
    f1, f2 = st.columns([1, 3])
    with f1:
        session_filter = st.multiselect("Filter Session:", options=df['market_session'].unique(), default=df['market_session'].unique())
    with f2:
        status_filter = st.multiselect("Filter Decision Status:", options=df['trade_status'].unique(), default=df['trade_status'].unique())

    filtered_df = df[(df['market_session'].isin(session_filter)) & (df['trade_status'].isin(status_filter))]

    # --- TABS SECTION ---
    tab_journal, tab_analytics, tab_last_signal = st.tabs(["📋 Live Journal Logs", "📊 Session Analytics", "🎯 Latest Scan Breakdown"])

    with tab_journal:
        st.subheader("Data Riwayat Scanner")
        
        # Format display dataframe
        display_df = filtered_df.copy()
        display_df['Confidence'] = display_df['confidence_score'].apply(lambda x: f"{x}%")
        display_df['RR Ratio'] = display_df['rr_ratio'].apply(lambda x: f"1:{x}")
        
        cols_to_show = ['created_at_local', 'symbol', 'direction', 'market_session', 'Confidence', 'entry_price', 'sl', 'tp', 'RR Ratio', 'lot_size', 'status_decision']
        
        st.dataframe(
            display_df[cols_to_show].rename(columns={
                'created_at_local': 'Timestamp (WITA)',
                'symbol': 'Pair',
                'direction': 'Type',
                'market_session': 'Session',
                'entry_price': 'Entry',
                'sl': 'SL',
                'tp': 'TP',
                'lot_size': 'Lot',
                'status_decision': 'Decision'
            }),
            use_container_width=True,
            hide_index=True
        )

    with tab_analytics:
        st.subheader("Analisis Distribusi Sinyal & Sesi Pasar")
        c_chart1, c_chart2 = st.columns(2)
        
        with c_chart1:
            fig_session = px.pie(
                df, names='market_session', title='Persentase Scan per Sesi Pasar',
                hole=0.4, color_discrete_sequence=px.colors.qualitative.Dark24
            )
            fig_session.update_layout(template="plotly_dark")
            st.plotly_chart(fig_session, use_container_width=True)
            
        with c_chart2:
            fig_confidence = px.histogram(
                df, x='confidence_score', nbins=10, 
                title='Distribusi Confidence Score SMC Logic',
                color_discrete_sequence=['#58a6ff']
            )
            fig_confidence.update_layout(template="plotly_dark", xaxis_title="Confidence Score (%)", yaxis_title="Jumlah Scan")
            st.plotly_chart(fig_confidence, use_container_width=True)

    with tab_last_signal:
        if not df.empty:
            latest = df.iloc[0]
            st.subheader(f"Detail Setup Terakhir ({latest['created_at_local']})")
            
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Symbol / Direction", f"{latest['symbol']} | {latest['direction']}")
            sc2.metric("Confidence Score", f"{latest['confidence_score']}%")
            sc3.metric("Status", f"{latest['status_decision']}")

            st.write("### SMC/ICT Confluence Checklist")
            
            # Matriks JSON Breakdown Parsing
            breakdown = latest['matrix_breakdown']
            if isinstance(breakdown, str):
                breakdown = json.loads(breakdown)
                
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"• **HTF & Premium/Discount Zone (+25p):** {'✅ PASSED' if breakdown.get('HTF_PD_Zone') else '❌ FAILED'}")
                st.write(f"• **Liquidity Sweep (+25p):** {'✅ PASSED' if breakdown.get('Liquidity_Sweep') else '❌ FAILED'}")
                st.write(f"• **MSS / CHoCH Structure (+20p):** {'✅ PASSED' if breakdown.get('MSS_CHoCH') else '❌ FAILED'}")
            with col_b:
                st.write(f"• **Unfilled FVG Alignment (+15p):** {'✅ PASSED' if breakdown.get('Unfilled_FVG') else '❌ FAILED'}")
                st.write(f"• **Risk:Reward Check >= 1:2 (+15p):** {'✅ PASSED' if breakdown.get('RR_Check') else '❌ FAILED'}")
