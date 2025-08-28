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

# スマホ最適化 + コンパクトUIのためのCSS
st.markdown("""
<style>
    /* 全体的な余白を削減 */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 0.5rem;
        padding-left: 1rem;
        padding-right: 1rem;
        font-size: 14px;
        max-width: 100%;
    }

    /* セクション間の余白を削減 */
    .element-container {
        margin-bottom: 0.3rem;
    }

    /* タイトルと見出しの余白削減 */
    h1, h2, h3, h4, h5, h6 {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
        line-height: 1.2 !important;
    }

    /* Streamlitの標準余白を削減 */
    .stMarkdown {
        margin-bottom: 0.3rem;
    }

    /* タブのスタイル調整 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 3px;
        margin-bottom: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 8px;
        color: #262730;
        font-size: 14px;
        font-weight: bold;
        padding: 0 12px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ff6b6b;
        color: white;
    }

    /* ボタンのスタイル調整 */
    .stButton > button {
        height: 35px;
        font-size: 13px;
        font-weight: bold;
        border-radius: 6px;
        margin-bottom: 0.2rem;
    }

    /* 入力フィールドの高さ調整 */
    .stTextInput > div > div > input {
        height: 35px;
        font-size: 14px;
    }
    .stTextArea > div > div > textarea {
        min-height: 70px;
        font-size: 14px;
    }

    /* DataFrameの余白削減 */
    .stDataFrame {
        margin-bottom: 0.3rem;
    }

    /* data_editorの余白削減 */
    .stDataEditor {
        margin-bottom: 0.3rem;
    }

    /* メトリクスの余白削減 */
    .stMetric {
        background-color: #f0f2f6;
        padding: 8px;
        border-radius: 6px;
        margin: 2px;
    }

    /* 区切り線の余白削減 */
    hr {
        margin-top: 0.8rem;
        margin-bottom: 0.8rem;
    }

    /* モバイル対応 */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            font-size: 12px;
            padding: 0 8px;
            height: 35px;
        }
        
        .stButton > button {
            height: 32px;
            font-size: 12px;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title("💰 トーク履歴集計アプリ")

# タブで機能を分割（スマホ優先で1回毎入力を最初に）
tab1, tab2 = st.tabs(["📱 1回毎入力", "📋 一括履歴"])

with tab1:
    st.subheader("📱 1回毎のトーク入力・累積")
    
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
        # 営業日変更を保存
        save_data_to_file()
    

    
    # 1回毎の入力フォーム（スマホ最適化）
    st.write("**📝 データ入力**")
    
    user_name = st.text_input("👤 入力者名", key="single_user", placeholder="例: 田中")
    
    # 店舗名と金額をまとめて入力
    st.write("**🏪 店舗名と金額・バック**")
    combined_input = st.text_area(
        "コピペしてください",
        placeholder="例:\nザクラブ🟢\n1.3000.❤️",
        height=120,
        key="combined_input"
    )
    
    # 処理ボタン（スマホ最適化）
    if st.button("➕ 追加", key="add_single_talk", use_container_width=True, type="primary"):
        if user_name and combined_input.strip():
            # コピペされたデータを解析
            lines = combined_input.strip().splitlines()
            
            if len(lines) == 2:
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
                    "金額": money
                }
                
                # データを累積に追加
                st.session_state.daily_data.append(entry)
                # データを自動保存
                save_data_to_file()
                st.success(f"✅ 追加しました: {user_name} - {store_name} - {money:,}円")
            
            elif len(lines) > 2:
                # 複数ペアの連続入力
                st.info("複数行データを処理中...")
                entries_added = 0
                
                # 金額パターン
                money_patterns = [
                    r'\d+\s*\.\s*\d+',
                    r'\d+\s*\.\s*\d*\s*\.',
                    r'\d+\s*\.\s*\d*'
                ]
                
                i = 0
                current_store = None
                
                while i < len(lines):
                    line = lines[i].strip()
                    if not line:
                        i += 1
                        continue
                    
                    # 現在行が金額行かチェック
                    is_money_line = any(re.search(pattern, line) for pattern in money_patterns)
                    
                    if is_money_line:
                        # 金額行の場合
                        if current_store:
                            # 店舗名がある場合、データを作成
                            money = parse_money(line)
                            
                            entry = {
                                "時刻": datetime.datetime.now().strftime("%H:%M"),
                                "入力者": user_name,
                                "店舗名": current_store,
                                "内容": line,
                                "金額": money
                            }
                            
                            st.session_state.daily_data.append(entry)
                            entries_added += 1
                        # current_storeはそのまま維持（連続する金額は同一店舗）
                    else:
                        # 金額行でない場合は店舗名として設定
                        current_store = line
                    
                    i += 1
                
                if entries_added > 0:
                    save_data_to_file()
                    st.success(f"✅ {entries_added}件のデータを追加しました")
                else:
                    st.warning("有効なデータペアが見つかりませんでした。")
                
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
                        "金額": money
                    }
                    
                    # データを累積に追加
                    st.session_state.daily_data.append(entry)
                    # データを自動保存
                    save_data_to_file()
                    st.success(f"✅ 追加しました: {user_name} - {store_name} - {money:,}円")
                else:
                    st.warning("金額部分が認識できませんでした。2行に分けて入力してください。")
            else:
                st.warning("入力データを確認してください。")
        else:
            st.warning("入力者名と店舗名・金額データを入力してください")
    
    # 今日の累積データ表示（スマホ最適化）
    if st.session_state.daily_data:
        st.subheader(f"📅 本日の累積データ ({st.session_state.today_date})")
        
        # データフレーム表示（見やすく整理）
        df_today = pd.DataFrame(st.session_state.daily_data)
        
        # 今日の合計を先に表示
        total_today = df_today['金額'].sum()
        data_count = len(st.session_state.daily_data)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💰 今日の総合計", f"{total_today:,}円")
        with col2:
            st.metric("📊 データ件数", f"{data_count}件")
        
        # データ一覧表示（内部スクロール＋行内削除ボタン）
        st.subheader("📋 データ一覧")
        
        # データを表示（セル内削除ボタン付きエディタ）
        if len(st.session_state.daily_data) > 0:
            # データエディタ用のデータフレーム作成
            editor_df = df_today[['時刻', '入力者', '店舗名', '金額', '内容']].copy()
            editor_df['金額'] = editor_df['金額'].apply(lambda x: f"{x:,}円")
            
            # 削除用の列を追加
            editor_df['🗑️ 削除'] = False  # チェックボックス列
            
            # データエディタ（セル内インタラクション可能）
            edited_df = st.data_editor(
                editor_df,
                use_container_width=True,
                hide_index=True,
                height=300,
                column_config={
                    "時刻": st.column_config.TextColumn("🕐 時刻", disabled=True),
                    "入力者": st.column_config.TextColumn("👤 入力者", disabled=True),
                    "店舗名": st.column_config.TextColumn("🏪 店舗名", disabled=True),
                    "金額": st.column_config.TextColumn("💰 金額", disabled=True),
                    "内容": st.column_config.TextColumn("📝 内容", disabled=True),
                    "🗑️ 削除": st.column_config.CheckboxColumn(
                        "🗑️ 削除",
                        help="削除する行にチェックを入れてください",
                        default=False,
                        width="small"
                    )
                },
                key="data_editor"
            )
            
            # 削除処理
            if edited_df is not None:
                # 削除にチェックが入った行を特定
                delete_indices = edited_df[edited_df['🗑️ 削除'] == True].index.tolist()
                
                if delete_indices:
                    # 削除確認
                    if st.button(f"🗑️ 選択した{len(delete_indices)}件を削除", type="primary"):
                        # 逆順で削除（インデックスがずれないように）
                        for idx in sorted(delete_indices, reverse=True):
                            if idx < len(st.session_state.daily_data):
                                st.session_state.daily_data.pop(idx)
                        
                        save_data_to_file()
                        st.success(f"{len(delete_indices)}件のデータを削除しました")
                        st.rerun()
            
            # 使い方説明
            st.info("💡 **使い方**: 削除したい行の「🗑️ 削除」列にチェックを入れて、削除ボタンをクリックしてください")
        else:
            st.info("まだデータがありません。")
        
        # 店舗別集計
        if not df_today.empty:
            store_summary = df_today.groupby('店舗名')['金額'].sum().reset_index()
            store_summary = store_summary.sort_values('金額', ascending=False)
            st.subheader("🏪 店舗別合計")
            st.dataframe(store_summary, use_container_width=True, hide_index=True)
            
            # 入力者毎の店舗集計（タブ化）
            st.subheader("👤 入力者毎の詳細")
            
            # ユニークな入力者を取得
            users = df_today['入力者'].unique()
            
            if len(users) > 0:
                # タブを作成
                user_tabs = st.tabs([f"👤 {user}" for user in users])
                
                for i, user in enumerate(users):
                    with user_tabs[i]:
                        # その入力者のデータをフィルタ
                        user_data = df_today[df_today['入力者'] == user]
                        
                        st.write(f"**{user}さんの入力内容**")
                        
                        # 店舗ごとにグループ化してコンパクト表示
                        stores = user_data['店舗名'].unique()
                        
                        for store in stores:
                            # 各店舗のデータをフィルタ
                            store_data = user_data[user_data['店舗名'] == store]
                            
                            # カスタムCSSでコンパクトな表示
                            st.markdown(f"""
                            <div style="
                                background-color: #f8f9fa; 
                                border-left: 4px solid #0066cc; 
                                padding: 8px 12px; 
                                margin: 8px 0 4px 0; 
                                border-radius: 4px;
                                font-weight: bold;
                                font-size: 14px;
                            ">
                                🏪 {store}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # その店舗の内容を一行ずつコンパクトに表示
                            for _, row in store_data.iterrows():
                                st.markdown(f"""
                                <div style="
                                    background-color: white;
                                    border: 1px solid #e9ecef;
                                    padding: 6px 12px;
                                    margin: 2px 0;
                                    border-radius: 3px;
                                    font-size: 13px;
                                    line-height: 1.2;
                                ">
                                    {row['内容']}
                                </div>
                                """, unsafe_allow_html=True)
        
        # データ管理機能
        st.markdown("---")
        st.subheader("📊 データ管理")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📄 Googleシート形式でダウンロード", key="download_csv", use_container_width=True):
                # CSV形式でダウンロード
                csv_data = df_today.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="💾 CSVファイルをダウンロード",
                    data=csv_data,
                    file_name=f"daily_data_{st.session_state.today_date}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col2:
            if st.button("💾 今日分を記録保持", key="save_daily", use_container_width=True):
                # 今日のデータを保存済みデータに追加
                st.session_state.saved_daily_data[st.session_state.today_date] = st.session_state.daily_data.copy()
                # データを自動保存
                save_data_to_file()
                st.success(f"✅ {st.session_state.today_date} のデータを記録保持しました")
    
    # 過去2日間の記録表示
    if st.session_state.saved_daily_data:
        st.markdown("---")
        st.subheader("📚 過去2日間の記録")
        
        # 保存されているデータを日付順でソート（新しい順）
        saved_dates = list(st.session_state.saved_daily_data.keys())
        saved_dates.sort(reverse=True)
        
        # 過去2日間のデータのみ表示
        recent_dates = saved_dates[:2]
        
        if recent_dates:
            for date in recent_dates:
                past_data = st.session_state.saved_daily_data[date]
                df_past = pd.DataFrame(past_data)
                
                with st.expander(f"📅 {date} の記録 ({len(past_data)}件)", expanded=False):
                    if not df_past.empty:
                        # 合計金額
                        total_past = df_past['金額'].sum()
                        st.metric("💰 その日の総合計", f"{total_past:,}円")
                        
                        # データ表示（インデックス非表示）
                        st.dataframe(df_past, use_container_width=True, hide_index=True)
                        
                        # ダウンロード機能
                        col1, col2 = st.columns(2)
                        with col1:
                            csv_past = df_past.to_csv(index=False, encoding='utf-8-sig')
                            st.download_button(
                                label=f"📄 {date} CSVダウンロード",
                                data=csv_past,
                                file_name=f"daily_data_{date}.csv",
                                mime="text/csv",
                                key=f"download_{date}",
                                use_container_width=True
                            )
                        
                        with col2:
                            if st.button(f"🗑️ {date}の記録を削除", key=f"delete_{date}", use_container_width=True):
                                del st.session_state.saved_daily_data[date]
                                save_data_to_file()
                                st.rerun()
                    else:
                        st.info("データがありません")
        else:
            st.info("過去2日間の保存データがありません")
    else:
        st.info("まだデータがありません。上記からデータを入力してください。")

with tab2:
    st.subheader("📋 一括トーク履歴処理")
    # テキスト入力
    text_input = st.text_area("一日分のトーク履歴をここに貼り付けてください", height=400)
    
    if st.button("抽出＆集計"):
        if not text_input.strip():
            st.warning("テキストを入力してください")
        else:
            lines = text_input.splitlines()
            pattern = re.compile(r'最終|追加')
            indices = [i for i, line in enumerate(lines) if pattern.search(line)]
            
            # メインデータ（最終・追加）
            main_data = []
            
            # 最終・追加のパターンを処理
            for i in indices:
                # 名前を抽出（最終・追加を含む行から）
                trigger_line = lines[i]
                name_match = re.search(r'\d{1,2}:\d{2}\s+(.+?)\s+.*(?:最終|追加)', trigger_line)
                current_user = name_match.group(1).strip() if name_match else "不明ユーザー"
                
                j = i + 1
                current_store = None
                while j < len(lines) and not re.match(r'\d{1,2}:\d{2}', lines[j]):
                    line = lines[j].strip()
                    
                    # 金額行の判定
                    line_without_time = re.sub(r'\d{1,2}:\d{2}', '', line)
                    money_patterns = [
                        r'\d+\s*\.\s*\d+',
                        r'\d+\s*\.\s*\d*\s*\.',
                        r'\d+\s*\.\s*\d*'
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
                    
                    # 店舗名行の判定
                    elif line:
                        if j + 1 < len(lines):
                            next_line_without_time = re.sub(r'\d{1,2}:\d{2}', '', lines[j + 1])
                            next_is_money = any(re.search(pattern, next_line_without_time) for pattern in money_patterns)
                            if next_is_money:
                                current_store = line
                    j += 1
            
            # DataFrame に変換
            df = pd.DataFrame(main_data)
            
            # === メイン結果 (最終・追加) ===
            st.markdown("---")
            st.markdown("## 📊 メイン集計結果 (最終・追加)")
            
            if not df.empty:
                st.subheader("📋 抽出詳細")
                st.dataframe(df, hide_index=True)

                # 店舗ごとの合計
                store_sum = df.groupby('店舗名')['金額'].sum().reset_index()
                st.subheader("🏪 店舗ごとの合計金額")
                st.dataframe(store_sum, hide_index=True)

                st.subheader("💰 全体合計金額")
                st.write(f"**{df['金額'].sum():,}円**")
            else:
                st.warning("メイン集計データがありません")
