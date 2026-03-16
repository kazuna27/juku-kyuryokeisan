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

# --- 📊 スプレッドシート連携 (1行秘密鍵対応版) ---
try:
    # Secretsから鍵の情報を一度取り出し、書き換え可能な形(dict)に変換する
    creds_info = dict(st.secrets["connections"]["gsheets"])
    
    # 秘密鍵の中の \n 文字を、本物の改行に変換（これで安全に書き換えられる！）
    if "private_key" in creds_info:
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
    
    # 手動で設定を渡して接続！
    # Secretsから鍵の情報をコピー（読み取り専用エラー回避）
    creds_info = dict(st.secrets["connections"]["gsheets"])
    
    # 【ここが重要！】
    # Secretsの中にある 'type' を消しちゃえば、コード側の type=GSheetsConnection とケンカしない！
    if "type" in creds_info:
        del creds_info["type"]
    
    # 秘密鍵の改行修復
    if "private_key" in creds_info:
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
    
    # 接続！
    conn = st.connection("gsheets", type=GSheetsConnection, **creds_info)
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
