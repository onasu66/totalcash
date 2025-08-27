import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import random
import re

def get_shop_urls():
    url = "https://www.host2.jp/shop/1_all.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        shop_urls = []
        # 店舗リンクを取得
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/shop/' in href and '/index.html' in href:
                if not href.startswith('http'):
                    href = f"https://www.host2.jp{href}"
                shop_urls.append(href)
        
        print(f"取得したURLの例: {shop_urls[:3]}")  # 最初の3つのURLを表示
        return list(set(shop_urls))  # 重複を除去
    
    except Exception as e:
        print(f"店舗URLの取得中にエラーが発生しました: {e}")
        return []

def get_shop_info(shop_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        print(f"\n店舗URLにアクセス: {shop_url}")
        time.sleep(random.uniform(1, 2))
        response = requests.get(shop_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 店舗名を取得
        path_nav = soup.find('nav', class_='path')
        if not path_nav:
            print("パンくずリストが見つかりません")
            return None
        
        shop_name = path_nav.find_all('li')[-2].text.strip()
        print(f"店舗名: {shop_name}")
        
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
        system_table = soup.find('div', class_='shop-system-tbl')
        if not system_table:
            print("システム情報テーブルが見つかりません")
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
        
        print(f"取得した情報: {info}")
        return info
    
    except Exception as e:
        print(f"店舗情報の取得中にエラーが発生しました ({shop_url}): {e}")
        return None

def scrape_host_clubs():
    print("店舗URLの取得を開始します...")
    shop_urls = get_shop_urls()
    print(f"{len(shop_urls)}件の店舗URLを取得しました。")
    
    clubs = []
    for i, url in enumerate(shop_urls[:3], 1):  # 最初の3つのURLのみを処理
        print(f"\n処理中: {i}/{len(shop_urls)}")
        shop_info = get_shop_info(url)
        if shop_info:
            clubs.append(shop_info)
    
    if not clubs:
        print("店舗情報が見つかりませんでした。")
        return
    
    # DataFrameに変換
    df = pd.DataFrame(clubs)
    
    # Excelファイルに出力
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'host_clubs_{timestamp}.xlsx'
    df.to_excel(filename, index=False)
    print(f"データを {filename} に保存しました。")
    print(f"合計 {len(clubs)} 件の店舗情報を取得しました。")

if __name__ == "__main__":
    scrape_host_clubs()
