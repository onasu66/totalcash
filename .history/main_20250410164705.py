import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import random

def scrape_host_clubs():
    url = "https://www.host2.jp/shop/1_all.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        # リクエスト前にランダムな遅延を追加
        time.sleep(random.uniform(1, 3))
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        clubs = []
        
        # 店舗情報を含む要素を取得
        shop_elements = soup.find_all('div', class_='shop-list-item')
        
        for shop in shop_elements:
            try:
                # 店舗名
                name = shop.find('h3', class_='shop-name').text.strip()
                
                # 店舗URL
                shop_url = shop.find('a')['href']
                if not shop_url.startswith('http'):
                    shop_url = f"https://www.host2.jp{shop_url}"
                
                # 電話番号
                tel = shop.find('div', class_='shop-tel').text.strip()
                
                # 営業時間
                hours = shop.find('div', class_='shop-hours').text.strip() if shop.find('div', class_='shop-hours') else '未設定'
                
                # 定休日
                holiday = shop.find('div', class_='shop-holiday').text.strip() if shop.find('div', class_='shop-holiday') else '未設定'
                
                # 初回料金
                first_visit_fee = shop.find('div', class_='shop-first-visit').text.strip() if shop.find('div', class_='shop-first-visit') else '未設定'
                
                clubs.append({
                    '店舗名': name,
                    '店舗URL': shop_url,
                    '電話番号': tel,
                    '営業時間': hours,
                    '定休日': holiday,
                    '初回料金': first_visit_fee
                })
                
                print(f"店舗情報を取得: {name}")
                
                # 各店舗の処理後にランダムな遅延を追加
                time.sleep(random.uniform(0.5, 1.5))
                
            except Exception as e:
                print(f"店舗情報の取得中にエラーが発生しました: {e}")
                continue
        
        if not clubs:
            print("店舗情報が見つかりませんでした。サイトの構造が変更された可能性があります。")
            return
        
        # DataFrameに変換
        df = pd.DataFrame(clubs)
        
        # Excelファイルに出力
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'host_clubs_{timestamp}.xlsx'
        df.to_excel(filename, index=False)
        print(f"データを {filename} に保存しました。")
        print(f"合計 {len(clubs)} 件の店舗情報を取得しました。")
        
    except requests.exceptions.RequestException as e:
        print(f"リクエスト中にエラーが発生しました: {e}")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    scrape_host_clubs()
