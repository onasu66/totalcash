# streamlit_app.py
import streamlit as st
import re
import pandas as pd

st.title("トーク履歴 最終・追加抽出＆金額集計（複数金額対応・絵文字無しOK）")

# テキスト入力
text_input = st.text_area("トーク履歴をここに貼り付けてください", height=500)

# バック金額定義
BACK_VALUES = {
    '❤': 5000,
    '❤️': 5000,
    '⭕': 4000,
    '⭕️': 4000,
    'S': 3000,
    '⭐️6': 9000,
    '⭐️7': 10000,
    '⭐️8': 11000,
    '⭐️9': 12000,
    '⭐️10': 13000,
    '⭐6': 9000,
    '⭐7': 10000,
    '⭐8': 11000,
    '⭐9': 12000,
    '⭐10': 13000,
    'E': 0  # 必要に応じて追加
}

def parse_money(line):
    """
    line: '2.2000S' や '1.1000 ❤' や '1 .2000❤️' や '1.300019:21❤️' のような文字列
    戻り値: 合計金額（人数 × 単価 + バック × 人数）
    """
    # 時間パターン（19:21など）を除去
    line_without_time = re.sub(r'\d{1,2}:\d{2}', '', line)
    
    # 金額部分を抽出（スペースを考慮）
    # パターン1: 1.3000 (通常)
    # パターン2: 1 .3000 (スペースあり)
    # パターン3: 2.1000. (末尾にドット)
    m = re.search(r'(\d+)\s*\.\s*(\d+)', line_without_time)
    if not m:
        return 0
    
    count = int(m.group(1))
    unit = int(m.group(2))
    back_total = 0
    
    # 絵文字の柔軟なマッチング（元のlineでチェック）
    for key, val in BACK_VALUES.items():
        if key in line:
            back_total += val * count
            break  # 最初にマッチしたもので処理を終了（重複を避ける）
    
    return count * unit + back_total

if st.button("抽出＆集計"):
    if not text_input.strip():
        st.warning("テキストを入力してください")
    else:
        lines = text_input.splitlines()
        pattern = re.compile(r'最終|追加')
        indices = [i for i, line in enumerate(lines) if pattern.search(line)]
        
        data = []
        for i in indices:
            # 名前を抽出（最終・追加を含む行から）
            trigger_line = lines[i]
            # パターン: "21:07 はかせ ラスター最終" -> "はかせ"
            # 時間の後、最終・追加の前の部分を名前として抽出
            name_match = re.search(r'\d{1,2}:\d{2}\s+(.+?)\s+.*(?:最終|追加)', trigger_line)
            current_user = name_match.group(1).strip() if name_match else "不明ユーザー"
            
            j = i + 1
            current_store = None
            while j < len(lines) and not re.match(r'\d{1,2}:\d{2}', lines[j]):
                line = lines[j].strip()
                
                # 金額行（時間パターンを考慮）
                line_without_time = re.sub(r'\d{1,2}:\d{2}', '', line)
                if re.search(r'\d+\s*\.\s*\d+', line_without_time):
                    if current_store:
                        money = parse_money(line)
                        data.append({
                            "入力者": current_user,
                            "店舗名": current_store, 
                            "内容": line, 
                            "金額": money
                        })
                
                # 店舗名行（次の行が金額行の場合）
                elif line:
                    if j + 1 < len(lines):
                        next_line_without_time = re.sub(r'\d{1,2}:\d{2}', '', lines[j + 1])
                        if re.search(r'\d+\s*\.\s*\d+', next_line_without_time):
                            current_store = line
                j += 1

        # DataFrame に変換
        df = pd.DataFrame(data)
        st.subheader("抽出結果")
        st.dataframe(df)

        if not df.empty:
            # 店舗ごとの合計
            store_sum = df.groupby('店舗名')['金額'].sum().reset_index()
            st.subheader("店舗ごとの合計金額")
            st.dataframe(store_sum)

            # 入力者ごとの合計
            user_sum = df.groupby('入力者')['金額'].sum().reset_index()
            st.subheader("入力者ごとの合計金額")
            st.dataframe(user_sum)

            # 店舗・入力者別の詳細集計
            detail_sum = df.groupby(['店舗名', '入力者'])['金額'].sum().reset_index()
            st.subheader("店舗・入力者別の合計金額")
            st.dataframe(detail_sum)

            st.subheader("全体合計金額")
            st.write(f"{df['金額'].sum():,}円")
        else:
            st.warning("抽出されたデータがありません")
