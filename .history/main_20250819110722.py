# streamlit_app.py
import streamlit as st
import re
import pandas as pd

st.title("トーク履歴 最終・追加抽出＆金額集計（複数金額行対応）")

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
    戻り値: 合計金額（人数 × 単価 + バック×人数）
    """
    m = re.match(r'(\d+)\.(\d+)', line)
    if not m:
        return 0
    count = int(m.group(1))
    unit = int(m.group(2))
    
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
        pattern = re.compile(r'最終|追加')
        indices = [i for i, line in enumerate(lines) if pattern.search(line)]
        
        data = []
        for i in indices:
            j = i + 1
            current_store = None
            while j < len(lines) and not re.match(r'\d{1,2}:\d{2}', lines[j]):
                line = lines[j].strip()
                
                # 店舗名判定（絵文字や特定パターン）
                if re.search(r'[🟢🟦]', line):
                    current_store = line
                
                # 金額行判定（1行に複数金額があればスペースで分割）
                elif re.search(r'\d+\.\d+', line):
                    if current_store:
                        money_parts = line.split()
                        for money_str in money_parts:
                            if re.match(r'\d+\.\d+', money_str):
                                money = parse_money(money_str)
                                data.append({"店舗名": current_store, "内容": money_str, "金額": money})
                j += 1
        
        df = pd.DataFrame(data)
        st.subheader("抽出結果")
        st.dataframe(df)

        store_sum = df.groupby('店舗名')['金額'].sum().reset_index()
        st.subheader("店舗ごとの合計金額")
        st.dataframe(store_sum)

        st.subheader("全体合計金額")
        st.write(df['金額'].sum())
