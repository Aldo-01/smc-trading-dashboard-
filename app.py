# --- FETCH MT5 LIVE ACCOUNT FEED ---
def load_mt5_feed():
    try:
        res = supabase.table("account_feed").select("*").eq("id", 1).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        pass
    return None

mt5_data = load_mt5_feed()

# MODUL 1: OVERVIEW AKUN & PERFORMANCE
st.header("1. Overview Akun & Performance", anchor="account-overview")

if mt5_data:
    sim_balance = mt5_data.get('balance', 0.0)
    sim_equity = mt5_data.get('equity', 0.0)
    free_margin = mt5_data.get('margin_free', 0.0)
    floating_pnl = mt5_data.get('floating_pnl', 0.0)
    drawdown_pct = mt5_data.get('drawdown_pct', 0.0)
    open_positions = mt5_data.get('open_positions', [])
    
    a1, a2, a3, a4, a5 = st.columns(5)
    a1.metric("Balance (MT5 Live)", f"${sim_balance:,.2f}")
    a2.metric("Equity", f"${sim_equity:,.2f}", delta=f"${floating_pnl:,.2f} Floating")
    a3.metric("Free Margin", f"${free_margin:,.2f}")
    a4.metric("Current Drawdown", f"{drawdown_pct:.2f}%")
    a5.metric("Total Net PnL", f"${floating_pnl:,.2f}")

    st.subheader("Active Positions (MT5 Live Bridge)")
    if not open_positions:
        st.info("ℹ️ Tidak ada posisi aktif yang sedang berjalan di MetaTrader 5 saat ini.")
    else:
        df_pos = pd.DataFrame(open_positions)
        st.dataframe(df_pos, use_container_width=True, hide_index=True)
else:
    st.warning("⚠️ Menunggu feed real-time dari skrip MT5 Bridge...")
