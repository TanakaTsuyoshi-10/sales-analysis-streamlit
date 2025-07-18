import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from openpyxl import load_workbook
import matplotlib
import warnings
from matplotlib import font_manager

# 📌 フォント設定：Cloudでも文字化け防止
font_path = "fonts/ipaexg.ttf"
font_manager.fontManager.addfont(font_path)
matplotlib.rcParams["font.family"] = font_manager.FontProperties(fname=font_path).get_name()
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.font_manager")

st.title("📊 店舗別売上分析アプリ")

uploaded_file = st.file_uploader("📂 CSVファイルをアップロードしてください（Shift-JIS形式）", type="csv")

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
    df["販売時"] = pd.to_numeric(df["販売時"], errors="coerce")
    df["日時"] = pd.to_datetime(df["販売日"].astype(str) + " " + df["販売時"].astype(str) + ":00", errors="coerce")
    df["曜日"] = df["日時"].dt.dayofweek.map({0: "月", 1: "火", 2: "水", 3: "木", 4: "金", 5: "土", 6: "日"})
    df["時間帯"] = df["日時"].dt.hour

    receipt_summary = df.groupby(["販売日", "年月", "販売時", "店舗名", "レシート番号"]).agg(
        客数=("レシート番号", "nunique"),
        販売個数=("数量", "sum"),
        売上金額=("小計", "sum")
    ).reset_index()
    receipt_summary["平均単価"] = receipt_summary["売上金額"] / receipt_summary["販売個数"]

    def summarize(data, group_keys):
        summary = data.groupby(group_keys).agg(
            売上高=("売上金額", "sum"),
            客数=("客数", "sum"),
            販売個数=("販売個数", "sum")
        ).reset_index()
        summary["1人あたり単価"] = summary["売上高"] / summary["客数"]
        return summary

    if st.button("📦 Excel集計"):
        daily = summarize(receipt_summary, ["販売日", "店舗名"])
        daily["販売日"] = pd.to_datetime(daily["販売日"]).dt.strftime("%Y/%-m/%-d")
        monthly = summarize(receipt_summary, ["年月", "店舗名"])
        hourly = summarize(receipt_summary, ["年月", "販売時", "店舗名"])
        product_summary = df.groupby(["店舗名", "商品名"]).agg(販売個数=("数量", "sum")).reset_index()
        product_pivot = product_summary.pivot(index="店舗名", columns="商品名", values="販売個数").fillna(0)
        ranking = df.groupby("商品名").agg(販売個数=("数量", "sum"), 売上金額=("小計", "sum")).sort_values("売上金額", ascending=False).head(10)
        weekday_summary = df.groupby(["店舗名", "曜日"]).agg(販売個数=("数量", "sum"), 売上金額=("小計", "sum")).reset_index()
        weekday_pivot = weekday_summary.pivot(index="店舗名", columns="曜日").fillna(0)

        weekday_store_time = (
            df.groupby(["曜日", "店舗名", "時間帯"])["レシート番号"]
            .nunique().reset_index()
            .pivot_table(index=["曜日", "店舗名"], columns="時間帯", values="レシート番号")
            .fillna(0).astype(int)
        )

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            daily.to_excel(writer, index=False, sheet_name="日次_店舗別")
            monthly.to_excel(writer, index=False, sheet_name="月次_店舗別")
            hourly.to_excel(writer, index=False, sheet_name="月次_時間帯別")
            product_pivot.to_excel(writer, sheet_name="月次_商品別")
            ranking.to_excel(writer, index=True, sheet_name="商品ランキング")
            weekday_pivot.to_excel(writer, sheet_name="曜日別_販売数")
            weekday_store_time.to_excel(writer, sheet_name="曜日別_時間帯別_店舗別")
        output.seek(0)
        st.download_button("⬇️ 分析レポートをダウンロード", data=output.getvalue(), file_name="売上分析レポート.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # 表示処理：曜日×店舗×時間帯ヒートマップ
    weekday_labels = ["月", "火", "水", "木", "金", "土", "日"]
    weekday_tables = {}
    for weekday in weekday_labels:
        temp_df = df[df["曜日"] == weekday]
        if not temp_df.empty:
            pivot = temp_df.groupby(["店舗名", "時間帯"])["レシート番号"].nunique().unstack().fillna(0)
        else:
            pivot = pd.DataFrame(columns=list(range(0, 24)), index=sorted(df["店舗名"].unique())).fillna(0)
        weekday_tables[weekday] = pivot

    st.title("📊 曜日別・時間帯別 来店客数（店舗別）")
    tabs = st.tabs(weekday_labels)
    for i, weekday in enumerate(weekday_labels):
        with tabs[i]:
            st.subheader(f"{weekday}曜日 - 店舗別・時間帯別 来店客数")
            st.table(weekday_tables[weekday].astype(int))
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.heatmap(weekday_tables[weekday], annot=True, fmt=".0f", cmap="YlOrRd", ax=ax)
            ax.set_title(f"{weekday}曜日の来店客数（店舗×時間帯）", fontsize=14)
            st.pyplot(fig)