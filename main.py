import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import datetime
import time

# --- アプリの設定 ---
st.set_page_config(page_title="塾バイト給料計算", layout="centered")

# 🎨 デザイン
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kosugi+Maru&display=swap');
    html, body, [data-testid="stHeader"] { font-family: 'Kosugi Maru', sans-serif; background-color: #fffdf5; }
    h1 { color: #ff9800; text-align: center; font-size: 32px; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 50px; background-color: #ff9800; color: white; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("💰 塾バイト給料計算 💰")

# --- 📊 スプレッドシート連携 (真・修正版) ---
try:
    # 接続の確立 (最新のライブラリに合わせた書き方)
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # データを読む
    df = conn.read(ttl=0)

    st.subheader("授業を記録する")
    with st.form("input_form"):
        date = st.date_input("日付", datetime.date.today())
        grade = st.selectbox("学年", ["小学生", "中学生", "高校生"])
        count = st.radio("生徒数", [1, 2, 3], horizontal=True)
        
        # 簡易計算
        prices = {"小学生": 1680, "中学生": 1760, "高校生": 2192}
        pay = int(prices[grade] + (count - 1) * 100)
        
        st.write(f"給料予測: **{pay:,} 円**")
        submitted = st.form_submit_button("保存する！")
        
        if submitted:
            new_row = pd.DataFrame([{
                "日付": str(date),
                "コマ": "授業",
                "学年": grade,
                "人数": count,
                "金額": pay
            }])
            # 追記
            conn.create(data=new_row)
            st.success("チャリン♪ スプレッドシートに保存したよ！")
            time.sleep(1)
            st.rerun()

    st.divider()
    st.subheader("直近の記録")
    if not df.empty:
        st.dataframe(df.tail(5), use_container_width=True)
    else:
        st.info("まだデータがないよ。最初の授業を記録しよう！")

except Exception as e:
    st.error("まだエラーが出るみたいだね。")
    st.write("エラー詳細:", e)
