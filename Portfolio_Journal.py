import requests
import datetime
import json 
import os   
import feedparser
import re
import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from streamlit_option_menu import option_menu
from st_supabase_connection import SupabaseConnection


st.set_page_config(page_title="Personal Portfolio", layout="wide")

conn = st.connection("supabase", type=SupabaseConnection)

# --- FUNGSI AUTENTIKASI ---
def login(email, password):
    try:
        res = conn.auth.sign_in_with_password({"email": email, "password": password})
        return res
    except Exception as e:
        # Pesan error disamarkan agar hacker tidak tahu masalah spesifiknya
        st.error("❌ Gagal Login: Email atau Password salah, atau akun belum terdaftar.")
        return None

def logout():
    conn.auth.sign_out()
    st.session_state.logged_in = False
    st.session_state.user_info = None
    st.rerun()

# --- HALAMAN LOGIN (SISTEM TERTUTUP) ---
if not st.session_state.logged_in:
    st.title("💼 Jurnal Portofolio & Trading")
    
    col1, col2, col3 = st.columns([1, 2, 1]) # Membuat form berada di tengah
    with col2:
        st.info("⚠️ **Sistem Tertutup (Invite-Only)**\n\nSilakan masuk menggunakan Email dan Password yang telah diberikan oleh Admin.")
        
        with st.form("login_form"):
            st.subheader("Login Access")
            email_log = st.text_input("Email")
            pass_log = st.text_input("Password", type="password")
            submit_log = st.form_submit_button("Masuk / Login", use_container_width=True)
            
            if submit_log:
                res = login(email_log, pass_log)
                if res:
                    st.session_state.logged_in = True
                    st.session_state.user_info = res.user
                    st.rerun()
                    
    # Hentikan proses render aplikasi utama jika belum login
    st.stop()

