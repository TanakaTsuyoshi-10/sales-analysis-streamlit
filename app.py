import streamlit as st
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from io import BytesIO

# 日本語フォント設定（Streamlit Cloud 対応）
matplotlib.rcParams['font.family'] = ['IPAexGothic']
matplotlib.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="店舗別売上分析", layout="wide")
st.title("📊 店舗別売上分析アプリ")

# CSVアップローダー
uploaded_file = st.file_uploader("📂 CSVファイルをアップロードしてください（Shift-JIS形式、2行ヘッダー）", type="csv")

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding="cp932", skiprows=2)
    except Exception as e:
        st.error(f"CSVの読み込みに失敗しました: {e}")
        st.stop()

    # 店舗マッピングと順序
    store_map = {
        "2": "隼人", "3": "鷹尾", "4": "中町", "5": "三股", "7": "宮崎", "8": "熊本",
        "14": "鹿屋", "15": "吉野", "16": "花山手東", "17": "大根田", "18": "中山",
        "21": "土井", "22": "空港東", "23": "有田", "24": "春日", "25": "長嶺"
    }

    store_order = [
        "三股", "鷹尾", "中町", "宮崎", "隼人", "熊本", "鹿屋", "吉野",
        "花山手東", "大根田", "中山", "土井", "空港東", "有田", "春日", "長嶺"
    ]

    # 前処理
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
    df["店舗名"] = pd.Categorical(df["店舗名"], categories=store_order, ordered=True)

    # 対象商品
    target_products = [
        "ぎょうざ２０個", "ぎょうざ３０個", "ぎょうざ４０個", "ぎょうざ５０個",
        "生姜入ぎょうざ３０個", "宅配ぎょうざ40個", "宅配ぎょうざ50個"
    ]
    df_gyoza = df[df["商品名"].isin(target_products)].copy()

    # 集計（レシート単位）
    receipt_summary = df.groupby(["販売日", "年月", "販売時", "店舗名", "レシート番号"]).agg(
        客数=("レシート番号", "nunique"),
        売上金額=("小計", "sum")
    ).reset_index()

    gyoza_counts = df_gyoza.groupby(["販売日", "年月", "販売時", "店舗名", "レシート番号"]).agg(
        販売個数=("数量", "sum")
    ).reset_index()

    receipt_summary = pd.merge(
        receipt_summary, gyoza_counts,
        on=["販売日", "年月", "販売時", "店舗名", "レシート番号"], how="left"
    )
    receipt_summary["販売個数"] = receipt_summary["販売個数"].fillna(0)
    receipt_summary["平均単価"] = receipt_summary["売上金額"] / receipt_summary["販売個数"].replace(0, 1)

    def summarize(data, group_keys):
        summary = data.groupby(group_keys).agg(
            売上高=("売上金額", "sum"),
            客数=("客数", "sum"),
            販売個数=("販売個数", "sum")
        ).reset_index()
        summary["1人あたり単価"] = summary["売上高"] / summary["客数"].replace(0, 1)
        if "店舗名" in group_keys:
            summary["店舗名"] = pd.Categorical(summary["店舗名"], categories=store_order, ordered=True)
            summary = summary.sort_values("店舗名")
        return summary

    # ボタン押下でExcel出力
    if st.button("📦 Excel集計（軽量版）"):
        daily = summarize(receipt_summary, ["販売日", "店舗名"])
        daily["販売日"] = daily["販売日"].dt.strftime("%Y/%-m/%-d")

        monthly = summarize(receipt_summary, ["年月", "店舗名"])
        hourly = summarize(receipt_summary, ["年月", "販売時", "店舗名"])

        product_summary = df_gyoza.groupby(["店舗名", "商品名"]).agg(
            販売個数=("数量", "sum")
        ).reset_index()
        product_summary["店舗名"] = pd.Categorical(product_summary["店舗名"], categories=store_order, ordered=True)
        product_pivot = product_summary.pivot(index="店舗名", columns="商品名", values="販売個数").fillna(0)
        product_pivot = product_pivot.loc[product_pivot.index.intersection(store_order)]

        ranking = df_gyoza.groupby("商品名").agg(
            販売個数=("数量", "sum"),
            売上金額=("小計", "sum")
        ).sort_values("売上金額", ascending=False).head(10)

        weekday_summary = df_gyoza.groupby(["店舗名", "曜日名"]).agg(
            販売個数=("数量", "sum"),
            売上金額=("小計", "sum")
        ).reset_index()
        weekday_summary["店舗名"] = pd.Categorical(weekday_summary["店舗名"], categories=store_order, ordered=True)
        weekday_pivot = weekday_summary.pivot(index="店舗名", columns="曜日名").fillna(0)
        weekday_pivot = weekday_pivot[[col for day in weekday_jp for col in weekday_pivot.columns if col[1] == day]]
        weekday_pivot = weekday_pivot.loc[weekday_pivot.index.intersection(store_order)]

        # Excel出力
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            daily.to_excel(writer, index=False, sheet_name="日次_店舗別")
            monthly.to_excel(writer, index=False, sheet_name="月次_店舗別")
            hourly.to_excel(writer, index=False, sheet_name="月次_時間帯別")
            product_pivot.to_excel(writer, sheet_name="月次_商品別")
            ranking.to_excel(writer, index=True, sheet_name="商品ランキング")
            weekday_pivot.to_excel(writer, sheet_name="曜日別_販売数")

        output.seek(0)
        st.download_button(
            "⬇️ 売上分析レポートをダウンロード",
            data=output.getvalue(),
            file_name="売上分析レポート.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
