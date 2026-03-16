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
    .stButton>button { width: 100%; border-radius: 50px; background-color: #ff9800; color: white; font-weight: bold; border: none; }
    div[data-testid="stMetricValue"] { color: #ff9800; }
</style>
""", unsafe_allow_html=True)

# --- 📊 接続設定 ---
try:
    creds_info = dict(st.secrets["connections"]["gsheets"])
    creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
    conn = st.connection("gsheets", type=GSheetsConnection, **creds_info)
    df = conn.read(ttl=0)
except Exception as e:
    st.error("接続エラー。Secretsを確認してくれ。")
    st.stop()

# --- 📱 画面切り替えタブ ---
tab1, tab2, tab3 = st.tabs(["🏠 ホーム", "📜 履歴・削除", "📈 分析"])

# --- 🏠 ホーム画面 ---
with tab1:
    st.title("💰 給料記録 💰")
    
    # 今月の給料見込み計算
    if not df.empty:
        df['日付'] = pd.to_datetime(df['日付']).dt.date
        today = datetime.date.today()
        this_month_pay = df[pd.to_datetime(df['日付']).dt.month == today.month]['金額'].sum()
        st.metric("今月の給料見込み", f"{int(this_month_pay):,} 円")
    else:
        st.metric("今月の給料見込み", "0 円")

    st.divider()

    # 次の日ボタンのロジック
    if 'target_date' not in st.session_state:
        st.session_state.target_date = datetime.date.today()

    col_d1, col_d2 = st.columns([3, 1])
    with col_d1:
        date = st.date_input("日付を選択", st.session_state.target_date)
    with col_d2:
        if st.button("翌日へ"):
            st.session_state.target_date += datetime.timedelta(days=1)
            st.rerun()

    with st.form("input_form"):
        grade = st.selectbox("学年", ["小学生", "中学生", "高校生"])
        count = st.radio("生徒数", [1, 2, 3], horizontal=True)
        
        # 給料計算
        prices = {"小学生": 1680, "中学生": 1760, "高校生": 2192}
        pay = int(prices[grade] + (count - 1) * 100)
        
        st.write(f"今回の給料: **{pay:,} 円**")
        submitted = st.form_submit_button("記録を保存")
        
        if submitted:
            new_row = pd.DataFrame([{"日付": date, "学年": grade, "人数": count, "金額": pay}])
            conn.create(data=new_row)
            st.success("保存したぜ！")
            time.sleep(1)
            st.rerun()

# --- 📜 履歴・削除画面 ---
with tab2:
    st.subheader("過去の記録と削除")
    if not df.empty:
        # 削除機能のためにインデックス付きで表示
        display_df = df.copy()
        display_df = display_df.sort_values('日付', ascending=False)
        
        for i, row in display_df.iterrows():
            with st.expander(f"詳細: {row['日付']} - {row['学年']} ({row['金額']}円)"):
                st.write(f"生徒数: {row['人数']}人")
                if st.button(f"この記録を削除する", key=f"del_{i}"):
                    # スプレッドシートからその行を削除（簡易版として、今の行以外を上書き）
                    updated_df = df.drop(i)
                    conn.create(data=updated_df)
                    st.warning("削除したぜ。再読み込みする...")
                    time.sleep(1)
                    st.rerun()
    else:
        st.info("データがありません。")

# --- 📈 分析画面 ---
with tab3:
    st.subheader("給料分析")
    if not df.empty:
        st.write("学年別の割合")
        grade_counts = df['学年'].value_counts()
        st.bar_chart(grade_counts)
        
        st.write("日別の給料推移")
        line_df = df.set_index('日付')['金額']
        st.line_chart(line_df)
    else:
        st.info("分析するデータがまだないぜ。")
