# streamlit_app.py
import streamlit as st
import re
import pandas as pd

st.title("トーク履歴 最終・追加抽出＆金額集計")

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
            # トーク内容（次の行から数行に渡る場合もある）
            content = []
            j = i + 1
            while j < len(lines) and not re.match(r'\d{1,2}:\d{2}', lines[j]):  # 次のタイムスタンプまで
                content.append(lines[j])
                j += 1
            # 金額の抽出
            money = sum([int(num.replace('.', '').replace('❤','').replace('⭕️','').replace('S','').replace('⭐️','').strip()) 
                         for line in content for num in re.findall(r'\d+\.?\d*', line)])
            
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
