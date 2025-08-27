# streamlit_app.py
import streamlit as st
import re
import pandas as pd
import datetime
import json
import os

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
    'e': 2000,   # 小文字のeも追加
    '🟢': 0,     # 🟢記号を追加（バック無し）
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

# データ永続化のための関数
def save_data_to_file():
    """データをJSONファイルに保存"""
    data = {
        'today_date': st.session_state.get('today_date', ''),
        'daily_data': st.session_state.get('daily_data', []),
        'saved_daily_data': st.session_state.get('saved_daily_data', {})
    }
    try:
        with open('app_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"データ保存エラー: {e}")

def load_data_from_file():
    """JSONファイルからデータを読み込み"""
    if os.path.exists('app_data.json'):
        try:
            with open('app_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except Exception as e:
            st.error(f"データ読み込みエラー: {e}")
            return None
    return None

st.title("トーク履歴 最終・追加抽出＆金額集計（複数金額対応・絵文字無しOK）")

# タブで機能を分割
tab1, tab2 = st.tabs(["📋 一括トーク履歴", "➕ 1回毎トーク入力"])

with tab1:
    st.subheader("📋 一括トーク履歴処理")
    # テキスト入力
    text_input = st.text_area("一日分のトーク履歴をここに貼り付けてください", height=400)

with tab2:
    st.subheader("➕ 1回毎のトーク入力・累積")
    
    # セッション状態の初期化（ファイルからデータを読み込み）
    if 'data_loaded' not in st.session_state:
        # アプリ起動時にデータを読み込み
        saved_data = load_data_from_file()
        if saved_data:
            st.session_state.today_date = saved_data.get('today_date', '')
            st.session_state.daily_data = saved_data.get('daily_data', [])
            st.session_state.saved_daily_data = saved_data.get('saved_daily_data', {})
        else:
            # ファイルがない場合は初期値を設定
            st.session_state.daily_data = []
            now_init = datetime.datetime.now()
            if now_init.hour < 7:
                st.session_state.today_date = (now_init - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                st.session_state.today_date = now_init.strftime("%Y-%m-%d")
            st.session_state.saved_daily_data = {}
        
        st.session_state.data_loaded = True
    
    # 追加の初期化チェック
    if 'daily_data' not in st.session_state:
        st.session_state.daily_data = []
    if 'today_date' not in st.session_state:
        now_init = datetime.datetime.now()
        if now_init.hour < 7:
            st.session_state.today_date = (now_init - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            st.session_state.today_date = now_init.strftime("%Y-%m-%d")
    if 'saved_daily_data' not in st.session_state:
        st.session_state.saved_daily_data = {}
    
    # 朝7時を基準にした日付管理
    now = datetime.datetime.now()
    # 朝7時前の場合は前日扱い
    if now.hour < 7:
        business_date = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        business_date = now.strftime("%Y-%m-%d")
    
    # 営業日が変わったら新しい日として扱う
    if business_date != st.session_state.today_date:
        # 前日のデータを保存
        if st.session_state.daily_data:
            st.session_state.saved_daily_data[st.session_state.today_date] = st.session_state.daily_data.copy()
        
        # 3日より古いデータを自動削除
        def cleanup_old_data():
            current_date = datetime.datetime.strptime(business_date, "%Y-%m-%d")
            cutoff_date = current_date - datetime.timedelta(days=3)
            
            dates_to_remove = []
            for saved_date in st.session_state.saved_daily_data.keys():
                saved_datetime = datetime.datetime.strptime(saved_date, "%Y-%m-%d")
                if saved_datetime < cutoff_date:
                    dates_to_remove.append(saved_date)
            
            for date_to_remove in dates_to_remove:
                del st.session_state.saved_daily_data[date_to_remove]
            
            return len(dates_to_remove)
        
        # 古いデータのクリーンアップ実行
        cleaned_count = cleanup_old_data()
        
        # 新しい日の開始
        st.session_state.today_date = business_date
        st.session_state.daily_data = []
    
    # 営業日と現在時刻の表示
    current_time = now.strftime("%H:%M")
    st.info(f"📅 **営業日**: {business_date} | ⏰ **現在時刻**: {current_time} | 🔄 **リセット時刻**: 毎朝7:00")
    
    # 1回毎の入力フォーム
    st.write("**1回毎のデータ入力**")
    
    col1, col2 = st.columns(2)
    with col1:
        user_name = st.text_input("入力者名", key="single_user")
    with col2:
        is_final = st.checkbox("最終・追加", key="single_final")
    
    # 店舗名と金額をまとめて入力
    st.write("**店舗名と金額・バックをそのままコピペしてください**")
    combined_input = st.text_area("例:\nザクラブ🟢\n1.3000.❤️", height=100, key="combined_input")
    
    # 処理ボタン
    if st.button("➕ この1回分を追加", key="add_single_talk"):
        if user_name and combined_input.strip():
            # コピペされたデータを解析
            lines = combined_input.strip().splitlines()
            
            if len(lines) >= 2:
                # 1行目: 店舗名
                store_name = lines[0].strip()
                # 2行目: 金額・バック
                content_input = lines[1].strip()
                
                # 金額を解析
                money = parse_money(content_input)
                
                # データを作成
                entry = {
                    "時刻": datetime.datetime.now().strftime("%H:%M"),
                    "入力者": user_name,
                    "店舗名": store_name,
                    "内容": content_input,
                    "金額": money,
                    "最終・追加": "○" if is_final else "－"
                }
                
                # データを累積に追加
                st.session_state.daily_data.append(entry)
                # データを自動保存
                save_data_to_file()
                st.success(f"✅ 追加しました: {user_name} - {store_name} - {money:,}円")
                
            elif len(lines) == 1:
                # 1行だけの場合（店舗名と金額が一緒になっている可能性）
                line = lines[0].strip()
                
                # 金額パターンを探す
                money_patterns = [
                    r'(\d+\s*\.\s*\d+[^0-9]*)',  # 金額部分を抽出
                    r'(\d+\s*\.\s*\d*\s*\.[^0-9]*)',
                    r'(\d+\s*\.\s*\d*[^0-9]*)'
                ]
                
                store_name = line
                content_input = ""
                
                for pattern in money_patterns:
                    match = re.search(pattern, line)
                    if match:
                        content_input = match.group(1).strip()
                        # 店舗名は金額部分を除いた残り
                        store_name = line.replace(content_input, '').strip()
                        break
                
                if content_input:
                    # 金額を解析
                    money = parse_money(content_input)
                    
                    # データを作成
                    entry = {
                        "時刻": datetime.datetime.now().strftime("%H:%M"),
                        "入力者": user_name,
                        "店舗名": store_name,
                        "内容": content_input,
                        "金額": money,
                        "最終・追加": "○" if is_final else "－"
                    }
                    
                    # データを累積に追加
                    st.session_state.daily_data.append(entry)
                    # データを自動保存
                    save_data_to_file()
                    st.success(f"✅ 追加しました: {user_name} - {store_name} - {money:,}円")
                else:
                    st.warning("金額部分が認識できませんでした。2行に分けて入力してください。")
            else:
                st.warning("店舗名と金額・バックを入力してください")
        else:
            st.warning("入力者名と店舗名・金額データを入力してください")
    
    # 今日の累積データ表示
    if st.session_state.daily_data:
        st.subheader(f"📅 本日の累積データ ({st.session_state.today_date})")
        df_today = pd.DataFrame(st.session_state.daily_data)
        st.dataframe(df_today)
        
        # 今日の合計
        total_today = df_today['金額'].sum()
        final_today = df_today[df_today['最終・追加'] == '○']['金額'].sum()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💰 今日の総合計", f"{total_today:,}円")
        with col2:
            st.metric("🎯 最終・追加合計", f"{final_today:,}円")
        
        # 店舗別集計
        if not df_today.empty:
            store_summary = df_today.groupby('店舗名')['金額'].sum().reset_index()
            store_summary = store_summary.sort_values('金額', ascending=False)
            st.subheader("🏪 店舗別合計")
            st.dataframe(store_summary)
        
        # データ管理ボタン
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 今日分をExcel保存", key="save_excel"):
                # 簡単なExcel保存機能
                filename = f"daily_data_{st.session_state.today_date}.xlsx"
                df_today.to_excel(filename, index=False)
                st.success(f"✅ {filename} として保存しました")
        with col2:
            if st.button("💾 今日分を記録保持", key="save_daily"):
                # 今日のデータを保存済みデータに追加
                st.session_state.saved_daily_data[st.session_state.today_date] = st.session_state.daily_data.copy()
                st.success(f"✅ {st.session_state.today_date} のデータを記録保持しました")
        with col3:
            if st.button("🗑️ 今日のデータをリセット", key="reset_today"):
                st.session_state.daily_data = []
                st.rerun()
    else:
        st.info("まだデータがありません。上記から1回分のデータを入力してください。")
    
    # 過去の記録表示
    if st.session_state.saved_daily_data:
        st.markdown("---")
        st.subheader("📚 過去の記録（最大3日間保持）")
        
        # 保存されているデータの日数を表示
        saved_count = len(st.session_state.saved_daily_data)
        if saved_count > 0:
            oldest_date = min(st.session_state.saved_daily_data.keys())
            newest_date = max(st.session_state.saved_daily_data.keys())
            st.write(f"**保存中**: {saved_count}日分のデータ ({oldest_date} ～ {newest_date})")
        
        # 日付選択
        saved_dates = list(st.session_state.saved_daily_data.keys())
        saved_dates.sort(reverse=True)  # 新しい日付順
        
        selected_date = st.selectbox("表示する日付を選択", saved_dates, key="select_date")
        
        if selected_date and selected_date in st.session_state.saved_daily_data:
            past_data = st.session_state.saved_daily_data[selected_date]
            df_past = pd.DataFrame(past_data)
            
            st.subheader(f"📅 {selected_date} の記録")
            st.dataframe(df_past)
            
            # 過去データの統計
            if not df_past.empty:
                total_past = df_past['金額'].sum()
                final_past = df_past[df_past['最終・追加'] == '○']['金額'].sum()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("💰 その日の総合計", f"{total_past:,}円")
                with col2:
                    st.metric("🎯 最終・追加合計", f"{final_past:,}円")
                
                # 店舗別集計
                store_summary_past = df_past.groupby('店舗名')['金額'].sum().reset_index()
                store_summary_past = store_summary_past.sort_values('金額', ascending=False)
                st.subheader("🏪 店舗別合計")
                st.dataframe(store_summary_past)
            
            # 過去データの操作
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"💾 {selected_date}をExcel保存", key=f"save_past_{selected_date}"):
                    filename = f"daily_data_{selected_date}.xlsx"
                    df_past.to_excel(filename, index=False)
                    st.success(f"✅ {filename} として保存しました")
            with col2:
                if st.button(f"🗑️ {selected_date}の記録を削除", key=f"delete_past_{selected_date}"):
                    del st.session_state.saved_daily_data[selected_date]
                    st.rerun()
        
        # 全体データ管理
        st.markdown("---")
        st.subheader("🔧 データ管理")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 全期間をExcel一括保存", key="save_all_excel"):
                # 全データを一つのExcelファイルに保存
                all_data = []
                for date, data in st.session_state.saved_daily_data.items():
                    for entry in data:
                        entry_copy = entry.copy()
                        entry_copy["営業日"] = date
                        all_data.append(entry_copy)
                
                if all_data:
                    df_all = pd.DataFrame(all_data)
                    # 列の順序を調整
                    columns_order = ["営業日", "時刻", "入力者", "店舗名", "内容", "金額", "最終・追加"]
                    df_all = df_all[columns_order]
                    
                    filename = f"all_daily_data_{business_date}.xlsx"
                    df_all.to_excel(filename, index=False)
                    st.success(f"✅ {filename} として{len(all_data)}件のデータを保存しました")
                else:
                    st.warning("保存するデータがありません")
        
        with col2:
            # 手動でのデータクリーンアップ
            if st.button("🧹 3日以前のデータを手動削除", key="manual_cleanup"):
                current_date = datetime.datetime.strptime(business_date, "%Y-%m-%d")
                cutoff_date = current_date - datetime.timedelta(days=3)
                
                dates_to_remove = []
                for saved_date in st.session_state.saved_daily_data.keys():
                    saved_datetime = datetime.datetime.strptime(saved_date, "%Y-%m-%d")
                    if saved_datetime < cutoff_date:
                        dates_to_remove.append(saved_date)
                
                if dates_to_remove:
                    for date_to_remove in dates_to_remove:
                        del st.session_state.saved_daily_data[date_to_remove]
                    st.success(f"✅ {len(dates_to_remove)}日分の古いデータを削除しました: {', '.join(dates_to_remove)}")
                    st.rerun()
                else:
                    st.info("削除対象の古いデータはありません")
        
        with col3:
            # 全データクリア（危険操作）
            if st.button("⚠️ 全記録を削除", key="clear_all_data"):
                if st.session_state.saved_daily_data:
                    count = len(st.session_state.saved_daily_data)
                    st.session_state.saved_daily_data = {}
                    st.warning(f"⚠️ {count}日分の全記録を削除しました")
                    st.rerun()
                else:
                    st.info("削除する記録がありません")



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

with tab1:
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
