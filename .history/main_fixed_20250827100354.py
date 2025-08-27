# streamlit_app.py
import streamlit as st
import re
import pandas as pd
import datetime

st.title("トーク履歴 最終・追加抽出＆金額集計（複数金額対応・絵文字無しOK）")

# タブで機能を分割
tab1, tab2 = st.tabs(["📋 一括トーク履歴", "➕ 一トーク入力"])

with tab2:
    st.subheader("➕ 一トーク毎の入力")
    
    # セッション状態の初期化
    if 'daily_data' not in st.session_state:
        st.session_state.daily_data = []
    if 'today_date' not in st.session_state:
        st.session_state.today_date = datetime.date.today().strftime("%Y-%m-%d")
    
    # バック金額定義
    BACK_VALUES = {
        '❤': 5000,
        '❤️': 5000,
        '♥': 5000,  # 白いハート追加
        '⭕': 4000,
        '⭕️': 4000,
        'S': 3000,
        's': 3000,  # 小文字のsも追加
        '🔺': 3000,  # 🔺記号を追加
        'B': 1000,  # Bバック追加
        'b': 1000,  # 小文字のbも追加
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
        'E': 2000,  # Eバック
        'e': 2000   # 小文字のeも追加
    }
    
    def parse_money(line):
        """
        line: '2.2000S' や '1.1000 ❤' や '1 .2000❤️' や '1.300019:21❤️' や '1.0❤️' のような文字列
        戻り値: 合計金額（人数 × 単価 + バック × 人数）
        """
        # 時間パターン（19:21など）を除去
        line_without_time = re.sub(r'\d{1,2}:\d{2}', '', line)
        
        # 金額部分を抽出（スペースを考慮、より柔軟に）
        # パターン1: 1.3000 (通常)
        # パターン2: 1 .3000 (スペースあり)
        # パターン3: 2.1000. (末尾にドット)
        # パターン4: 1.0 (小数点以下0)
        # パターン5: 2.3000.S (末尾にドット+記号)
        
        # まず数字の部分を抽出（より柔軟に）
        money_patterns = [
            r'(\d+)\s*\.\s*(\d+)',  # 基本パターン: 1.3000
            r'(\d+)\s*\.\s*(\d*)\s*\.',  # 末尾ドットパターン: 2.1000.
            r'(\d+)\s*\.\s*(\d*)'   # より一般的なパターン
        ]
        
        m = None
        for pattern in money_patterns:
            m = re.search(pattern, line_without_time)
            if m:
                break
        
        if not m:
            return 0
        
        count = int(m.group(1))
        unit_str = m.group(2) if m.group(2) else '0'
        unit = int(unit_str) if unit_str else 0
        back_total = 0
        
        # 絵文字の柔軟なマッチング（元のlineでチェック）
        # スペースを除去してからチェックしてマッチングの精度を向上
        line_for_emoji_check = line.replace(' ', '')
        for key, val in BACK_VALUES.items():
            if key in line_for_emoji_check:
                back_total += val * count
                break  # 最初にマッチしたもので処理を終了（重複を避ける）
        
        return count * unit + back_total
    
    # 入力フォーム
    col1, col2 = st.columns(2)
    with col1:
        user_name = st.text_input("入力者名", key="single_user")
        store_name = st.text_input("店舗名", key="single_store")
    with col2:
        content_input = st.text_input("内容（例: 1.3000❤️）", key="single_content")
        is_final = st.checkbox("最終・追加", key="single_final")
    
    # 追加ボタン
    if st.button("➕ 追加", key="add_single"):
        if user_name and store_name and content_input:
            money = parse_money(content_input)
            entry = {
                "時刻": datetime.datetime.now().strftime("%H:%M"),
                "入力者": user_name,
                "店舗名": store_name,
                "内容": content_input,
                "金額": money,
                "最終・追加": "○" if is_final else "－"
            }
            st.session_state.daily_data.append(entry)
            st.success(f"追加されました: {user_name} - {store_name} - {money:,}円")
            # 入力フィールドをクリア
            st.rerun()
        else:
            st.warning("すべての項目を入力してください")
    
    # 今日のデータ表示
    if st.session_state.daily_data:
        st.subheader(f"📅 今日のデータ ({st.session_state.today_date})")
        df_today = pd.DataFrame(st.session_state.daily_data)
        st.dataframe(df_today)
        
        # 今日の合計
        total_today = df_today['金額'].sum()
        final_today = df_today[df_today['最終・追加'] == '○']['金額'].sum()
        st.metric("💰 今日の総合計", f"{total_today:,}円")
        st.metric("🎯 最終・追加合計", f"{final_today:,}円")
        
        # リセットボタン
        if st.button("🗑️ 今日のデータをリセット", key="reset_today"):
            st.session_state.daily_data = []
            st.rerun()
    else:
        st.info("まだデータがありません。上記のフォームから入力してください。")

