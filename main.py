import streamlit as st
import datetime
import json
import os
import pandas as pd
import plotly.express as px
import time

# --- アプリの設定 ---
st.set_page_config(page_title="塾バイト給料計算", layout="centered", initial_sidebar_state="collapsed")

# 🎨 カスタムCSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kosugi+Maru&display=swap');
    html, body, [data-testid="stHeader"] { font-family: 'Kosugi Maru', sans-serif; background-color: #fffdf5; }
    h1 { color: #ff9800; text-align: center; font-size: 32px; font-weight: bold; }
    h2, h3 { color: #f57c00; }
    .stButton>button { 
        width: 100%; border-radius: 50px; 
        background-color: #ff9800; color: white; 
        font-weight: bold; font-size: 18px; 
        padding: 10px 20px; border: none; 
        box-shadow: 0 4px 0 #e65100;
    }
    .stButton>button:active { transform: translateY(2px); box-shadow: 0 2px 0 #e65100; }
    div[data-testid="stMetricValue"] { color: #ff5722 !important; font-size: 40px !important; font-weight: bold !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #ffe0b2; border-radius: 20px; padding: 5px; }
    .stTabs [data-baseweb="tab"] { color: #e65100; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("💰 塾バイト給料計算 💰")

# --- 💾 保存機能 ---
SAVE_FILE = "salary_data.json"
def load_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []
def save_data(data_list):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data_list, f, indent=4, ensure_ascii=False)

if "all_history" not in st.session_state:
    st.session_state.all_history = load_data()

# 状態保持用（バグ防止）
if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.date.today()
if "current_grade" not in st.session_state:
    st.session_state.current_grade = "小学生"
if "current_count" not in st.session_state:
    st.session_state.current_count = 1

# --- 🛠 計算ロジック ---
def calc_juku_pay(grade, count):
    prices = {"小学生": 1680, "中学生": 1760, "高校生": 2192}
    base = prices.get(grade, 1760)
    return int(base + (count - 1) * 100)

# 曜日の日本語変換用
WEEKDAYS_JP = ["月", "火", "水", "木", "金", "土", "日"]

# --- 📊 データ処理 ---
df = pd.DataFrame(st.session_state.all_history)
if not df.empty:
    df['date'] = pd.to_datetime(df['date'])
    df['月'] = df['date'].dt.strftime("%Y-%m")

# --- 📱 画面構成 ---
tab_input, tab_dashboard, tab_total = st.tabs(["📅 授業を入力", "📈 グラフ", "💰 履歴"])

with tab_input:
    st.subheader("今日の授業を記録")
    
    # 1. 日付選択（曜日付き表示）
    col_date, col_next = st.columns([3, 1])
    with col_date:
        current_date = st.date_input("日付を選択", st.session_state.selected_date)
        st.session_state.selected_date = current_date
        # 曜日を取得
        wd = WEEKDAYS_JP[st.session_state.selected_date.weekday()]
        st.write(f"選択中: **{st.session_state.selected_date.strftime('%Y/%m/%d')} ({wd})**")

    with col_next:
        st.write("")
        st.write("")
        if st.button("次の日⏩"):
            st.session_state.selected_date += datetime.timedelta(days=1)
            st.rerun()
            
    date_str = st.session_state.selected_date.strftime("%Y-%m-%d")
    
    # 2. コマ・学年・人数の選択（セッションで状態を固定）
    koma_options = {"1限 (16:30-)": 1.0, "2限 (17:30-)": 1.8, "3限 (19:00-)": 1.8, "4限 (20:30-)": 1.8}
    koma_choice = st.selectbox("コマを選択", list(koma_options.keys()))
    
    # 学年と人数をセッションから取得
    grade = st.selectbox("最高学年", ["小学生", "中学生", "高校生"], 
                         index=["小学生", "中学生", "高校生"].index(st.session_state.current_grade))
    st.session_state.current_grade = grade # 選択を即座に保持

    count = st.radio("生徒数", [1, 2, 3], index=[1, 2, 3].index(st.session_state.current_count), horizontal=True)
    st.session_state.current_count = count # 選択を即座に保持
    
    # 3. 給料計算
    if koma_options[koma_choice] == 1.0:
        one_pay = int(1050 + (count-1)*100)
    else:
        one_pay = calc_juku_pay(grade, count)
    
    st.markdown(f"給料予測: <span style='color:#ff5722; font-size:28px; font-weight:bold;'>{one_pay:,} 円</span>", unsafe_allow_html=True)

    # 重複チェック
    is_duplicate = any(item for item in st.session_state.all_history if item['date'] == date_str and item['koma'] == koma_choice)

    if is_duplicate:
        st.warning(f"⚠️ {date_str} の {koma_choice} は既に登録済み。")
    else:
        if st.button("記録を保存する"):
            data = {"date": date_str, "koma": koma_choice, "grade": grade, "count": count, "amount": one_pay}
            st.session_state.all_history.append(data)
            save_data(st.session_state.all_history)
            st.success(f"保存したよ！ {date_str}({wd})")
            time.sleep(0.4)
            st.rerun()

with tab_dashboard:
    st.subheader("頑張りの成果！")
    if df.empty:
        st.write("データがまだないよ。")
    else:
        current_month = datetime.date.today().strftime("%Y-%m")
        month_total = df[df['月'] == current_month]['amount'].sum() if current_month in df['月'].values else 0
        st.metric(label=f"{current_month} の合計", value=f"{month_total:,} 円")
        st.progress(min(month_total / 100000, 1.0))
        st.divider()
        monthly_df = df.groupby('月')['amount'].sum().reset_index()
        monthly_df.columns = ['月', '給料合計']
        fig = px.bar(monthly_df, x='月', y='給料合計', text='給料合計', color_discrete_sequence=['#ff9800'])
        fig.update_traces(texttemplate='%{text:,}円', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

with tab_total:
    st.subheader("詳細履歴")
    if not df.empty:
        available_months = sorted(df['月'].unique(), reverse=True)
        target_month = st.selectbox("表示月", available_months)
        month_data = df[df['月'] == target_month].sort_values('date')
        for i, row in month_data.iterrows():
            col_detail, col_del = st.columns([5, 1])
            with col_detail:
                # 履歴にも曜日を表示
                row_wd = WEEKDAYS_JP[row['date'].weekday()]
                st.write(f"📅 {row['date'].strftime('%m/%d')}({row_wd}) | {row['koma'][:2]} | {row['amount']:,}円")
            with col_del:
                if st.button("消去", key=f"del_{i}"):
                    new_hist = [item for item in st.session_state.all_history if not (item['date'] == row['date'].strftime("%Y-%m-%d") and item['koma'] == row['koma'])]
                    st.session_state.all_history = new_hist
                    save_data(new_hist)
                    st.rerun()