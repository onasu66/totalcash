# streamlit_app.py
import streamlit as st
import re
import pandas as pd

st.title("トーク履歴 最終・追加抽出＆金額集計（人数×単価＋バック対応）")

# 入力
text_input = st.text_area("トーク履歴をここに貼り付けてください", height=400)

if st.button("抽出＆集計"):
    if not text_input.strip():
        st.warning("テキストを入力してください")
    else:
        lines = text_input.splitlines()
        
        # 最終・追加の行
        indices = [i for i, line in enumerate(lines) if re.search(r'最終|追加', line)]
        
        # バック金額定義
        back_dict = {
            "❤": 5000,
            "⭕️": 4000,
            "S": 3000,
            "E": 2000
        }
        star_dict = {"6": 9000, "7": 10000, "8": 11000, "9": 12000, "10": 13000}
        
        data = []
        
        for i in indices:
            j = i + 1
            while j < len(lines) and not re.match(r'\d{1,2}:\d{2}', lines[j]):
                line = lines[j].strip()
                if not line:
                    j += 1
                    continue
                
                # 行から人数と単価を抽出
                m = re.match(r'(\d+)\.(\d+)', line)
                if m:
                    num_people = int(m.group(1))
                    price_per_person = int(m.group(2))
                    total = num_people * price_per_person
                else:
                    total = 0
                    num_people = 1
                
                # バックの判定
                for key, val in back_dict.items():
                    if key in line:
                        total += val * num_people
                
                # ⭐️対応
                star_m = re.search(r'⭐️(\d+)', line)
                if star_m:
                    star_val = star_dict.get(star_m.group(1), 0)
                    total += star_val * num_people
                
                # 店舗名抽出（記号🟢や色付き文字も含む）
                store_match = re.search(r'[\w\(\)@\-・一-龥]+[🟢🟦🟡🔺]?', line)
                store = store_match.group(0) if store_match else "不明店舗"
                
                data.append({
                    "元行": lines[i],
                    "店舗": store,
                    "人数": num_people,
                    "内容": line,
                    "金額": total
                })
                
                j += 1
        
        # DataFrame化
        df = pd.DataFrame(data)
        
        # 店舗ごとに合算
        summary = df.groupby("店舗")["金額"].sum().reset_index()
        
        st.subheader("抽出詳細")
        st.dataframe(df)
        
        st.subheader("店舗ごとの合計金額")
        st.dataframe(summary)
        
        st.subheader("全体合計金額")
        st.write(df['金額'].sum())