with tab1:
    st.subheader("📋 一括トーク履歴処理")
    # テキスト入力
    text_input = st.text_area("トーク履歴をここに貼り付けてください", height=400)

    # バック金額定義
    BACK_VALUES = {
        '❤': 5000,
        '❤️': 5000,
        '♥': 5000,  # 白いハート追加
        '⭕': 4000,
        '⭕️': 4000,
        'S': 3000,
        's': 3000,  # 小文字のsも追加
        '🔺': 3000,  # 🔺記号を追加
        'B': 1000,  # Bバック追加
        'b': 1000,  # 小文字のbも追加
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
        'E': 2000,  # Eバック
        'e': 2000   # 小文字のeも追加
    }

    def parse_money(line):
        """
        line: '2.2000S' や '1.1000 ❤' や '1 .2000❤️' や '1.300019:21❤️' や '1.0❤️' のような文字列
        戻り値: 合計金額（人数 × 単価 + バック × 人数）
        """
        # 時間パターン（19:21など）を除去
        line_without_time = re.sub(r'\d{1,2}:\d{2}', '', line)
        
        # 金額部分を抽出（スペースを考慮、より柔軟に）
        # パターン1: 1.3000 (通常)
        # パターン2: 1 .3000 (スペースあり)
        # パターン3: 2.1000. (末尾にドット)
        # パターン4: 1.0 (小数点以下0)
        # パターン5: 2.3000.S (末尾にドット+記号)
        
        # まず数字の部分を抽出（より柔軟に）
        money_patterns = [
            r'(\d+)\s*\.\s*(\d+)',  # 基本パターン: 1.3000
            r'(\d+)\s*\.\s*(\d*)\s*\.',  # 末尾ドットパターン: 2.1000.
            r'(\d+)\s*\.\s*(\d*)'   # より一般的なパターン
        ]
        
        m = None
        for pattern in money_patterns:
            m = re.search(pattern, line_without_time)
            if m:
                break
        
        if not m:
            return 0
        
        count = int(m.group(1))
        unit_str = m.group(2) if m.group(2) else '0'
        unit = int(unit_str) if unit_str else 0
        back_total = 0
        
        # 絵文字の柔軟なマッチング（元のlineでチェック）
        # スペースを除去してからチェックしてマッチングの精度を向上
        line_for_emoji_check = line.replace(' ', '')
        for key, val in BACK_VALUES.items():
            if key in line_for_emoji_check:
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
            
            # メインデータ（最終・追加）
            main_data = []
            # 参考データ（その他のパターン）
            reference_data = []
            
            # 最終・追加のパターンを処理
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
                    
                    # 金額行（時間パターンを考慮、より柔軟に）
                    line_without_time = re.sub(r'\d{1,2}:\d{2}', '', line)
                    # 複数のパターンをチェック
                    money_patterns = [
                        r'\d+\s*\.\s*\d+',      # 基本: 1.3000
                        r'\d+\s*\.\s*\d*\s*\.', # 末尾ドット: 2.1000.
                        r'\d+\s*\.\s*\d*'       # 一般的: 1.0
                    ]
                    is_money_line = any(re.search(pattern, line_without_time) for pattern in money_patterns)
                    
                    if is_money_line:
                        if current_store:
                            money = parse_money(line)
                            main_data.append({
                                "入力者": current_user,
                                "店舗名": current_store, 
                                "内容": line, 
                                "金額": money
                            })
                    
                    # 店舗名行（次の行が金額行の場合）
                    elif line:
                        if j + 1 < len(lines):
                            next_line_without_time = re.sub(r'\d{1,2}:\d{2}', '', lines[j + 1])
                            next_is_money = any(re.search(pattern, next_line_without_time) for pattern in money_patterns)
                            if next_is_money:
                                current_store = line
                    j += 1
            
            # その他のパターン（時間付きの行で、最終・追加以外）を処理
            for i, line in enumerate(lines):
                if re.match(r'\d{1,2}:\d{2}', line) and not pattern.search(line):
                    # 名前と店舗名を抽出（時間の後の部分から）
                    # パターン: "19:34 ゆうすけ ルビー" -> 名前="ゆうすけ", 店舗名="ルビー"
                    time_content_match = re.search(r'\d{1,2}:\d{2}\s+(.+)', line)
                    if time_content_match:
                        content_after_time = time_content_match.group(1).strip()
                        # スペースで分割して最初の単語を名前、残りを店舗名として扱う
                        parts = content_after_time.split(None, 1)  # 最大1回分割
                        current_user = parts[0] if parts else "不明ユーザー"
                        initial_store = parts[1] if len(parts) > 1 else None
                    else:
                        current_user = "不明ユーザー"
                        initial_store = None
                    
                    j = i + 1
                    current_store = initial_store  # 最初の行から取得した店舗名を使用
                    
                    while j < len(lines) and not re.match(r'\d{1,2}:\d{2}', lines[j]):
                        content_line = lines[j].strip()
                        
                        # 空行や特定の文言をスキップ
                        if not content_line or "メッセージの送信を取り消しました" in content_line or content_line == "出勤":
                            j += 1
                            continue
                        
                        # 金額行（時間パターンを考慮、より柔軟に）
                        line_without_time = re.sub(r'\d{1,2}:\d{2}', '', content_line)
                        # 複数のパターンをチェック
                        money_patterns = [
                            r'\d+\s*\.\s*\d+',      # 基本: 1.3000
                            r'\d+\s*\.\s*\d*\s*\.', # 末尾ドット: 2.1000.
                            r'\d+\s*\.\s*\d*'       # 一般的: 1.0
                        ]
                        is_money_line = any(re.search(pattern, line_without_time) for pattern in money_patterns)
                        
                        if is_money_line:
                            if current_store:
                                money = parse_money(content_line)
                                reference_data.append({
                                    "入力者": current_user,
                                    "店舗名": current_store, 
                                    "内容": content_line, 
                                    "金額": money
                                })
                        
                        # 金額行でない場合、新しい店舗名の可能性をチェック
                        else:
                            if j + 1 < len(lines):
                                next_line_without_time = re.sub(r'\d{1,2}:\d{2}', '', lines[j + 1])
                                next_is_money = any(re.search(pattern, next_line_without_time) for pattern in money_patterns)
                                if next_is_money:
                                    current_store = content_line
                        j += 1

            # DataFrame に変換
            df = pd.DataFrame(main_data)
            
            # === メイン結果 (最終・追加) ===
            st.markdown("---")
            st.markdown("## 📊 メイン集計結果 (最終・追加)")
            
            if not df.empty:
                st.subheader("📋 抽出詳細")
                st.dataframe(df)

                # 店舗ごとの合計
                store_sum = df.groupby('店舗名')['金額'].sum().reset_index()
                st.subheader("🏪 店舗ごとの合計金額")
                st.dataframe(store_sum)

                st.subheader("💰 全体合計金額")
                st.write(f"**{df['金額'].sum():,}円**")
            else:
                st.warning("メイン集計データがありません")

            # === 参考結果 (その他のパターン) ===
            st.markdown("---")
            st.markdown("## 📝 参考集計結果 (その他のパターン)")
            st.info("ℹ️ 「最終」「追加」が付いていないデータです（メイン集計には含まれません）")
            
            # 参考データのDataFrameを作成
            df_reference = pd.DataFrame(reference_data)
            
            if not df_reference.empty:
                st.subheader("📋 入力者毎の店舗と内容")
                # 入力者、店舗名、内容のみを表示（金額列は除外）
                display_df = df_reference[['入力者', '店舗名', '内容']].copy()
                st.dataframe(display_df)
            else:
                st.warning("参考データがありません")
