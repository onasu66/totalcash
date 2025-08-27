# streamlit_app_v2.py
import streamlit as st
import re
import pandas as pd

st.title("トーク履歴 最終・追加抽出＆金額集計（改良版）")

# テキスト入力
text_input = st.text_area("トーク履歴をここに貼り付けてください", height=500)

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
    戻り値: 合計金額（人数 × 単価 + バック）
    """
    m = re.match(r'(\d+)\.(\d+)', line)
    if not m:
        return 0
    count = int(m.group(1))
    unit = int(m.group(2))
    
    # バックの抽出
    back = 0
    for key, val in BACK_VALUES.items():
        if key in line:
            back += val
    return count * unit + back

if st.button("抽出＆集計"):
    if not text_input.strip():
        st.warning("テキストを入力してください")
    else:
        lines = text_input.splitlines()
        pattern = re.compile(r'最終|追加')
        data = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if pattern.search(line):
                # 次の行から店舗名・金額を取得
                i += 1
                current_store = ""
                while i < len(lines) and not re.match(r'\d{1,2}:\d{2}', lines[i]):
                    l = lines[i].strip()
                    # 金額行か？
                    m_money = re.match(r'(\d+\.\d+.*)', l)
                    if m_money and current_store:
                        money = parse_money(m_money.group(1))
                        data.append({"店舗名": current_store, "内容": m_money.group(1), "金額": money})
                        current_store = ""  # 一度使ったらリセット
                    else:
                        # 店舗名行と判断
                        if l:
                            current_store = l
                    i += 1
            else:
                i += 1
        
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