# --- WHITE MODERN FINTECH UI ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    /* 1. Reset Global: Latar Belakang Abu-abu Sangat Terang (SaaS Style) */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #F8FAFC; 
    }

    /* 2. Metric Box (Card) Putih Bersih dengan Bayangan Lembut */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }

    /* 3. Header & Sidebar Putih */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }
    
    /* 4. NAVIGASI BAR MODERN (Mengubah st.button di Sidebar menjadi Menu App) */
    [data-testid="stSidebar"] .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: transparent; /* Hilangkan kotak hijau/warna bawaan */
        color: #475569; /* Teks abu-abu gelap */
        border: none;
        padding: 12px 16px;
        text-align: left !important; /* Rata kiri seperti menu app sungguhan */
        font-weight: 600;
        font-size: 15px;
        transition: all 0.2s ease;
        box-shadow: none;
        display: flex;
        justify-content: flex-start;
    }
    /* Efek saat kursor diarahkan ke menu navigasi */
    [data-testid="stSidebar"] .stButton>button:hover {
        background-color: #F1F5F9;
        color: #2563EB; /* Berubah jadi Biru Modern saat dihover */
    }

    /* 5. Custom Warna Angka & Anti-Overflow */
    [data-testid="stMetricValue"] {
        color: #0F172A !important; /* Warna text utama: Hitam Pekat Navy */
        font-weight: 800;
        font-size: clamp(1.2rem, 1.8vw, 1.8rem) !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        line-height: 1.2 !important;
    }
    
    /* Warna Judul Metrik (Label) */
    [data-testid="stMetricLabel"] {
        color: #64748B !important; /* Abu-abu profesional */
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.85rem;
    }

    /* Targetkan kolom 3 (Hijau) dan kolom 4 (Merah) di Streamlit Metric bawaan */
    div[data-testid="column"]:nth-of-type(3) [data-testid="stMetricValue"] {
        color: #10B981 !important; /* Emerald Green (Lebih lembut dari warna neon) */
    }
    div[data-testid="column"]:nth-of-type(4) [data-testid="stMetricValue"] {
        color: #EF4444 !important; /* Red Rose */
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI DATA CLOUD ---
def fetch_supabase_data(table_name):
    try:
        # Supabase otomatis memfilter data berdasarkan User ID jika RLS aktif
        res = conn.table(table_name).select("*").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        return pd.DataFrame()

# Inisialisasi Data dari Cloud
if st.session_state.get('logged_in'):
    if 'trades' not in st.session_state:
        st.session_state.trades = fetch_supabase_data("trades")
    if 'cash' not in st.session_state:
        st.session_state.cash = fetch_supabase_data("cashflow")
    if 'investing' not in st.session_state:
        st.session_state.investing = fetch_supabase_data("investing")

# --- LOGIKA TAMPILAN UTAMA ---
if not st.session_state.logged_in:
    # HALAMAN LOGIN & REGISTER
    st.title("Portfolio Management")
    st.subheader("Silakan masuk untuk membangun portfolio investasi Anda.")
    
    tab_login, tab_signup = st.tabs(["Login", "Buat Akun Baru"])
    
    with tab_login:
        email_in = st.text_input("Email", key="login_email")
        pass_in = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", use_container_width=True):
            res = login(email_in, pass_in)
            if res:
                st.session_state.logged_in = True
                st.session_state.user_info = res.user
                st.success("Login Berhasil! Mengalihkan...")
                st.rerun()
            else:
                st.error("Email atau Password salah.")

    with tab_signup:
        st.info("Setelah mendaftar, silakan cek email Anda untuk konfirmasi (jika fitur email aktif di Supabase).")
        email_up = st.text_input("Email Baru", key="signup_email")
        pass_up = st.text_input("Password Baru", type="password", key="signup_pass")
        if st.button("Daftar Sekarang", use_container_width=True):
            res = sign_up(email_up, pass_up)
            if res:
                st.success("Akun berhasil dibuat! Silakan coba login.")
            else:
                st.error("Gagal membuat akun. Pastikan format email benar dan password minimal 6 karakter.")

else:
    # --- AREA DALAM (Setelah Login) ---
    with st.sidebar:
        # --- MODUL PROFIL USER (REKAT & SEIRAMA) ---
        user_email = st.session_state.user_info.email
        inisial = user_email[0].upper()
        
        # 1. Bagian Atas: Card Informasi (Sudut bawah dibuat tajam/0)
        st.markdown(f"""
            <div style="background-color: #FFFFFF; padding: 16px; border-radius: 12px 12px 0 0; border: 1px solid #E2E8F0; border-bottom: none;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="background-color: #2563EB; color: white; width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 18px; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);">
                        {inisial}
                    </div>
                    <div style="overflow: hidden;">
                        <p style="margin: 0; font-size: 11px; color: #64748B; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">Account Session</p>
                        <p style="margin: 0; font-size: 14px; color: #1E293B; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            {user_email}
                        </p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 2. CSS Khusus untuk "Merekatkan" tombol ke card di atasnya
        st.markdown("""
            <style>
            /* Menargetkan tombol logout agar menyatu dengan card di atas */
            div.stButton > button:first-child {
                border-radius: 0 0 12px 12px !important;
                border: 1px solid #E2E8F0 !important;
                border-top: 1px solid #F1F5F9 !important; /* Garis pemisah halus */
                background-color: #FFFFFF !important;
                color: #64748B !important;
                font-weight: 600 !important;
                font-size: 13px !important;
                margin-top: -1px !important; /* Menghilangkan celah */
                height: 42px !important;
                transition: all 0.2s ease !important;
                width: 100% !important;
            }
            div.stButton > button:first-child:hover {
                background-color: #FFF1F2 !important; /* Warna merah sangat muda */
                color: #E11D48 !important; /* Warna teks merah saat hover */
                border-color: #E2E8F0 !important;
            }
            </style>
        """, unsafe_allow_html=True)

        # 3. Bagian Bawah: Tombol Logout (Secara otomatis akan terkena CSS di atas)
        if st.button("🚪 Sign Out from Device", use_container_width=True):
            logout()
            
        st.divider()

        menu_pilihan = option_menu(
            menu_title="MAIN MENU", # Judul kategori
            options=[
                "Live Market Overview",
                "News",
                "Dashboard Utama", 
                "Dashboard Trading", 
                "Portfolio Live", 
                "Input Trading", 
                "Input Investasi", 
                "Kalkulator Finansial",
                "Jurnal Strategi"
            ],
            icons=[
                "bi bi-activity",   # Ikon Live market
                "bi bi-newspaper",  # Ikon News
                "house-door",       # Ikon untuk Dashboard Utama
                "bar-chart-line",   # Ikon untuk Dashboard Trading
                "briefcase",        # Ikon untuk Portfolio
                "pencil-square",    # Ikon untuk Input Trading
                "wallet2",          # Ikon untuk Input Investasi
                "calculator",        # Ikon untuk Kalkulator
                "bi bi-book"       # Ikon Jurnal
            ],
            menu_icon="list", # Ikon di sebelah tulisan MAIN MENU
            default_index=0,  # Menu yang aktif pertama kali
            styles={
                "container": {"padding": "0!important", "background-color": "#FFFFFF", "border": "none"},
                "icon": {"color": "#64748B", "font-size": "16px"}, 
                "nav-link": {
                    "font-size": "14px", 
                    "text-align": "left", 
                    "margin": "5px 0px", 
                    "color": "#475569", 
                    "font-weight": "600",
                    "border-radius": "8px"
                },
                "nav-link-selected": {
                    "background-color": "#2563EB", # Warna biru saat aktif
                    "color": "white"
                },
                "menu-title": {
                    "font-size": "12px",
                    "color": "#94A3B8",
                    "font-weight": "700",
                    "letter-spacing": "1px",
                    "margin-bottom": "10px"
                }
            }
        )

    # --- MENYAMBUNGKAN MENU BARU KE LOGIKA HALAMAN ---
    menu = menu_pilihan
    # ==========================================
    # BAGIAN 1: TRADING (Kode Sama Seperti Sebelumnya)
    # ==========================================
    if menu == "Dashboard Trading":
        st.title("Dashboard Performa Trading")
        
        df_trades = st.session_state.trades
        df_cash = st.session_state.cash
        
        # 1. KALKULASI METRIK UTAMA
        total_depo = df_cash[df_cash['tipe'] == 'Deposit']['nominal'].sum() if not df_cash.empty else 0
        total_wd = df_cash[df_cash['tipe'] == 'Withdraw']['nominal'].sum() if not df_cash.empty else 0
        total_pnl = df_trades['pnl'].sum() if not df_trades.empty else 0
        
        current_balance = total_depo - total_wd + total_pnl
        
    # 2. MENAMPILKAN METRIK DI ATAS GRAFIK
        st.markdown("### Ringkasan Akun")
        col1, col2, col3 = st.columns(3)
        
        # Menghitung Persentase pnl (Mencegah pembagian dengan nol)
        net_deposit = total_depo - total_wd
        if net_deposit > 0:
            pnl_pct = (total_pnl / net_deposit) * 100
        else:
            pnl_pct = 0.0
        
        with col1:
            st.metric(label="Total Balance (USD)", value=f"${current_balance:,.2f}")
        with col2:
            # Delta sekarang menampilkan persentase (%)
            st.metric(label="Total pnl Bersih", value=f"${total_pnl:,.2f}", delta=f"{pnl_pct:.2f}%")
        with col3:
            st.metric(label="Total Deposit Bersih", value=f"${net_deposit:,.2f}")
            
        st.markdown("<hr>", unsafe_allow_html=True)
        
        if not df_trades.empty or not df_cash.empty:
            st.subheader("Equity Curve (Growth)")
            trades_flow = df_trades[['tanggal_exit', 'pnl']].rename(columns={'tanggal_exit': 'tanggal', 'pnl': 'nominal'}) if not df_trades.empty else pd.DataFrame()
            cash_flow = df_cash[['tanggal', 'nominal']] if not df_cash.empty else pd.DataFrame()
            
            equity_df = pd.concat([trades_flow, cash_flow])
            if not equity_df.empty:
                # Perbaikan format tanggal agar tidak error
                equity_df['tanggal'] = pd.to_datetime(equity_df['tanggal'], format='mixed', errors='coerce')
                equity_df = equity_df.dropna(subset=['tanggal'])
                
                equity_df = equity_df.sort_values('tanggal')
                equity_df['Balance'] = equity_df['nominal'].cumsum()

                # --- MAKEOVER CHART AESTHETIC ---
                fig = px.line(equity_df, x='tanggal', y='Balance', markers=True, 
                            template="plotly_dark")

                fig.update_traces(
                    line=dict(color="#EA990D", width=3), # Warna Neon Cyan
                    marker=dict(size=8, color='#5CBEFA', symbol='circle')
                )

                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=30, b=0),
                    xaxis=dict(showgrid=False, color='#8B949E'),
                    yaxis=dict(showgrid=True, gridcolor='#30363D', color='#8B949E', 
                    tickprefix='$', tickformat=',.2f'),
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # --- STATISTIK GLOBAL & PER pair ---
            if not df_trades.empty:
                st.subheader("Global Trading Statistics")
                
                # Logika Consecutive Win/Loss
                pnl_list = df_trades['pnl'].tolist()
                def get_max_streak(lst, win=True):
                    max_s = current_s = 0
                    for val in lst:
                        if (win and val > 0) or (not win and val <= 0):
                            current_s += 1
                            max_s = max(max_s, current_s)
                        else: current_s = 0
                    return max_s

                # Kalkulasi Global
                total_trades = len(df_trades)
                win_trades = df_trades[df_trades['pnl'] > 0]
                loss_trades = df_trades[df_trades['pnl'] <= 0]
                
                winrate = (len(win_trades) / total_trades) * 100 if total_trades > 0 else 0
                avg_win = win_trades['pnl'].mean() if not win_trades.empty else 0
                avg_loss = loss_trades['pnl'].mean() if not loss_trades.empty else 0
                best_trade = df_trades['pnl'].max()
                worst_trade = df_trades['pnl'].min()
                cons_win = get_max_streak(pnl_list, True)
                cons_loss = get_max_streak(pnl_list, False)

                # --- HIERARKI INFORMASI SERAGAM ---
                with st.container():
                    col1, col2, col3, col4 = st.columns(4)
                # Metrik biasa (Tetap warna Cyan)
                col1.metric("Total Trades", total_trades)
                col2.metric("Winrate", f"{winrate:.1f}%")
                
                # HTML Card: Avg Win (Hijau)
                with col3:
                    st.markdown(f"""
                        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.3);">
                            <p style="color: #64748B; font-size: 14px; font-weight: 600; margin-bottom: 0px;">AVG WIN</p>
                            <p style="color: #2ea043; font-size: clamp(1.2rem, 1.8vw, 1.8rem); font-weight: 700; margin-top: 5px; margin-bottom: 0px;word-wrap: break-word;">${avg_win:,.2f}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                # HTML Card: Avg Loss (Merah)
                with col4:
                    st.markdown(f"""
                        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.3);">
                            <p style="color: #64748B; font-size: 14px; font-weight: 00; margin-bottom: 0px;">AVG LOSS</p>
                            <p style="color: #da3633; font-size: clamp(1.2rem, 1.8vw, 1.8rem); font-weight: 700; margin-top: 5px; margin-bottom: 0px;word-wrap: break-word;">${avg_loss:,.2f}</p>
                        </div>
                    """, unsafe_allow_html=True)

            st.write("---") # Garis pemisah

            with st.container():
                col5, col6, col7, col8 = st.columns(4)
                # Metrik biasa (Tetap warna Cyan)
                col5.metric("Consecutive Win", cons_win)
                col6.metric("Consecutive Loss", cons_loss)
                
                # HTML Card: Best Trade (Hijau)
                with col7:
                    st.markdown(f"""
                        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.3);">
                            <p style="color: #64748B; font-size: 14px; font-weight: 600; margin-bottom: 0px;">BEST TRADE</p>
                            <p style="color: #2ea043; font-size: clamp(1.2rem, 1.8vw, 1.8rem); font-weight: 700; margin-top: 5px; margin-bottom: 0px;word-wrap: break-word;">${best_trade:,.2f}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                # HTML Card: Worst Trade (Merah)
                with col8:
                    st.markdown(f"""
                        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.3);">
                            <p style="color: #64748B; font-size: 14px; font-weight: 600; margin-bottom: 0px;">WORST TRADE</p>
                            <p style="color: #da3633; font-size: clamp(1.2rem, 1.8vw, 1.8rem); font-weight: 700; margin-top: 5px; margin-bottom: 0px;word-wrap: break-word;">${worst_trade:,.2f}</p>
                        </div>
                    """, unsafe_allow_html=True)
                st.divider()
                
                # --- TABEL PER pair ---
                st.subheader("Detail Performa per pair")
                
                # Mengelompokkan data berdasarkan pair
                pair_stats = df_trades.groupby('pair').agg(
                    Total_Trade=('pnl', 'count'), 
                    Win_Count=('pnl', lambda x: (x > 0).sum()), 
                    Total_pnl=('pnl', 'sum')
                ).reset_index()
                
                # Hitung Winrate
                pair_stats['Winrate'] = (pair_stats['Win_Count'] / pair_stats['Total_Trade']) * 100
                
                # Buat DataFrame khusus untuk ditampilkan
                pair_display = pair_stats[['pair', 'Total_Trade', 'Winrate', 'Total_pnl']]
                
                # Tampilkan dengan Streamlit dataframe dan konfigurasi USD
                st.dataframe(
                    pair_display,
                    column_config={
                        "pair": "Ticker / pair",
                        "Total_Trade": "Total Trade",
                        "Winrate": st.column_config.NumberColumn("Winrate (%)", format="%.1f%%"),
                        "Total_pnl": st.column_config.NumberColumn("Total pnl (USD)", format="$%.2f")
                    },
                    hide_index=True, 
                    use_container_width=True
                )
                
                # --- TABEL RIWAYAT TRANSAKSI (TRADE HISTORY) ---
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("Riwayat Transaksi (Trade History)")
            
            df_trades = st.session_state.trades
            
            if not df_trades.empty:
                # Membuat area filter agar tabel lebih rapi dan fungsional
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    # Ambil daftar pair unik yang pernah ditradingkan
                    list_pair = ["Semua pair"] + list(df_trades['pair'].unique())
                    filter_pair = st.selectbox("🔍 Filter pair Aset:", list_pair)
                
                with col_f2:
                    filter_hasil = st.selectbox("Filter Hasil Trade:", ["Semua Hasil", "Win (Profit)", "Loss (Rugi)", "Break Even"])
                    
                # Menerapkan Logika Filter ke Data
                df_tampil = df_trades.copy()
                
                if filter_pair != "Semua pair":
                    df_tampil = df_tampil[df_tampil['pair'] == filter_pair]
                    
                if filter_hasil != "Semua Hasil":
                    if filter_hasil == "Win (Profit)":
                        df_tampil = df_tampil[df_tampil['pnl'] > 0]
                    elif filter_hasil == "Loss (Rugi)":
                        df_tampil = df_tampil[df_tampil['pnl'] < 0]
                    else: # Break Even
                        df_tampil = df_tampil[df_tampil['pnl'] == 0]
                
                # Menampilkan tabel jika data setelah difilter tidak kosong
                if not df_tampil.empty:
                    # Mengurutkan tanggal dari yang paling baru (Descending)
                    if 'tanggal_exit' in df_tampil.columns:
                        df_tampil = df_tampil.sort_values(by='tanggal_exit', ascending=False)
                    
                # --- TAMBAHAN BARU: Membuang kolom "Unnamed" ---
                    df_tampil = df_tampil.loc[:, ~df_tampil.columns.str.contains('^Unnamed')]
                    
                    # Ubah nama kolom pnl langsung di Pandas agar headernya rapi
                    df_tampil = df_tampil.rename(columns={"pnl": "pnl (USD)"})
                    
                    # --- FUNGSI PEWARNAAN KONDISIONAL ---
                    def color_profit_loss(val):
                        try:
                            nilai = float(val)
                            if nilai > 0:
                                return 'color: #10B981; font-weight: bold;' # Hijau Emerald
                            elif nilai < 0:
                                return 'color: #EF4444; font-weight: bold;' # Merah Rose
                            else:
                                return 'color: #64748B;' # Abu-abu untuk Break Even
                        except:
                            return ''

                    # Menerapkan warna dan format Dollar menggunakan Pandas Styler
                    styled_df = df_tampil.style.map(color_profit_loss, subset=['pnl (USD)']).format({
                        'pnl (USD)': '${:,.2f}'
                    })
                        
                    # Menampilkan tabel yang sudah di-style
                    st.dataframe(
                        styled_df, 
                        use_container_width=True, 
                        hide_index=True
                    )
                    
                else:
                    st.warning("Data dengan filter tersebut tidak ditemukan.")
            else:
                st.info("Belum ada data transaksi. Silakan input *trade* pertamamu di menu Input Trading.")
        else:
            st.warning("Data trading kosong. Silakan masuk ke menu 'Input Trading'.")

    elif menu == "Input Trading":
        st.title("Input Data Trading & Cashflow")
        col1, col2 = st.columns(2)
        
        # --- Form 1: Input Log Trading ---
        with col1:
            with st.form("trade_form"):
                st.subheader("Input Log Trading")
                t_entry = st.date_input("tanggal entry")
                pair = st.text_input("pair (Contoh: EURUSD)").upper()
                pos = st.selectbox("Position", ["Long", "Short"])
                t_exit = st.date_input("tanggal exit")
                pnl = st.number_input("pnl Bersih (USD)", step=1.0)
                
                if st.form_submit_button("Simpan Trade"):
                    # 1. Siapkan "Paket Data" dengan NAMA VARIABEL YANG BENAR
                    new_trade = {
                        "user_id": st.session_state.user_info.id, 
                        "tanggal_entry": str(t_entry),  # Variabel Anda: t_entry
                        "pair": pair,
                        "position": pos,                # Variabel Anda: pos
                        "tanggal_exit": str(t_exit) if t_exit else None, # Variabel Anda: t_exit
                        "pnl": float(pnl)
                    }
                    
                    try:
                        conn.table("trades").insert(new_trade).execute()
                        st.session_state.trades = fetch_supabase_data("trades")
                        st.success(f"🔥 Trade {pair} berhasil mendarat di Cloud!")
                    except Exception as e:
                        st.error(f"Gagal menyimpan ke database: {e}")

        # --- Form 2: Input Cashflow (Deposit/Withdraw) ---
        with col2:
            with st.form("cash_form"):
                st.subheader("Input Cashflow (Deposit/WD)")
                c_tgl = st.date_input("tanggal")
                c_tipe = st.selectbox("Tipe", ["Deposit", "Withdraw"])
                c_nom = st.number_input("Nominal (USD)", min_value=0.0)
                
                if st.form_submit_button("Simpan Cashflow"):
                    # Paket Data untuk Cashflow
                    new_cash = {
                        "user_id": st.session_state.user_info.id,
                        "tanggal": str(c_tgl),
                        "tipe": c_tipe,
                        "nominal": float(c_nom)
                    }
                    
                    try:
                        conn.table("cashflow").insert(new_cash).execute()
                        st.session_state.cash = fetch_supabase_data("cashflow")
                        st.success(f"💰 {c_tipe} sebesar {c_nom} berhasil dicatat di Cloud!")
                    except Exception as e:
                        st.error(f"Gagal mencatat cashflow: {e}")

        # ==========================================
        # FITUR HAPUS DATA (KOREKSI TYPO) - FULL WIDTH
        # ==========================================
        # (Perhatikan bahwa indentasi di sini ditarik kembali ke kiri, sejajar dengan col1, col2)
        st.markdown("<hr style='margin-top: 40px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        st.subheader("Manajemen Data (Hapus Baris)")
        st.write("Gunakan fitur ini jika terjadi kesalahan input (typo) pada Log Trading maupun data Deposit/Penarikan.")
        
        # 1. Menggunakan Radio Button horizontal agar rapi dan melebar
        jenis_data = st.radio("Pilih Data yang Ingin Dikoreksi:", ["Log Trading", "Deposit / Withdrawal"], horizontal=True)
        
        # 2. Menentukan dataset mana yang sedang aktif
        if jenis_data == "Log Trading":
            df_edit = st.session_state.trades
            nama_file = 'trades.csv'
        else:
            df_edit = st.session_state.cash
            nama_file = 'cashflow.csv'
            
        if not df_edit.empty:
            # --- TAMBAHAN BARU: Membuang kolom "Unnamed" sebelum ditampilkan ---
            df_edit_tampil = df_edit.loc[:, ~df_edit.columns.str.contains('^Unnamed')]
            
            # Menampilkan tabel secara penuh (Full-width) menggunakan data yang sudah bersih
            st.dataframe(df_edit_tampil, use_container_width=True)
            
            # 3. Form Hapus tanpa kolom (Melebar penuh dari kiri ke kanan)
            st.markdown("<br>", unsafe_allow_html=True)
            index_to_delete = st.selectbox(f"Pilih Nomor Index yang ingin dihapus:", df_edit.index)
            
            st.write("") # Sedikit spasi agar tidak terlalu menempel
            
            # Tombol melebar penuh
            if st.button(f"Hapus Baris Terpilih", use_container_width=True):
                # Eksekusi penghapusan berdasarkan tabel yang dipilih
                if jenis_data == "Log Trading":
                    st.session_state.trades = st.session_state.trades.drop(index_to_delete).reset_index(drop=True)
                    st.session_state.trades.to_csv(nama_file, index=False)
                else:
                    st.session_state.cash = st.session_state.cash.drop(index_to_delete).reset_index(drop=True)
                    st.session_state.cash.to_csv(nama_file, index=False)
                
                st.success(f"Data pada Index {index_to_delete} berhasil dihapus dari {jenis_data}!")
                st.rerun() # Refresh halaman
        else:
            st.info(f"Data pada {jenis_data} masih kosong.")

    elif menu == "Jurnal Strategi":
        st.title("Catatan Strategi & Trading Plan")
        st.write("Gunakan halaman ini untuk mencatat *checklist* evaluasi sebelum melakukan *entry*.")
        
        # Menentukan nama file untuk menyimpan catatan
        NOTE_FILE = "strategy_notes.txt"
        
        # Template default yang relevan dengan parameter analisis teknikalmu
        default_notes = """### 📋 CONTOH Checklist Breakout & Fase Markup
        
    1. **Analisis Fase Konsolidasi:**
    - [ ] Apakah durasi konsolidasi sudah cukup matang?
    - [ ] Bagaimana struktur akumulasinya?

    2. **Konfirmasi Indikator (Relative Volume & Price Spread):**
    - [ ] Apakah ada lonjakan volume yang signifikan saat *breakout*?
    - [ ] Apakah *price spread* (rentang harga) melebar searah dengan tren?

    3. **Manajemen Risiko:**
    - [ ] *Risk/Reward Ratio* minimal 1:2?
    - [ ] Penentuan level *stop-loss* yang logis di bawah level *support* minor?

    *Catatan tambahan untuk evaluasi saham LQ45:*
    Fokus pada likuiditas dan sentimen arah pasar secara keseluruhan sebelum mengambil posisi agresif.
    """
        
        # Membaca catatan yang sudah tersimpan sebelumnya (jika ada)
        if os.path.exists(NOTE_FILE):
            with open(NOTE_FILE, "r", encoding="utf-8") as f:
                saved_notes = f.read()
        else:
            saved_notes = default_notes

        # Menampilkan area teks yang bisa diedit
        notes = st.text_area("Trading Notes / Aturan Strategi:", value=saved_notes, height=400)
        
        # Tombol untuk menyimpan ke dalam file .txt
        if st.button("Simpan Catatan Permanen"):
            with open(NOTE_FILE, "w", encoding="utf-8") as f:
                f.write(notes)
            st.success("Catatan strategimu berhasil disimpan permanen!")

    # ==========================================
    # BAGIAN 2: INVESTING (FITUR BARU)
    # ==========================================
    elif menu == "Input Investasi":
        st.title("Input Data Investasi (Multi-Aset)")
        
        col1, col2 = st.columns([1.5, 1]) # Kolom kiri lebih lebar sedikit
        
        with col1:
            st.subheader("Catat Portofolio Baru")
            
            # 1. Pilihan kelas aset (DITARUH DI LUAR FORM AGAR BISA BERUBAH REAL-TIME!)
            kelas_aset = st.selectbox("Pilih kelas aset:", ["Saham Indonesia", "Kripto", "Emas", "Reksadana", "Obligasi (SBN)"])
            
            # 2. Form Input (Label akan otomatis mengikuti kelas aset di atas)
            with st.form("invest_form"):
                if kelas_aset in ["Reksadana", "Obligasi (SBN)"]:
                    ticker = st.text_input("Nama Produk (Contoh: Sucorinvest / ORI023)")
                    satuan = "Unit"
                    pengali = 1
                    mata_uang = "IDR"  # <-- Tambahan mata uang
                    st.caption("💡 Tidak perlu format Ticker Yahoo Finance.")
                elif kelas_aset == "Saham Indonesia":
                    ticker = st.text_input("Ticker Saham (Contoh: BBCA.JK)").upper()
                    satuan = "Lot"
                    pengali = 100 
                    mata_uang = "IDR"  # <-- Tambahan mata uang
                    st.caption("💡 Wajib gunakan akhiran .JK untuk saham Indonesia.")
                elif kelas_aset == "Kripto":
                    ticker = st.text_input("Ticker Kripto (Contoh: BTC-USD)").upper()
                    satuan = "Koin / Token"
                    pengali = 1
                    mata_uang = "USD"  # <-- Tambahan mata uang
                else: # Emas
                    ticker = st.text_input("Ticker Emas (Contoh: GC=F atau Antam)").upper()
                    satuan = "Gram / Oz"
                    pengali = 1
                    mata_uang = "USD"  # <-- Tambahan mata uang (Jika antam bisa diganti IDR)
                
                t_inv = st.date_input("tanggal Transaksi")
                action_inv = st.selectbox("Aksi Transaksi", ["Buy", "Sell"])
                
                # --- LABEL KINI 100% DINAMIS MENGKUTI kelas aset ---
                harga_inv = st.number_input(f"harga Beli/Jual per {satuan} ({mata_uang})", min_value=0.0, step=100.0)
                jumlah_input = st.number_input(f"Jumlah Pembelian ({satuan})", min_value=0.0, step=0.01)
                
                if st.form_submit_button("Simpan Investasi"):
                    # Menghitung jumlah aktual berdasarkan pengali (contoh: Lot -> Lembar)
                    jumlah_aktual = jumlah_input * pengali
                    
                    # --- KODE BARU: KIRIM DATA KE SUPABASE CLOUD ---
                    new_invest = {
                        "user_id": st.session_state.user_info.id, # Identitas user
                        "tanggal": str(t_inv), 
                        "kelas_aset": kelas_aset,
                        "ticker": ticker, 
                        "action": action_inv, 
                        "harga": float(harga_inv), 
                        "jumlah": float(jumlah_aktual)
                    }
                    
                    try:
                        conn.table("investing").insert(new_invest).execute()
                        # Refresh data di session state agar tabel di halaman lain langsung update
                        st.session_state.investing = fetch_supabase_data("investing")
                        st.success(f"✅ Data {kelas_aset} ({ticker}) berhasil mendarat di Cloud!")
                    except Exception as e:
                        st.error(f"Gagal menyimpan investasi: {e}")
                    
        with col2:
            st.info("💡 **Panduan Diversifikasi Aset:**\n\n"
                    "- **Saham:** Input dalam satuan *Lot*. Sistem otomatis menyimpannya sebagai lembar saham.\n\n"
                    "- **Kripto & Emas:** Mendukung input desimal (Contoh: Beli 0.05 BTC atau 2.5 Gram Emas).\n\n"
                    "- **Reksadana/Obligasi:** Cukup masukkan Nama Produk, harga NAV/Unit rata-rata, dan Jumlah Unit. Aset ini bersifat statis dan tidak ditarik dari Yahoo Finance setiap detik.")

        # ==========================================
        # FITUR HAPUS DATA INVESTASI (FULL WIDTH)
        # ==========================================
        st.markdown("<hr style='margin-top: 40px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        st.subheader("Manajemen Data (Hapus Baris)")
        
        df_inv_edit = st.session_state.investing
        if not df_inv_edit.empty:
            # 1. Bersihkan kolom yang tidak perlu
            kolom_dibuang = ['Lot']
            df_inv_tampil = df_inv_edit.drop(columns=kolom_dibuang, errors='ignore')
            df_inv_tampil = df_inv_tampil.loc[:, ~df_inv_tampil.columns.str.contains('^Unnamed')]
            
            # 2. --- TRIK AGAR INDEX DIMULAI DARI 1 ---
            df_inv_tampil.index = range(1, len(df_inv_tampil) + 1)
            
            # Tampilkan Tabel
            st.dataframe(df_inv_tampil, use_container_width=True)
            
            # 3. Form Hapus
            st.markdown("<br>", unsafe_allow_html=True)
            # Selectbox sekarang akan menampilkan angka 1, 2, 3... sesuai tabel di atas
            pilihan_user = st.selectbox("Pilih Nomor Index yang ingin dihapus:", df_inv_tampil.index)
            
            if st.button("Hapus Baris Terpilih", use_container_width=True):
                # Karena di tabel kita tambah 1, maka untuk menghapus di database asli kita kurang 1
                index_asli = pilihan_user - 1
                
                st.session_state.investing = st.session_state.investing.drop(index_asli).reset_index(drop=True)
                st.session_state.investing.to_csv('investing.csv', index=False)
                st.success(f"Data Investasi nomor {pilihan_user} berhasil dihapus!")
                st.rerun()
        else:
            st.info("Data Investasi masih kosong.")

    elif menu == "Portfolio Live":
        st.title("Portfolio Live (Multi-Aset)")
        
        df_inv = st.session_state.investing
        
        if not df_inv.empty:
            st.write("Sedang menarik data harga real-time dan kurs Rupiah terbaru dari Yahoo Finance... ⏳")
            
            # 1. Menarik Kurs USD/IDR secara Real-Time
            try:
                kurs_idr_data = yf.Ticker("IDR=X").history(period="1d")
                kurs_idr = kurs_idr_data['Close'].iloc[-1]
            except:
                kurs_idr = 15500.0 # harga fallback jika sedang offline/gagal
                st.warning("Gagal menarik kurs live. Menggunakan kurs fallback Rp 15.500/USD")

            # Menampilkan badge kurs hari ini
            st.info(f"💵 **Kurs Live USD/IDR Hari Ini:** Rp {kurs_idr:,.0f} / USD")
            
            # 2. Memproses Data Portofolio
            portfolio_summary = []
            total_modal_semua_idr = 0.0
            total_nilai_semua_idr = 0.0
            
            # Mengelompokkan berdasarkan kelas aset dan Ticker
            for (kelas, ticker), group in df_inv.groupby(['kelas_aset', 'ticker']):
                # Menghitung sisa barang (Buy - Sell)
                total_beli = group[group['action'] == 'Buy']['jumlah'].sum()
                total_jual = group[group['action'] == 'Sell']['jumlah'].sum()
                qty_sekarang = total_beli - total_jual
                
                if qty_sekarang > 0:
                    # Menghitung harga Beli Rata-Rata (Weighted Average)
                    df_beli = group[group['action'] == 'Buy']
                    if not df_beli.empty:
                        avg_price = (df_beli['harga'] * df_beli['jumlah']).sum() / df_beli['jumlah'].sum()
                    else:
                        avg_price = 0
                    
                    # Menarik harga Saat Ini (Live)
                    current_price = avg_price # Default ke harga beli jika aset statis
                    if kelas in ["Saham Indonesia", "Kripto", "Emas"]:
                        try:
                            ticker_yf = yf.Ticker(ticker)
                            hist = ticker_yf.history(period="1d")
                            if not hist.empty:
                                current_price = hist['Close'].iloc[-1]
                        except:
                            pass # Tetap pakai harga rata-rata jika YF error/ticker salah
                    
                    # Konversi ke Rupiah Berdasarkan kelas aset
                    if kelas in ["Kripto", "Emas"]:
                        # Aset dalam USD (Floating Rate)
                        modal_idr = (qty_sekarang * avg_price) * kurs_idr
                        nilai_kini_idr = (qty_sekarang * current_price) * kurs_idr
                        mata_uang = "USD"
                    else:
                        # Saham IDR, Reksadana, Obligasi (Langsung Rupiah)
                        modal_idr = qty_sekarang * avg_price
                        nilai_kini_idr = qty_sekarang * current_price
                        mata_uang = "IDR"
                    
                    # Menghitung pnl
                    pnl_idr = nilai_kini_idr - modal_idr
                    return_pct = (pnl_idr / modal_idr * 100) if modal_idr > 0 else 0
                    
                    total_modal_semua_idr += modal_idr
                    total_nilai_semua_idr += nilai_kini_idr
                    
                    portfolio_summary.append({
                        "kelas aset": kelas,
                        "Ticker": ticker,
                        "Jumlah Satuan": qty_sekarang,
                        "Mata Uang": mata_uang,
                        "harga Rata2": avg_price,
                        "harga Live": current_price,
                        "Nilai Total (IDR)": nilai_kini_idr,
                        "Return (%)": return_pct
                    })
            
            # --- MENAMPILKAN DASHBOARD ---
            if portfolio_summary:
                df_port = pd.DataFrame(portfolio_summary) # Mendefinisikan tabel utama
                
                # 1. Metrik Utama (Tetap di atas)
                col_m1, col_m2, col_m3 = st.columns(3)
                pnl_keseluruhan = total_nilai_semua_idr - total_modal_semua_idr
                pct_keseluruhan = (pnl_keseluruhan / total_modal_semua_idr * 100) if total_modal_semua_idr > 0 else 0
                
                col_m1.metric("Total Modal Investasi (IDR)", f"Rp {total_modal_semua_idr:,.0f}")
                col_m2.metric("Nilai Portofolio Saat Ini", f"Rp {total_nilai_semua_idr:,.0f}", f"{pnl_keseluruhan:,.0f} Rp")
                col_m3.metric("Return Keseluruhan", f"{pct_keseluruhan:.2f}%")
                
                st.write("---")
                
                # ==========================================
                # BAGIAN 1: ALOKASI ASET (Posisi Tengah)
                # ==========================================
                st.subheader("Alokasi Aset", anchor=False)
                
                # Trik 3 kolom: Kolom kiri(1), Tengah(2), Kanan(1). Grafik dimasukkan ke tengah agar presisi.
                col_kiri, col_tengah, col_kanan = st.columns([1, 2, 1])
                with col_tengah:
                    df_alokasi = df_port.groupby('kelas aset')['Nilai Total (IDR)'].sum().reset_index()
                    
                    fig_pie = px.pie(
                        df_alokasi, 
                        names='kelas aset', 
                        values='Nilai Total (IDR)', 
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig_pie.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(t=10, b=10, l=0, r=0),
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                    
                st.markdown("<br>", unsafe_allow_html=True)
                
                # ==========================================
                # BAGIAN 2: RINCIAN ASET (Posisi Bawah, Lebar Penuh)
                # ==========================================
                st.subheader("Rincian Aset", anchor=False)
                
                def color_return(val):
                    try:
                        nilai = float(val)
                        if nilai > 0: return 'color: #10B981; font-weight: bold;'
                        elif nilai < 0: return 'color: #EF4444; font-weight: bold;'
                        else: return 'color: #64748B;'
                    except:
                        return ''
                        
                # --- FUNGSI FORMATTER CUSTOM ---
                def format_angka_pintar(val):
                    if val == int(val): # Jika angka bulat
                        return f"{int(val):,}"
                    return f"{val:g}" # Menghilangkan nol berlebih di belakang koma (misal 0.0500 -> 0.05)

                def format_harga_pintar(val):
                    # Jika angka sangat besar (IDR), hilangkan desimal
                    if val >= 100: 
                        return f"{int(val):,}"
                    # Jika angka kecil (USD/Kripto), berikan 2 desimal
                    return f"{val:,.2f}"

                # --- MENERAPKAN STYLE KE TABEL ---
                styled_port = df_port.style.map(color_return, subset=['Return (%)']).format({
                    'Jumlah Satuan': format_angka_pintar,
                    'harga Rata2': format_harga_pintar,
                    'harga Live': format_harga_pintar,
                    'Nilai Total (IDR)': 'Rp {:,.0f}',
                    'Return (%)': '{:.2f}%'
                })
                
                st.dataframe(styled_port, use_container_width=True, hide_index=True)
        
                    
            else:
                st.info("Anda belum memiliki aset yang aktif (Semua aset mungkin sudah dijual).")
                
        else:
            st.info("Data investasi masih kosong. Silakan masuk ke menu 'Input Investasi' untuk mulai mencatat.")

    elif menu == "Kalkulator Finansial":
        st.title("Advanced Financial Analytics")
        st.write("Gunakan alat ini untuk memproyeksikan target investasi dan menghitung valuasi risiko.")
        
        # Membagi layar menjadi dua tab
        tab_capm, tab_compound = st.tabs(["CAPM Expected Return", "Compounding"])
        
        # --- TAB 1: PORTFOLIO CAPM & MPT CALCULATOR ---
        with tab_capm:
            st.subheader("Capital Asset Pricing Model (CAPM) - Multi Asset")
            st.markdown("Menghitung ekspektasi imbal hasil berdasarkan **bobot** masing-masing aset.")
            
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                tickers_input = st.text_input("Kode Saham (Pisahkan koma, contoh: BBCA, ASII, BMRI):", "BBCA, ASII").upper()
                weights_input = st.text_input("Bobot Portofolio % (Pisahkan koma, total 100%):", "60, 40")
                
                col_rf, col_rm = st.columns(2)
                rf_rate = col_rf.number_input("Risk-Free Rate (Suku Bunga BI) %:", value=6.00, step=0.1) / 100
                rm_rate = col_rm.number_input("Expected Market Return (IHSG) %:", value=10.00, step=0.1) / 100
                
            with col_c2:
                st.write("  ") # Spacing
                if st.button("Hitung Portfolio Expected Return", use_container_width=True):
                    # Membersihkan input dari spasi berlebih
                    ticker_list = [t.strip() for t in tickers_input.split(",")]
                    weight_list_str = [w.strip() for w in weights_input.split(",")]
                    
                    # VALIDASI 1: Jumlah saham harus sama dengan jumlah bobot
                    if len(ticker_list) != len(weight_list_str):
                        st.error("⚠️ Jumlah kode saham dan jumlah input bobot harus sama!")
                    else:
                        try:
                            # Mengubah string bobot menjadi desimal
                            weight_list = [float(w) / 100 for w in weight_list_str]
                            
                            # VALIDASI 2: Peringatan jika total bobot tidak 100%
                            if abs(sum(weight_list) - 1.0) > 0.01:
                                st.warning(f"💡 Info: Total bobot alokasi kamu saat ini adalah {sum(weight_list)*100:.0f}%. Idealnya adalah 100%.")
                                
                            with st.spinner("Menarik data Beta dari Yahoo Finance..."):
                                portfolio_data = []
                                total_portfolio_beta = 0
                                market_premium = rm_rate - rf_rate
                                
                                for i, t in enumerate(ticker_list):
                                    ticker_yf = f"{t}.JK"
                                    stock_info = yf.Ticker(ticker_yf).info
                                    
                                    beta = stock_info.get('beta', 1.0)
                                    exp_return = rf_rate + (beta * market_premium)
                                    
                                    # Menggunakan bobot kustom
                                    w = weight_list[i]
                                    weighted_beta = beta * w
                                    total_portfolio_beta += weighted_beta
                                    
                                    portfolio_data.append({
                                        "Saham": t,
                                        "Bobot (%)": w * 100,
                                        "Beta": beta,
                                        "Expected Return (%)": exp_return * 100
                                    })
                                
                                portfolio_exp_return = rf_rate + (total_portfolio_beta * market_premium)
                                
                                st.success("Kalkulasi berhasil!")
                                
                                # Menampilkan metrik Portofolio
                                st.markdown("""
                                    <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                                        <h4 style="margin-top: 0px; color: #64748B;">TOTAL PORTFOLIO METRICS</h4>
                                        <div style="display: flex; justify-content: space-between;">
                                            <div>
                                                <p style="color: #64748B; margin-bottom: 5px; font-size: 14px;">Portfolio Beta (Risiko)</p>
                                                <p style="color: #2563EB; font-size: 24px; font-weight: 700; margin-top: 0px;">{:.2f}</p>
                                            </div>
                                            <div>
                                                <p style="color: #64748B; margin-bottom: 5px; font-size: 14px;">Portfolio Expected Return</p>
                                                <p style="color: #2ea043; font-size: 24px; font-weight: 700; margin-top: 0px;">{:.2f}%</p>
                                            </div>
                                        </div>
                                    </div>
                                """.format(total_portfolio_beta, portfolio_exp_return * 100), unsafe_allow_html=True)
                                
                        except ValueError:
                            st.error("⚠️ Pastikan input bobot hanya berupa angka (pisahkan dengan koma).")
                        except Exception as e:
                            st.error(f"⚠️ Gagal menarik data. Error: {e}")
            
            # Menampilkan Tabel dan Grafik secara berdampingan
            if 'portfolio_data' in locals() and len(portfolio_data) > 0:
                st.divider()
                st.subheader("Rincian Alokasi & Return per Aset")
                
                df_portfolio = pd.DataFrame(portfolio_data)
                
                # ==========================================
                # 1. TABEL DI ATAS (FULL WIDTH)
                # ==========================================
                st.dataframe(
                    df_portfolio, 
                    hide_index=True, 
                    use_container_width=True,
                    column_config={
                        "Bobot (%)": st.column_config.NumberColumn(format="%.1f%%"),
                        "Beta": st.column_config.NumberColumn(format="%.2f"),
                        "Expected Return (%)": st.column_config.NumberColumn(format="%.2f%%")
                    }
                )
                
                st.markdown("<br>", unsafe_allow_html=True) # Spasi pembatas
                
                # ==========================================
                # 2. GRAFIK PIE DI BAWAH (TENGAH)
                # ==========================================
                st.subheader("Persentase Alokasi")
                
                # Trik 3 kolom untuk menjepit grafik di tengah
                col_kiri, col_tengah, col_kanan = st.columns([1, 2, 1])
                
                with col_tengah:
                    # Menggunakan fig_alloc sesuai aslinya, dan menambahkan legenda horizontal di bawah
                    fig_alloc = px.pie(df_portfolio, values='Bobot (%)', names='Saham', hole=0.4,
                                    color_discrete_sequence=px.colors.sequential.Teal)
                    fig_alloc.update_layout(
                        margin=dict(t=10, b=10, l=0, r=0),
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                    )
                    st.plotly_chart(fig_alloc, use_container_width=True)

        # --- TAB 2: COMPOUNDING & PENSIUN ---
        with tab_compound:
            st.subheader("Simulasi Compounding Interest")
            
            c1, c2, c3 = st.columns(3)
            modal_awal = c1.number_input("Modal Awal (Rp):", min_value=0, value=10000000, step=1000000)
            investasi_bulanan = c2.number_input("Tambahan per Bulan (Rp):", min_value=0, value=1000000, step=100000)
            asumsi_return = c3.number_input("Asumsi Return per Tahun (%):", min_value=1.0, value=12.0, step=1.0)
            
            tahun_pensiun = st.slider("Durasi Investasi (Tahun):", min_value=1, max_value=40, value=10)
            
            # Kalkulasi Array untuk Grafik
            saldo = modal_awal
            data_proyeksi = []
            for tahun in range(1, tahun_pensiun + 1):
                modal_terkumpul_tahun_ini = modal_awal + (investasi_bulanan * 12 * tahun)
                for bulan in range(12):
                    saldo += investasi_bulanan
                    saldo *= (1 + (asumsi_return / 100 / 12))
                    
                data_proyeksi.append({
                    "Tahun": f"Tahun {tahun}",
                    "Total Modal Disetor": modal_terkumpul_tahun_ini,
                    "Total Nilai Portofolio": saldo
                })
                
            df_proyeksi = pd.DataFrame(data_proyeksi)
            
            # Menampilkan Grafik dengan Plotly
            fig_comp = px.bar(df_proyeksi, x="Tahun", y=["Total Modal Disetor", "Total Nilai Portofolio"], 
                            barmode="overlay", title="Proyeksi Pertumbuhan Aset (Compounding Magic)",
                            color_discrete_sequence=['#30363D', '#00FFCC'], template="plotly_dark")
            st.plotly_chart(fig_comp, use_container_width=True)
            
            st.info(f"💡 Dalam {tahun_pensiun} tahun, uang yang kamu setorkan adalah **Rp {df_proyeksi['Total Modal Disetor'].iloc[-1]:,.0f}**, namun dengan keajaiban *Compounding Interest*, nilainya bertumbuh menjadi **Rp {saldo:,.0f}**!")

    elif menu == "Dashboard Utama":
        st.title("Dashboard Utama (Keseluruhan)")
        st.write("Ringkasan total kekayaan Anda dari aktivitas Trading dan Portofolio Investasi.")
        
        # ==========================================
        # 1. KALKULASI SALDO TRADING (FIX RATE)
        # ==========================================
        FIX_RATE = 14000 # Kurs Fix Rate Broker
        
        df_trades = st.session_state.trades
        df_cash = st.session_state.cash
        
        total_depo = df_cash[df_cash['tipe'] == 'Deposit']['nominal'].sum() if not df_cash.empty else 0
        total_wd = df_cash[df_cash['tipe'] == 'Withdraw']['nominal'].sum() if not df_cash.empty else 0
        total_pnl = df_trades['pnl'].sum() if not df_trades.empty else 0
        
        equity_usd = total_depo - total_wd + total_pnl
        equity_idr = equity_usd * FIX_RATE
        
        # ==========================================
        # 2. KALKULASI PORTOFOLIO INVESTASI (FLOATING RATE)
        # ==========================================
        df_inv = st.session_state.investing
        total_investasi_idr = 0.0
        
        # Dictionary untuk menyimpan nilai per kelas aset untuk grafik
        alokasi_gabungan = {"Saldo Trading (Kas & Margin)": equity_idr}
        
        if not df_inv.empty:
            # Tarik kurs live
            try:
                kurs_idr = yf.Ticker("IDR=X").history(period="1d")['Close'].iloc[-1]
            except:
                kurs_idr = 15500.0 # Fallback
                
            for (kelas, ticker), group in df_inv.groupby(['kelas_aset', 'ticker']):
                total_beli = group[group['action'] == 'Buy']['jumlah'].sum()
                total_jual = group[group['action'] == 'Sell']['jumlah'].sum()
                qty_sekarang = total_beli - total_jual
                
                if qty_sekarang > 0:
                    # Cari harga beli rata-rata
                    df_beli = group[group['action'] == 'Buy']
                    avg_price = (df_beli['harga'] * df_beli['jumlah']).sum() / df_beli['jumlah'].sum() if not df_beli.empty else 0
                    
                    # Tarik harga live
                    current_price = avg_price
                    if kelas in ["Saham Indonesia", "Kripto", "Emas"]:
                        try:
                            hist = yf.Ticker(ticker).history(period="1d")
                            if not hist.empty:
                                current_price = hist['Close'].iloc[-1]
                        except:
                            pass
                    
                    # Hitung Nilai (IDR)
                    if kelas in ["Kripto", "Emas"]:
                        nilai_kini_idr = (qty_sekarang * current_price) * kurs_idr
                    else:
                        nilai_kini_idr = qty_sekarang * current_price
                        
                    total_investasi_idr += nilai_kini_idr
                    
                    # Tambahkan ke dictionary alokasi
                    nama_kategori = f"Investasi: {kelas}"
                    if nama_kategori in alokasi_gabungan:
                        alokasi_gabungan[nama_kategori] += nilai_kini_idr
                    else:
                        alokasi_gabungan[nama_kategori] = nilai_kini_idr

        # ==========================================
        # 3. METRIK TOTAL KEKAYAAN (NET WORTH)
        # ==========================================
        grand_total_idr = equity_idr + total_investasi_idr
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_m1, col_m2, col_m3 = st.columns(3)
        
        # Metrik Utama Net Worth
        col_m1.metric("Total Net Worth", f"Rp {grand_total_idr:,.0f}")
        
        # Rincian Trading vs Investasi
        col_m2.metric("Ekuitas Trading", f"Rp {equity_idr:,.0f}")
        col_m3.metric("Nilai Investasi", f"Rp {total_investasi_idr:,.0f}")
        
        st.markdown("<hr style='margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        
        # ==========================================
        # FITUR BARU: FINANCIAL GOAL TRACKER
        # ==========================================
        st.subheader("🎯 Target Kekayaan (Financial Goal)")
        
        # Inisialisasi default target di session_state (misal: 100 Juta) jika belum ada
        if 'financial_goal' not in st.session_state:
            st.session_state.financial_goal = 100000000.0
            
        # Layout untuk Input Target dan Progress Bar
        col_goal_input, col_goal_bar = st.columns([1, 2.5])
        
        with col_goal_input:
            # Input target di halaman yang sama
            target_baru = st.number_input(
                "Setel Target Net Worth (Rp):", 
                min_value=0.0, 
                value=float(st.session_state.financial_goal), 
                step=5000000.0, # Naik/turun per 5 Juta
                format="%f"
            )
            st.session_state.financial_goal = target_baru
            
        with col_goal_bar:
            # Kalkulasi Persentase
            target = st.session_state.financial_goal
            if target > 0:
                progress_ratio = grand_total_idr / target
                progress_pct = progress_ratio * 100
            else:
                progress_ratio = 0.0
                progress_pct = 0.0
                
            # Streamlit st.progress hanya menerima nilai 0.0 sampai 1.0
            progress_bar_val = min(progress_ratio, 1.0)
            
            # Menampilkan teks persentase
            st.markdown(f"**Progress Anda:** <span style='color: #10B981; font-weight: bold; font-size: 18px;'>{progress_pct:,.2f}%</span> menuju target 🚀", unsafe_allow_html=True)
            
            # Menampilkan Bar Progress
            st.progress(progress_bar_val)
            
            # Pesan motivasi dinamis
            # Pesan motivasi dinamis (Rata Kanan & Tanpa Kotak)
            if progress_ratio >= 1.0:
                pesan = "🎉 Luar biasa! Anda telah mencapai target finansial Anda."
                warna = "#10B981" # Hijau untuk Sukses
            elif progress_ratio >= 0.5:
                pesan = "🔥 Hebat! Anda sudah melewati setengah jalan. Tetap disiplin!"
                warna = "#3B82F6" # Biru untuk Info
            elif progress_ratio > 0.0:
                pesan = "💪 Perjalanan baru dimulai. Biarkan compounding bekerja."
                warna = "#F59E0B" # Oranye/Emas untuk Peringatan (Warning)
            else:
                pesan = "Ayo mulai perjalanan finansialmu!"
                warna = "#64748B" # Abu-abu
                
            # Menggunakan HTML untuk text-align: right
            st.markdown(f"<div style='text-align: right; color: {warna}; font-size: 13px; margin-top: 8px; font-weight: 500;'>{pesan}</div>", unsafe_allow_html=True)
                
        st.markdown("<hr style='margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        
        # ==========================================
        # 4. VISUALISASI ALOKASI KEKAYAAN KESELURUHAN
        # ==========================================
        st.subheader("Alokasi Total Kekayaan Bersih")
        
        # Mengubah dictionary menjadi dataframe untuk Plotly
        df_gabungan = pd.DataFrame(list(alokasi_gabungan.items()), columns=['Kategori Aset', 'Nilai (IDR)'])
        # Buang nilai yang 0 atau minus (agar tidak merusak grafik pie)
        df_gabungan = df_gabungan[df_gabungan['Nilai (IDR)'] > 0]
        
        if not df_gabungan.empty:
            col_g1, col_g2, col_g3 = st.columns([1, 2, 1])
            with col_g2:
                fig_networth = px.pie(
                    df_gabungan, 
                    names='Kategori Aset', 
                    values='Nilai (IDR)', 
                    hole=0.45,
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig_networth.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=20, b=20, l=0, r=0),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
                # Menambahkan teks di tengah Donut
                fig_networth.add_annotation(text="Net Worth", x=0.5, y=0.5, font_size=20, showarrow=False)
                
                st.plotly_chart(fig_networth, use_container_width=True)
        else:
            st.info("Belum ada data Kekayaan yang dapat ditampilkan. Silakan input Deposit/Trade atau Investasi baru.")

    elif menu == "News":
        st.title("Berita Pasar Terkini")
        st.write("Pantau berita market dan finansial dari berbagai sumber lokal maupun global.")
        
        st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        
        # ==========================================
        # 1. DAFTAR SUMBER BERITA (BISA DITAMBAH BEBAS)
        # ==========================================
        sumber_berita = {
            # --- LOKAL INDONESIA ---
            "CNBC Indonesia": "https://www.cnbcindonesia.com/market/rss",
            "CNN Ekonomi": "https://www.cnnindonesia.com/ekonomi/rss",
            
            # --- GLOBAL MARKET ---
            "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
            "Wall Street Journal": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
            "MarketWatch": "http://feeds.marketwatch.com/marketwatch/topstories/",
            "Investing.com": "https://www.investing.com/rss/news.rss",
            "Seeking Alpha": "https://seekingalpha.com/market_currents.xml",
            
            # --- CRYPTO & FINTECH ---
            "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "Bitcoin Magazine": "https://bitcoinmagazine.com/.rss/full/",
            "TechCrunch Fintech": "https://techcrunch.com/category/fintech/feed/"
        }
        
        # 2. Membuat Dropdown untuk Memilih Sumber Berita
        pilihan_sumber = st.selectbox("Pilih Sumber Berita:", list(sumber_berita.keys()))
        rss_url = sumber_berita[pilihan_sumber]
        
        # URL Gambar Cadangan (Fallback)
        fallback_image = "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80"
        
        with st.spinner(f"Mengambil berita dari {pilihan_sumber}... ⏳"):
            try:
                feed = feedparser.parse(rss_url)
                
                if feed.entries:
                    # Mengambil 12 berita terbaru
                    for entry in feed.entries[:12]:
                        judul = entry.title
                        link = entry.link
                        
                        # Mengatasi perbedaan format waktu tiap situs
                        tanggal = entry.get('published', entry.get('updated', 'Waktu tidak diketahui'))
                        
                        # 1. Mengambil dan Membersihkan Deskripsi
                        deskripsi_mentah = entry.get('description', entry.get('summary', ''))
                        deskripsi_bersih = re.sub('<[^<]+>', '', deskripsi_mentah)
                        deskripsi_singkat = deskripsi_bersih[:150] + "..." if len(deskripsi_bersih) > 150 else deskripsi_bersih
                        
                        # 2. LOGIKA PENCARIAN GAMBAR YANG LEBIH AGRESIF
                        image_url = fallback_image # Default awal
                        
                        # Cek 1: Jalur Standar (Enclosures)
                        if 'enclosures' in entry and len(entry.enclosures) > 0:
                            image_url = entry.enclosures[0].get('href', fallback_image)
                        
                        # Cek 2: Jalur Media Content (Sering dipakai Seeking Alpha/Global)
                        elif 'media_content' in entry and len(entry.media_content) > 0:
                            image_url = entry.media_content[0].get('url', fallback_image)
                            
                        # Cek 3: Jalur Media Thumbnail
                        elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
                            image_url = entry.media_thumbnail[0].get('url', fallback_image)
                        
                        # Cek 4: Mencari di dalam isi konten (Cari URL yang berakhiran .jpg atau .png)
                        else:
                            # Mencari di deskripsi atau summary mentah
                            konten_lengkap = entry.get('description', '') + entry.get('summary', '')
                            img_match = re.search(r'src="([^">]+(?:jpg|png|jpeg|webp)[^">]*)"', konten_lengkap, re.IGNORECASE)
                            if img_match:
                                image_url = img_match.group(1)
                                
                        # --- NAMA SUMBER DINAMIS ---
                        # Menghapus emoji di depan untuk ditampilkan di label bawah
                        nama_sumber_label = pilihan_sumber[3:].upper()
                                
                        # --- DESAIN KARTU HTML ---
                        card_html = f"""
                        <a href="{link}" target="_blank" style="text-decoration: none; color: inherit;">
                            <div style="border: 1px solid #E2E8F0; border-radius: 12px; padding: 15px; margin-bottom: 20px; background-color: #FFFFFF; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); transition: 0.3s; display: flex; align-items: center; gap: 20px;">
                                <div style="flex-shrink: 0;">
                                    <img src="{image_url}" alt="thumbnail" style="width: 140px; height: 100px; object-fit: cover; border-radius: 8px;">
                                </div>
                                <div>
                                    <h4 style="margin-top: 0px; margin-bottom: 8px; color: #0F172A; font-family: 'Inter', sans-serif; font-size: 16px;">{judul}</h4>
                                    <p style="color: #475569; font-size: 13px; margin-bottom: 8px; line-height: 1.4;">{deskripsi_singkat}</p>
                                    <span style="color: #64748B; font-size: 11px; font-weight: 600;">🔗 {nama_sumber_label} | 🕒 {tanggal}</span>
                                </div>
                            </div>
                        </a>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
                else:
                    st.info("Saat ini tidak ada berita yang dapat ditampilkan dari sumber ini.")
            except Exception as e:
                st.error(f"Gagal menarik data berita. Error: {e}")

    elif menu == "Live Market Overview":
        st.title("Live Market Overview & Macro Data")
        st.write("Pantau indikator pasar finansial dan data makroekonomi global untuk analisis Top-Down.")
        
        st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        
        # ==========================================
        # 1. MENARIK DATA MAKRO (JALUR ALPHA VANTAGE)
        # ==========================================
        st.subheader("Indikator Makroekonomi Global (US Benchmark)")
        
        # 🔴 GANTI TEKS DI BAWAH INI DENGAN API KEY MILIKMU 🔴
        ALPHA_VANTAGE_API_KEY = "5STW7XG1P4VQ7GVN"
        
        # Fungsi pintar dengan CACHE (Agar kuota API gratisanmu tidak cepat habis!)
        # Data akan disimpan di memori selama 86400 detik (24 Jam)
        # Fungsi pintar dengan FALLBACK (Menyimpan data ke file lokal)
        def fetch_macro_alpha_vantage(api_key):
            cache_file = "macro_cache.json"
            
            # Nilai default realistis (Q1 2024) jika aplikasi baru pertama kali dijalankan dan langsung kena limit
            data_makro = {"GDP": 27360.0, "Pengangguran": 3.8, "Inflasi": 3.5, "Suku Bunga": 4.3}
            
            try:
                # 1. Kita ketuk pintunya dulu (Cek Limit) dengan menarik data GDP
                cek_limit = requests.get(f"https://www.alphavantage.co/query?function=REAL_GDP&interval=annual&apikey={api_key}").json()
                
                if 'Information' in cek_limit or 'Note' in cek_limit:
                    # JIKA KENA LIMIT API:
                    st.warning("⚠️ Limit Alpha Vantage harianmu habis. Menggunakan data terakhir yang tersimpan di sistem.")
                    
                    # Baca buku catatan (file JSON) jika ada
                    if os.path.exists(cache_file):
                        with open(cache_file, "r") as f:
                            data_makro = json.load(f)
                
                elif 'data' in cek_limit:
                    # JIKA BERHASIL (TIDAK KENA LIMIT):
                    data_makro["GDP"] = float(cek_limit['data'][0]['value'])
                    
                    # Lanjutkan menarik sisa datanya
                    res_unemp = requests.get(f"https://www.alphavantage.co/query?function=UNEMPLOYMENT&apikey={api_key}").json()
                    if 'data' in res_unemp: data_makro["Pengangguran"] = float(res_unemp['data'][0]['value'])
                    
                    res_inf = requests.get(f"https://www.alphavantage.co/query?function=INFLATION&apikey={api_key}").json()
                    if 'data' in res_inf: data_makro["Inflasi"] = float(res_inf['data'][0]['value'])
                    
                    res_yield = requests.get(f"https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=monthly&maturity=10year&apikey={api_key}").json()
                    if 'data' in res_yield: data_makro["Suku Bunga"] = float(res_yield['data'][0]['value'])
                    
                    # Simpan data terbaru yang sukses ditarik ini ke dalam file JSON
                    with open(cache_file, "w") as f:
                        json.dump(data_makro, f)
                        
            except Exception as e:
                st.error(f"Ada masalah koneksi internet. Menggunakan data historis. Error: {e}")
                if os.path.exists(cache_file):
                    with open(cache_file, "r") as f:
                        data_makro = json.load(f)
                        
            return data_makro

        macro_data_dict = {}
        
        with st.spinner("Menggunakan 'Kartu VIP' Alpha Vantage untuk mengambil data makro... ⏳"):
            if ALPHA_VANTAGE_API_KEY == "MASUKKAN_API_KEY_KAMU_DISINI":
                st.warning("⚠️ Kamu belum memasukkan API Key! Silakan edit kode Python-mu dan masukkan API Key Alpha Vantage.")
            else:
                # Memanggil fungsi penarik data
                macro_data_dict = fetch_macro_alpha_vantage(ALPHA_VANTAGE_API_KEY)
                
                # Menampilkan di Dashboard (4 Kolom agar lebih rapi dan simetris)
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                col_m1.metric("GDP (US$ Billions)", f"${macro_data_dict['GDP']:,.0f}")
                col_m2.metric("Unemployment Rate", f"{macro_data_dict['Pengangguran']:.1f}%")
                col_m3.metric("Treasury Yield / Suku Bunga", f"{macro_data_dict['Suku Bunga']:.2f}%")
                col_m4.metric("Inflation (YoY)", f"{macro_data_dict['Inflasi']:.2f}%")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # ==========================================
        # 2. MENARIK DATA PASAR SAHAM & KRIPTO (Yahoo Finance)
        # ==========================================
        st.subheader("Pergerakan Aset Finansial")
        
        market_tickers = {
            "🇮🇩 IHSG (Indonesia)": "^JKSE",
            "🇺🇸 S&P 500 (US Market)": "^GSPC",
            "💵 USD/IDR (Kurs)": "IDR=X",
            "🥇 Emas (Safe Haven)": "GC=F",
            "🪙 Bitcoin (Risk Asset)": "BTC-USD"
        }
        
        market_data = {}
        
        with st.spinner("Menarik data aset dari Yahoo Finance... ⏳"):
            col_a1, col_a2, col_a3, col_a4, col_a5 = st.columns(5)
            cols_aset = [col_a1, col_a2, col_a3, col_a4, col_a5]
            
            for i, (nama, ticker) in enumerate(market_tickers.items()):
                try:
                    hist = yf.Ticker(ticker).history(period="5d")
                    hist = hist.dropna(subset=['Close']) # Membersihkan nilai NaN
                    
                    if len(hist) >= 2:
                        harga_sekarang = hist['Close'].iloc[-1]
                        harga_kemarin = hist['Close'].iloc[-2]
                        perubahan_persen = ((harga_sekarang - harga_kemarin) / harga_kemarin) * 100
                        
                        market_data[nama] = {"persen": perubahan_persen}
                        
                        if "IHSG" in nama or "S&P" in nama:
                            harga_str = f"{harga_sekarang:,.2f}"
                        elif "USD/IDR" in nama:
                            harga_str = f"Rp {harga_sekarang:,.0f}"
                        else:
                            harga_str = f"${harga_sekarang:,.2f}"
                            
                        with cols_aset[i]:
                            st.metric(label=nama.split(" ")[1], value=harga_str, delta=f"{perubahan_persen:.2f}%")
                except:
                    with cols_aset[i]:
                        st.metric(label=nama.split(" ")[1], value="N/A", delta="Error")
                        
        st.markdown("<hr style='margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        
        # ==========================================
        # 3. ROBO-ADVISOR: ANALISIS TOP-DOWN OTOMATIS
        # ==========================================
        st.subheader("Analisis Makro & Sentimen")
        
        if macro_data_dict and market_data:
            kesimpulan = []
            
            # Logika 1: Kondisi Makroekonomi (Inflasi & Suku Bunga)
            inf = macro_data_dict["Inflasi"]
            rate = macro_data_dict["Suku Bunga"]
            
            if inf > 3.0 and rate > 4.0:
                kesimpulan.append(f"🏛️ **Kondisi Makro:** Inflasi global masih tinggi ({inf:.1f}%), memaksa bank sentral menahan suku bunga di level ketat ({rate:.2f}%). Era *Higher for Longer* ini membuat modal asing enggan masuk ke *emerging market* secara agresif.")
            elif inf < 2.5 and rate < 3.0:
                kesimpulan.append(f"🏛️ **Kondisi Makro:** Inflasi mereda ({inf:.1f}%) dan suku bunga rendah ({rate:.2f}%). Ini adalah kondisi *Goldilocks* yang memicu likuiditas berlimpah, sangat positif untuk pasar saham dan pertumbuhan emiten.")
            else:
                kesimpulan.append(f"🏛️ **Kondisi Makro:** Ekonomi berada dalam masa transisi. Dengan inflasi di {inf:.1f}% dan suku bunga {rate:.2f}%, pasar sedang mencermati arah kebijakan The Fed selanjutnya.")

            # Logika 2: Risiko Resesi & Fiskal (Pengangguran & Debt)
            # Menggunakan .get(kunci, nilai_default) agar TIDAK ERROR jika data Debt tidak ada dari Alpha Vantage
            unemp = macro_data_dict.get("Pengangguran", 0)
            debt = macro_data_dict.get("Debt/GDP", 0) 
            
            if unemp > 4.5:
                kesimpulan.append(f"⚠️ **Risiko Resesi:** Tingkat pengangguran naik mencapai {unemp:.1f}%, mengindikasikan roda ekonomi mulai melambat. Waspadai penurunan daya beli.")
            if debt > 100:
                kesimpulan.append(f"📉 **Risiko Fiskal:** Rasio utang pemerintah AS terhadap PDB sangat tinggi ({debt:.1f}%), memicu ketidakpastian nilai tukar mata uang global di masa depan.")
            
            # Logika 3: Respons Pasar Jangka Pendek (Market Action)
            pct_sp500 = market_data.get("🇺🇸 S&P 500 (US Market)", {}).get("persen", 0)
            pct_ihsg = market_data.get("🇮🇩 IHSG (Indonesia)", {}).get("persen", 0)
            pct_gold = market_data.get("🥇 Emas (Safe Haven)", {}).get("persen", 0)
            
            if pct_sp500 > 0.5 and pct_ihsg > 0:
                market_action = "🟢 **Sentimen Pasar:** Investor merespons data makro dengan optimisme (*Risk-On*). Aliran dana mendorong IHSG dan bursa global menghijau."
            elif pct_sp500 < -0.5 and pct_gold > 0.2:
                market_action = "🔴 **Sentimen Pasar:** Pasar saham tertekan. Investor merespons data makro dengan berlindung ke aset *safe haven* seperti Emas."
            else:
                market_action = "🟡 **Sentimen Pasar:** Pasar merespons data makro secara *mixed* (konsolidasi). Tidak ada tren yang mendominasi pergerakan hari ini."
                
            kesimpulan.append(market_action)
            teks_paragraf = "".join([f"<p style='margin-bottom: 10px;'>{teks}</p>" for teks in kesimpulan])
            
            html_kesimpulan = f"""
            <div style="background-color: #F8FAFC; border-left: 5px solid #0EA5E9; padding: 20px; border-radius: 8px; font-size: 14.5px; line-height: 1.6; color: #1E293B; margin-top: 15px;">
                {teks_paragraf}
            </div>
            """
            st.markdown(html_kesimpulan, unsafe_allow_html=True)
        else:
            st.info("Menunggu data makro dan aset terkumpul penuh untuk melakukan analisis...")
        
        # ==========================================
        # 4. AI TRADING AGENT (ANALISIS SENTIMEN SPESIFIK)
        # ==========================================
        st.markdown("<hr style='margin-top: 40px; margin-bottom: 30px;'>", unsafe_allow_html=True)
        
        st.subheader("AI Trading Agent")
        st.write("Pindai ratusan artikel berita finansial global secara real-time untuk mendapatkan rekomendasi arah pergerakan harga spesifik pada satu aset.")
        
        col_input, col_info = st.columns([1, 1.5])
        
        with col_input:
            # Input dari user
            ticker_input = st.text_input("🎯 Masukkan Simbol Aset (Market US/Kripto):", "AAPL").upper()
            analyze_button = st.button("🔍 Jalankan Agen Analisis", use_container_width=True)
            
        with col_info:
            st.info("💡 **Tips:** Fitur AI Alpha Vantage bekerja sangat baik untuk pasar saham Amerika (contoh: **NVDA, TSLA, MSFT**) dan Kripto (contoh: **CRYPTO:BTC, CRYPTO:ETH**).")

        if analyze_button:
            # Kita menggunakan variabel ALPHA_VANTAGE_API_KEY yang sudah kamu buat di bagian atas halaman ini
            if ALPHA_VANTAGE_API_KEY == "MASUKKAN_API_KEY_KAMU_DISINI":
                st.error("⚠️ Silakan masukkan API Key Alpha Vantage kamu terlebih dahulu di dalam kode.")
            else:
                with st.spinner(f"Agen sedang membaca dan menganalisis berita terbaru tentang {ticker_input}... ⏳"):
                    try:
                        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker_input}&apikey={ALPHA_VANTAGE_API_KEY}"
                        res = requests.get(url).json()
                        
                        if "feed" in res and len(res["feed"]) > 0:
                            berita_list = res["feed"]
                            total_score = 0.0
                            artikel_relevan = 0
                            
                            for artikel in berita_list:
                                for sentimen in artikel.get("ticker_sentiment", []):
                                    if sentimen["ticker"] == ticker_input:
                                        total_score += float(sentimen["ticker_sentiment_score"])
                                        artikel_relevan += 1
                                        
                            if artikel_relevan > 0:
                                avg_score = total_score / artikel_relevan
                                
                                # Logika Kesimpulan
                                if avg_score >= 0.35:
                                    status, warna = "STRONG BUY 🚀", "#10B981"
                                    penjelasan = "Sentimen pasar sangat euforia. Terdapat katalis fundamental yang sangat kuat mendorong optimisme investor institusi. Hati-hati jika volume mulai mengecil, bisa jadi ini akhir dari fase Mark-Up."
                                elif avg_score >= 0.15:
                                    status, warna = "BUY 🟢", "#34D399"
                                    penjelasan = "Sentimen dominan positif. Pasar merespons prospek aset ini dengan baik, menunjukkan potensi kelanjutan tren naik."
                                elif avg_score <= -0.35:
                                    status, warna = "STRONG SELL 🩸", "#EF4444"
                                    penjelasan = "Sentimen sangat panik atau negatif parah. Tekanan distribusi sangat tinggi. Jika harga berada di area support kuat dengan volume raksasa, ini bisa jadi fase 'Selling Climax'."
                                elif avg_score <= -0.15:
                                    status, warna = "SELL 🔴", "#F87171"
                                    penjelasan = "Sentimen cenderung negatif. Berita buruk mulai mendominasi dan tekanan jual berpotensi meningkat di pasar."
                                else:
                                    status, warna = "HOLD / NEUTRAL ⚖️", "#94A3B8"
                                    penjelasan = "Sentimen pasar sedang bercampur atau sepi katalis. Kemungkinan besar aset sedang berada dalam rentang konsolidasi (Trading Range)."
                                
                                # Tampilkan Hasil
                                st.markdown("### 📊 Rekomendasi Agen Cerdas")
                                html_result = f"""
                                <div style="border: 1px solid #E2E8F0; border-radius: 12px; padding: 25px; background-color: #FFFFFF; text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                                    <p style="color: #64748B; font-size: 14px; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1px;">Konsensus Sentimen Pasar</p>
                                    <h1 style="color: {warna}; font-size: 36px; margin-top: 0; margin-bottom: 15px;">{status}</h1>
                                    <div style="background-color: #F8FAFC; padding: 15px; border-radius: 8px; display: inline-block; margin-bottom: 20px;">
                                        <span style="font-size: 14px; color: #475569;">Skor Kuantitatif: <b>{avg_score:,.3f}</b> <i>(Rentang -1.0 s/d 1.0)</i></span><br>
                                        <span style="font-size: 13px; color: #64748B;">Diambil dari {artikel_relevan} artikel berita terbaru.</span>
                                    </div>
                                    <p style="color: #334155; font-size: 15px; line-height: 1.6; text-align: left; border-left: 4px solid {warna}; padding-left: 15px; margin: 0 auto; max-width: 600px;">
                                        {penjelasan}
                                    </p>
                                </div>
                                """
                                st.markdown(html_result, unsafe_allow_html=True)
                                
                            else:
                                st.warning(f"Agen tidak menemukan berita yang cukup relevan untuk {ticker_input} saat ini.")
                        else:
                            st.warning("Data tidak ditemukan atau limit Alpha Vantage mungkin sudah habis. Coba lagi besok!")
                            
                    except Exception as e:
                        st.error(f"Terjadi kesalahan teknis pada Agen: {e}")
