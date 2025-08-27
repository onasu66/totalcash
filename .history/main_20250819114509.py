# streamlit_app.py
import streamlit as st
import re
import pandas as pd

st.title("トーク履歴 最終・追加抽出＆金額集計（複数金額・連続対応）")

# テキスト入力
text_input = st.text_area("トーク履歴をここに貼り付けてください", height=400)

# バック金額定義
BACK_VALUES = {
    '❤': 5000,
    '⭕️': 4000,
    'S': 3000,
    '⭐️6': 9000,
    '⭐️7': 10000,
    '⭐️8': 11000,
    '⭐️9': 12000,
    '⭐️10': 13000,
    'E': 0
}

def parse_money(line):
    """
    line: '2.2000S' のような文字列
    戻り値: 合計金額（人数 × 単価 + 人数 × バック）
    """
    m = re.search(r'(\d+)\.(\d+)', line)
    if not m:
        return 0
    count = int(m.group(1))
    unit = int(m.group(2))

    # バックの抽出（人数分）
    back = 0
    for key, val in BACK_VALUES.items():
        if key in line:
            back += val * count

    return count * unit + back

if st.button("抽出＆集計"):
    if not text_input.strip():
        st.warning("テキストを入力してください")
    else:
        lines = text_input.splitlines()
        # 最終 or 追加 行のインデックス
        pattern = re.compile(r'最終|追加')
        indices = [i for i, line in enumerate(lines) if pattern.search(line)]
        
        data = []
        for i in indices:
            j = i + 1
            current_store = None
            while j < len(lines) and not re.match(r'\d{1,2}:\d{2}', lines[j]):
                line = lines[j].strip()
                
                # 金額行の抽出
                money_match = re.search(r'(\d+\.\d+.*)', line)
                if money_match:
                    money_str = money_match.group(1)
                    money = parse_money(money_str)

                    # 店舗名は金額より前の文字列
                    store_candidate = line[:line.find(money_str)].strip()
                    if store_candidate:
                        current_store = store_candidate

                    if current_store:
                        data.append({"店舗名": current_store, "内容": money_str, "金額": money})
                j += 1
        
        # DataFrame に変換
        df = pd.DataFrame(data)
        st.subheader("抽出結果")
        st.dataframe(df)

        # 店舗ごとの合計
        store_sum = df.groupby('店舗名')['金額'].sum().reset_index()
        st.subheader("店舗ごとの合計金額")
        st.dataframe(store_sum)

        st.subheader("全体合計金額")
        st.write(df['金額'].sum())
