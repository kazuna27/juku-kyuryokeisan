import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
import time

# --- アプリの設定 ---
st.set_page_config(page_title="塾バイト給料計算", layout="centered", initial_sidebar_state="collapsed")

# 🎨 カスタムCSS (完璧版を再現)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kosugi+Maru&display=swap');
    html, body, [data-testid="stHeader"] { font-family: 'Kosugi Maru', sans-serif; background-color: #fffdf5; }
    h1 { color: #ff9800; text-align: center; font-size: 32px; font-weight: bold; }
    .stButton>button { 
        width: 100%; border-radius: 50px; 
        background-color: #ff9800; color: white; 
        font-weight: bold; font-size: 18px; 
        box-shadow: 0 4px 0 #e65100;
    }
    div[data-testid="stMetricValue"] { color: #ff5722 !important; font-size: 40px !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #ffe0b2; border-radius: 20px; padding: 5px; }
</style>
""", unsafe_allow_html=True)

st.title("💰 塾バイト給料計算 💰")

# --- 💾 ローカル保存機能 (ブラウザのセッション/擬似ローカル) ---
# ※Streamlit Cloudで完全に永続化するには少し工夫が必要ですが、
# まずは「端末・セッションごと」に爆速で動く仕組みにします。
if "local_history" not in st.session_state:
    st.session_state.local_history = []

# 状態保持
if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.date.today()

# 曜日
WEEKDAYS_JP = ["月", "火", "水", "木", "金", "土", "日"]

# --- 📊 データ処理 ---
df = pd.DataFrame(st.session_state.local_history)
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

    koma_choice = st.selectbox("コマを選択", ["1限 (16:30-)", "2限 (17:30-)", "3限 (19:00-)", "4限 (20:30-)"])
    grade = st.selectbox("最高学年", ["小学生", "中学生", "高校生"])
    count = st.radio("生徒数", [1, 2, 3], horizontal=True)
    
    # 計算ロジック
    prices = {"小学生": 1680, "中学生": 1760, "高校生": 2192}
    one_pay = int(1050 + (count-1)*100) if "1限" in koma_choice else int(prices[grade] + (count-1)*100)
    
    st.markdown(f"給料予測: **{one_pay:,} 円**")

    if st.button("記録を保存する"):
        new_data = {
            "id": time.time(), # 削除用にユニークなIDを付与
            "日付": st.session_state.selected_date.strftime("%Y-%m-%d"), 
            "コマ": koma_choice, 
            "学年": grade, 
            "人数": int(count), 
            "金額": int(one_pay)
        }
        st.session_state.local_history.append(new_data)
        st.success("保存したぜ！ (この端末のみ)")
        time.sleep(0.5)
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
        # 削除ボタンが確実に動くように修正
        for i, row in enumerate(reversed(st.session_state.local_history)):
            # 逆順（新しい順）で表示
            idx = len(st.session_state.local_history) - 1 - i
            col_detail, col_del = st.columns([4, 1])
            with col_detail:
                st.write(f"📅 {row['日付']} | {row['コマ'][:2]} | {row['金額']:,}円")
            with col_del:
                # 削除ボタン。keyをユニークにすることで確実に動作させる
                if st.button("消去", key=f"del_btn_{row['id']}"):
                    st.session_state.local_history.pop(idx)
                    st.warning("消したぜ！")
                    time.sleep(0.5)
                    st.rerun()
    else:
        st.info("履歴はまだないぜ。")
