# streamlit_app.py
import streamlit as st
import re
import pandas as pd

st.title("トーク履歴 最終・追加抽出＆金額集計（バック込み）")

# 1. テキスト入力エリア
text_input = st.text_area("トーク履歴をここに貼り付けてください", height=400)

if st.button("抽出＆集計"):
    if not text_input.strip():
        st.warning("テキストを入力してください")
    else:
        # 2. 行ごとに分割
        lines = text_input.splitlines()
        
        # 3. 抽出対象の行（最終 or 追加）のインデックスを取得
        pattern = re.compile(r'最終|追加')
        indices = [i for i, line in enumerate(lines) if pattern.search(line)]
        
        # 4. 抽出したトークと金額をまとめる
        data = []
        for i in indices:
            content = []
            j = i + 1
            while j < len(lines) and not re.match(r'\d{1,2}:\d{2}', lines[j]):  # 次のタイムスタンプまで
                content.append(lines[j])
                j += 1

            money = 0
            for line in content:
                # 通常の金額部分を抽出
                matches = re.findall(r'(\d+)(❤️|⭕️|S|E|⭐️\d+)?', line)
                for num, symbol in matches:
                    base = int(num)
                    bonus = 0
                    if symbol == "❤️":
                        bonus = 5000
                    elif symbol == "⭕️":
                        bonus = 4000
                    elif symbol == "S":
                        bonus = 3000
                    elif symbol == "E":
                        bonus = 2000
                    elif symbol and "⭐️" in symbol:
                        # ⭐️の場合、後ろの数字に応じて変化
                        star_num = int(symbol.replace("⭐️", ""))
                        if star_num == 6:
                            bonus = 9000
                        elif star_num == 7:
                            bonus = 1000
                        elif star_num == 8:
                            bonus = 11000
                        elif star_num == 9:
                            bonus = 12000
                        elif star_num == 10:
                            bonus = 13000
                    money += base + bonus
            
            data.append({
                "行": lines[i],
                "内容": "\n".join(content),
                "金額": money
            })
        
        # 5. DataFrame にして表示
        df = pd.DataFrame(data)
        st.subheader("抽出結果")
        st.dataframe(df)
        
        st.subheader("合計金額")
        st.write(df['金額'].sum())
