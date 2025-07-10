
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from openpyxl.drawing.image import Image as XLImage
from openpyxl import load_workbook
import matplotlib
import calendar

# ✅ macOSで日本語表示するためのフォント設定
matplotlib.rcParams['font.family'] = 'Hiragino Mincho ProN'

st.title("📊 店舗別売上分析アプリ")

uploaded_file = st.file_uploader(
    "📂 CSVファイルをアップロードしてください（Shift-JIS形式）",
    type="csv"
)

if uploaded_file:
    df = pd.read_csv(uploaded_file, encoding="cp932", skiprows=2)

    store_map = {
        "2": "隼人", "3": "鷹尾", "4": "中町", "5": "三股", "7": "宮崎", "8": "熊本",
        "14": "鹿屋", "15": "吉野", "16": "花山手東", "17": "大根田", "18": "中山",
        "21": "土井", "22": "空港東", "23": "有田", "24": "春日", "25": "長嶺"
    }

    df["販売日"] = df["販売日時"].str.extract(r"(\d{4}年\d{2}月\d{2}日)")
    df["販売時刻"] = df["販売日時"].str.extract(r"(\d{2}:\d{2})")
    df["販売時"] = df["販売時刻"].str[:2]
    df["店舗番号"] = df["レシート番号"].str.extract(r"No\.(\d+)-")[0]
    df["店舗名"] = df["店舗番号"].map(store_map).fillna("不明")
    df["販売単価"] = pd.to_numeric(df["販売単価"].astype(str).str.replace("@", "").str.replace(",", ""), errors="coerce")
    df["数量"] = pd.to_numeric(df["数量"], errors="coerce")
    df["小計"] = pd.to_numeric(df["小計"], errors="coerce")
    df = df[df["数量"].notnull() & df["小計"].notnull() & df["販売日"].notnull()]

    df["年月"] = df["販売日"].str.extract(r"(\d{4}年\d{2}月)")
    df["販売日"] = pd.to_datetime(df["販売日"].str.replace("年", "-").str.replace("月", "-").str.replace("日", ""), errors="coerce")
    df = df[df["販売日"].notnull()]
    df["曜日"] = df["販売日"].dt.dayofweek
    weekday_jp = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    df["曜日名"] = df["曜日"].apply(lambda x: weekday_jp[x])

    receipt_summary = df.groupby(["販売日", "年月", "販売時", "店舗名", "レシート番号"]).agg(
        客数=("レシート番号", "nunique"),
        販売個数=("数量", "sum"),
        売上金額=("小計", "sum")
    ).reset_index()
    receipt_summary["平均単価"] = receipt_summary["売上金額"] / receipt_summary["販売個数"]

    # df_time を定義
    df_time = receipt_summary.copy()
    df_time["販売時"] = df_time["販売時"].astype(int)
    df_time["日時"] = pd.to_datetime(
        df_time["年月"].str.replace("年", "-").str.replace("月", "-01 ") + df_time["販売時"].astype(str) + ":00",
        errors="coerce"
    )
    df_time["曜日"] = df_time["日時"].dt.dayofweek.map({0: "月", 1: "火", 2: "水", 3: "木", 4: "金", 5: "土", 6: "日"})
    df_time["時間帯"] = df_time["日時"].dt.hour

    # --- 曜日・時間帯・店舗別 来店客数の分析 ---
    weekday_tables = {}
    for weekday in df_time["曜日"].unique():
        temp_df = df_time[df_time["曜日"] == weekday]
        pivot = temp_df.groupby(["店舗名", "時間帯"])["客数"].sum().unstack().fillna(0)
        weekday_tables[weekday] = pivot

    st.title("📊 曜日別・時間帯別 来店客数（店舗別）")

    tabs = st.tabs(list(weekday_tables.keys()))
    for i, weekday in enumerate(weekday_tables.keys()):
        with tabs[i]:
            st.subheader(f"{weekday}曜日 - 店舗別・時間帯別 来店客数")
            st.dataframe(weekday_tables[weekday].style.format("{:.0f}"))

            fig, ax = plt.subplots(figsize=(12, 6))
            sns.heatmap(weekday_tables[weekday], annot=True, fmt=".0f", cmap="YlOrRd", ax=ax)
            ax.set_title(f"{weekday}曜日の来店客数（店舗×時間帯）")
            st.pyplot(fig)
