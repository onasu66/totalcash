# streamlit_app.py
import streamlit as st
import re
import pandas as pd

st.title("トーク履歴 最終・追加抽出＆金額集計（店舗別）")

# テキスト入力エリア
text_input = st.text_area("トーク履歴をここに貼り付けてください", height=500)

if st.button("抽出＆集計"):
    if not text_input.strip():
        st.warning("テキストを入力してください")
    else:
        lines = text_input.splitlines()
        
        # 最終 or 追加行のインデックス
        indices = [i for i, line in enumerate(lines) if re.search(r'最終|追加', line)]
        
        data = []
        
        for idx in indices:
            i = idx + 1
            while i < len(lines) and not re.match(r'\d{1,2}:\d{2}', lines[i]):
                line = lines[i].strip()
                if not line:
                    i += 1
                    continue
                
                # 金額がある行
                money_match = re.search(r'(\d+\.?\d*)([❤⭕️S⭐️])?', line)
                if money_match:
                    amount = float(money_match.group(1).replace('.', ''))
                    mark = money_match.group(2)
                    
                    # マークごとの金額補正
                    if mark == '❤' or mark == '❤️':
                        pass  # そのまま
                    elif mark == '⭕️':
                        pass  # そのまま
                    elif mark == 'S':
                        pass  # そのまま
                    elif mark == '⭐️':
                        next_digit = re.search(r'⭐️(\d+)', line)
                        if next_digit:
                            n = int(next_digit.group(1))
                            if n == 6:
                                amount = 9000
                            elif n == 7:
                                amount = 1000
                            elif n == 8:
                                amount = 11000
                            elif n == 9:
                                amount = 12000
                            elif n == 10:
                                amount = 13000
                    # 店舗名は直前の行と仮定
                    if i - 1 >= 0:
                        shop = lines[i-1].strip()
                    else:
                        shop = "不明店舗"
                    
                    data.append({
                        "店舗名": shop,
                        "金額": amount
                    })
                i += 1
        
        # DataFrame化
        df = pd.DataFrame(data)
        if not df.empty:
            df_grouped = df.groupby("店舗名", as_index=False).sum()
            st.subheader("店舗別集計")
            st.dataframe(df_grouped)
            
            st.subheader("合計金額")
            st.write(df_grouped['金額'].sum())
        else:
            st.info("抽出できるデータがありませんでした。")
