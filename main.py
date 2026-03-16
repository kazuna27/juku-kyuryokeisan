import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
import time
from streamlit_gsheets import GSheetsConnection

# --- アプリの設定 ---
st.set_page_config(page_title="塾バイト給料計算", layout="centered", initial_sidebar_state="collapsed")

# 🎨 カスタムCSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kosugi+Maru&display=swap');
    html, body, [data-testid="stHeader"] { font-family: 'Kosugi Maru', sans-serif; background-color: #fffdf5; }
    h1 { color: #ff9800; text-align: center; font-size: 32px; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 50px; background-color: #ff9800; color: white; font-weight: bold; }
    div[data-testid="stMetricValue"] { color: #ff5722 !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #ffe0b2; border-radius: 20px; padding: 5px; }
</style>
""", unsafe_allow_html=True)

st.title("💰 塾バイト給料計算 💰")

# --- 👤 ユーザー識別 ---
if "user_name" not in st.session_state:
    st.subheader("まずは名前を教えてくれ！")
    name = st.text_input("名前 (例: kazuna, taro)", placeholder="友達も自分の名前を入れてね")
    if st.button("ログイン"):
        if name:
            # 安全のために全角やスペースを考慮
            st.session_state.user_name = name.strip()
            st.rerun()
        else:
            st.warning("名前を入れてくれよな！")
    st.stop()

user_sheet = st.session_state.user_name
st.sidebar.write(f"👤 ユーザー: {user_sheet}")
if st.sidebar.button("ログアウト"):
    del st.session_state.user_name
    st.rerun()

# --- 💾 GSheets 連携 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# データを読み込む関数
def fetch_user_data(sheet_name):
    try:
        # 指定されたシート名のデータを読み込む
        df_raw = conn.read(worksheet=sheet_name, ttl="1s")
        return df_raw.to_dict('records') if df_raw is not None and not df_raw.empty else []
    except:
        # シートが存在しない場合は空リスト
        return []

if "all_history" not in st.session_state:
    st.session_state.all_history = fetch_user_data(user_sheet)

# --- 📊 データ処理 ---
df = pd.DataFrame(st.session_state.all_history)
if not df.empty:
    df['日付'] = pd.to_datetime(df['日付'])
    df['月'] = df['日付'].dt.strftime("%Y-%m")

# --- 📱 画面構成 ---
tab_input, tab_dashboard, tab_total = st.tabs(["📅 入力", "📈 グラフ", "💰 履歴"])

with tab_input:
    st.subheader(f"{user_sheet} の記録を追加")
    date_val = st.date_input("日付", datetime.date.today())
    koma = st.selectbox("コマ", ["1限 (16:30-)", "2限 (17:30-)", "3限 (19:00-)", "4限 (20:30-)"])
    grade = st.selectbox("最高学年", ["小学生", "中学生", "高校生"])
    count = st.radio("生徒数", [1, 2, 3], horizontal=True)
    
    # 計算ロジック
    prices = {"小学生": 1680, "中学生": 1760, "高校生": 2192}
    one_pay = int(1050 + (count-1)*100) if "1限" in koma else int(prices[grade] + (count-1)*100)
    
    st.write(f"給料予測: **{one_pay:,} 円**")

    if st.button("記録を保存する"):
        new_row = {
            "日付": date_val.strftime("%Y-%m-%d"), 
            "コマ": koma, 
            "学年": grade, 
            "人数": int(count), 
            "金額": int(one_pay)
        }
        # ローカルのリストを更新
        st.session_state.all_history.append(new_row)
        
        # 🚀 データの書き込み
        # conn.update を使い、worksheetにユーザー名を指定。
        # 内部的に、シートがなければ新規作成してくれます。
        try:
            conn.update(worksheet=user_sheet, data=pd.DataFrame(st.session_state.all_history))
            st.success(f"シート '{user_sheet}' に保存したよ！")
            time.sleep(0.5)
            st.rerun()
        except Exception as e:
            st.error("保存に失敗したぜ...。")
            st.write("エラー詳細:", e)

with tab_dashboard:
    if df.empty:
        st.info("データがまだないよ。")
    else:
        month = datetime.date.today().strftime("%Y-%m")
        total = df[df['月'] == month]['金額'].sum() if month in df['月'].values else 0
        st.metric(f"{month} の合計", f"{total:,} 円")
        st.plotly_chart(px.bar(df.groupby('月')['金額'].sum().reset_index(), x='月', y='金額', color_discrete_sequence=['#ff9800']))

with tab_total:
    st.subheader("履歴の確認・消去")
    if not df.empty:
        # 最新順に表示
        current_history = st.session_state.all_history
        for i in range(len(current_history) - 1, -1, -1):
            row = current_history[i]
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(f"📅 {row['日付']} | {row['金額']:,}円")
            with col2:
                if st.button("消去", key=f"del_{i}"):
                    current_history.pop(i)
                    st.session_state.all_history = current_history
                    conn.update(worksheet=user_sheet, data=pd.DataFrame(st.session_state.all_history))
                    st.rerun()
