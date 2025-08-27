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
        
        return info
    
    except Exception as e:
        return None

def scrape_host_clubs_async():
    global scraping_status
    
    try:
        scraping_status['message'] = '店舗URLの取得を開始します...'
        shop_urls = get_shop_urls()
        
        if not shop_urls:
            scraping_status['message'] = '店舗URLの取得に失敗しました。'
            scraping_status['is_running'] = False
            return
        
        scraping_status['total'] = len(shop_urls)
        scraping_status['message'] = f'{len(shop_urls)}件の店舗URLを取得しました。スクレイピングを開始します...'
        
        clubs = []
        for i, url in enumerate(shop_urls, 1):
            if not scraping_status['is_running']:
                break
                
            scraping_status['progress'] = i
            scraping_status['current_url'] = url
            
            shop_info = get_shop_info(url)
            if shop_info:
                clubs.append(shop_info)
                scraping_status['message'] = f'成功: {i}/{len(shop_urls)} ({len(clubs)}件取得済み)'
            else:
                scraping_status['message'] = f'失敗: {i}/{len(shop_urls)}'
        
        if clubs:
            df = pd.DataFrame(clubs)
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
    include_staff = data.get('include_staff', False)
    
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
        'include_staff': include_staff
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 