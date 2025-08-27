# streamlit_app.py
import streamlit as st
import re
import pandas as pd
import unicodedata

st.title("トーク履歴 最終・追加抽出＆店舗別金額集計")

# バック金額ルール
def get_bonus(symbol: str) -> int:
    if symbol == "❤️":
        return 5000
    elif symbol == "⭕️":
        return 4000
    elif symbol == "S":
        return 3000
    elif symbol == "E":
        return 2000
    elif symbol and "⭐️" in symbol:
        star_num = int(symbol.replace("⭐️", ""))
        if star_num == 6:
            return 9000
        elif star_num == 7:
            return 1000
        elif star_num == 8:
            return 11000
        elif star_num == 9:
            return 12000
        elif star_num == 10:
            return 13000
    return 0

# 店舗名を正規化する関数
def normalize_store_name(name: str) -> str:
    # 全角 → 半角
    name = unicodedata.normalize("NFKC", name)
    # 前後のスペース削除（全角・半角両方）
    name = name.strip().replace("　", "")
    return name

# 1. テキスト入力エリア
text_input = st.text_area("トーク履歴をここに貼り付けてください", height=400)

if st.button("抽出＆集計"):
    if not text_input.strip():
        st.warning("テキストを入力してください")
    else:
        lines = text_input.splitlines()

        # 「最終」「追加」を探す
        pattern = re.compile(r'(最終|追加)\s*(.*)')
        indices = [(i, pattern.search(line)) for i, line in enumerate(lines) if pattern.search(line)]

        data = []
        for i, match in indices:
            store = normalize_store_name(match.group(2) if match.group(2) else "不明店舗")

            content = []
            j = i + 1
            while j < len(lines) and not re.match(r'\d{1,2}:\d{2}', lines[j]):  # 次のタイムスタンプまで
                content.append(lines[j])
                j += 1

            money = 0
            for line in content:
                matches = re.findall(r'(\d+)(❤️|⭕️|S|E|⭐️\d+)?', line)
                for num, symbol in matches:
                    base = int(num)
                    bonus = get_bonus(symbol)
                    money += base + bonus

            data.append({
                "店舗": store,
                "内容": "\n".join(content),
                "金額": money
            })

        # DataFrame
        df = pd.DataFrame(data)

        st.subheader("抽出結果（店舗ごと）")
        st.dataframe(df)

        # 店舗ごとに合算（正規化済み店舗名でまとめる）
        df_store = df.groupby("店舗")["金額"].sum().reset_index().sort_values("金額", ascending=False)

        st.subheader("店舗別 合計金額")
        st.dataframe(df_store)

        st.subheader("総合計")
        st.write(int(df["金額"].sum()))
