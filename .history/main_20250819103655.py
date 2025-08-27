# streamlit_app.py
import streamlit as st
import re
import pandas as pd

st.title("トーク履歴 最終・追加抽出＆金額集計")

# テキスト入力エリア
text_input = st.text_area("トーク履歴をここに貼り付けてください", height=400)

# ボタン押下時
if st.button("抽出＆集計"):
    if not text_input.strip():
        st.warning("テキストを入力してください")
    else:
        lines = text_input.splitlines()
        pattern = re.compile(r'最終|追加')
        indices = [i for i, line in enumerate(lines) if pattern.search(line)]
        
        data = []
        for i in indices:
            # 「行」 = タイムスタンプ + 名前 + 最終/追加
            header = lines[i]
            header_parts = header.split()
            timestamp = header_parts[0]
            user = header_parts[1] if len(header_parts) > 1 else "不明"
            type_label = header_parts[2] if len(header_parts) > 2 else "不明"

            # トーク内容（次のタイムスタンプまで）
            content = []
            j = i + 1
            while j < len(lines) and not re.match(r'\d{1,2}:\d{2}', lines[j]):
                if lines[j].strip():
                    content.append(lines[j].strip())
                j += 1

            # 店舗名と金額抽出
            money_total = 0
            store_money = {}
            for line in content:
                # 金額抽出
                amounts = re.findall(r'\d+\.?\d*', line)
                for a in amounts:
                    a_int = int(a.replace('.', ''))

                    if '❤️' in line or '❤' in line:
                        val = a_int
                    elif '⭕️' in line:
                        val = a_int
                    elif 'S' in line:
                        val = a_int
                    elif '⭐️' in line:
                        # ⭐️の次の数字を取得
                        star_match = re.search(r'⭐️(\d+)', line)
                        if star_match:
                            num = int(star_match.group(1))
                            star_map = {6:9000, 7:1000, 8:11000, 9:12000, 10:13000}
                            val = star_map.get(num, 0)
                        else:
                            val = 0
                    else:
                        val = a_int

                    # 店舗名は数字の前の文字列を店舗名と仮定
                    store_match = re.match(r'([^\d]+)', line)
                    store = store_match.group(1).strip() if store_match else "不明店舗"

                    store_money[store] = store_money.get(store, 0) + val
                    money_total += val

            data.append({
                "ユーザー": user,
                "タイプ": type_label,
                "内容": "\n".join(content),
                "合計金額": money_total,
                "店舗ごと": store_money
            })

        # DataFrame作成
        df = pd.DataFrame(data)
        st.subheader("抽出結果")
        st.dataframe(df)

        # 店舗ごとに合算
        all_store_totals = {}
        for row in data:
            for store, amount in row['店舗ごと'].items():
                all_store_totals[store] = all_store_totals.get(store, 0) + amount

        st.subheader("店舗ごとの合計金額")
        store_df = pd.DataFrame(list(all_store_totals.items()), columns=['店舗名', '合計金額'])
        st.dataframe(store_df)

        st.subheader("全体合計")
        st.write(sum(all_store_totals.values()))
