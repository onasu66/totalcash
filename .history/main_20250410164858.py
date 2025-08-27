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
        
        # デバッグ用：レスポンスの内容を確認
        print("レスポンスステータスコード:", response.status_code)
        print("レスポンスの最初の500文字:")
        print(response.text[:500])
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # デバッグ用：すべてのdiv要素のクラス名を表示
        print("\n見つかったdiv要素のクラス名:")
        for div in soup.find_all('div'):
            if div.get('class'):
                print(div['class'])
        
        clubs = []
        
        # 店舗情報を含む要素を取得（暫定的にすべてのdivを表示）
        shop_elements = soup.find_all('div')
        print(f"\n見つかったdiv要素の数: {len(shop_elements)}")
        
        for shop in shop_elements:
            try:
                # 店舗名
                name = shop.find('h3')
                if name:
                    name = name.text.strip()
                    print(f"店舗名を見つけました: {name}")
                
                # 電話番号
                tel = shop.find(text=lambda t: 'TEL' in t if t else False)
                if tel:
                    print(f"電話番号を見つけました: {tel}")
                
            except Exception as e:
                print(f"要素の解析中にエラーが発生しました: {e}")
                continue
        
        if not clubs:
            print("\n店舗情報が見つかりませんでした。サイトの構造が変更された可能性があります。")
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
