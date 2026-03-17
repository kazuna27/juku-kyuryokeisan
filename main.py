import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
import time
from supabase import create_client, Client

# --- アプリの設定 ---
st.set_page_config(page_title="塾講師 給料管理システム", layout="centered")

# 🎨 プロ仕様のカスタムCSS (清潔感のあるオレンジ＆ホワイト)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    html, body, [data-testid="stHeader"] { font-family: 'Noto Sans JP', sans-serif; }
    
    /* ヘッダーデザイン */
    .main-title { color: #E67E22; text-align: center; font-size: 28px; font-weight: bold; margin-bottom: 30px; }
    
    /* ボタンデザイン */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #E67E22;
        color: white;
        border: none;
        padding: 10px;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #D35400; color: white; border: none; }
    
    /* タブの見た目 */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f8f9fa;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #E67E22 !important; color: white !important; }
</style>
<div class="main-title">塾講師 給料管理システム</div>
""", unsafe_allow_html=True)

# --- 🔌 Supabase 接続設定 ---
url: str = st.secrets["supabase"]["url"]
key: str = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

# --- 🔑 ログイン・認証システム ---
if "user_name" not in st.session_state:
    st.info("💡 **初めての方へ**: お名前とパスワードを入力してログインしてください。初めて入力するお名前の場合は、そのまま新規登録として保存されます。")
    
    with st.container():
        name = st.text_input("利用者名 (例: 山田太郎)")
        pwd = st.text_input("パスワード", type="password", help="他人に推測されにくいものを入力してください。")
        
        if st.button("ログイン / 新規登録"):
            if name and pwd:
                # DBにそのユーザーがいるか確認
                res = supabase.table("salary_history").select("password").eq("user_name", name).limit(1).execute()
                
                if len(res.data) == 0:
                    # 新規ユーザー
                    st.session_state.user_name = name
                    st.session_state.user_pwd = pwd
                    st.success(f"ようこそ、{name}さん。最初のデータを保存するとアカウントが作成されます。")
                    time.sleep(1.5)
                    st.rerun()
                elif res.data[0]["password"] == pwd:
                    # 認証成功
                    st.session_state.user_name = name
                    st.session_state.user_pwd = pwd
                    st.rerun()
                else:
                    st.error("パスワードが正しくありません。入力内容を確認してください。")
            else:
                st.warning("利用者名とパスワードを両方入力してください。")
    st.stop()

# ユーザー情報
user = st.session_state.user_name
pwd_current = st.session_state.user_pwd

# --- 📊 データ取得関数 ---
def load_data():
    try:
        res = supabase.table("salary_history").select("*").eq("user_name", user).execute()
        return res.data
    except Exception:
        return []

if "all_history" not in st.session_state:
    st.session_state.all_history = load_data()

df = pd.DataFrame(st.session_state.all_history)
if not df.empty:
    df['date_dt'] = pd.to_datetime(df['date'])
    df['月'] = df['date_dt'].dt.strftime("%Y-%m")

# --- 📱 メイン画面 ---
tab1, tab2, tab3 = st.tabs(["📝 勤務入力", "📊 実績分析", "📋 履歴管理"])

with tab1:
    st.markdown(f"### 勤務内容の入力")
    st.caption(f"ログイン中: {user} さん")
    
    # 日付選択の改善
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = datetime.date.today()
    
    col_d1, col_d2 = st.columns([3, 1])
    with col_d1:
        date_val = st.date_input("勤務日", st.session_state.selected_date)
        st.session_state.selected_date = date_val
    with col_d2:
        st.write("")
        if st.button("翌日 ⏩"):
            st.session_state.selected_date += datetime.timedelta(days=1)
            st.rerun()

    koma = st.selectbox("授業時間", ["1限 (16:30-)", "2限 (17:30-)", "3限 (19:00-)", "4限 (20:30-)"])
    grade = st.selectbox("生徒の学年区分", ["小学生", "中学生", "高校生"])
    count = st.radio("生徒人数", [1, 2, 3], horizontal=True)
    
    # 給与計算ロジック
    prices = {"小学生": 1680, "中学生": 1760, "高校生": 2192}
    pay = int(1050 + (count-1)*100) if "1限" in koma else int(prices[grade] + (count-1)*100)
    
    st.metric("算定給与 (概算)", f"{pay:,} 円")

    if st.button("この内容で記録する"):
        new_record = {
            "user_name": user,
            "password": pwd_current,
            "date": date_val.strftime("%Y-%m-%d"),
            "koma": koma,
            "grade": grade,
            "count": int(count),
            "amount": int(pay)
        }
        with st.spinner("データベースに保存しています..."):
            supabase.table("salary_history").insert(new_record).execute()
            st.session_state.all_history = load_data()
            st.success("正常に保存されました。")
            time.sleep(1)
            st.rerun()

with tab2:
    st.markdown("### 勤務実績の可視化")
    if df.empty:
        st.info("データが登録されると、ここにグラフが表示されます。")
    else:
        current_month = datetime.date.today().strftime("%Y-%m")
        monthly_sum = df[df['月'] == current_month]['amount'].sum() if current_month in df['月'].values else 0
        st.metric(f"{current_month} の総支給額", f"{monthly_sum:,} 円")
        
        st.write("---")
        st.markdown("##### 月別支給額の推移")
        monthly_df = df.groupby('月')['amount'].sum().reset_index()
        fig = px.bar(monthly_df, x='月', y='amount', text_auto='.s', color_discrete_sequence=['#E67E22'])
        fig.update_layout(xaxis_title="月", yaxis_title="給与額 (円)", margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("### 勤務履歴の照会")
    if not df.empty:
        st.caption("※ 誤って登録した場合は「取消」ボタンで削除できます。")
        # 日付順に並び替え
        sorted_history = sorted(st.session_state.all_history, key=lambda x: x['date'], reverse=True)
        for row in sorted_history:
            with st.expander(f"📅 {row['date']} | {row['amount']:,} 円"):
                st.write(f"**詳細:** {row['koma']} / {row['grade']} / {row['count']}名")
                if st.button("この記録を取り消す", key=f"del_{row['id']}"):
                    supabase.table("salary_history").delete().eq("id", row['id']).execute()
                    st.session_state.all_history = load_data()
                    st.rerun()
    else:
        st.info("現在、登録されている履歴はありません。")
