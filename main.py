import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
import time
from streamlit_gsheets import GSheetsConnection

# --- アプリの設定 ---
st.set_page_config(page_title="塾バイト給料計算", layout="centered", initial_sidebar_state="collapsed")

# 🎨 カスタムCSS (ポップなデザイン)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kosugi+Maru&display=swap');
    html, body, [data-testid="stHeader"] { font-family: 'Kosugi Maru', sans-serif; background-color: #fffdf5; }
    h1 { color: #ff9800; text-align: center; font-size: 32px; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 50px; background-color: #ff9800; color: white; font-weight: bold; font-size: 18px; padding: 10px 20px; border: none; box-shadow: 0 4px 0 #e65100; }
    div[data-testid="stMetricValue"] { color: #ff5722 !important; font-size: 40px !important; font-weight: bold !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #ffe0b2; border-radius: 20px; padding: 5px; }
</style>
""", unsafe_allow_html=True)

st.title("💰 塾バイト給料計算 💰")

# --- 📊 スプレッドシート連携 ---
# 接続の確立
conn = st.connection("gsheets", type=GSheetsConnection)

# データを読み込む関数 (キャッシュを無効にして常に最新を取得)
def load_data():
    return conn.read(ttl=0)

# データを保存する関数 (追記モードに変更)
def save_data(new_row_df):
    conn.create(data=new_row_df)

# --- 状態保持 ---
if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.date.today()
if "current_grade" not in st.session_state:
    st.session_state.current_grade = "小学生"
if "current_count" not in st.session_state:
    st.session_state.current_count = 1

# 曜日変換
WEEKDAYS_JP = ["月", "火", "水", "木", "金", "土", "日"]

# --- 🛠 計算ロジック ---
def calc_juku_pay(grade, count):
    prices = {"小学生": 1680, "中学生": 1760, "高校生": 2192}
    base = prices.get(grade, 1760)
    return int(base + (count - 1) * 100)

# --- 📱 画面構成 ---
tab_input, tab_dashboard, tab_total = st.tabs(["📅 入力", "📈 グラフ", "💰 履歴"])

# 最新データを取得
all_data = load_data()

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
        st.write("")
        if st.button("次の日⏩"):
            st.session_state.selected_date += datetime.timedelta(days=1)
            st.rerun()

    date_str = st.session_state.selected_date.strftime("%Y-%m-%d")
    koma_options = {"1限 (16:30-)": 1.0, "2限 (17:30-)": 1.8, "3限 (19:00-)": 1.8, "4限 (20:30-)": 1.8}
    koma_choice = st.selectbox("コマを選択", list(koma_options.keys()))
    
    grade = st.selectbox("最高学年", ["小学生", "中学生", "高校生"], 
                         index=["小学生", "中学生", "高校生"].index(st.session_state.current_grade))
    st.session_state.current_grade = grade
    count = st.radio("生徒数", [1, 2, 3], index=[1, 2, 3].index(st.session_state.current_count), horizontal=True)
    st.session_state.current_count = count
    
    if koma_options[koma_choice] == 1.0:
        one_pay = int(1050 + (count-1)*100)
    else:
        one_pay = calc_juku_pay(grade, count)
    
    st.markdown(f"給料予測: <span style='color:#ff5722; font-size:28px; font-weight:bold;'>{one_pay:,} 円</span>", unsafe_allow_html=True)

    # 重複チェック (スプレッドシートのデータから判定)
    is_duplicate = False
    if not all_data.empty:
        is_duplicate = any((all_data['日付'] == date_str) & (all_data['コマ'] == koma_choice))

    if is_duplicate:
        st.warning("⚠️ このコマは既に登録済みだよ。")
    else:
        if st.button("スプレッドシートへ保存！"):
            new_entry = pd.DataFrame([{
                "日付": date_str, "コマ": koma_choice, "学年": grade, "人数": count, "金額": one_pay
            }])
            # updated_df = pd.concat... の行を消して、直接 new_entry を送る
            save_data(new_entry)
            st.success(f"チャリン♪ {date_str}({wd}) を保存！")
            time.sleep(1)
            st.rerun()

with tab_dashboard:
    st.subheader("頑張りの成果！")
    if all_data.empty:
        st.write("データがまだないよ。")
    else:
        all_data['日付'] = pd.to_datetime(all_data['日付'])
        all_data['月'] = all_data['日付'].dt.strftime("%Y-%m")
        current_month = datetime.date.today().strftime("%Y-%m")
        month_total = all_data[all_data['月'] == current_month]['金額'].sum()
        
        st.metric(label=f"{current_month} の合計給料", value=f"{month_total:,} 円")
        st.progress(min(month_total / 100000, 1.0))
        st.divider()
        monthly_df = all_data.groupby('月')['金額'].sum().reset_index()
        fig = px.bar(monthly_df, x='月', y='金額', text='金額', color_discrete_sequence=['#ff9800'])
        st.plotly_chart(fig, use_container_width=True)

with tab_total:
    st.subheader("詳細履歴")
    if not all_data.empty:
        all_data['日付'] = pd.to_datetime(all_data['日付'])
        all_data['月'] = all_data['日付'].dt.strftime("%Y-%m")
        available_months = sorted(all_data['月'].unique(), reverse=True)
        target_month = st.selectbox("表示月", available_months)
        month_data = all_data[all_data['月'] == target_month].sort_values('日付')
        for i, row in month_data.iterrows():
            col1, col2 = st.columns([5, 1])
            with col1:
                r_wd = WEEKDAYS_JP[row['日付'].weekday()]
                st.write(f"📅 {row['日付'].strftime('%m/%d')}({r_wd}) | {row['コマ'][:2]} | {row['金額']:,}円")
            with col2:
                if st.button("消去", key=f"del_{i}"):
                    # 特定の行を除外して更新
                    # インデックスを正しく扱うために all_data から削除
                    all_data = all_data.drop(i)
                    # 日付を文字列に戻して保存
                    all_data['日付'] = all_data['日付'].dt.strftime("%Y-%m-%d")
                    save_data(all_data.drop(columns=['月']))
                    st.rerun()
