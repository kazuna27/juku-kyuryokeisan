import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
import time
from supabase import create_client, Client

# --- アプリの設定 ---
st.set_page_config(page_title="塾バイト給料計算", layout="centered", initial_sidebar_state="collapsed")

# 🎨 カスタムCSS (ブラザーお気に入りのオレンジデザイン)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kosugi+Maru&display=swap');
    html, body, [data-testid="stHeader"] { font-family: 'Kosugi Maru', sans-serif; background-color: #fffdf5; }
    h1 { color: #ff9800; text-align: center; font-size: 32px; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 50px; background-color: #ff9800; color: white; font-weight: bold; box-shadow: 0 4px 0 #e65100; }
    div[data-testid="stMetricValue"] { color: #ff5722 !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #ffe0b2; border-radius: 20px; padding: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 🔌 Supabase 接続設定 ---
url: str = st.secrets["supabase"]["url"]
key: str = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

st.title("💰 塾バイト給料計算 💰")

# --- 🔑 ログイン・パスワード認証 ---
if "user_name" not in st.session_state:
    st.subheader("🔑 ログイン / 新規登録")
    name = st.text_input("名前 (例: kazuna)")
    pwd = st.text_input("パスワード", type="password")
    
    if st.button("ログイン"):
        if name and pwd:
            # DBにそのユーザーがいるか確認
            res = supabase.table("salary_history").select("password").eq("user_name", name).limit(1).execute()
            
            if len(res.data) == 0:
                # 新規ユーザー：名前とパスをセットして進む（最初の保存時にDBへ送る）
                st.session_state.user_name = name
                st.session_state.user_pwd = pwd
                st.success(f"ようこそ {name}！最初の記録を保存すると、このパスワードで登録されるぜ。")
                time.sleep(1)
                st.rerun()
            elif res.data[0]["password"] == pwd:
                # 既存ユーザー：パスワード一致
                st.session_state.user_name = name
                st.session_state.user_pwd = pwd
                st.rerun()
            else:
                st.error("パスワードが違うみたいだぜ、ブラザー。")
        else:
            st.warning("名前とパスワードを両方入れてくれ！")
    st.stop()

# ログイン中のユーザー情報
user = st.session_state.user_name
pwd_current = st.session_state.user_pwd

# --- 📊 データ読み込み関数 ---
def load_data():
    res = supabase.table("salary_history").select("*").eq("user_name", user).execute()
    return res.data

if "all_history" not in st.session_state:
    st.session_state.all_history = load_data()

df = pd.DataFrame(st.session_state.all_history)
if not df.empty:
    df['date_dt'] = pd.to_datetime(df['date'])
    df['月'] = df['date_dt'].dt.strftime("%Y-%m")

# --- 📱 画面構成 ---
tab1, tab2, tab3 = st.tabs(["📅 授業を入力", "📈 グラフ", "💰 履歴"])

with tab1:
    st.subheader(f"👤 {user} さんの入力画面")
    
    # 日付選択
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = datetime.date.today()
    
    col_d1, col_d2 = st.columns([3, 1])
    with col_d1:
        date_val = st.date_input("日付", st.session_state.selected_date)
        st.session_state.selected_date = date_val
    with col_d2:
        st.write("")
        if st.button("次の日⏩"):
            st.session_state.selected_date += datetime.timedelta(days=1)
            st.rerun()

    koma = st.selectbox("コマ", ["1限 (16:30-)", "2限 (17:30-)", "3限 (19:00-)", "4限 (20:30-)"])
    grade = st.selectbox("最高学年", ["小学生", "中学生", "高校生"])
    count = st.radio("生徒数", [1, 2, 3], horizontal=True)
    
    # 計算
    prices = {"小学生": 1680, "中学生": 1760, "高校生": 2192}
    pay = int(1050 + (count-1)*100) if "1限" in koma else int(prices[grade] + (count-1)*100)
    
    st.markdown(f"給料予測: <span style='color:#ff5722; font-size:24px; font-weight:bold;'>{pay:,} 円</span>", unsafe_allow_html=True)

    if st.button("データベースに記録を保存"):
        new_record = {
            "user_name": user,
            "password": pwd_current,
            "date": date_val.strftime("%Y-%m-%d"),
            "koma": koma,
            "grade": grade,
            "count": int(count),
            "amount": int(pay)
        }
        # 🚀 Supabaseへ挿入
        supabase.table("salary_history").insert(new_record).execute()
        # メモリ上のデータを更新
        st.session_state.all_history = load_data()
        st.success("DBに保存したぜ！これで友達がスマホで見てもデータは混ざらない！")
        time.sleep(0.5)
        st.rerun()

with tab2:
    st.subheader("頑張りの成果！")
    if df.empty:
        st.info("データがまだないよ。")
    else:
        month = datetime.date.today().strftime("%Y-%m")
        total = df[df['月'] == month]['amount'].sum() if month in df['月'].values else 0
        st.metric(f"{month} の合計額", f"{total:,} 円")
        
        # 月別グラフ
        monthly_df = df.groupby('月')['amount'].sum().reset_index()
        fig = px.bar(monthly_df, x='月', y='amount', text='amount', color_discrete_sequence=['#ff9800'])
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("詳細履歴 (削除も可能)")
    if not df.empty:
        # 最新順
        for row in sorted(st.session_state.all_history, key=lambda x: x['date'], reverse=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                st.write(f"📅 {row['date']} | {row['koma'][:2]} | {row['amount']:,}円")
            with c2:
                if st.button("消去", key=f"del_{row['id']}"):
                    # 🚀 ID指定でDBから削除
                    supabase.table("salary_history").delete().eq("id", row['id']).execute()
                    st.session_state.all_history = load_data()
                    st.rerun()
    else:
        st.info("履歴はまだないぜ。")
