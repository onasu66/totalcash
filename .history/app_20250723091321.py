from flask import Flask, render_template, request, jsonify, send_file
import os
import threading
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
import random
import re

app = Flask(__name__)

# グローバル変数でスクレイピング状態を管理
scraping_status = {
    'is_running': False,
    'progress': 0,
    'total': 0,
    'current_url': '',
    'message': '',
    'filename': '',
    'completed': False
}

# スクレイピング結果を保存
scraping_results = {
    'shop_data': [],
    'staff_data': [],
    'timestamp': None
}

def get_shop_urls():
    url = "https://www.host2.jp/shop/1_all.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        shop_urls = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/shop/' in href and '/index.html' in href:
                if not href.startswith('http'):
                    href = f"https://www.host2.jp{href}"
                shop_urls.append(href)
        
        return list(set(shop_urls))
    
    except Exception as e:
        return []

def get_shop_info(shop_url, include_staff=False):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        time.sleep(random.uniform(1, 2))
        response = requests.get(shop_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 店舗名を取得
        path_nav = soup.find('nav', class_='path')
        if not path_nav:
            return None
        
        shop_name = path_nav.find_all('li')[-2].text.strip()
        
        # 電話番号を取得
        tel = None
        tel_pattern = re.compile(r'TEL:(\d{2,4}-\d{2,4}-\d{4})')
        for script in soup.find_all('script'):
            if script.string:
                match = tel_pattern.search(script.string)
                if match:
                    tel = match.group(1)
                    break
        
        # システム情報を取得
        system_url = shop_url.replace('/index.html', '/system.html')
        system_response = requests.get(system_url, headers=headers, timeout=10)
        system_response.encoding = 'utf-8'
        system_soup = BeautifulSoup(system_response.text, 'html.parser')
        
        system_table = system_soup.find('div', class_='shop-system-tbl')
        if not system_table:
            return None
        
        info = {
            '店舗名': shop_name,
            '店舗URL': shop_url,
            '電話番号': tel if tel else '未設定'
        }
        
        # イベント情報を抽出
        event_info = extract_event_info(soup)
        if event_info:
            info['イベント情報'] = event_info
        
        # テーブルから情報を取得
        for row in system_table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 2:
                key = cells[0].text.strip()
                value = cells[1].text.strip()
                if key == '営業時間':
                    info['営業時間'] = value
                elif key == '定休日':
                    info['定休日'] = value
                elif key == '初回料金':
                    info['初回料金'] = value
        
        # スタッフ情報を取得（オプション）
        if include_staff:
            staff_info = get_staff_info(shop_url, headers)
            if staff_info:
                info['スタッフ情報'] = staff_info
            else:
                # スタッフページが見つからない場合、メインページからスタッフ情報を探す
                main_page_staff = extract_staff_from_main_page(soup)
                if main_page_staff:
                    info['スタッフ情報'] = main_page_staff
                    print(f"メインページからスタッフ情報を取得: {shop_url}")
        
        return info
    
    except Exception as e:
        return None

def get_staff_info(shop_url, headers):
    """スタッフ情報を取得する関数"""
    try:
        # まずスタッフリストページから個別スタッフページへのリンクを取得
        staff_links = get_staff_links(shop_url, headers)
        
        if staff_links:
            # 個別スタッフページから詳細情報を取得
            return get_staff_details_from_links(staff_links, headers)
        
        # スタッフリストページが見つからない場合、従来の方法を試す
        staff_url_patterns = [
            shop_url.replace('/index.html', '/staff.html'),
            shop_url.replace('/index.html', '/member.html'),
            shop_url.replace('/index.html', '/cast.html'),
            shop_url.replace('/index.html', '/girls.html'),
            shop_url.replace('/index.html', '/staff/'),
            shop_url.replace('/index.html', '/member/'),
            shop_url.replace('/index.html', '/cast/'),
            shop_url.replace('/index.html', '/girls/'),
        ]
        
        # 各URLパターンを試す
        for staff_url in staff_url_patterns:
            try:
                time.sleep(random.uniform(0.3, 0.8))
                response = requests.get(staff_url, headers=headers, timeout=10)
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    break  # 成功したらループを抜ける
                elif response.status_code == 404:
                    continue  # 404の場合は次のパターンを試す
                else:
                    response.raise_for_status()
            except requests.exceptions.RequestException:
                continue  # エラーの場合は次のパターンを試す
        else:
            # すべてのパターンが失敗した場合
            print(f"スタッフページが見つかりません: {shop_url} (試行パターン: {len(staff_url_patterns)}個)")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        staff_list = []
        
        # より多くのスタッフ情報パターンを試す
        staff_selectors = [
            # 一般的なスタッフコンテナ
            ['div', 'section'],
            # より具体的なクラス名
            ['div', 'section', 'article'],
            # 画像ベースの検索
            ['img'],
        ]
        
        for selector_type in staff_selectors:
            if selector_type == ['img']:
                # 画像ベースの検索
                staff_images = soup.find_all('img', src=lambda x: x and any(keyword in x.lower() for keyword in ['staff', 'member', 'cast', 'girl', 'photo', 'image']))
                for img in staff_images:
                    parent = img.find_parent(['div', 'section', 'article'])
                    if parent:
                        staff_name = parent.find(['h3', 'h4', 'p', 'span', 'div'])
                        if staff_name:
                            staff_text = parent.get_text().strip()
                            height = extract_height(staff_text)
                            staff_list.append({
                                '名前': staff_name.text.strip(),
                                '画像URL': img.get('src', ''),
                                '身長': height,
                                '詳細': staff_text[:200] + '...' if len(staff_text) > 200 else staff_text
                            })
            else:
                # クラス名ベースの検索
                staff_containers = soup.find_all(selector_type, class_=lambda x: x and any(keyword in x.lower() for keyword in ['staff', 'member', 'cast', 'girl', 'profile', 'info']))
                
                for container in staff_containers:
                    staff_items = container.find_all(['div', 'article', 'section'], recursive=False)
                    if not staff_items:
                        # 直接コンテナ内のテキストを処理
                        staff_text = container.get_text().strip()
                        name_elem = container.find(['h3', 'h4', 'p', 'span', 'div'])
                        img_elem = container.find('img')
                        
                        if name_elem:
                            height = extract_height(staff_text)
                            staff_list.append({
                                '名前': name_elem.text.strip(),
                                '画像URL': img_elem.get('src', '') if img_elem else '',
                                '身長': height,
                                '詳細': staff_text[:200] + '...' if len(staff_text) > 200 else staff_text
                            })
                    else:
                        for item in staff_items:
                            name_elem = item.find(['h3', 'h4', 'p', 'span', 'div'])
                            img_elem = item.find('img')
                            
                            if name_elem:
                                staff_text = item.get_text().strip()
                                height = extract_height(staff_text)
                                staff_info = {
                                    '名前': name_elem.text.strip(),
                                    '画像URL': img_elem.get('src', '') if img_elem else '',
                                    '身長': height,
                                    '詳細': staff_text[:200] + '...' if len(staff_text) > 200 else staff_text
                                }
                                staff_list.append(staff_info)
        
        # 重複を除去（名前で判定）
        unique_staff = []
        seen_names = set()
        for staff in staff_list:
            if staff['名前'] not in seen_names:
                unique_staff.append(staff)
                seen_names.add(staff['名前'])
        
        return unique_staff if unique_staff else None
        
    except Exception as e:
        print(f"スタッフ情報取得エラー ({shop_url}): {e}")
        return None

def extract_height(text):
    """テキストから身長を抽出する関数"""
    # 身長のパターンを検索（より多くのパターンに対応）
    height_patterns = [
        r'身長[：:]\s*(\d{3})cm',  # 身長：183cm
        r'身長[：:]\s*(\d{3})㎝',  # 身長：183㎝
        r'身長[：:]\s*(\d{3})',    # 身長：183
        r'T[：:]\s*(\d{3})cm',     # T: 183cm
        r'T[：:]\s*(\d{3})㎝',     # T: 183㎝
        r'T[：:]\s*(\d{3})',       # T: 183
        r'身長\s*(\d{3})cm',       # 身長 183cm
        r'身長\s*(\d{3})㎝',       # 身長 183㎝
        r'身長\s*(\d{3})',         # 身長 183
        r'T\s*(\d{3})cm',          # T 183cm
        r'T\s*(\d{3})㎝',          # T 183㎝
        r'T\s*(\d{3})',            # T 183
        r'(\d{3})cm',              # 183cm
        r'(\d{3})㎝',              # 183㎝（全角）
        r'(\d{3})センチ',          # 183センチ
        r'(\d{3})',                # 単純に3桁の数字（最後の手段）
    ]
    
    # デバッグ用：身長らしいテキストをログ出力
    height_keywords = ['身長', 'cm', '㎝', 'センチ', 't:', 't：']
    if any(keyword in text.lower() for keyword in height_keywords):
        print(f"身長抽出デバッグ - テキスト: {text[:100]}...")
    
    for pattern in height_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            height = int(match.group(1))
            # 身長の妥当性チェック（140cm-200cmの範囲に拡張）
            if 140 <= height <= 200:
                print(f"身長抽出成功: {height}cm (パターン: {pattern})")
                return height
    
    return None
    
    for pattern in height_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            height = int(match.group(1))
            # 身長の妥当性チェック（140cm-200cmの範囲に拡張）
            if 140 <= height <= 200:
                return height
    
    return None

def extract_event_info(soup):
    """イベント情報を抽出する関数"""
    try:
        event_info = []
        
        # イベント関連のキーワード
        event_keywords = [
            '初回', 'デー', 'イベント', 'キャンペーン', '特典', '割引', 
            'セール', '期間限定', '新規', 'オープン', '記念', '特別',
            '無料', '料金', '価格', 'サービス', 'プラン'
        ]
        
        # ページ全体のテキストを取得
        page_text = soup.get_text()
        
        # イベント情報を含む要素を探す
        event_elements = soup.find_all(['div', 'section', 'p', 'span'], 
                                      string=lambda text: text and any(keyword in text for keyword in event_keywords))
        
        for element in event_elements:
            text = element.get_text().strip()
            if len(text) > 10 and len(text) < 500:  # 適切な長さのテキストのみ
                event_info.append(text)
        
        # 日付情報も抽出
        date_patterns = [
            r'\d{1,2}月\d{1,2}日',
            r'\d{4}年\d{1,2}月\d{1,2}日',
            r'\d{1,2}/\d{1,2}',
            r'\d{1,2}-\d{1,2}',
            r'今日', '明日', '今月', '来月'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, page_text)
            for match in matches:
                if match not in event_info:
                    event_info.append(f"日付: {match}")
        
        return event_info if event_info else None
        
    except Exception as e:
        return None

def extract_staff_from_main_page(soup):
    """メインページからスタッフ情報を抽出する関数"""
    try:
        staff_list = []
        
        # メインページでスタッフ情報を探す
        staff_selectors = [
            # スタッフ紹介セクション
            ['div', 'section'],
            # 画像ベースの検索
            ['img'],
            # 個別スタッフページの構造
            ['h1', 'h2', 'h3'],
        ]
        
        for selector_type in staff_selectors:
            if selector_type == ['img']:
                # スタッフ画像を探す
                staff_images = soup.find_all('img', src=lambda x: x and any(keyword in x.lower() for keyword in ['staff', 'member', 'cast', 'girl', 'photo', 'image', 'profile']))
                for img in staff_images:
                    parent = img.find_parent(['div', 'section', 'article'])
                    if parent:
                        staff_name = parent.find(['h3', 'h4', 'p', 'span', 'div'])
                        if staff_name:
                            staff_text = parent.get_text().strip()
                            height = extract_height(staff_text)
                            staff_list.append({
                                '名前': staff_name.text.strip(),
                                '画像URL': img.get('src', ''),
                                '身長': height,
                                '詳細': staff_text[:200] + '...' if len(staff_text) > 200 else staff_text
                            })
            elif selector_type == ['h1', 'h2', 'h3']:
                # 個別スタッフページの構造に対応
                for tag in ['h1', 'h2', 'h3']:
                    headers = soup.find_all(tag)
                    for header in headers:
                        header_text = header.get_text().strip()
                        # スタッフ名らしいテキストを探す
                        if len(header_text) > 2 and len(header_text) < 50:
                            # ヘッダーの周辺テキストを取得
                            parent = header.find_parent(['div', 'section', 'article'])
                            if parent:
                                parent_text = parent.get_text().strip()
                                height = extract_height(parent_text)
                                if height:  # 身長が見つかった場合のみ追加
                                    staff_list.append({
                                        '名前': header_text,
                                        '画像URL': '',
                                        '身長': height,
                                        '詳細': parent_text[:300] + '...' if len(parent_text) > 300 else parent_text
                                    })
            else:
                # スタッフ情報を含む要素を探す
                staff_containers = soup.find_all(selector_type, class_=lambda x: x and any(keyword in x.lower() for keyword in ['staff', 'member', 'cast', 'girl', 'profile', 'info', 'introduction']))
                
                for container in staff_containers:
                    staff_items = container.find_all(['div', 'article', 'section'], recursive=False)
                    if not staff_items:
                        # 直接コンテナ内のテキストを処理
                        staff_text = container.get_text().strip()
                        name_elem = container.find(['h3', 'h4', 'p', 'span', 'div'])
                        img_elem = container.find('img')
                        
                        if name_elem and len(staff_text) > 20:
                            height = extract_height(staff_text)
                            staff_list.append({
                                '名前': name_elem.text.strip(),
                                '画像URL': img_elem.get('src', '') if img_elem else '',
                                '身長': height,
                                '詳細': staff_text[:200] + '...' if len(staff_text) > 200 else staff_text
                            })
                    else:
                        for item in staff_items:
                            name_elem = item.find(['h3', 'h4', 'p', 'span', 'div'])
                            img_elem = item.find('img')
                            
                            if name_elem:
                                staff_text = item.get_text().strip()
                                height = extract_height(staff_text)
                                staff_info = {
                                    '名前': name_elem.text.strip(),
                                    '画像URL': img_elem.get('src', '') if img_elem else '',
                                    '身長': height,
                                    '詳細': staff_text[:200] + '...' if len(staff_text) > 200 else staff_text
                                }
                                staff_list.append(staff_info)
        
        # 重複を除去（名前で判定）
        unique_staff = []
        seen_names = set()
        for staff in staff_list:
            if staff['名前'] not in seen_names:
                unique_staff.append(staff)
                seen_names.add(staff['名前'])
        
        return unique_staff if unique_staff else None
        
    except Exception as e:
        print(f"メインページスタッフ情報取得エラー: {e}")
        return None

def get_staff_links(shop_url, headers):
    """スタッフリストページから個別スタッフページへのリンクを取得"""
    try:
        # スタッフリストページのURLパターンを試す
        staff_list_patterns = [
            shop_url.replace('/index.html', '/staff.html'),
            shop_url.replace('/index.html', '/member.html'),
            shop_url.replace('/index.html', '/cast.html'),
            shop_url,  # メインページ自体がスタッフリストの場合
        ]
        
        for staff_list_url in staff_list_patterns:
            try:
                time.sleep(random.uniform(0.3, 0.8))
                response = requests.get(staff_list_url, headers=headers, timeout=10)
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # スタッフリンクを探す
                    staff_links = []
                    
                    # リンクからスタッフページを探す
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        link_text = link.get_text().strip()
                        
                        # スタッフ名らしいリンクを探す
                        if (len(link_text) > 1 and len(link_text) < 20 and 
                            not any(keyword in link_text.lower() for keyword in ['home', 'top', 'menu', 'staff', 'member', 'cast', 'girls', '店舗', 'システム', 'スケジュール', 'トピックス', 'グラビア', '動画', '初回特典', 'ブログ', '求人'])):
                            
                            # 相対URLを絶対URLに変換
                            if href.startswith('/'):
                                full_url = f"https://www.host2.jp{href}"
                            elif href.startswith('http'):
                                full_url = href
                            else:
                                # 相対パスの場合
                                base_url = '/'.join(staff_list_url.split('/')[:-1])
                                full_url = f"{base_url}/{href}"
                            
                            staff_links.append({
                                'name': link_text,
                                'url': full_url
                            })
                    
                    if staff_links:
                        print(f"スタッフリンクを{len(staff_links)}個発見: {staff_list_url}")
                        return staff_links
                        
            except Exception as e:
                continue
        
        return None
        
    except Exception as e:
        print(f"スタッフリンク取得エラー: {e}")
        return None

def get_staff_details_from_links(staff_links, headers):
    """個別スタッフページから詳細情報を取得"""
    try:
        all_staff = []
        
        for i, staff_link in enumerate(staff_links[:10]):  # 最初の10名のみ（テスト用）
            try:
                print(f"スタッフ情報取得中: {staff_link['name']} ({i+1}/{min(len(staff_links), 10)})")
                
                time.sleep(random.uniform(0.5, 1.0))
                response = requests.get(staff_link['url'], headers=headers, timeout=10)
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # スタッフ情報を抽出
                    staff_text = soup.get_text()
                    height = extract_height(staff_text)
                    
                    # より詳細な情報を抽出
                    profile_info = extract_profile_info(soup)
                    
                    # 画像URLを探す
                    img_url = ""
                    img_elem = soup.find('img', src=True)
                    if img_elem:
                        img_src = img_elem['src']
                        if img_src.startswith('/'):
                            img_url = f"https://www.host2.jp{img_src}"
                        elif img_src.startswith('http'):
                            img_url = img_src
                        else:
                            base_url = '/'.join(staff_link['url'].split('/')[:-1])
                            img_url = f"{base_url}/{img_src}"
                    
                    staff_info = {
                        '名前': staff_link['name'],
                        '画像URL': img_url,
                        '身長': height,
                        '詳細': staff_text[:300] + '...' if len(staff_text) > 300 else staff_text,
                        '個別URL': staff_link['url'],
                        **profile_info
                    }
                    
                    all_staff.append(staff_info)
                    
                    if height:
                        print(f"  ✓ 身長: {height}cm")
                    else:
                        print(f"  ✗ 身長情報なし")
                        
                else:
                    print(f"  ✗ HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  ✗ エラー: {e}")
                continue
        
        return all_staff if all_staff else None
        
    except Exception as e:
        print(f"スタッフ詳細取得エラー: {e}")
        return None

def extract_profile_info(soup):
    """プロフィール情報を抽出する関数"""
    try:
        profile_info = {}
        
        # 誕生日、血液型、星座などの情報を抽出
        profile_patterns = {
            '誕生日': [
                r'誕生日[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日)',
                r'誕生日[：:]\s*(\d{1,2}月\d{1,2}日)',
                r'生年月日[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日)',
            ],
            '血液型': [
                r'血液型[：:]\s*([ABO]型)',
                r'血液型[：:]\s*([ABO]型)',
            ],
            '星座': [
                r'星座[：:]\s*([ぁ-んァ-ン一-龯]+座)',
                r'星座[：:]\s*([ぁ-んァ-ン一-龯]+座)',
            ],
            '年齢': [
                r'(\d{1,2})才',
                r'(\d{1,2})歳',
                r'年齢[：:]\s*(\d{1,2})',
            ]
        }
        
        text = soup.get_text()
        
        for info_type, patterns in profile_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    profile_info[info_type] = match.group(1)
                    break
        
        return profile_info
        
    except Exception as e:
        print(f"プロフィール情報抽出エラー: {e}")
        return {}

def scrape_host_clubs_async():
    global scraping_status, scraping_results
    
    try:
        scraping_status['message'] = '店舗URLの取得を開始します...'
        shop_urls = get_shop_urls()
        
        if not shop_urls:
            scraping_status['message'] = '店舗URLの取得に失敗しました。'
            scraping_status['is_running'] = False
            return
        
        # キーワードフィルタリング
        search_keyword = scraping_status.get('search_keyword', '')
        if search_keyword:
            filtered_urls = []
            for url in shop_urls:
                if search_keyword.lower() in url.lower():
                    filtered_urls.append(url)
            shop_urls = filtered_urls
            scraping_status['message'] = f'キーワード "{search_keyword}" でフィルタリング: {len(shop_urls)}件'
        
        scraping_status['total'] = len(shop_urls)
        scraping_status['message'] = f'{len(shop_urls)}件の店舗URLを取得しました。スクレイピングを開始します...'
        
        clubs = []
        include_staff = scraping_status.get('include_staff', False)
        staff_success_count = 0
        staff_total_count = 0
        
        for i, url in enumerate(shop_urls, 1):
            if not scraping_status['is_running']:
                break
                
            scraping_status['progress'] = i
            scraping_status['current_url'] = url
            
            shop_info = get_shop_info(url, include_staff)
            if shop_info:
                clubs.append(shop_info)
                staff_count = len(shop_info.get('スタッフ情報', [])) if include_staff else 0
                if include_staff:
                    staff_total_count += 1
                    if staff_count > 0:
                        staff_success_count += 1
                scraping_status['message'] = f'成功: {i}/{len(shop_urls)} ({len(clubs)}件取得済み, スタッフ{staff_count}名, スタッフ成功率: {staff_success_count}/{staff_total_count})'
            else:
                scraping_status['message'] = f'失敗: {i}/{len(shop_urls)}'
        
        if clubs:
            # イベントキーワードフィルタリング
            event_keyword = scraping_status.get('event_keyword', '')
            if event_keyword:
                filtered_clubs = []
                for club in clubs:
                    # 店舗情報でイベントキーワードを検索
                    club_text = ' '.join([str(v) for v in club.values() if v and isinstance(v, str)])
                    if event_keyword.lower() in club_text.lower():
                        filtered_clubs.append(club)
                clubs = filtered_clubs
                scraping_status['message'] = f'イベントキーワード "{event_keyword}" でフィルタリング: {len(clubs)}件'
            
            # スタッフ情報がある場合は別シートに保存
            if include_staff:
                # 店舗情報とスタッフ情報を分離
                shop_data = []
                staff_data = []
                min_height = scraping_status.get('min_height')
                
                for club in clubs:
                    shop_info = {k: v for k, v in club.items() if k != 'スタッフ情報'}
                    shop_data.append(shop_info)
                    
                    if 'スタッフ情報' in club and club['スタッフ情報']:
                        for staff in club['スタッフ情報']:
                            # 身長フィルタリング
                            if min_height is not None:
                                staff_height = staff.get('身長')
                                if staff_height is None or staff_height < min_height:
                                    continue
                                # デバッグ情報を追加
                                print(f"身長フィルタ: {staff['名前']} - 身長: {staff_height}cm (閾値: {min_height}cm)")
                            
                            # イベントキーワードフィルタリング（スタッフ情報）
                            if event_keyword:
                                staff_text = ' '.join([str(v) for v in staff.values() if v and isinstance(v, str)])
                                if event_keyword.lower() not in staff_text.lower():
                                    continue
                            
                            staff_info = {
                                '店舗名': club['店舗名'],
                                '店舗URL': club['店舗URL'],
                                **staff
                            }
                            staff_data.append(staff_info)
                
                # 結果をグローバル変数に保存
                scraping_results = {
                    'shop_data': shop_data,
                    'staff_data': staff_data,
                    'timestamp': datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
                }
                
                # Excelファイルに複数シートで保存
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'host_clubs_{timestamp}.xlsx'
                
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    pd.DataFrame(shop_data).to_excel(writer, sheet_name='店舗情報', index=False)
                    if staff_data:
                        pd.DataFrame(staff_data).to_excel(writer, sheet_name='スタッフ情報', index=False)
            else:
                # 通常の店舗情報のみ
                df = pd.DataFrame(clubs)
                
                # 結果をグローバル変数に保存
                scraping_results = {
                    'shop_data': clubs,
                    'staff_data': [],
                    'timestamp': datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
                }
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'host_clubs_{timestamp}.xlsx'
                df.to_excel(filename, index=False)
            
            scraping_status['filename'] = filename
            scraping_status['message'] = f'データを {filename} に保存しました。合計 {len(clubs)} 件の店舗情報を取得しました。'
            scraping_status['completed'] = True
        else:
            scraping_status['message'] = '店舗情報が見つかりませんでした。'
    
    except Exception as e:
        scraping_status['message'] = f'エラーが発生しました: {str(e)}'
    
    finally:
        scraping_status['is_running'] = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    global scraping_status
    
    if scraping_status['is_running']:
        return jsonify({'status': 'error', 'message': 'スクレイピングは既に実行中です。'})
    
    # リクエストからパラメータを取得
    data = request.get_json()
    search_keyword = data.get('search_keyword', '').strip()
    event_keyword = data.get('event_keyword', '').strip()
    include_staff = data.get('include_staff', False)
    min_height = data.get('min_height', None)
    
    # 身長の妥当性チェック
    if min_height is not None:
        try:
            min_height = int(min_height)
            if min_height < 100 or min_height > 200:
                return jsonify({'status': 'error', 'message': '身長は100cm〜200cmの範囲で入力してください。'})
        except ValueError:
            return jsonify({'status': 'error', 'message': '身長は数値で入力してください。'})
    
    # スクレイピング状態をリセット
    scraping_status = {
        'is_running': True,
        'progress': 0,
        'total': 0,
        'current_url': '',
        'message': 'スクレイピングを開始します...',
        'filename': '',
        'completed': False,
        'search_keyword': search_keyword,
        'event_keyword': event_keyword,
        'include_staff': include_staff,
        'min_height': min_height
    }
    
    # バックグラウンドでスクレイピングを実行
    thread = threading.Thread(target=scrape_host_clubs_async)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'success', 'message': 'スクレイピングを開始しました。'})

