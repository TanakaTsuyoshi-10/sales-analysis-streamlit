import streamlit as st
import pandas as pd

st.title("✅ Streamlit 起動確認")

uploaded_file = st.file_uploader("CSVをアップロードしてください", type="csv")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding="cp932", skiprows=2)
        st.success("ファイルを読み込みました")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"エラー: {e}")