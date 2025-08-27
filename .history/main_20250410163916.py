import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

def scrape_host_clubs():
    url = "https://www.host2.jp/shop/1_all.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    clubs = []
    
    # 店舗情報を含む要素を取得
    shop_elements = soup.find_all('div', class_='shop-info')
    
    for shop in shop_elements:
        try:
            # 店舗名
            name = shop.find('h3').text.strip()
            
            # 店舗URL
            shop_url = shop.find('a')['href']
            if not shop_url.startswith('http'):
                shop_url = f"https://www.host2.jp{shop_url}"
            
            # 電話番号
            tel = shop.find('p', class_='tel').text.strip()
            
            # 営業時間
            hours = shop.find('p', class_='hours').text.strip()
            
            # 定休日
            holiday = shop.find('p', class_='holiday').text.strip()
            
            # 初回料金
            first_visit_fee = shop.find('p', class_='first-visit-fee').text.strip()
            
            clubs.append({
                '店舗名': name,
                '店舗URL': shop_url,
                '電話番号': tel,
                '営業時間': hours,
                '定休日': holiday,
                '初回料金': first_visit_fee
            })
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            continue
    
    # DataFrameに変換
    df = pd.DataFrame(clubs)
    
    # Excelファイルに出力
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'host_clubs_{timestamp}.xlsx'
    df.to_excel(filename, index=False)
    print(f"データを {filename} に保存しました。")

if __name__ == "__main__":
    scrape_host_clubs()
