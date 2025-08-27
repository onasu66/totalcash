# streamlit_app.py
import streamlit as st
import re
import pandas as pd

st.title("トーク履歴 最終・追加抽出＆金額集計（時間付きバック対応）")

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
    'E': 0  # 必要に応じて追加
}

def parse_money(line):
    """
    line: '2.2000 21:56❤️' のような文字列
    戻り値: 合計金額（人数 × 単価 + バック人数分）
    """
    # 時間や余分な文字を除去
    line_clean = re.split(r'\s', line)[0]  # '2.2000 21:56❤️' -> '2.2000'
    
    # 人数.単価の抽出
    m = re.match(r'(\d+)\.(\d+)', line_clean)
    if not m:
        return 0
    count = int(m.group(1))
    unit = int(m.group(2))

    # バックの抽出（元の line から）
    back_total = 0
    for key, val in BACK_VALUES.items():
        if key in line:
            back_total += val * count

    return count * unit + back_total

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
            j
