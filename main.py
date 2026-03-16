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
</style>
""", unsafe_allow_html=True)

st.title("💰 塾バイト給料計算 💰")

# --- 📊 接続設定 (読み込み停止回避版) ---
try:
    # URLを直接渡すことで、探しに行く手間を省いて高速化するぜ
    URL = "https://docs.google.com/spreadsheets/d/13GlOlfmq5EqPeWvpydnuDUzk-OkU8jPNPb8IkFTHSFo/edit?usp=sharing"
    
    conn = st.connection("gsheets", type=GSheetsConnection)
    # ここで spreadsheet=URL を指定するのがポイントだ！
    df_raw = conn.read(spreadsheet=URL, ttl=0)
    
    if df_raw is not None and not df_raw.empty:
        st.session_state.all_history = df_raw.to_dict('records')
    else:
        st.session_state.all_history = []
except Exception as e:
    st.error("まだ扉が開かないぜ、ブラザー。")
    st.write("エラーの正体:", e)
    st.stop()

# 状態保持
if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.date.today()

# 曜日の日本語変換
WEEKDAYS_JP = ["月", "火", "水", "木", "金", "土", "日"]

# --- 📊 データ処理 (日本語項目名に対応) ---
df = pd.DataFrame(st.session_state.all_history)
if not df.empty:
    df['日付'] = pd.to_datetime(df['日付'])
    df['月'] = df['日付'].dt.strftime("%Y-%m")

# --- 📱 画面構成 ---
tab_input, tab_dashboard, tab_total = st.tabs(["📅 授業を入力", "📈 グラフ", "💰 履歴"])

with tab_input:
    st.subheader("今日の授業を記録")
    col_date, col_next = st.columns([3, 1])
    with col_date:
        current_date = st.date_input("日付を選択", st.session_state.selected_date)
        st.session_state.selected_date = current_date
        wd = WEEKDAYS_JP[st.session_state.selected_date.weekday()]
        st.write(f"選択中: **{st.session_state.selected_date.strftime('%Y/%m/%d')} ({wd})**")
    with col_next:
        st.write("")
        if st.button("次の日⏩"):
            st.session_state.selected_date += datetime.timedelta(days=1)
            st.rerun()
            
    date_str = st.session_state.selected_date.strftime("%Y-%m-%d")
    koma_choice = st.selectbox("コマを選択", ["1限 (16:30-)", "2限 (17:30-)", "3限 (19:00-)", "4限 (20:30-)"])
    grade = st.selectbox("最高学年", ["小学生", "中学生", "高校生"])
    count = st.radio("生徒数", [1, 2, 3], horizontal=True)
    
    # 計算
    prices = {"小学生": 1680, "中学生": 1760, "高校生": 2192}
    if "1限" in koma_choice:
        one_pay = int(1050 + (count-1)*100)
    else:
        one_pay = int(prices[grade] + (count-1)*100)
    
    st.markdown(f"給料予測: **{one_pay:,} 円**")

    if st.button("記録を保存する"):
        # スプレッドシートの項目名に合わせる（重要！）
        new_data = {
            "日付": date_str, 
            "コマ": koma_choice, 
            "学年": grade, 
            "人数": int(count), 
            "金額": int(one_pay)
        }
        new_history = st.session_state.all_history + [new_data]
        # 保存実行
        conn.update(worksheet="シート1", data=pd.DataFrame(new_history))
        st.success(f"保存したよ！ {date_str}")
        time.sleep(0.4)
        st.rerun()

with tab_dashboard:
    st.subheader("頑張りの成果！")
    if df.empty:
        st.info("データがまだないよ。")
    else:
        current_month = datetime.date.today().strftime("%Y-%m")
        month_total = df[df['月'] == current_month]['金額'].sum() if current_month in df['月'].values else 0
        st.metric(label=f"{current_month} の合計", value=f"{month_total:,} 円")
        st.progress(min(float(month_total / 100000), 1.0))
        st.divider()
        monthly_df = df.groupby('月')['金額'].sum().reset_index()
        fig = px.bar(monthly_df, x='月', y='金額', text='金額', color_discrete_sequence=['#ff9800'])
        st.plotly_chart(fig, use_container_width=True)

with tab_total:
    st.subheader("詳細履歴")
    if not df.empty:
        # 削除機能も日本語キーに修正
        available_months = sorted(df['月'].unique(), reverse=True)
        target_month = st.selectbox("表示月", available_months)
        month_data = df[df['月'] == target_month].sort_values('日付')
        for i, row in month_data.iterrows():
            col_detail, col_del = st.columns([5, 1])
            with col_detail:
                # 日付がTimestamp型の場合があるため変換
                d_obj = pd.to_datetime(row['日付'])
                st.write(f"📅 {d_obj.strftime('%m/%d')} | {row['コマ'][:2]} | {row['金額']:,}円")
            with col_del:
                if st.button("消去", key=f"del_{i}"):
                    # 削除処理
                    new_hist = [item for item in st.session_state.all_history if not (item['日付'] == row['日付'] and item['コマ'] == row['コマ'])]
                    conn.update(worksheet="シート1", data=pd.DataFrame(new_hist) if new_hist else pd.DataFrame(columns=["日付","コマ","学年","人数","金額"]))
                    st.rerun()
