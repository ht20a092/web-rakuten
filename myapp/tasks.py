from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from django.core.mail import send_mail
from myapp.models import FavoriteProduct
from myapp.views import RAKUTEN_APP_ID, YAHOO_APP_ID, search_products_on_rakuten, search_products_on_yahoo, send_line_notify
import requests
from datetime import datetime, timedelta

def check_favorite_products_price():
    print("Checking favorite products price...")
    favorite_products = FavoriteProduct.objects.all()

    for favorite_product in favorite_products:
        if favorite_product.platform == 'rakuten':
            product = search_products_on_rakuten(item_code=favorite_product.product_id)
        elif favorite_product.platform == 'yahoo':
            product = search_products_on_yahoo(item_code=favorite_product.product_id)

        if product is not None:
            current_price = product['itemPrice']

            if current_price < favorite_product.price:
                message = f"【価格変更】 {favorite_product.name} が {favorite_product.price} 円から {current_price} 円に下がりました。"
                send_line_notify(message)
                favorite_product.price = current_price
                favorite_product.save()
        else:
            print(f"Product with id {favorite_product.product_id} not found.")

def start_scheduler():
    print("Starting scheduler...")  # 追加
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_favorite_products_price, 'interval', hours=1)

    # 1分おきにテストメッセージを送るジョブを追加
    scheduler.add_job(send_test_line_message, 'interval', minutes=1)

    scheduler.start()

# 関数呼び出しの直後に print() ステートメントを追加
start_scheduler()
print("Scheduler started.")  # 追加

# 以下はテスト用のソースコードです
def send_test_line_message():
    print("Sending test LINE message...")
    message = "テストです"
    response = send_line_notify(message)
    if response.status_code != 200:
        print(f"Error sending LINE message: {response.status_code}, {response.text}")