@app.route('/stop_scraping', methods=['POST'])
def stop_scraping():
    global scraping_status
    scraping_status['is_running'] = False
    scraping_status['message'] = 'スクレイピングを停止しました。'
    return jsonify({'status': 'success', 'message': 'スクレイピングを停止しました。'})

@app.route('/get_status')
def get_status():
    return jsonify(scraping_status)

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_file(filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': 'ファイルが見つかりません。'})

@app.route('/results')
def show_results():
    global scraping_results
    return render_template('results.html', results=scraping_results)

@app.route('/get_results')
def get_results():
    global scraping_results
    return jsonify(scraping_results)

@app.route('/debug_height/<path:url>')
def debug_height(url):
    """身長抽出のデバッグ用エンドポイント"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # URLをデコード
        import urllib.parse
        decoded_url = urllib.parse.unquote(url)
        
        # メインページとスタッフページの両方を試す
        urls_to_try = [
            decoded_url,  # メインページ
            decoded_url.replace('/index.html', '/staff.html'),
            decoded_url.replace('/index.html', '/member.html'),
        ]
        
        all_results = []
        
        for test_url in urls_to_try:
            try:
                response = requests.get(test_url, headers=headers, timeout=10)
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 身長が含まれそうなテキストを抽出
                    height_texts = []
                    for text in soup.stripped_strings:
                        if any(keyword in text.lower() for keyword in ['cm', '㎝', 'センチ', '身長', 't:', 't：']):
                            height_texts.append(text)
                    
                    # 身長抽出テスト
                    test_results = []
                    for text in height_texts[:10]:  # 最初の10個のみ
                        height = extract_height(text)
                        test_results.append({
                            'text': text,
                            'extracted_height': height
                        })
                    
                    # メインページからのスタッフ情報抽出テスト
                    main_staff = extract_staff_from_main_page(soup)
                    
                    all_results.append({
                        'url': test_url,
                        'status': 'success',
                        'height_texts': height_texts,
                        'test_results': test_results,
                        'main_staff': main_staff,
                        'html_preview': soup.get_text()[:1000]  # HTMLの最初の1000文字
                    })
                else:
                    all_results.append({
                        'url': test_url,
                        'status': 'error',
                        'error': f'HTTP {response.status_code}'
                    })
                    
            except Exception as e:
                all_results.append({
                    'url': test_url,
                    'status': 'error',
                    'error': str(e)
                })
        
        return jsonify({
            'original_url': decoded_url,
            'results': all_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 