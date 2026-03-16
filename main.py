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

# --- 📊 秘密鍵 (Secretsを使わない力技・修正版) ---
creds = {
    "project_id": "juku-app-490419",
    "private_key_id": "64ba85aebfe8f98251481de4a1589cf25b5133d3",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEugIBADANBgkqhkiG9w0BAQEFAASCBKQwggSgAgEAAoIBAQCwBRWwD8K/Bhdg\ngVqL7l2tmySjMi7a0HhvJ8TOSyJQEuqJfXPKG9rUbjw6wn1Fy3OflOjIbWLBPDpz\nuY7V1EHud28QluvEsMbFCFFfglIJvzS0nLv3CTgmfzAkVUPxxnlZKKmgkjVL8TGi\nlaiBpCehvhfYOQ4rNmyfOTiVPOe6yPFa4ZFxWsDy+igN+SZRZtyZIv0/vtx7uhAH\n9JLzV/Zxn1FtqhxWm8Bd9n+ZyrLhXkn9M9lDy5zZy13+1gHmqUwdblzaZVaYR/gX\nlnWL5zU2sv2ICr7553p/IjIco0KR98s8VhK1YKtwOeEIEqy+oYR2/Uc9rpJMkwv9\nH9+iizRtAgMBAAECgf94Cv+z2N1JgQDkxGp8MsLfIymfOjGLrFuNobSLKvheo83E\nmadSgH4l7fDfxPLZD2e/vzcxHH/rvZBOLadHuPqD4cGi93kCFBkeL7DyN+Lpws6A\njUyMZ+AdpuYLVb4jpaDW3Ade+uNG8yuse/AeS4QwM1Fs06sQQdOMw23fE+SY5fMX\nU0CA8UyjOEbN36QA90pAwSKJcL3QfurV2+KbGk4QiFuZ7eI2VbGPkGngp5/23hSW\n1IBkimeo1h4r7ljmR1swxapLKW9a3Xvs3udjoQnx6uUHe0ZChOpooM/1612UK9t2\nA9koWZEQHfTDr+Hnn2rznj3hRfNYnz0HzJAIstECgYEA239ZDFzTO7t8wiNJtiif\nj99Z2B69e5wfBxJMrHZpIWZ0HrXNtS0yalynECHtZRF3GelfmhtX7OpChZFx9/FN\nyWexmLpAq+rQMoSLXE6qXtTQ4ENzzRD8yI4Iz/01GFKnOP53kxgOm5h0hsXSG7MM\nsW0E7xAtpUVfL/xo0kP2kVkCgYEAzUrEmdvs6oobWXwYBm7v7MNRaEjAUglyX1Ft\nQj/EPaM76FdU7VG/UX4qnazRK5RlfUEU9qZshOuD1wQUbpSqHXKzLiKHkoajQ2He\fn+SdDuOo0+ikC5mvRx9f+sJlFsNrrT1cF2DYwQF+XU6npLfMtaY886BpBJtL+QA\Ot5/ZTUCgYBHszHDeA8IVBZM1HofpuV4ed0/W8tJtZXtGW0yaPuujWkhHwIzTLBL\nTjjEbFC/0xS0wicYkBYIrf1M5FX2SDzArb61xSGbBvk7h1B+trOwhpQ0rdQGCKaK\nXNtEFdJiP52gYH9u7UzYRtTJsZUQt0xOKO6TqRVAB4kwg6M6DDlfAQKBgH88xwuB\ndp6LSJY2xoE+QvAgwpT6+lAeUMfpJOm5sfxt7pR7hESutQBiTTF6yg3TpO9z5fVV\ngs8DVaxvd+Ztt94WmB2RAyv6zLfXsdn/YZsuyqJHmj74s26keNhOqZpMsPdGaxTg\nsK0u8jEByno8F6Bfx17c8Bbr4Mac7tON0bG9AoGAZUJ9Bcm2RPVfghws2i5JRKHS\nV6pIDMwbvHmgQoT5/OEeelHJdxeffoLU7w4s/NyAanuaCuDkiAOjOGwSOICErdDm\n2rwbbaDnX/jOQyjooFL+hWKf46prcG2Snum5vbp7LtKiAGwxmv0zohFPODNHPPKh\nn777ZCN3LoFBT52qIgk=\n-----END PRIVATE KEY-----\n",
    "client_email": "juku-calc@juku-app-490419.iam.gserviceaccount.com",
    "client_id": "113297807438041206143",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/juku-calc%40juku-app-490419.iam.gserviceaccount.com"
}

# 秘密鍵の改行を修復
creds["private_key"] = creds["private_key"].replace("\\n", "\n")

# スプレッドシートのURL
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/13GlOlfmq5EqPeWvpydnuDUzk-OkU8jPNPb8IkFTHSFo/edit?usp=sharing"

try:
    # 🚀 ここが修正ポイント！ 'type'を重複させない
    conn = st.connection("gsheets", type=GSheetsConnection, spreadsheet=SPREADSHEET_URL, **creds)
    df = conn.read(ttl=0)

    st.subheader("今日の授業を記録")
    with st.form("input_form"):
        date = st.date_input("日付", datetime.date.today())
        grade = st.selectbox("学年", ["小学生", "中学生", "高校生"])
        count = st.radio("生徒数", [1, 2, 3], horizontal=True)
        
        prices = {"小学生": 1680, "中学生": 1760, "高校生": 2192}
        pay = int(prices[grade] + (count - 1) * 100)
        
        st.write(f"給料予測: **{pay:,} 円**")
        submitted = st.form_submit_button("保存する！")
        
        if submitted:
            new_row = pd.DataFrame([{"日付": str(date), "学年": grade, "人数": count, "金額": pay}])
            conn.create(data=new_row)
            st.success("スプレッドシートに保存したよ！")
            time.sleep(1)
            st.rerun()

    st.divider()
    st.subheader("直近の記録")
    if not df.empty:
        st.dataframe(df.tail(5), use_container_width=True)

except Exception as e:
    st.error("接続エラー。でも諦めるなブラザー！")
    st.write(e)
